#!/usr/bin/env python3
"""
Complete database setup with EXACT kicker.at data
"""

import sqlite3

def setup_database():
    """Setup complete database with exact kicker.at historical data"""
    
    conn = sqlite3.connect('nfl_pickem.db')
    cursor = conn.cursor()
    
    print("🔧 SETTING UP DATABASE WITH EXACT KICKER.AT DATA...")
    
    # Create all tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY,
        week INTEGER NOT NULL,
        away_team_id INTEGER NOT NULL,
        home_team_id INTEGER NOT NULL,
        game_time TEXT NOT NULL,
        away_score INTEGER DEFAULT NULL,
        home_score INTEGER DEFAULT NULL,
        completed BOOLEAN DEFAULT FALSE
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS picks (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        match_id INTEGER NOT NULL,
        team_id INTEGER NOT NULL,
        week INTEGER NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS historical_picks (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        team_id INTEGER NOT NULL,
        week INTEGER NOT NULL,
        correct BOOLEAN NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS team_usage (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        team_id INTEGER NOT NULL,
        usage_type TEXT NOT NULL
    )
    ''')
    
    print("✅ Created all tables")
    
    # Clear existing data
    cursor.execute('DELETE FROM users')
    cursor.execute('DELETE FROM historical_picks')
    cursor.execute('DELETE FROM team_usage')
    
    # Insert users
    users_data = [
        (1, 'Manuel'),
        (2, 'Daniel'),
        (3, 'Raff'),
        (4, 'Haunschi')
    ]
    cursor.executemany('INSERT INTO users (id, username) VALUES (?, ?)', users_data)
    print("✅ Inserted users")
    
    # Insert EXACT historical picks from kicker.at
    historical_picks_data = [
        # Week 1 - EXACT from kicker.at
        (1, 25, 1, 0),  # Manuel: Atlanta Falcons @ Buccaneers (lost 20:23) = 0 points
        (2, 13, 1, 1),  # Daniel: Denver Broncos @ Titans (won 20:12) = 1 point  
        (4, 20, 1, 1),  # Haunschi: Washington Commanders @ Giants (won 21:6) = 1 point
        (3, 6, 1, 1),   # Raff: Cincinnati Bengals vs Browns (won 17:16) = 1 point
        
        # Week 2 - EXACT from kicker.at
        (1, 17, 2, 1),  # Manuel: Dallas Cowboys @ Giants (won 40:37 OT) = 1 point
        (2, 19, 2, 1),  # Daniel: Philadelphia Eagles vs Chiefs (won 20:17) = 1 point
        (4, 1, 2, 1),   # Haunschi: Buffalo Bills vs Jets (won 30:10) = 1 point
        (3, 17, 2, 1),  # Raff: Dallas Cowboys @ Giants (won 40:37 OT) = 1 point
    ]
    
    cursor.executemany('INSERT INTO historical_picks (user_id, team_id, week, correct) VALUES (?, ?, ?, ?)', historical_picks_data)
    print("✅ Inserted EXACT historical picks from kicker.at")
    
    # Insert CORRECT team usage based on PICKS (not NFL results)
    team_usage_data = [
        # Manuel: Picked Falcons & Cowboys (winners), Buccaneers & Giants (automatic losers)
        (1, 25, 'winner'),  # Falcons (picked as winner W1)
        (1, 28, 'loser'),   # Buccaneers (automatic loser W1)
        (1, 17, 'winner'),  # Cowboys (picked as winner W2)
        (1, 18, 'loser'),   # Giants (automatic loser W2)
        
        # Daniel: Picked Broncos & Eagles (winners), Titans & Chiefs (automatic losers)
        (2, 13, 'winner'),  # Broncos (picked as winner W1)
        (2, 12, 'loser'),   # Titans (automatic loser W1)
        (2, 19, 'winner'),  # Eagles (picked as winner W2)
        (2, 14, 'loser'),   # Chiefs (automatic loser W2)
        
        # Haunschi: Picked Commanders & Bills (winners), Giants & Jets (automatic losers)
        (4, 20, 'winner'),  # Commanders (picked as winner W1)
        (4, 18, 'loser'),   # Giants (automatic loser W1)
        (4, 1, 'winner'),   # Bills (picked as winner W2)
        (4, 4, 'loser'),    # Jets (automatic loser W2)
        
        # Raff: Picked Bengals & Cowboys (winners), Browns & Giants (automatic losers)
        (3, 6, 'winner'),   # Bengals (picked as winner W1)
        (3, 7, 'loser'),    # Browns (automatic loser W1)
        (3, 17, 'winner'),  # Cowboys (picked as winner W2)
        (3, 18, 'loser'),   # Giants (automatic loser W2)
    ]
    
    cursor.executemany('INSERT INTO team_usage (user_id, team_id, usage_type) VALUES (?, ?, ?)', team_usage_data)
    print("✅ Inserted CORRECT team usage based on picks")
    
    # Add sample Week 3 matches
    matches_data = [
        (3, 1, 2, '2025-09-21 19:00:00'),   # Bills @ Dolphins
        (3, 7, 23, '2025-09-21 22:00:00'),  # Browns @ Packers
        (3, 24, 6, '2025-09-22 01:00:00'),  # Vikings @ Bengals
        (3, 11, 9, '2025-09-22 19:00:00'),  # Jaguars @ Texans
    ]
    
    cursor.executemany('INSERT INTO matches (week, away_team_id, home_team_id, game_time) VALUES (?, ?, ?, ?)', matches_data)
    print("✅ Inserted sample Week 3 matches")
    
    conn.commit()
    conn.close()
    
    print("🎉 DATABASE SETUP COMPLETE WITH EXACT KICKER.AT DATA!")
    print("📊 FINAL POINTS:")
    print("   Manuel: 1 point (Falcons ❌, Cowboys ✅)")
    print("   Daniel: 2 points (Broncos ✅, Eagles ✅)")
    print("   Haunschi: 2 points (Commanders ✅, Bills ✅)")
    print("   Raff: 2 points (Bengals ✅, Cowboys ✅)")
    print("")
    print("🎯 TEAM USAGE:")
    print("   Manuel: Winners(Falcons,Cowboys), Losers(Buccaneers,Giants)")
    print("   Daniel: Winners(Broncos,Eagles), Losers(Titans,Chiefs)")
    print("   Haunschi: Winners(Commanders,Bills), Losers(Giants,Jets)")
    print("   Raff: Winners(Bengals,Cowboys), Losers(Browns,Giants)")

if __name__ == "__main__":
    setup_database()
