# Auto-init wrapper for NFL PickEm app
import os
from setup_database import setup_database

# Auto-initialize database on import
if not os.path.exists('nfl_pickem.db') or os.path.getsize('nfl_pickem.db') == 0:
    print("🔧 Auto-initializing database...")
    setup_database()
    print("✅ Database initialized!")

# Import the main app
from app import app

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
