import os
from pathlib import Path
from dotenv import load_dotenv
from notion_client import Client

def debug():
    backend_root = Path(__file__).resolve().parents[1]
    load_dotenv(dotenv_path=backend_root / ".env", override=True)
    notion_secret = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_SECRET")
    notion_database_id = os.getenv("NOTION_DATABASE_ID")

    if not notion_secret or not notion_database_id:
        print("Missing config")
        return

    client = Client(auth=notion_secret)
    db = client.databases.retrieve(database_id=notion_database_id)
    
    print(f"Database ID: {notion_database_id}")
    print(f"Title: {db.get('title', [{}])[0].get('plain_text', 'No Title')}")
    print(f"Has properties: {bool(db.get('properties'))}")
    print(f"Has data_sources: {'data_sources' in db}")
    if 'data_sources' in db:
        print(f"Data Sources: {db['data_sources']}")
    
    if not db.get('properties') and 'data_sources' in db:
        source_id = db['data_sources'][0].get('database_id')
        print(f"Attempting to retrieve source DB: {source_id}")
        try:
            source_db = client.databases.retrieve(database_id=source_id)
            print(f"Source DB Title: {source_db.get('title', [{}])[0].get('plain_text', 'No Title')}")
            print(f"Source Properties: {list(source_db.get('properties', {}).keys())}")
        except Exception as e:
            print(f"Error retrieving source DB: {e}")

if __name__ == "__main__":
    debug()
