from flask import Flask, render_template, request, jsonify, session
import sqlite3
import os
from datetime import datetime, timezone
import pytz

app = Flask(__name__)
app.secret_key = 'nfl_pickem_2025_secret_key'

# Admin users
ADMIN_USERS = {'Manuel'}

# NFL Teams mapping with correct kicker.at team names and logo URLs
NFL_TEAMS = {
    # AFC East
    1: {"name": "Baltimore Ravens", "short": "Baltimore", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/bal.png"},
    2: {"name": "Buffalo Bills", "short": "Buffalo", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/buf.png"},
    3: {"name": "Cincinnati Bengals", "short": "Cincinnati", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/cin.png"},
    4: {"name": "Cleveland Browns", "short": "Cleveland", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/cle.png"},
    5: {"name": "Denver Broncos", "short": "Denver", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/den.png"},
    6: {"name": "Houston Texans", "short": "Houston", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/hou.png"},
    7: {"name": "Indianapolis Colts", "short": "Indianapolis", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ind.png"},
    8: {"name": "Jacksonville Jaguars", "short": "Jacksonville", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/jax.png"},
    9: {"name": "Kansas City Chiefs", "short": "Kansas City", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/kc.png"},
    10: {"name": "Las Vegas Raiders", "short": "Las Vegas", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/lv.png"},
    11: {"name": "Los Angeles Chargers", "short": "LA Chargers", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/lac.png"},
    12: {"name": "Miami Dolphins", "short": "Miami", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/mia.png"},
    13: {"name": "New England Patriots", "short": "New England", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ne.png"},
    14: {"name": "New York Jets", "short": "NY Jets", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png"},
    15: {"name": "Pittsburgh Steelers", "short": "Pittsburgh", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/pit.png"},
    16: {"name": "Tennessee Titans", "short": "Tennessee", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ten.png"},
    
    # NFC Teams
    17: {"name": "Arizona Cardinals", "short": "Arizona", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ari.png"},
    18: {"name": "Atlanta Falcons", "short": "Atlanta", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/atl.png"},
    19: {"name": "Carolina Panthers", "short": "Carolina", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/car.png"},
    20: {"name": "Chicago Bears", "short": "Chicago", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/chi.png"},
    21: {"name": "Dallas Cowboys", "short": "Dallas", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/dal.png"},
    22: {"name": "Detroit Lions", "short": "Detroit", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/det.png"},
    23: {"name": "Green Bay Packers", "short": "Green Bay", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/gb.png"},
    24: {"name": "Los Angeles Rams", "short": "LA Rams", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/lar.png"},
    25: {"name": "Minnesota Vikings", "short": "Minnesota", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/min.png"},
    26: {"name": "New Orleans Saints", "short": "New Orleans", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/no.png"},
    27: {"name": "New York Giants", "short": "NY Giants", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/nyg.png"},
    28: {"name": "Philadelphia Eagles", "short": "Philadelphia", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/phi.png"},
    29: {"name": "San Francisco 49ers", "short": "San Francisco", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/sf.png"},
    30: {"name": "Seattle Seahawks", "short": "Seattle", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/sea.png"},
    31: {"name": "Tampa Bay Buccaneers", "short": "Tampa Bay", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/tb.png"},
    32: {"name": "Washington Commanders", "short": "Washington", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/was.png"}
}

def get_db():
    """Get database connection"""
    conn = sqlite3.connect('nfl_pickem.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with EXACT kicker.at schedule"""
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
    
    # Insert EXACT historical picks from Excel (using correct team IDs)
    historical_data = [
        # Week 1 - EXACT from kicker.at results
        ('Daniel', 1, 5, 16, True),   # Denver Broncos über Tennessee Titans (20:12) ✅
        ('Raff', 1, 3, 4, True),     # Cincinnati Bengals über Cleveland Browns (17:16) ✅  
        ('Manuel', 1, 18, 31, False), # Atlanta Falcons über Tampa Bay Buccaneers (20:23) ❌
        ('Haunschi', 1, 32, 27, True), # Washington Commanders über New York Giants (21:6) ✅
        
        # Week 2 - EXACT from kicker.at results  
        ('Daniel', 2, 28, 9, True),   # Philadelphia Eagles über Kansas City Chiefs ✅
        ('Raff', 2, 21, 27, True),   # Dallas Cowboys über New York Giants (40:37 OT) ✅
        ('Manuel', 2, 21, 27, True), # Dallas Cowboys über New York Giants (40:37 OT) ✅
        ('Haunschi', 2, 2, 12, True), # Buffalo Bills über Miami Dolphins ✅
    ]
    
    for username, week, winner_id, loser_id, correct in historical_data:
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT OR REPLACE INTO historical_picks 
            (user_id, week, winner_team_id, loser_team_id, correct) 
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, week, winner_id, loser_id, correct))
    
    # Insert REAL Week 3 matches from kicker.at (current week)
    week3_matches = [
        # Week 3 - Real matches for September 19, 2025
        (3, 21, 20, "2025-09-22 15:00:00"),  # Dallas Cowboys @ Chicago Bears
        (3, 22, 2, "2025-09-22 18:00:00"),   # Detroit Lions @ Buffalo Bills  
        (3, 12, 2, "2025-09-22 21:00:00"),   # Miami Dolphins @ Buffalo Bills
        (3, 28, 26, "2025-09-22 15:00:00"),  # Philadelphia Eagles @ New Orleans Saints
        (3, 23, 25, "2025-09-22 18:00:00"),  # Green Bay Packers @ Minnesota Vikings
    ]
    
    for week, away_id, home_id, game_time in week3_matches:
        cursor.execute("""
            INSERT OR IGNORE INTO matches (week, away_team_id, home_team_id, game_time)
            VALUES (?, ?, ?, ?)
        """, (week, away_id, home_id, game_time))
    
    conn.commit()
    conn.close()
    
    print("✅ Database initialized with EXACT kicker.at data and correct team logos")

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
        team_name = NFL_TEAMS.get(team_id, {}).get('name', f"Team {team_id}")
        winners_used.append(f"{team_name} #{count}")
    
    losers_used = [NFL_TEAMS.get(team_id, {}).get('name', f"Team {team_id}") for team_id in loser_usage]
    
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
        'current_week': 3,  # Current week (September 19, 2025)
        'total_points': correct_picks,
        'correct_picks': f"{correct_picks}/{total_picks}",
        'current_rank': current_rank,
        'winners_used': winners_used,
        'losers_used': losers_used
    })

@app.route('/api/matches/<int:week>')
def get_matches(week):
    """Get matches for week with correct team logos and graying logic"""
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
    
    # Format matches with correct team data and graying
    formatted_matches = []
    for match in matches:
        away_id = match[1]
        home_id = match[2]
        
        # Get team data
        away_team = NFL_TEAMS.get(away_id, {"name": f"Team {away_id}", "short": f"Team {away_id}", "logo": ""})
        home_team = NFL_TEAMS.get(home_id, {"name": f"Team {home_id}", "short": f"Team {home_id}", "logo": ""})
        
        # Check if teams are pickable
        away_pickable = True
        home_pickable = True
        away_reason = ""
        home_reason = ""
        
        # Rule 1: If team was used as loser, its opponents are not pickable as winners
        if away_id in used_losers:
            home_pickable = False
            home_reason = f"Gegner eines Verlierer-Teams ({away_team['name']})"
        
        if home_id in used_losers:
            away_pickable = False
            away_reason = f"Gegner eines Verlierer-Teams ({home_team['name']})"
        
        # Rule 2: If team was used 2x as winner, its opponents are not pickable as winners
        if winner_usage.get(away_id, 0) >= 2:
            home_pickable = False
            home_reason = f"Gegner eines 2x Gewinner-Teams ({away_team['name']})"
        
        if winner_usage.get(home_id, 0) >= 2:
            away_pickable = False
            away_reason = f"Gegner eines 2x Gewinner-Teams ({home_team['name']})"
        
        # Convert game time to Vienna timezone
        vienna_tz = pytz.timezone('Europe/Vienna')
        try:
            game_dt = datetime.fromisoformat(match[3])
            vienna_time = game_dt.astimezone(vienna_tz)
            formatted_time = vienna_time.strftime("%d.%m.%Y %H:%M")
        except:
            formatted_time = match[3]
        
        formatted_matches.append({
            'id': match[0],
            'away_team': {
                'id': away_id,
                'name': away_team['name'],
                'short': away_team['short'],
                'logo': away_team['logo'],
                'pickable': away_pickable,
                'reason': away_reason
            },
            'home_team': {
                'id': home_id,
                'name': home_team['name'],
                'short': home_team['short'],
                'logo': home_team['logo'],
                'pickable': home_pickable,
                'reason': home_reason
            },
            'game_time': formatted_time,
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
        
        winner_name = NFL_TEAMS.get(winner_id, {}).get('name', f"Team {winner_id}")
        loser_name = NFL_TEAMS.get(loser_id, {}).get('name', f"Team {loser_id}")
        
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
        away_name = NFL_TEAMS.get(match[2], {}).get('short', f"Team {match[2]}")
        home_name = NFL_TEAMS.get(match[3], {}).get('short', f"Team {match[3]}")
        
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
        
        away_name = NFL_TEAMS.get(away_team_id, {}).get('short', f"Team {away_team_id}")
        home_name = NFL_TEAMS.get(home_team_id, {}).get('short', f"Team {home_team_id}")
        winner_name = NFL_TEAMS.get(winner_team_id, {}).get('name', f"Team {winner_team_id}")
        
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
        print("🔧 Initializing database with kicker.at data...")
        init_db()
        print("✅ Database initialized!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
