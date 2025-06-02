from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def get_database():
    """Get database connection"""
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://mongodb:27017/'))
    db = client[os.getenv('DB_NAME', 'vulnerability_scanner')]
    return db

def get_collections():
    """Get database collections"""
    db = get_database()
    return {
        'users': db['users'],
        'scans': db['scans']
    } 