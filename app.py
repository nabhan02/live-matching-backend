from flask import Flask, request, jsonify
from flask_cors import CORS
import csv
import io
import os
import bcrypt
from dotenv import load_dotenv
from database import (
    init_db,
    add_participant,
    get_all_participants,
    get_participant_by_token,
    add_selection,
    get_selections_by_participant,
    clear_selections,
    clear_all_data,
    get_all_matches
)
from matching import run_matching_algorithm

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Get password hash from environment variable
ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH', '').encode('utf-8')

# Initialize database on startup
init_db()

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Admin login endpoint with bcrypt password verification"""
    data = request.json
    password = data.get('password', '')
    
    try:
        if bcrypt.checkpw(password.encode('utf-8'), ADMIN_PASSWORD_HASH):
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid password'}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': 'Authentication error'}), 401

@app.route('/api/admin/upload-csv', methods=['POST'])
def upload_csv():
    """Upload CSV file with participants"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400
    
    try:
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        participants_added = 0
        errors = []
        
        for row in csv_reader:
            participant_id = int(row.get('id', 0))
            first_name = row.get('first_name', '').strip()
            gender = row.get('gender', '').strip().lower()
            email = row.get('email', '').strip()
            
            if not participant_id or not first_name or not gender or not email:
                errors.append(f"Invalid row: {row}")
                continue
            
            if gender not in ['male', 'female']:
                errors.append(f"Invalid gender for ID {participant_id}: {gender}")
                continue
            
            token = add_participant(participant_id, first_name, gender, email)
            if token:
                participants_added += 1
            else:
                errors.append(f"Duplicate ID: {participant_id}")
        
        return jsonify({
            'success': True,
            'participants_added': participants_added,
            'errors': errors
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/participants', methods=['GET'])
def get_participants():
    """Get all participants with their unique links"""
    participants = get_all_participants()
    
    # Add full URL for each participant - pointing to frontend
    frontend_url = 'http://localhost:5173'
    for participant in participants:
        participant['link'] = f"{frontend_url}/select/{participant['unique_token']}"
    
    return jsonify(participants)

@app.route('/api/admin/run-matching', methods=['POST'])
def run_matching():
    """Run the matching algorithm"""
    try:
        num_matches = run_matching_algorithm()
        return jsonify({
            'success': True,
            'matches_found': num_matches
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/matches', methods=['GET'])
def get_matches():
    """Get all matches"""
    matches = get_all_matches()
    return jsonify(matches)

@app.route('/api/admin/clear-all', methods=['POST'])
def clear_all():
    """Clear all data (participants, selections, matches)"""
    try:
        clear_all_data()
        return jsonify({'success': True, 'message': 'All data cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/participant/<token>', methods=['GET'])
def get_participant(token):
    """Get participant info by token"""
    participant = get_participant_by_token(token)
    
    if not participant:
        return jsonify({'error': 'Invalid token'}), 404
    
    # Get all participants for selection (excluding self and same gender)
    all_participants = get_all_participants()
    participant_gender = participant['gender']
    opposite_gender = 'female' if participant_gender == 'male' else 'male'
    
    available_participants = [
        {'id': p['id'], 'first_name': p['first_name']}
        for p in all_participants
        if p['id'] != participant['id'] and p['gender'] == opposite_gender
    ]
    
    # Get current selections with ranks
    current_selections = get_selections_by_participant(participant['id'])
    
    return jsonify({
        'participant': participant,
        'available_participants': available_participants,
        'current_selections': current_selections
    })

@app.route('/api/participant/<token>/selections', methods=['POST'])
def submit_selections(token):
    """Submit participant selections with rankings"""
    participant = get_participant_by_token(token)
    
    if not participant:
        return jsonify({'error': 'Invalid token'}), 404
    
    data = request.json
    selections = data.get('selections', [])  # Array of {id, rank}
    
    try:
        # Clear previous selections
        clear_selections(participant['id'])
        
        # Add new selections with ranks
        for selection in selections:
            selected_id = selection.get('id')
            rank = selection.get('rank', 0)
            add_selection(participant['id'], selected_id, rank)
        
        return jsonify({
            'success': True,
            'message': f'Submitted {len(selections)} selections'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
