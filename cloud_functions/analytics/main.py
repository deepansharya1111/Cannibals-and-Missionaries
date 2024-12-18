import functions_framework
from google.cloud import firestore
import datetime
from collections import defaultdict
from firebase_admin import credentials, initialize_app
import firebase_admin

@functions_framework.http
def analyze_gameplay(request):
    """Analyze all game sessions"""
    if not firebase_admin._apps:
        initialize_app()
    
    db = firestore.Client()
    print("Firebase initialized successfully")
    
    try:
        # Get all game sessions
        games_ref = db.collection('game_sessions')
        games = list(games_ref.stream())
        print(f"Found {len(games)} game sessions")
        
        analytics = {
            'total_games': 0,            # Total game sessions
            'active_games': 0,           # Games in progress
            'completed_games': 0,        # Completed games
            'wins': 0,                   # Number of wins
            'average_moves': 0,          # Average moves per win
            'optimal_solutions': 0,      # Games won in 11 moves
            'common_mistakes': defaultdict(int),
            'success_rate': 0,
            'average_time': 0,
            'total_moves_made': 0        # Total moves across all games
        }
        
        total_moves_in_wins = 0
        total_duration = 0
        
        for game in games:
            game_data = game.to_dict()
            print(f"Analyzing game session: {game.id}")
            
            # Count game status
            analytics['total_games'] += 1
            if game_data.get('status') == 'completed':
                analytics['completed_games'] += 1
                if game_data.get('win'):
                    analytics['wins'] += 1
                    moves_count = game_data.get('moves_count', 0)
                    total_moves_in_wins += moves_count
                    if moves_count == 11:
                        analytics['optimal_solutions'] += 1
                
                if game_data.get('game_duration'):
                    total_duration += game_data.get('game_duration')
            else:
                analytics['active_games'] += 1
            
            # Analyze moves array
            moves_array = game_data.get('moves', [])
            analytics['total_moves_made'] += len(moves_array)
            
            # Analyze mistakes in each move
            for move in moves_array:
                if isinstance(move, dict):
                    for mistake in move.get('mistakes', []):
                        analytics['common_mistakes'][mistake] += 1
        
        # Calculate statistics
        if analytics['completed_games'] > 0:
            if analytics['wins'] > 0:
                analytics['average_moves'] = total_moves_in_wins / analytics['wins']
                analytics['success_rate'] = (analytics['wins'] / analytics['completed_games']) * 100
            analytics['average_time'] = total_duration / analytics['completed_games']
        
        # Convert defaultdict to regular dict
        analytics['common_mistakes'] = dict(analytics['common_mistakes'])
        
        print(f"Analysis complete:")
        print(f"- Total sessions: {analytics['total_games']}")
        print(f"- Active games: {analytics['active_games']}")
        print(f"- Completed games: {analytics['completed_games']}")
        print(f"- Total moves made: {analytics['total_moves_made']}")
        print(f"- Wins: {analytics['wins']}")
        
        return analytics
        
    except Exception as e:
        print(f"Error analyzing gameplay: {e}")
        import traceback
        print(traceback.format_exc())
        return {"error": str(e)} 