from pymongo import MongoClient, ASCENDING, TEXT
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables
load_dotenv()

def init_database():
    try:
        # Connect to MongoDB
        client = MongoClient(os.getenv('MONGO_URI'))
        db = client[os.getenv('DB_NAME')]
        
        # Create collections
        scans = db.create_collection('scans')
        users = db.create_collection('users')
        
        # Create indexes
        scans.create_index([('timestamp', ASCENDING)])
        scans.create_index([('user_id', ASCENDING)])
        users.create_index([('username', ASCENDING)], unique=True)
        
        # Insert sample scan data
        sample_scan = {
            "timestamp": datetime.utcnow(),
            "code_snippet": "apikey = 'abc123'\nhttp://example.com\neval('2+2')",
            "language": "python",
            "results": {
                "total_findings": 3,
                "findings": [
                    {
                        "severity": "High",
                        "category": "Security",
                        "description": "Hardcoded API key found",
                        "line": 1
                    },
                    {
                        "severity": "Medium",
                        "category": "Network",
                        "description": "Unsecured HTTP used",
                        "line": 2
                    },
                    {
                        "severity": "Critical",
                        "category": "Code Execution",
                        "description": "Dangerous eval() usage",
                        "line": 3
                    }
                ]
            }
        }
        
        # Insert sample user
        sample_user = {
            "username": "test_user",
            "email": "test@example.com",
            "created_at": datetime.utcnow()
        }
        
        # Insert the samples
        scans.insert_one(sample_scan)
        users.insert_one(sample_user)
        
        print("✅ Database initialized successfully!")
        print("Created collections:")
        print("- scans (with indexes: timestamp, user_id)")
        print("- users (with unique index: username)")
        print("\nInserted sample data:")
        print("- 1 scan with 3 vulnerabilities")
        print("- 1 test user")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    init_database() 