from flask import Flask, render_template, request, jsonify, session
import sqlite3
import os
from datetime import datetime, timezone
import pytz

app = Flask(__name__)
app.secret_key = 'nfl_pickem_2025_secret_key'

# Admin users
ADMIN_USERS = {'Manuel'}

# NFL Teams mapping (32 teams)
NFL_TEAMS = {
    1: "Baltimore Ravens", 2: "Buffalo Bills", 3: "Cincinnati Bengals", 4: "Cleveland Browns",
    5: "Denver Broncos", 6: "Houston Texans", 7: "Indianapolis Colts", 8: "Jacksonville Jaguars",
    9: "Kansas City Chiefs", 10: "Las Vegas Raiders", 11: "Los Angeles Chargers", 12: "Miami Dolphins",
    13: "New England Patriots", 14: "New York Jets", 15: "Pittsburgh Steelers", 16: "Tennessee Titans",
    17: "Arizona Cardinals", 18: "Atlanta Falcons", 19: "Carolina Panthers", 20: "Chicago Bears",
    21: "Dallas Cowboys", 22: "Detroit Lions", 23: "Green Bay Packers", 24: "Los Angeles Rams",
    25: "Minnesota Vikings", 26: "New Orleans Saints", 27: "New York Giants", 28: "Philadelphia Eagles",
    29: "San Francisco 49ers", 30: "Seattle Seahawks", 31: "Tampa Bay Buccaneers", 32: "Washington Commanders"
}

def get_db():
    """Get database connection"""
    conn = sqlite3.connect('nfl_pickem.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with Excel-based structure"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY,
            week INTEGER NOT NULL,
            away_team_id INTEGER NOT NULL,
            home_team_id INTEGER NOT NULL,
            away_score INTEGER,
            home_score INTEGER,
            game_time TEXT,
            completed BOOLEAN DEFAULT FALSE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS picks (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            match_id INTEGER NOT NULL,
            team_id INTEGER NOT NULL,
            week INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (match_id) REFERENCES matches (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historical_picks (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            week INTEGER NOT NULL,
            winner_team_id INTEGER NOT NULL,
            loser_team_id INTEGER NOT NULL,
            correct BOOLEAN NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Insert users
    users = ['Manuel', 'Daniel', 'Raff', 'Haunschi']
    for user in users:
        cursor.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (user,))
    
    # Insert EXACT historical picks from Excel
    historical_data = [
        # Week 1 - EXACT from Excel
        ('Daniel', 1, 5, 16, True),   # Broncos über Titans ✅
        ('Raff', 1, 3, 4, True),     # Bengals über Browns ✅  
        ('Manuel', 1, 18, 31, False), # Falcons über Buccaneers ❌
        ('Haunschi', 1, 32, 27, True), # Commanders über Giants ✅
        
        # Week 2 - EXACT from Excel
        ('Daniel', 2, 28, 9, True),   # Eagles über Chiefs ✅
        ('Raff', 2, 21, 27, True),   # Cowboys über Giants ✅
        ('Manuel', 2, 21, 27, True), # Cowboys über Giants ✅
        ('Haunschi', 2, 2, 12, True), # Bills über Dolphins ✅
    ]
    
    for username, week, winner_id, loser_id, correct in historical_data:
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT OR REPLACE INTO historical_picks 
            (user_id, week, winner_team_id, loser_team_id, correct) 
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, week, winner_id, loser_id, correct))
    
    # Insert sample Week 3 matches for testing
    week3_matches = [
        (3, 21, 20, "2025-09-21 18:00:00"),  # Cowboys @ Bears
        (3, 22, 2, "2025-09-21 21:00:00"),   # Lions @ Bills
        (3, 12, 2, "2025-09-22 18:00:00"),   # Dolphins @ Bills
    ]
    
    for week, away_id, home_id, game_time in week3_matches:
        cursor.execute("""
            INSERT OR IGNORE INTO matches (week, away_team_id, home_team_id, game_time)
            VALUES (?, ?, ?, ?)
        """, (week, away_id, home_id, game_time))
    
    conn.commit()
    conn.close()
    
    print("✅ Database initialized with EXACT Excel data")

@app.route('/')
def index():
    """Main page"""
    username = session.get('username')
    logged_in = username is not None
    is_admin = username in ADMIN_USERS if username else False
    
    valid_users = ['Manuel', 'Daniel', 'Raff', 'Haunschi']
    
    return render_template('index.html', 
                         logged_in=logged_in, 
                         username=username,
                         is_admin=is_admin,
                         valid_users=valid_users)

@app.route('/api/login', methods=['POST'])
def login():
    """Simple login"""
    data = request.get_json()
    username = data.get('username')
    
    if username in ['Manuel', 'Daniel', 'Raff', 'Haunschi']:
        session['username'] = username
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid username'})

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout"""
    session.pop('username', None)
    return jsonify({'success': True})

@app.route('/api/dashboard')
def dashboard():
    """Dashboard data with Excel format"""
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not logged in'})
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get user ID
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user_row = cursor.fetchone()
    if not user_row:
        return jsonify({'error': 'User not found'})
    user_id = user_row[0]
    
    # Get historical picks for points calculation
    cursor.execute("""
        SELECT COUNT(*) as total, SUM(CASE WHEN correct THEN 1 ELSE 0 END) as correct_count
        FROM historical_picks WHERE user_id = ?
    """, (user_id,))
    picks_data = cursor.fetchone()
    
    total_picks = picks_data[0] if picks_data[0] else 0
    correct_picks = picks_data[1] if picks_data[1] else 0
    
    # Get team usage in Excel format
    cursor.execute("""
        SELECT winner_team_id, loser_team_id, week
        FROM historical_picks WHERE user_id = ?
        ORDER BY week
    """, (user_id,))
    
    historical_picks = cursor.fetchall()
    
    # Calculate team usage
    winner_usage = {}
    loser_usage = []
    
    for pick in historical_picks:
        winner_id = pick[0]
        loser_id = pick[1]
        
        # Track winner usage (max 2x)
        if winner_id not in winner_usage:
            winner_usage[winner_id] = 0
        winner_usage[winner_id] += 1
        
        # Track loser usage (max 1x)
        if loser_id not in loser_usage:
            loser_usage.append(loser_id)
    
    # Format team usage for display
    winners_used = []
    for team_id, count in winner_usage.items():
        team_name = NFL_TEAMS.get(team_id, f"Team {team_id}")
        winners_used.append(f"{team_name} #{count}")
    
    losers_used = [NFL_TEAMS.get(team_id, f"Team {team_id}") for team_id in loser_usage]
    
    # Get current rank
    cursor.execute("""
        SELECT u.username, SUM(CASE WHEN hp.correct THEN 1 ELSE 0 END) as points
        FROM users u
        LEFT JOIN historical_picks hp ON u.id = hp.user_id
        GROUP BY u.id, u.username
        ORDER BY points DESC
    """)
    
    leaderboard = cursor.fetchall()
    current_rank = next((i+1 for i, row in enumerate(leaderboard) if row[0] == username), '-')
    
    conn.close()
    
    return jsonify({
        'current_week': 3,  # Current week
        'total_points': correct_picks,
        'correct_picks': f"{correct_picks}/{total_picks}",
        'current_rank': current_rank,
        'winners_used': winners_used,
        'losers_used': losers_used
    })

@app.route('/api/matches/<int:week>')
def get_matches(week):
    """Get matches for week with team graying logic"""
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not logged in'})
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get user ID
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user_row = cursor.fetchone()
    if not user_row:
        return jsonify({'error': 'User not found'})
    user_id = user_row[0]
    
    # Get matches for the week
    cursor.execute("""
        SELECT id, away_team_id, home_team_id, game_time, completed
        FROM matches WHERE week = ?
    """, (week,))
    
    matches = cursor.fetchall()
    
    if not matches:
        return jsonify({'error': 'No matches found for this week'})
    
    # Get user's team usage for graying logic
    cursor.execute("""
        SELECT winner_team_id, loser_team_id
        FROM historical_picks WHERE user_id = ?
    """, (user_id,))
    
    historical_picks = cursor.fetchall()
    
    # Calculate unpickable teams
    winner_usage = {}
    used_losers = set()
    
    for pick in historical_picks:
        winner_id = pick[0]
        loser_id = pick[1]
        
        # Track winner usage
        if winner_id not in winner_usage:
            winner_usage[winner_id] = 0
        winner_usage[winner_id] += 1
        
        # Track used losers
        used_losers.add(loser_id)
    
    # Format matches with team graying
    formatted_matches = []
    for match in matches:
        away_id = match[1]
        home_id = match[2]
        
        # Check if teams are pickable
        away_pickable = True
        home_pickable = True
        away_reason = ""
        home_reason = ""
        
        # Rule 1: If team was used as loser, its opponents are not pickable as winners
        if away_id in used_losers:
            home_pickable = False
            home_reason = f"Gegner eines Verlierer-Teams ({NFL_TEAMS.get(away_id)})"
        
        if home_id in used_losers:
            away_pickable = False
            away_reason = f"Gegner eines Verlierer-Teams ({NFL_TEAMS.get(home_id)})"
        
        # Rule 2: If team was used 2x as winner, its opponents are not pickable as winners
        if winner_usage.get(away_id, 0) >= 2:
            home_pickable = False
            home_reason = f"Gegner eines 2x Gewinner-Teams ({NFL_TEAMS.get(away_id)})"
        
        if winner_usage.get(home_id, 0) >= 2:
            away_pickable = False
            away_reason = f"Gegner eines 2x Gewinner-Teams ({NFL_TEAMS.get(home_id)})"
        
        formatted_matches.append({
            'id': match[0],
            'away_team': {
                'id': away_id,
                'name': NFL_TEAMS.get(away_id, f"Team {away_id}"),
                'logo': f"https://a.espncdn.com/i/teamlogos/nfl/500/{away_id}.png",
                'pickable': away_pickable,
                'reason': away_reason
            },
            'home_team': {
                'id': home_id,
                'name': NFL_TEAMS.get(home_id, f"Team {home_id}"),
                'logo': f"https://a.espncdn.com/i/teamlogos/nfl/500/{home_id}.png",
                'pickable': home_pickable,
                'reason': home_reason
            },
            'game_time': match[3],
            'completed': bool(match[4])
        })
    
    conn.close()
    
    return jsonify({'matches': formatted_matches})

@app.route('/api/leaderboard')
def leaderboard():
    """Get leaderboard"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT u.username, SUM(CASE WHEN hp.correct THEN 1 ELSE 0 END) as points
        FROM users u
        LEFT JOIN historical_picks hp ON u.id = hp.user_id
        GROUP BY u.id, u.username
        ORDER BY points DESC
    """)
    
    results = cursor.fetchall()
    
    leaderboard_data = []
    current_rank = 1
    prev_points = None
    
    for i, row in enumerate(results):
        points = row[1] if row[1] else 0
        
        # Handle ties
        if prev_points is not None and points != prev_points:
            current_rank = i + 1
        
        leaderboard_data.append({
            'rank': current_rank,
            'username': row[0],
            'points': points
        })
        
        prev_points = points
    
    conn.close()
    
    return jsonify({'leaderboard': leaderboard_data})

@app.route('/api/all-picks')
def all_picks():
    """Get all historical picks in Excel format"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT u.username, hp.week, hp.winner_team_id, hp.loser_team_id, hp.correct
        FROM historical_picks hp
        JOIN users u ON hp.user_id = u.id
        ORDER BY u.username, hp.week
    """)
    
    results = cursor.fetchall()
    
    picks_by_user = {}
    for row in results:
        username = row[0]
        week = row[1]
        winner_id = row[2]
        loser_id = row[3]
        correct = row[4]
        
        if username not in picks_by_user:
            picks_by_user[username] = []
        
        winner_name = NFL_TEAMS.get(winner_id, f"Team {winner_id}")
        loser_name = NFL_TEAMS.get(loser_id, f"Team {loser_id}")
        
        picks_by_user[username].append({
            'week': week,
            'team': f"{winner_name} über {loser_name}",
            'correct': correct
        })
    
    conn.close()
    
    return jsonify({'picks': picks_by_user})

@app.route('/api/pending-games')
def pending_games():
    """Get pending games for admin"""
    username = session.get('username')
    if username not in ADMIN_USERS:
        return jsonify({'error': 'Not authorized'})
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, week, away_team_id, home_team_id
        FROM matches WHERE completed = FALSE
        ORDER BY week, id
    """)
    
    matches = cursor.fetchall()
    
    games = []
    for match in matches:
        away_name = NFL_TEAMS.get(match[2], f"Team {match[2]}")
        home_name = NFL_TEAMS.get(match[3], f"Team {match[3]}")
        
        games.append({
            'id': match[0],
            'description': f"W{match[1]}: {away_name} @ {home_name}"
        })
    
    conn.close()
    
    return jsonify({'games': games})

@app.route('/api/set-game-result', methods=['POST'])
def set_game_result():
    """Set game result and auto-validate picks"""
    username = session.get('username')
    if username not in ADMIN_USERS:
        return jsonify({'error': 'Not authorized'})
    
    data = request.get_json()
    match_id = data.get('match_id')
    away_score = data.get('away_score')
    home_score = data.get('home_score')
    
    if not all([match_id, away_score is not None, home_score is not None]):
        return jsonify({'error': 'Missing required fields'})
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Update match result
        cursor.execute("""
            UPDATE matches 
            SET away_score = ?, home_score = ?, completed = TRUE
            WHERE id = ?
        """, (away_score, home_score, match_id))
        
        # Get match details
        cursor.execute("""
            SELECT week, away_team_id, home_team_id
            FROM matches WHERE id = ?
        """, (match_id,))
        
        match = cursor.fetchone()
        if not match:
            return jsonify({'error': 'Match not found'})
        
        week = match[0]
        away_team_id = match[1]
        home_team_id = match[2]
        
        # Determine winner
        winner_team_id = home_team_id if home_score > away_score else away_team_id
        loser_team_id = away_team_id if home_score > away_score else home_team_id
        
        # Find all picks for this match and validate them
        cursor.execute("""
            SELECT p.user_id, p.team_id, u.username
            FROM picks p
            JOIN users u ON p.user_id = u.id
            WHERE p.match_id = ?
        """, (match_id,))
        
        picks = cursor.fetchall()
        updated_picks = 0
        
        for pick in picks:
            user_id = pick[0]
            picked_team_id = pick[1]
            username = pick[2]
            
            # Check if pick was correct
            correct = picked_team_id == winner_team_id
            
            # Update or insert historical pick
            cursor.execute("""
                INSERT OR REPLACE INTO historical_picks 
                (user_id, week, winner_team_id, loser_team_id, correct)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, week, winner_team_id, loser_team_id, correct))
            
            updated_picks += 1
        
        conn.commit()
        
        away_name = NFL_TEAMS.get(away_team_id, f"Team {away_team_id}")
        home_name = NFL_TEAMS.get(home_team_id, f"Team {home_team_id}")
        winner_name = NFL_TEAMS.get(winner_team_id, f"Team {winner_team_id}")
        
        message = f"Ergebnis gesetzt: {away_name} {away_score}:{home_score} {home_name}. "
        message += f"Gewinner: {winner_name}. {updated_picks} User-Picks automatisch validiert."
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': f'Database error: {str(e)}'})
    finally:
        conn.close()

if __name__ == '__main__':
    # Initialize database on startup
    if not os.path.exists('nfl_pickem.db') or os.path.getsize('nfl_pickem.db') == 0:
        print("🔧 Initializing database...")
        init_db()
        print("✅ Database initialized!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
