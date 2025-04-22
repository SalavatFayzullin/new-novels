from app import app, db
import os
import shutil

# Delete existing database
db_path = os.path.join('instance', 'site.db')
if os.path.exists(db_path):
    try:
        os.remove(db_path)
        print(f"Database file '{db_path}' has been deleted.")
    except Exception as e:
        print(f"Error deleting database file: {e}")
else:
    print(f"Database file '{db_path}' does not exist.")

# Recreate database with updated schema
with app.app_context():
    db.create_all()
    print("Database has been recreated with the updated schema.") 