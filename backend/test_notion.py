import os
from dotenv import load_dotenv
load_dotenv('.env', override=True)
from notion_client import Client

client = Client(auth=os.getenv('NOTION_API_KEY'))
try:
    res = client.search()
    print("Databases accessible to bot:")
    for d in res['results']:
        if d['object'] == 'database':
            title = d['title'][0]['plain_text'] if d.get('title') else 'No Title'
            print(f"Title: {title}, ID: {d['id']}")
except Exception as e:
    print(f"Error: {e}")
