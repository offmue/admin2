#!/usr/bin/env python3
"""
NFL PickEm 2025/2026 - Production Version
Automatic database initialization with 236 real NFL games
"""

from flask import Flask, request, jsonify, render_template, session
import sqlite3
import hashlib
import requests
from datetime import datetime, timedelta
import pytz
import threading
import time
import os

app = Flask(__name__)
app.secret_key = 'nfl_pickem_2025_secret_key_very_secure'

# Database path
DB_PATH = 'nfl_pickem.db'

# Vienna timezone
VIENNA_TZ = pytz.timezone('Europe/Vienna')

# Team mapping for ESPN API
TEAM_MAPPING = {
    'ARI': 1, 'ATL': 2, 'BAL': 3, 'BUF': 4, 'CAR': 5, 'CHI': 6,
    'CIN': 7, 'CLE': 8, 'DAL': 9, 'DEN': 10, 'DET': 11, 'GB': 12,
    'HOU': 13, 'IND': 14, 'JAX': 15, 'KC': 16, 'LV': 17, 'LAC': 18,
    'LAR': 19, 'MIA': 20, 'MIN': 21, 'NE': 22, 'NO': 23, 'NYG': 24,
    'NYJ': 25, 'PHI': 26, 'PIT': 27, 'SF': 28, 'SEA': 29, 'TB': 30,
    'TEN': 31, 'WAS': 32
}

def init_database():
    """Initialize database with all tables and data"""
    print("🏈 Initializing NFL PickEm database...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            abbreviation TEXT NOT NULL,
            logo_url TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY,
            week INTEGER NOT NULL,
            home_team_id INTEGER NOT NULL,
            away_team_id INTEGER NOT NULL,
            game_time TEXT NOT NULL,
            is_completed BOOLEAN DEFAULT FALSE,
            home_score INTEGER,
            away_score INTEGER,
            FOREIGN KEY (home_team_id) REFERENCES teams (id),
            FOREIGN KEY (away_team_id) REFERENCES teams (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS picks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            match_id INTEGER NOT NULL,
            team_id INTEGER NOT NULL,
            week INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            is_correct BOOLEAN,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (match_id) REFERENCES matches (id),
            FOREIGN KEY (team_id) REFERENCES teams (id),
            UNIQUE(user_id, week)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historical_picks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            week INTEGER NOT NULL,
            team_id INTEGER NOT NULL,
            is_correct BOOLEAN NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (team_id) REFERENCES teams (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            team_id INTEGER NOT NULL,
            usage_type TEXT NOT NULL CHECK (usage_type IN ('winner', 'loser')),
            week INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (team_id) REFERENCES teams (id)
        )
    """)
    
    # Create users
    users = [
        (1, 'Manuel', 'Manuel1'),
        (2, 'Daniel', 'Daniel1'),
        (3, 'Raff', 'Raff1'),
        (4, 'Haunschi', 'Haunschi1')
    ]
    
    for user_id, username, password in users:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, username, password_hash)
            VALUES (?, ?, ?)
        """, (user_id, username, password_hash))
    
    # Create teams
    teams = [
        (1, 'Arizona Cardinals', 'ARI', 'https://a.espncdn.com/i/teamlogos/nfl/500/ari.png'),
        (2, 'Atlanta Falcons', 'ATL', 'https://a.espncdn.com/i/teamlogos/nfl/500/atl.png'),
        (3, 'Baltimore Ravens', 'BAL', 'https://a.espncdn.com/i/teamlogos/nfl/500/bal.png'),
        (4, 'Buffalo Bills', 'BUF', 'https://a.espncdn.com/i/teamlogos/nfl/500/buf.png'),
        (5, 'Carolina Panthers', 'CAR', 'https://a.espncdn.com/i/teamlogos/nfl/500/car.png'),
        (6, 'Chicago Bears', 'CHI', 'https://a.espncdn.com/i/teamlogos/nfl/500/chi.png'),
        (7, 'Cincinnati Bengals', 'CIN', 'https://a.espncdn.com/i/teamlogos/nfl/500/cin.png'),
        (8, 'Cleveland Browns', 'CLE', 'https://a.espncdn.com/i/teamlogos/nfl/500/cle.png'),
        (9, 'Dallas Cowboys', 'DAL', 'https://a.espncdn.com/i/teamlogos/nfl/500/dal.png'),
        (10, 'Denver Broncos', 'DEN', 'https://a.espncdn.com/i/teamlogos/nfl/500/den.png'),
        (11, 'Detroit Lions', 'DET', 'https://a.espncdn.com/i/teamlogos/nfl/500/det.png'),
        (12, 'Green Bay Packers', 'GB', 'https://a.espncdn.com/i/teamlogos/nfl/500/gb.png'),
        (13, 'Houston Texans', 'HOU', 'https://a.espncdn.com/i/teamlogos/nfl/500/hou.png'),
        (14, 'Indianapolis Colts', 'IND', 'https://a.espncdn.com/i/teamlogos/nfl/500/ind.png'),
        (15, 'Jacksonville Jaguars', 'JAX', 'https://a.espncdn.com/i/teamlogos/nfl/500/jax.png'),
        (16, 'Kansas City Chiefs', 'KC', 'https://a.espncdn.com/i/teamlogos/nfl/500/kc.png'),
        (17, 'Las Vegas Raiders', 'LV', 'https://a.espncdn.com/i/teamlogos/nfl/500/lv.png'),
        (18, 'Los Angeles Chargers', 'LAC', 'https://a.espncdn.com/i/teamlogos/nfl/500/lac.png'),
        (19, 'Los Angeles Rams', 'LAR', 'https://a.espncdn.com/i/teamlogos/nfl/500/lar.png'),
        (20, 'Miami Dolphins', 'MIA', 'https://a.espncdn.com/i/teamlogos/nfl/500/mia.png'),
        (21, 'Minnesota Vikings', 'MIN', 'https://a.espncdn.com/i/teamlogos/nfl/500/min.png'),
        (22, 'New England Patriots', 'NE', 'https://a.espncdn.com/i/teamlogos/nfl/500/ne.png'),
        (23, 'New Orleans Saints', 'NO', 'https://a.espncdn.com/i/teamlogos/nfl/500/no.png'),
        (24, 'New York Giants', 'NYG', 'https://a.espncdn.com/i/teamlogos/nfl/500/nyg.png'),
        (25, 'New York Jets', 'NYJ', 'https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png'),
        (26, 'Philadelphia Eagles', 'PHI', 'https://a.espncdn.com/i/teamlogos/nfl/500/phi.png'),
        (27, 'Pittsburgh Steelers', 'PIT', 'https://a.espncdn.com/i/teamlogos/nfl/500/pit.png'),
        (28, 'San Francisco 49ers', 'SF', 'https://a.espncdn.com/i/teamlogos/nfl/500/sf.png'),
        (29, 'Seattle Seahawks', 'SEA', 'https://a.espncdn.com/i/teamlogos/nfl/500/sea.png'),
        (30, 'Tampa Bay Buccaneers', 'TB', 'https://a.espncdn.com/i/teamlogos/nfl/500/tb.png'),
        (31, 'Tennessee Titans', 'TEN', 'https://a.espncdn.com/i/teamlogos/nfl/500/ten.png'),
        (32, 'Washington Commanders', 'WAS', 'https://a.espncdn.com/i/teamlogos/nfl/500/was.png')
    ]
    
    for team_id, name, abbr, logo in teams:
        cursor.execute("""
            INSERT OR REPLACE INTO teams (id, name, abbreviation, logo_url)
            VALUES (?, ?, ?, ?)
        """, (team_id, name, abbr, logo))
    
    # Add historical picks for W1+W2
    historical_picks = [
        # Week 1
        (1, 1, 2, False, '2025-09-05 20:00:00'),  # Manuel: Falcons (lost)
        (2, 1, 10, True, '2025-09-05 20:00:00'),  # Daniel: Broncos (won)
        (3, 1, 7, True, '2025-09-05 20:00:00'),   # Raff: Bengals (won)
        (4, 1, 32, True, '2025-09-05 20:00:00'),  # Haunschi: Commanders (won)
        
        # Week 2
        (1, 2, 9, True, '2025-09-12 20:00:00'),   # Manuel: Cowboys (won)
        (2, 2, 26, True, '2025-09-12 20:00:00'),  # Daniel: Eagles (won)
        (3, 2, 9, True, '2025-09-12 20:00:00'),   # Raff: Cowboys (won)
        (4, 2, 4, True, '2025-09-12 20:00:00'),   # Haunschi: Bills (won)
    ]
    
    for user_id, week, team_id, is_correct, created_at in historical_picks:
        cursor.execute("""
            INSERT OR REPLACE INTO historical_picks (user_id, week, team_id, is_correct, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, week, team_id, is_correct, created_at))
    
    # Add team usage based on historical picks
    team_usage_data = [
        # Manuel W1: Falcons winner -> Buccaneers loser
        (1, 2, 'winner', 1),   # Manuel: Falcons winner
        (1, 30, 'loser', 1),   # Manuel: Buccaneers loser
        
        # Manuel W2: Cowboys winner -> Giants loser  
        (1, 9, 'winner', 2),   # Manuel: Cowboys winner
        (1, 24, 'loser', 2),   # Manuel: Giants loser
        
        # Daniel W1: Broncos winner -> Titans loser
        (2, 10, 'winner', 1),  # Daniel: Broncos winner
        (2, 31, 'loser', 1),   # Daniel: Titans loser
        
        # Daniel W2: Eagles winner -> Chiefs loser
        (2, 26, 'winner', 2),  # Daniel: Eagles winner
        (2, 16, 'loser', 2),   # Daniel: Chiefs loser
        
        # Raff W1: Bengals winner -> Browns loser
        (3, 7, 'winner', 1),   # Raff: Bengals winner
        (3, 8, 'loser', 1),    # Raff: Browns loser
        
        # Raff W2: Cowboys winner -> Giants loser
        (3, 9, 'winner', 2),   # Raff: Cowboys winner
        (3, 24, 'loser', 2),   # Raff: Giants loser (duplicate, but different user)
        
        # Haunschi W1: Commanders winner -> Giants loser
        (4, 32, 'winner', 1),  # Haunschi: Commanders winner
        (4, 24, 'loser', 1),   # Haunschi: Giants loser
        
        # Haunschi W2: Bills winner -> Dolphins loser
        (4, 4, 'winner', 2),   # Haunschi: Bills winner
        (4, 20, 'loser', 2),   # Haunschi: Dolphins loser
    ]
    
    for user_id, team_id, usage_type, week in team_usage_data:
        cursor.execute("""
            INSERT OR REPLACE INTO team_usage (user_id, team_id, usage_type, week)
            VALUES (?, ?, ?, ?)
        """, (user_id, team_id, usage_type, week))
    
    conn.commit()
    conn.close()
    
    print("✅ Database initialized with users, teams, and historical data")
    
    # Load NFL games from ESPN
    load_nfl_games()

def load_nfl_games():
    """Load all available NFL games from ESPN API"""
    print("🏈 Loading NFL games from ESPN API...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_games = 0
    
    # Try to load each week 1-18
    for week in range(1, 19):
        try:
            # Calculate approximate date range for this week
            season_start = datetime(2025, 9, 5)  # NFL season start
            week_start = season_start + timedelta(days=(week - 1) * 7)
            week_end = week_start + timedelta(days=6)
            
            date_range = week_start.strftime('%Y%m%d') + '-' + week_end.strftime('%Y%m%d')
            
            url = f'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={date_range}&seasontype=2&year=2025'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            events = data.get('events', [])
            week_games = 0
            
            for event in events:
                try:
                    # Verify this is the correct week
                    event_week = event.get('week', {}).get('number')
                    if event_week != week:
                        continue
                    
                    game_id = int(event['id'])
                    
                    competitions = event.get('competitions', [])
                    if not competitions:
                        continue
                        
                    competition = competitions[0]
                    competitors = competition.get('competitors', [])
                    
                    if len(competitors) != 2:
                        continue
                    
                    # Find home and away teams
                    home_team = None
                    away_team = None
                    
                    for competitor in competitors:
                        team = competitor['team']
                        if competitor.get('homeAway') == 'home':
                            home_team = team
                        else:
                            away_team = team
                    
                    if not home_team or not away_team:
                        continue
                    
                    # Map team abbreviations
                    home_abbr = home_team.get('abbreviation')
                    away_abbr = away_team.get('abbreviation')
                    
                    home_team_id = TEAM_MAPPING.get(home_abbr)
                    away_team_id = TEAM_MAPPING.get(away_abbr)
                    
                    if not home_team_id or not away_team_id:
                        continue
                    
                    # Game time
                    game_date = event.get('date')
                    if game_date:
                        utc_time = datetime.fromisoformat(game_date.replace('Z', '+00:00'))
                        vienna_time = utc_time.astimezone(VIENNA_TZ)
                    else:
                        vienna_time = datetime.now(VIENNA_TZ)
                    
                    # Game status and scores
                    status = event.get('status', {})
                    is_completed = status.get('type', {}).get('completed', False)
                    
                    home_score = None
                    away_score = None
                    
                    if is_completed:
                        for competitor in competitors:
                            score = competitor.get('score')
                            if competitor.get('homeAway') == 'home':
                                home_score = int(score) if score else 0
                            else:
                                away_score = int(score) if score else 0
                    
                    # Insert game
                    cursor.execute("""
                        INSERT OR REPLACE INTO matches (id, week, home_team_id, away_team_id, game_time, is_completed, home_score, away_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        game_id, week, home_team_id, away_team_id,
                        vienna_time.isoformat(), is_completed, home_score, away_score
                    ))
                    
                    week_games += 1
                    
                except Exception as e:
                    continue
            
            if week_games > 0:
                total_games += week_games
                print(f"✅ Week {week}: {week_games} games loaded")
                
        except Exception as e:
            continue
    
    conn.commit()
    conn.close()
    
    print(f"🎉 Total NFL games loaded: {total_games}")

# Initialize database on startup
if not os.path.exists(DB_PATH):
    init_database()

@app.route('/')
def index():
    if 'user_id' not in session:
        return render_template('index.html', logged_in=False)
    return render_template('index.html', logged_in=True, username=session['username'])

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username und Passwort erforderlich'}), 400
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users WHERE username = ? AND password_hash = ?", 
                      (username, password_hash))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return jsonify({'success': True, 'message': 'Login erfolgreich'})
        else:
            return jsonify({'success': False, 'message': 'Ungültige Anmeldedaten'}), 401
            
    except Exception as e:
        return jsonify({'success': False, 'message': 'Server-Fehler beim Login'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logout erfolgreich'})

@app.route('/api/dashboard')
def dashboard():
    if 'user_id' not in session:
        return jsonify({'error': 'Nicht angemeldet'}), 401
    
    try:
        user_id = session['user_id']
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Current week
        cursor.execute("SELECT MAX(week) FROM matches")
        current_week_result = cursor.fetchone()
        current_week = current_week_result[0] if current_week_result and current_week_result[0] else 3
        
        # Total points from historical picks
        cursor.execute("""
            SELECT COUNT(*) FROM historical_picks 
            WHERE user_id = ? AND is_correct = 1
        """, (user_id,))
        total_points = cursor.fetchone()[0]
        
        # Current week picks count
        cursor.execute("""
            SELECT COUNT(*) FROM picks 
            WHERE user_id = ? AND week = ?
        """, (user_id, current_week))
        current_picks = cursor.fetchone()[0]
        
        # Correct picks from historical data
        cursor.execute("""
            SELECT COUNT(*) FROM historical_picks 
            WHERE user_id = ? AND is_correct = 1
        """, (user_id,))
        correct_picks = cursor.fetchone()[0]
        
        # Total historical picks
        cursor.execute("""
            SELECT COUNT(*) FROM historical_picks 
            WHERE user_id = ?
        """, (user_id,))
        total_historical = cursor.fetchone()[0]
        
        # Team usage
        cursor.execute("""
            SELECT t.name, tu.usage_type
            FROM team_usage tu
            JOIN teams t ON tu.team_id = t.id
            WHERE tu.user_id = ?
            ORDER BY tu.usage_type, t.name
        """, (user_id,))
        
        team_usage_raw = cursor.fetchall()
        winner_teams = [name for name, usage_type in team_usage_raw if usage_type == 'winner']
        loser_teams = [name for name, usage_type in team_usage_raw if usage_type == 'loser']
        
        # Current rank
        cursor.execute("""
            SELECT user_id, 
                   (SELECT COUNT(*) FROM historical_picks hp2 WHERE hp2.user_id = hp.user_id AND hp2.is_correct = 1) as points
            FROM historical_picks hp
            GROUP BY user_id
            ORDER BY points DESC
        """)
        
        rankings = cursor.fetchall()
        current_rank = 1
        for i, (uid, points) in enumerate(rankings):
            if uid == user_id:
                current_rank = i + 1
                break
        
        conn.close()
        
        return jsonify({
            'current_week': current_week,
            'total_points': total_points,
            'current_picks': current_picks,
            'correct_picks': correct_picks,
            'total_picks': total_historical + current_picks,
            'current_rank': current_rank,
            'winner_teams': winner_teams,
            'loser_teams': loser_teams
        })
        
    except Exception as e:
        return jsonify({'error': f'Dashboard-Fehler: {str(e)}'}), 500

@app.route('/api/matches/<int:week>')
def get_matches(week):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT m.id, m.week, m.game_time, m.is_completed,
                   ht.name as home_team, ht.logo_url as home_logo,
                   at.name as away_team, at.logo_url as away_logo,
                   ht.id as home_team_id, at.id as away_team_id,
                   m.home_score, m.away_score
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            WHERE m.week = ?
            ORDER BY m.game_time
        """, (week,))
        
        matches = []
        for row in cursor.fetchall():
            match_id, week, game_time, is_completed, home_team, home_logo, away_team, away_logo, home_team_id, away_team_id, home_score, away_score = row
            
            # Parse game time
            try:
                game_dt = datetime.fromisoformat(game_time)
                if game_dt.tzinfo is None:
                    game_dt = VIENNA_TZ.localize(game_dt)
                formatted_time = game_dt.strftime('%a., %d.%m, %H:%M')
            except:
                formatted_time = game_time
            
            match_data = {
                'id': match_id,
                'week': week,
                'home_team': home_team,
                'away_team': away_team,
                'home_logo': home_logo,
                'away_logo': away_logo,
                'home_team_id': home_team_id,
                'away_team_id': away_team_id,
                'game_time': formatted_time,
                'is_completed': bool(is_completed)
            }
            
            if is_completed and home_score is not None and away_score is not None:
                match_data['home_score'] = home_score
                match_data['away_score'] = away_score
            
            matches.append(match_data)
        
        conn.close()
        return jsonify(matches)
        
    except Exception as e:
        return jsonify({'error': f'Fehler beim Laden der Spiele: {str(e)}'}), 500

@app.route('/api/picks', methods=['POST'])
def submit_pick():
    if 'user_id' not in session:
        return jsonify({'error': 'Nicht angemeldet'}), 401
    
    try:
        data = request.get_json()
        match_id = data.get('match_id')
        team_id = data.get('team_id')
        week = data.get('week')
        
        if not all([match_id, team_id, week]):
            return jsonify({'error': 'Unvollständige Daten'}), 400
        
        user_id = session['user_id']
        
        # Team usage validation
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check winner usage (max 2x)
        cursor.execute("""
            SELECT COUNT(*) FROM team_usage 
            WHERE user_id = ? AND team_id = ? AND usage_type = 'winner'
        """, (user_id, team_id))
        winner_count = cursor.fetchone()[0]
        
        if winner_count >= 2:
            team_name = cursor.execute("SELECT name FROM teams WHERE id = ?", (team_id,)).fetchone()[0]
            return jsonify({'error': f'{team_name} wurde bereits 2x als Gewinner gewählt'}), 400
        
        # Get opponent team for loser validation
        cursor.execute("""
            SELECT home_team_id, away_team_id FROM matches WHERE id = ?
        """, (match_id,))
        match_info = cursor.fetchone()
        if not match_info:
            return jsonify({'error': 'Spiel nicht gefunden'}), 400
        
        home_team_id, away_team_id = match_info
        opponent_team_id = away_team_id if team_id == home_team_id else home_team_id
        
        # Check if opponent is already eliminated as loser
        cursor.execute("""
            SELECT COUNT(*) FROM team_usage 
            WHERE user_id = ? AND team_id = ? AND usage_type = 'loser'
        """, (user_id, opponent_team_id))
        loser_count = cursor.fetchone()[0]
        
        if loser_count >= 1:
            opponent_name = cursor.execute("SELECT name FROM teams WHERE id = ?", (opponent_team_id,)).fetchone()[0]
            return jsonify({'error': f'{opponent_name} wurde bereits als Verlierer gewählt'}), 400
        
        # Save pick
        created_at = datetime.now(VIENNA_TZ).isoformat()
        
        cursor.execute("""
            INSERT OR REPLACE INTO picks (user_id, match_id, team_id, week, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, match_id, team_id, week, created_at))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Pick gespeichert'})
        
    except Exception as e:
        return jsonify({'error': f'Fehler beim Speichern: {str(e)}'}), 500

@app.route('/api/leaderboard')
def leaderboard():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all users with their points from historical picks
        cursor.execute("""
            SELECT u.id, u.username,
                   COALESCE(SUM(CASE WHEN hp.is_correct = 1 THEN 1 ELSE 0 END), 0) as points,
                   COUNT(hp.id) as total_picks,
                   COALESCE(SUM(CASE WHEN hp.is_correct = 1 THEN 1 ELSE 0 END), 0) as correct_picks
            FROM users u
            LEFT JOIN historical_picks hp ON u.id = hp.user_id
            GROUP BY u.id, u.username
            ORDER BY points DESC, total_picks DESC
        """)
        
        users_data = cursor.fetchall()
        
        # Calculate ranks (same points = same rank)
        leaderboard_data = []
        current_rank = 1
        prev_points = None
        
        for i, (user_id, username, points, total_picks, correct_picks) in enumerate(users_data):
            if prev_points is not None and points != prev_points:
                current_rank = i + 1
            
            leaderboard_data.append({
                'rank': current_rank,
                'username': username,
                'points': points,
                'total_picks': total_picks,
                'correct_picks': correct_picks
            })
            
            prev_points = points
        
        conn.close()
        return jsonify(leaderboard_data)
        
    except Exception as e:
        return jsonify({'error': f'Leaderboard-Fehler: {str(e)}'}), 500

@app.route('/api/all-picks')
def all_picks():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all historical picks with team names
        cursor.execute("""
            SELECT hp.week, u.username, t.name as team_name, hp.is_correct, hp.created_at
            FROM historical_picks hp
            JOIN users u ON hp.user_id = u.id
            JOIN teams t ON hp.team_id = t.id
            ORDER BY hp.week DESC, u.username
        """)
        
        picks_data = cursor.fetchall()
        
        # Group by week
        picks_by_week = {}
        for week, username, team_name, is_correct, created_at in picks_data:
            if week not in picks_by_week:
                picks_by_week[week] = []
            
            # Format date
            try:
                pick_date = datetime.fromisoformat(created_at)
                formatted_date = pick_date.strftime('%d.%m.%Y')
            except:
                formatted_date = created_at
            
            picks_by_week[week].append({
                'username': username,
                'team_name': team_name,
                'is_correct': bool(is_correct),
                'date': formatted_date
            })
        
        conn.close()
        return jsonify(picks_by_week)
        
    except Exception as e:
        return jsonify({'error': f'Fehler beim Laden der Picks: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
