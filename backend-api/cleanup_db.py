from pymongo import MongoClient
import os

def cleanup_database():
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['vulnerability_scanner']
    
    # Drop collections entirely
    db.drop_collection('users')
    db.drop_collection('scans')
    
    print("Collections 'users' and 'scans' have been completely removed!")
    print("\nDatabase cleaned successfully!")
    
    client.close()

if __name__ == "__main__":
    cleanup_database() 