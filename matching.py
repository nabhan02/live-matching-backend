from database import (
    get_all_participants,
    get_selections_by_participant,
    add_match,
    clear_matches
)

def find_mutual_matches():
    """
    Find all mutual matches where:
    - Person A selected Person B
    - Person B selected Person A
    
    Returns list of match pairs with ranks
    """
    participants = get_all_participants()
    matches = []
    processed_pairs = set()
    
    for participant in participants:
        participant_id = participant['id']
        their_selections = get_selections_by_participant(participant_id)
        
        # Create a dict for quick rank lookup
        their_selections_dict = {sel['selected_id']: sel['rank'] for sel in their_selections}
        
        for selected_id in their_selections_dict.keys():
            # Check if it's a mutual selection
            reverse_selections = get_selections_by_participant(selected_id)
            reverse_selections_dict = {sel['selected_id']: sel['rank'] for sel in reverse_selections}
            
            if participant_id in reverse_selections_dict:
                # Create a sorted tuple to avoid duplicates
                pair = tuple(sorted([participant_id, selected_id]))
                
                if pair not in processed_pairs:
                    # Get the ranks - participant1 ranked participant2, and vice versa
                    if pair[0] == participant_id:
                        rank1 = their_selections_dict[selected_id]
                        rank2 = reverse_selections_dict[participant_id]
                    else:
                        rank1 = reverse_selections_dict[participant_id]
                        rank2 = their_selections_dict[selected_id]
                    
                    matches.append({
                        'participant1_id': pair[0],
                        'participant2_id': pair[1],
                        'rank1': rank1,
                        'rank2': rank2
                    })
                    processed_pairs.add(pair)
    
    return matches

def run_matching_algorithm():
    """
    Run the matching algorithm and store results in database
    Returns number of matches found
    """
    # Clear previous matches
    clear_matches()
    
    # Find mutual matches
    matches = find_mutual_matches()
    
    # Store matches in database with ranks
    for match in matches:
        add_match(
            match['participant1_id'], 
            match['participant2_id'],
            match['rank1'],
            match['rank2']
        )
    
    return len(matches)
