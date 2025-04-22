from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from pymongo import MongoClient, DESCENDING
from datetime import datetime, timedelta
from bson import ObjectId
from scanner import scan_code
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler
from marshmallow import Schema, fields, validate, ValidationError

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Enable CORS for all routes
CORS(app)

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/vulnerability_scanner.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Vulnerability Scanner startup')

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
jwt = JWTManager(app)

# Rate Limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# MongoDB Connection
client = MongoClient(os.getenv('MONGO_URI'))
db = client[os.getenv('DB_NAME')]
users_collection = db['users']
scans_collection = db['scans']

# Input Validation Schemas
class ScanRequestSchema(Schema):
    code = fields.Str(required=True, validate=validate.Length(min=1))
    language = fields.Str(required=True, validate=validate.OneOf(['python', 'javascript', 'java']))

class UserSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3))
    password = fields.Str(required=True, validate=validate.Length(min=6))

# Error Handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad Request', 'message': str(error)}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized', 'message': 'Invalid credentials'}), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found', 'message': 'Resource not found'}), 404

@app.errorhandler(429)
def ratelimit_handler(error):
    return jsonify({'error': 'Too Many Requests', 'message': str(error)}), 429

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal Server Error', 'message': str(error)}), 500

# Authentication Endpoints
@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ['username', 'password']):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Check if username exists
        if users_collection.find_one({'username': data['username']}):
            return jsonify({'error': 'Username already exists'}), 400
            
        # Create user document
        user = {
            'username': data['username'],
            'password': data['password'],  # In production, this should be hashed
            'created_at': datetime.utcnow(),
            'last_login': None,
            'scan_count': 0
        }
        
        # Insert user
        result = users_collection.insert_one(user)
        
        # Create access token
        access_token = create_access_token(identity=str(result.inserted_id))
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': str(result.inserted_id),
            'token': access_token
        }), 201
        
    except Exception as e:
        app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """Login and get access token"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ['username', 'password']):
            return jsonify({'error': 'Missing username or password'}), 400
            
        # Find user
        user = users_collection.find_one({'username': data['username']})
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
            
        # Update last login
        users_collection.update_one(
            {'_id': user['_id']},
            {'$set': {'last_login': datetime.utcnow()}}
        )
        
        # Create access token
        access_token = create_access_token(identity=str(user['_id']))
        
        return jsonify({
            'access_token': access_token,
            'user_id': str(user['_id']),
            'username': user['username']
        }), 200
        
    except Exception as e:
        app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

# Scanning Endpoints
@app.route('/api/scan', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def perform_scan():
    """Perform vulnerability scan on provided code"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        # Validate request
        if not data or 'code' not in data:
            return jsonify({'error': 'No code provided'}), 400
            
        # Get language (default to python)
        language = data.get('language', 'python')
        
        # Perform scan
        scan_results = scan_code(data['code'], language)
        
        # Create scan document
        scan_doc = {
            'user_id': ObjectId(user_id),
            'timestamp': datetime.utcnow(),
            'code_snippet': data['code'],
            'language': language,
            'results': scan_results,
            'metadata': {
                'ip_address': request.remote_addr,
                'user_agent': request.user_agent.string
            }
        }
        
        # Save scan results
        result = scans_collection.insert_one(scan_doc)
        
        # Update user scan count
        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$inc': {'scan_count': 1}}
        )
        
        # Return results
        return jsonify({
            'scan_id': str(result.inserted_id),
            'results': scan_results
        }), 200
        
    except Exception as e:
        app.logger.error(f"Scan error: {str(e)}")
        return jsonify({'error': 'Scan failed'}), 500

@app.route('/api/scans', methods=['GET'])
@jwt_required()
def get_scans():
    """Get scan history for the authenticated user"""
    try:
        user_id = get_jwt_identity()
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Calculate skip
        skip = (page - 1) * per_page
        
        # Get total count
        total_scans = scans_collection.count_documents({'user_id': ObjectId(user_id)})
        
        # Get scans
        scans = list(scans_collection.find(
            {'user_id': ObjectId(user_id)},
            {'code_snippet': 0}  # Exclude code snippet for performance
        ).sort('timestamp', DESCENDING)
         .skip(skip)
         .limit(per_page))
        
        # Convert ObjectId to string
        for scan in scans:
            scan['_id'] = str(scan['_id'])
            scan['user_id'] = str(scan['user_id'])
            scan['timestamp'] = scan['timestamp'].isoformat()
        
        return jsonify({
            'scans': scans,
            'pagination': {
                'total': total_scans,
                'page': page,
                'per_page': per_page,
                'pages': (total_scans + per_page - 1) // per_page
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Get scans error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve scans'}), 500

@app.route('/api/scans/<scan_id>', methods=['GET'])
@jwt_required()
def get_scan_details(scan_id):
    """Get detailed results for a specific scan"""
    try:
        user_id = get_jwt_identity()
        
        # Find scan
        scan = scans_collection.find_one({
            '_id': ObjectId(scan_id),
            'user_id': ObjectId(user_id)
        })
        
        if not scan:
            return jsonify({'error': 'Scan not found'}), 404
            
        # Convert ObjectId to string
        scan['_id'] = str(scan['_id'])
        scan['user_id'] = str(scan['user_id'])
        scan['timestamp'] = scan['timestamp'].isoformat()
        
        return jsonify(scan), 200
        
    except Exception as e:
        app.logger.error(f"Get scan details error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve scan details'}), 500

@app.route('/api/scans/<scan_id>', methods=['DELETE'])
@jwt_required()
def delete_scan(scan_id):
    """Delete a specific scan"""
    try:
        user_id = get_jwt_identity()
        
        # Delete scan
        result = scans_collection.delete_one({
            '_id': ObjectId(scan_id),
            'user_id': ObjectId(user_id)
        })
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Scan not found'}), 404
            
        return jsonify({'message': 'Scan deleted successfully'}), 200
        
    except Exception as e:
        app.logger.error(f"Delete scan error: {str(e)}")
        return jsonify({'error': 'Failed to delete scan'}), 500

if __name__ == '__main__':
    # Enable debug mode and bind to all interfaces
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
