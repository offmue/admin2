from flask import Flask, render_template, request, jsonify, session
import sqlite3
import os
from datetime import datetime, timezone
import pytz

app = Flask(__name__)
app.secret_key = 'nfl_pickem_2025_secret_key'

# Admin users
ADMIN_USERS = {'Manuel'}

# NFL Teams mapping with correct team names and logo URLs
NFL_TEAMS = {
    # AFC Teams
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

# Team name to ID mapping
TEAM_NAME_TO_ID = {
    "Baltimore Ravens": 1, "Buffalo Bills": 2, "Cincinnati Bengals": 3, "Cleveland Browns": 4,
    "Denver Broncos": 5, "Houston Texans": 6, "Indianapolis Colts": 7, "Jacksonville Jaguars": 8,
    "Kansas City Chiefs": 9, "Las Vegas Raiders": 10, "Los Angeles Chargers": 11, "Miami Dolphins": 12,
    "New England Patriots": 13, "New York Jets": 14, "Pittsburgh Steelers": 15, "Tennessee Titans": 16,
    "Arizona Cardinals": 17, "Atlanta Falcons": 18, "Carolina Panthers": 19, "Chicago Bears": 20,
    "Dallas Cowboys": 21, "Detroit Lions": 22, "Green Bay Packers": 23, "Los Angeles Rams": 24,
    "Minnesota Vikings": 25, "New Orleans Saints": 26, "New York Giants": 27, "Philadelphia Eagles": 28,
    "San Francisco 49ers": 29, "Seattle Seahawks": 30, "Tampa Bay Buccaneers": 31, "Washington Commanders": 32
}

def get_db():
    """Get database connection"""
    conn = sqlite3.connect('nfl_pickem.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with EXACT Excel schedule"""
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
        ('Daniel', 1, 5, 16, True),   # Denver Broncos über Tennessee Titans ✅
        ('Raff', 1, 3, 4, True),     # Cincinnati Bengals über Cleveland Browns ✅  
        ('Manuel', 1, 18, 31, False), # Atlanta Falcons über Tampa Bay Buccaneers ❌
        ('Haunschi', 1, 32, 27, True), # Washington Commanders über New York Giants ✅
        
        # Week 2 - EXACT from Excel  
        ('Daniel', 2, 28, 9, True),   # Philadelphia Eagles über Kansas City Chiefs ✅
        ('Raff', 2, 21, 27, True),   # Dallas Cowboys über New York Giants ✅
        ('Manuel', 2, 21, 27, True), # Dallas Cowboys über New York Giants ✅
        ('Haunschi', 2, 2, 14, True), # Buffalo Bills über New York Jets ✅
    ]
    
    for username, week, winner_id, loser_id, correct in historical_data:
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT OR REPLACE INTO historical_picks 
            (user_id, week, winner_team_id, loser_team_id, correct) 
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, week, winner_id, loser_id, correct))
    
    # Insert COMPLETE schedule from Excel
    schedule_data = [(1, 'Dallas Cowboys', 'Philadelphia Eagles'), (1, 'Kansas City Chiefs', 'Los Angeles Chargers'), (1, 'Tampa Bay Buccaneers', 'Atlanta Falcons'), (1, 'Cincinnati Bengals', 'Cleveland Browns'), (1, 'Miami Dolphins', 'Indianapolis Colts'), (1, 'Carolina Panthers', 'Jacksonville Jaguars'), (1, 'Las Vegas Raiders', 'New England Patriots'), (1, 'Arizona Cardinals', 'New Orleans Saints'), (1, 'Pittsburgh Steelers', 'New York Jets'), (1, 'New York Giants', 'Washington Commanders'), (1, 'Tennessee Titans', 'Denver Broncos'), (1, 'San Francisco 49ers', 'Seattle Seahawks'), (1, 'Detroit Lions', 'Green Bay Packers'), (1, 'Houston Texans', 'Los Angeles Rams'), (1, 'Baltimore Ravens', 'Buffalo Bills'), (1, 'Minnesota Vikings', 'Chicago Bears'), (2, 'Washington Commanders', 'Green Bay Packers'), (2, 'Cleveland Browns', 'Baltimore Ravens'), (2, 'Jacksonville Jaguars', 'Cincinnati Bengals'), (2, 'New York Giants', 'Dallas Cowboys'), (2, 'Chicago Bears', 'Detroit Lions'), (2, 'New England Patriots', 'Miami Dolphins'), (2, 'San Francisco 49ers', 'New Orleans Saints'), (2, 'Buffalo Bills', 'New York Jets'), (2, 'Seattle Seahawks', 'Pittsburgh Steelers'), (2, 'Los Angeles Rams', 'Tennessee Titans'), (2, 'Carolina Panthers', 'Arizona Cardinals'), (2, 'Denver Broncos', 'Indianapolis Colts'), (2, 'Philadelphia Eagles', 'Kansas City Chiefs'), (2, 'Atlanta Falcons', 'Minnesota Vikings'), (2, 'Tampa Bay Buccaneers', 'Houston Texans'), (2, 'Los Angeles Chargers', 'Las Vegas Raiders'), (3, 'Miami Dolphins', 'Buffalo Bills'), (3, 'Carolina Panthers', 'Atlanta Falcons'), (3, 'Cleveland Browns', 'Green Bay Packers'), (3, 'Jacksonville Jaguars', 'Houston Texans'), (3, 'Minnesota Vikings', 'Cincinnati Bengals'), (3, 'New England Patriots', 'Pittsburgh Steelers'), (3, 'Philadelphia Eagles', 'Los Angeles Rams'), (3, 'Tampa Bay Buccaneers', 'New York Jets'), (3, 'Tennessee Titans', 'Indianapolis Colts'), (3, 'Washington Commanders', 'Las Vegas Raiders'), (3, 'Los Angeles Chargers', 'Denver Broncos'), (3, 'Seattle Seahawks', 'New Orleans Saints'), (3, 'Chicago Bears', 'Dallas Cowboys'), (3, 'San Francisco 49ers', 'Arizona Cardinals'), (3, 'New York Giants', 'Kansas City Chiefs'), (3, 'Baltimore Ravens', 'Detroit Lions'), (4, 'Arizona Cardinals', 'Seattle Seahawks'), (4, 'Pittsburgh Steelers', 'Minnesota Vikings'), (4, 'Atlanta Falcons', 'Washington Commanders'), (4, 'Buffalo Bills', 'New Orleans Saints'), (4, 'Detroit Lions', 'Cleveland Browns'), (4, 'Houston Texans', 'Tennessee Titans'), (4, 'New England Patriots', 'Carolina Panthers'), (4, 'New York Giants', 'Los Angeles Chargers'), (4, 'Tampa Bay Buccaneers', 'Philadelphia Eagles'), (4, 'Los Angeles Rams', 'Indianapolis Colts'), (4, 'San Francisco 49ers', 'Jacksonville Jaguars'), (4, 'Kansas City Chiefs', 'Baltimore Ravens'), (4, 'Las Vegas Raiders', 'Chicago Bears'), (4, 'Dallas Cowboys', 'Green Bay Packers'), (4, 'Miami Dolphins', 'New York Jets'), (4, 'Denver Broncos', 'Cincinnati Bengals'), (5, 'San Francisco 49ers', 'Los Angeles Rams'), (5, 'Minnesota Vikings', 'Cleveland Browns'), (5, 'Baltimore Ravens', 'Houston Texans'), (5, 'Carolina Panthers', 'Miami Dolphins'), (5, 'Indianapolis Colts', 'Las Vegas Raiders'), (5, 'New Orleans Saints', 'New York Giants'), (5, 'New York Jets', 'Dallas Cowboys'), (5, 'Philadelphia Eagles', 'Denver Broncos'), (5, 'Arizona Cardinals', 'Tennessee Titans'), (5, 'Seattle Seahawks', 'Tampa Bay Buccaneers'), (5, 'Cincinnati Bengals', 'Detroit Lions'), (5, 'Los Angeles Chargers', 'Washington Commanders'), (5, 'Buffalo Bills', 'New England Patriots'), (5, 'Jacksonville Jaguars', 'Kansas City Chiefs'), (6, 'New York Giants', 'Philadelphia Eagles'), (6, 'New York Jets', 'Denver Broncos'), (6, 'Baltimore Ravens', 'Los Angeles Rams'), (6, 'Carolina Panthers', 'Dallas Cowboys'), (6, 'Indianapolis Colts', 'Arizona Cardinals'), (6, 'Jacksonville Jaguars', 'Seattle Seahawks'), (6, 'Miami Dolphins', 'Los Angeles Chargers'), (6, 'Pittsburgh Steelers', 'Cleveland Browns'), (6, 'Tampa Bay Buccaneers', 'San Francisco 49ers'), (6, 'Las Vegas Raiders', 'Tennessee Titans'), (6, 'Green Bay Packers', 'Cincinnati Bengals'), (6, 'New Orleans Saints', 'New England Patriots'), (6, 'Kansas City Chiefs', 'Detroit Lions'), (6, 'Atlanta Falcons', 'Buffalo Bills'), (6, 'Washington Commanders', 'Chicago Bears'), (7, 'Cincinnati Bengals', 'Pittsburgh Steelers'), (7, 'Baltimore Ravens', 'Miami Dolphins'), (7, 'Green Bay Packers', 'Washington Commanders'), (7, 'Jacksonville Jaguars', 'New York Giants'), (7, 'Atlanta Falcons', 'Tennessee Titans'), (7, 'New England Patriots', 'Detroit Lions'), (7, 'Dallas Cowboys', 'New Orleans Saints'), (7, 'Los Angeles Chargers', 'Tampa Bay Buccaneers'), (7, 'Buffalo Bills', 'Pittsburgh Steelers'), (7, 'Minnesota Vikings', 'San Francisco 49ers'), (7, 'Miami Dolphins', 'Chicago Bears'), (7, 'Kansas City Chiefs', 'Arizona Cardinals'), (7, 'Philadelphia Eagles', 'Houston Texans'), (7, 'New York Jets', 'Carolina Panthers'), (7, 'Seattle Seahawks', 'Los Angeles Rams'), (8, 'Pittsburgh Steelers', 'Cincinnati Bengals'), (8, 'Chicago Bears', 'Atlanta Falcons'), (8, 'Carolina Panthers', 'Jacksonville Jaguars'), (8, 'New York Giants', 'Dallas Cowboys'), (8, 'Los Angeles Chargers', 'Denver Broncos'), (8, 'Tennessee Titans', 'Detroit Lions'), (8, 'Buffalo Bills', 'Miami Dolphins'), (8, 'Indianapolis Colts', 'Houston Texans'), (8, 'New England Patriots', 'New York Jets'), (8, 'Los Angeles Rams', 'New Orleans Saints'), (8, 'Green Bay Packers', 'San Francisco 49ers'), (8, 'Miami Dolphins', 'Las Vegas Raiders'), (8, 'Philadelphia Eagles', 'Carolina Panthers'), (8, 'Seattle Seahawks', 'Arizona Cardinals'), (8, 'Kansas City Chiefs', 'Jacksonville Jaguars'), (9, 'Atlanta Falcons', 'Buffalo Bills'), (9, 'Carolina Panthers', 'Baltimore Ravens'), (9, 'Cleveland Browns', 'Las Vegas Raiders'), (9, 'Dallas Cowboys', 'Minnesota Vikings'), (9, 'Detroit Lions', 'Tennessee Titans'), (9, 'Green Bay Packers', 'New York Giants'), (9, 'Houston Texans', 'Jacksonville Jaguars'), (9, 'Indianapolis Colts', 'New England Patriots'), (9, 'Jacksonville Jaguars', 'Miami Dolphins'), (9, 'Los Angeles Chargers', 'New Orleans Saints'), (9, 'Minnesota Vikings', 'Chicago Bears'), (9, 'New England Patriots', 'Carolina Panthers'), (9, 'New York Jets', 'Pittsburgh Steelers'), (9, 'Philadelphia Eagles', 'Denver Broncos'), (9, 'San Francisco 49ers', 'Seattle Seahawks'), (10, 'Buffalo Bills', 'Cincinnati Bengals'), (10, 'Carolina Panthers', 'Pittsburgh Steelers'), (10, 'Cleveland Browns', 'Houston Texans'), (10, 'Dallas Cowboys', 'Washington Commanders'), (10, 'Detroit Lions', 'Minnesota Vikings'), (10, 'Green Bay Packers', 'Indianapolis Colts'), (10, 'Miami Dolphins', 'New York Jets'), (10, 'New England Patriots', 'Tennessee Titans'), (10, 'New Orleans Saints', 'Los Angeles Chargers'), (10, 'Philadelphia Eagles', 'Chicago Bears'), (10, 'Pittsburgh Steelers', 'Jacksonville Jaguars'), (10, 'San Francisco 49ers', 'Tampa Bay Buccaneers'), (10, 'Seattle Seahawks', 'Los Angeles Rams'), (11, 'Baltimore Ravens', 'New York Giants'), (11, 'Buffalo Bills', 'Los Angeles Chargers'), (11, 'Carolina Panthers', 'Washington Commanders'), (11, 'Chicago Bears', 'Jacksonville Jaguars'), (11, 'Cincinnati Bengals', 'Tennessee Titans'), (11, 'Dallas Cowboys', 'New England Patriots'), (11, 'Denver Broncos', 'Miami Dolphins'), (11, 'Detroit Lions', 'New Orleans Saints'), (11, 'Green Bay Packers', 'Atlanta Falcons'), (11, 'Houston Texans', 'San Francisco 49ers'), (11, 'Indianapolis Colts', 'New York Jets'), (11, 'Jacksonville Jaguars', 'Pittsburgh Steelers'), (11, 'Kansas City Chiefs', 'Los Angeles Rams'), (11, 'Las Vegas Raiders', 'Philadelphia Eagles'), (12, 'Buffalo Bills', 'Denver Broncos'), (12, 'Carolina Panthers', 'New England Patriots'), (12, 'Chicago Bears', 'Miami Dolphins'), (12, 'Cincinnati Bengals', 'Detroit Lions'), (12, 'Dallas Cowboys', 'Green Bay Packers'), (12, 'Denver Broncos', 'New York Giants'), (12, 'Green Bay Packers', 'Las Vegas Raiders'), (12, 'Houston Texans', 'Indianapolis Colts'), (12, 'Indianapolis Colts', 'Tennessee Titans'), (12, 'Jacksonville Jaguars', 'Cleveland Browns'), (12, 'Kansas City Chiefs', 'New Orleans Saints'), (12, 'Los Angeles Chargers', 'Pittsburgh Steelers'), (12, 'Miami Dolphins', 'Baltimore Ravens'), (12, 'New England Patriots', 'Tampa Bay Buccaneers'), (12, 'Philadelphia Eagles', 'San Francisco 49ers'), (13, 'Arizona Cardinals', 'Minnesota Vikings'), (13, 'Atlanta Falcons', 'New England Patriots'), (13, 'Buffalo Bills', 'Dallas Cowboys'), (13, 'Carolina Panthers', 'Kansas City Chiefs'), (13, 'Chicago Bears', 'Indianapolis Colts'), (13, 'Cleveland Browns', 'New York Jets'), (13, 'Denver Broncos', 'Los Angeles Chargers'), (13, 'Detroit Lions', 'New Orleans Saints'), (13, 'Green Bay Packers', 'Tennessee Titans'), (13, 'Houston Texans', 'Philadelphia Eagles'), (13, 'Indianapolis Colts', 'Jacksonville Jaguars'), (13, 'Jacksonville Jaguars', 'Miami Dolphins'), (13, 'Kansas City Chiefs', 'Las Vegas Raiders'), (13, 'Los Angeles Rams', 'Seattle Seahawks'), (13, 'Miami Dolphins', 'Cleveland Browns'), (14, 'Arizona Cardinals', 'Washington Commanders'), (14, 'Atlanta Falcons', 'San Francisco 49ers'), (14, 'Buffalo Bills', 'Carolina Panthers'), (14, 'Chicago Bears', 'Pittsburgh Steelers'), (14, 'Cincinnati Bengals', 'Tennessee Titans'), (14, 'Dallas Cowboys', 'Jacksonville Jaguars'), (14, 'Detroit Lions', 'Green Bay Packers'), (14, 'Green Bay Packers', 'New England Patriots'), (14, 'Houston Texans', 'Los Angeles Chargers'), (14, 'Indianapolis Colts', 'New York Giants'), (14, 'Jacksonville Jaguars', 'New Orleans Saints'), (14, 'Kansas City Chiefs', 'Miami Dolphins'), (14, 'Los Angeles Rams', 'Buffalo Bills'), (14, 'Miami Dolphins', 'New York Jets'), (14, 'New England Patriots', 'Denver Broncos'), (14, 'New York Giants', 'Philadelphia Eagles'), (15, 'Arizona Cardinals', 'Buffalo Bills'), (15, 'Atlanta Falcons', 'Baltimore Ravens'), (15, 'Carolina Panthers', 'Detroit Lions'), (15, 'Chicago Bears', 'New England Patriots'), (15, 'Cleveland Browns', 'Pittsburgh Steelers'), (15, 'Dallas Cowboys', 'New York Giants'), (15, 'Denver Broncos', 'Miami Dolphins'), (15, 'Green Bay Packers', 'San Francisco 49ers'), (15, 'Houston Texans', 'Jacksonville Jaguars'), (15, 'Indianapolis Colts', 'Tennessee Titans'), (15, 'Jacksonville Jaguars', 'Cincinnati Bengals'), (15, 'Kansas City Chiefs', 'Los Angeles Chargers'), (15, 'Los Angeles Rams', 'Las Vegas Raiders'), (15, 'Minnesota Vikings', 'New Orleans Saints'), (15, 'New York Jets', 'Seattle Seahawks'), (16, 'Atlanta Falcons', 'New England Patriots'), (16, 'Buffalo Bills', 'Arizona Cardinals'), (16, 'Carolina Panthers', 'Cleveland Browns'), (16, 'Chicago Bears', 'Cincinnati Bengals'), (16, 'Cleveland Browns', 'Buffalo Bills'), (16, 'Dallas Cowboys', 'Seattle Seahawks'), (16, 'Denver Broncos', 'Tennessee Titans'), (16, 'Green Bay Packers', 'Los Angeles Chargers'), (16, 'Houston Texans', 'Miami Dolphins'), (16, 'Indianapolis Colts', 'New York Giants'), (16, 'Jacksonville Jaguars', 'New England Patriots'), (16, 'Kansas City Chiefs', 'Minnesota Vikings'), (16, 'Las Vegas Raiders', 'Pittsburgh Steelers'), (16, 'Los Angeles Rams', 'Washington Commanders'), (16, 'Miami Dolphins', 'Tampa Bay Buccaneers'), (17, 'Arizona Cardinals', 'Dallas Cowboys'), (17, 'Atlanta Falcons', 'Washington Commanders'), (17, 'Buffalo Bills', 'Detroit Lions'), (17, 'Carolina Panthers', 'Philadelphia Eagles'), (17, 'Chicago Bears', 'Minnesota Vikings'), (17, 'Cleveland Browns', 'New York Jets'), (17, 'Dallas Cowboys', 'San Francisco 49ers'), (17, 'Denver Broncos', 'Green Bay Packers'), (17, 'Green Bay Packers', 'Chicago Bears'), (17, 'Houston Texans', 'Jacksonville Jaguars'), (17, 'Indianapolis Colts', 'Tennessee Titans'), (17, 'Jacksonville Jaguars', 'Cincinnati Bengals'), (17, 'Kansas City Chiefs', 'Los Angeles Chargers'), (17, 'Las Vegas Raiders', 'New York Giants'), (17, 'Los Angeles Rams', 'Miami Dolphins'), (17, 'Minnesota Vikings', 'Seattle Seahawks'), (18, 'Buffalo Bills', 'Miami Dolphins'), (18, 'Chicago Bears', 'Cincinnati Bengals'), (18, 'Cleveland Browns', 'Green Bay Packers'), (18, 'Dallas Cowboys', 'New York Giants'), (18, 'Detroit Lions', 'Minnesota Vikings'), (18, 'Green Bay Packers', 'Indianapolis Colts'), (18, 'Houston Texans', 'Jacksonville Jaguars'), (18, 'Indianapolis Colts', 'Houston Texans'), (18, 'Jacksonville Jaguars', 'Indianapolis Colts'), (18, 'Kansas City Chiefs', 'Kansas City Chiefs')]
    
    for week, away_team_name, home_team_name in schedule_data:
        away_team_id = TEAM_NAME_TO_ID.get(away_team_name)
        home_team_id = TEAM_NAME_TO_ID.get(home_team_name)
        
        if away_team_id and home_team_id:
            # Generate game time (simplified - using app times)
            game_time = f"2025-09-138 15:00:00"
            
            cursor.execute("""
                INSERT OR IGNORE INTO matches (week, away_team_id, home_team_id, game_time)
                VALUES (?, ?, ?, ?)
            """, (week, away_team_id, home_team_id, game_time))
    
    conn.commit()
    conn.close()
    
    print("✅ Database initialized with EXACT Excel schedule")

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

@app.route('/api/current-week')
def current_week():
    """Get current week - automatically jumps to next week when all games completed"""
    username = session.get('username')
    if username not in ADMIN_USERS:
        return jsonify({'current_week': 3})  # Default for non-admin
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Find the first week with incomplete games
    cursor.execute("""
        SELECT week FROM matches 
        WHERE completed = FALSE 
        ORDER BY week 
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    current_week = result[0] if result else 18  # Default to week 18 if all done
    
    conn.close()
    
    return jsonify({'current_week': current_week})

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
        
        # Check if all games in this week are completed
        cursor.execute("""
            SELECT COUNT(*) FROM matches 
            WHERE week = ? AND completed = FALSE
        """, (week,))
        
        remaining_games = cursor.fetchone()[0]
        
        message = f"Ergebnis gesetzt: {away_name} {away_score}:{home_score} {home_name}. "
        message += f"Gewinner: {winner_name}. {updated_picks} User-Picks automatisch validiert."
        
        if remaining_games == 0:
            message += f" Alle Spiele der Woche {week} abgeschlossen - UI springt automatisch zur nächsten Woche."
        
        return jsonify({'success': True, 'message': message, 'week_completed': remaining_games == 0})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}))
    finally:
        conn.close()

if __name__ == '__main__':
    # Initialize database on startup
    if not os.path.exists('nfl_pickem.db') or os.path.getsize('nfl_pickem.db') == 0:
        print("🔧 Initializing database with Excel schedule...")
        init_db()
        print("✅ Database initialized!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
