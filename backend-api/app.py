from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from scanner import scan_code
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler
from marshmallow import Schema, fields, validate, ValidationError
import random
import string
from collections import defaultdict
from database import get_collections

# Load environment variables
load_dotenv()

# Get database collections
collections = get_collections()
users_collection = collections['users']
scans_collection = collections['scans']

def generate_short_token():
    """Generate a 4-character token using uppercase letters and numbers"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=4))

def validate_token(token):
    """Validate the token format and check if it exists in the database"""
    if not token or len(token.strip()) != 4:
        return None
    user = users_collection.find_one({'token': token.strip()})
    return user

app = Flask(__name__)
# Enable CORS for all routes
CORS(app, origins=["http://localhost:5173"], supports_credentials=True, allow_headers="*", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/vulnerability_scanner.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.ERROR)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.ERROR)
app.logger.info('Vulnerability Scanner startup')

# Rate Limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

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
    """Register a new user and return an access token"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ['username', 'password']):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Check if username exists
        if users_collection.find_one({'username': data['username']}):
            return jsonify({'error': 'Username already exists'}), 400
            
        # Generate short token
        access_token = generate_short_token()
            
        # Create user document
        user = {
            'username': data['username'],
            'password': data['password'],  # In production, this should be hashed
            'created_at': datetime.utcnow(),
            'last_login': None,
            'scan_count': 0,
            'scans': [],
            'token': access_token
        }
        
        # Insert user
        result = users_collection.insert_one(user)

        return jsonify({
            'message': 'User registered successfully',
            'user_id': str(result.inserted_id),
            'access_token': access_token
        }), 201
        
    except Exception as e:
        app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500


@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("1000 per minute")
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = users_collection.find_one({'username': username})
        if not user or user['password'] != password:
            return jsonify({'error': 'Invalid username or password'}), 401

        # Use the user's existing token
        access_token = user['token']

        # Optionally update last_login
        users_collection.update_one({'_id': user['_id']}, {'$set': {'last_login': datetime.utcnow()}})

        return jsonify({
            'message': 'Login successful',
            'user_id': str(user['_id']),
            'access_token': access_token
        }), 200

    except Exception as e:
        app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500



@app.route('/api/scan', methods=['POST'])
@limiter.limit("1000 per minute")
def perform_scan():
    try:
        data = request.get_json()
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
            
        user = validate_token(auth_header)
        if not user:
            return jsonify({'error': 'Invalid token'}), 401

        if not data or 'code' not in data:
            return jsonify({'error': 'No code provided'}), 400

        language = data.get('language', 'python')
        scan_results = scan_code(data['code'], language)

        scan_id = ObjectId()

        scan_doc = {
            '_id': scan_id,
            'timestamp': datetime.utcnow(),
            'code_snippet': data['code'],
            'language': language,
            'results': scan_results,
            'metadata': {
                'ip_address': request.remote_addr,
                'user_agent': request.user_agent.string
            }
        }

        result = users_collection.update_one(
            {'_id': user['_id']},
            {
                '$push': {'scans': scan_doc},
                '$inc': {'scan_count': 1}
            }
        )

        if result.modified_count == 0:
            return jsonify({'error': 'Failed to update user scans'}), 500

        return jsonify({
            'scan_id': str(scan_id),
            'results': scan_results
        }), 200

    except Exception as e:
        app.logger.error(f"Scan error: {str(e)}")
        return jsonify({'error': 'Scan failed'}), 500

@app.route('/api/scans', methods=['GET'])
@limiter.limit("5000 per hour")
def get_scans():
    try:
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
            
        user = validate_token(auth_header)
        if not user:
            return jsonify({'error': 'Invalid token'}), 401

        if 'scans' not in user:
            return jsonify({'scans': []}), 200

        scans = []
        for scan in user.get('scans', []):
            scan_copy = scan.copy()
            scan_copy['_id'] = str(scan_copy['_id'])

            # Handle top-level timestamp
            ts = scan_copy.get('timestamp')
            if hasattr(ts, 'isoformat'):
                scan_copy['timestamp'] = ts.isoformat()
            else:
                scan_copy['timestamp'] = str(ts) if ts else None

            # Handle nested results.timestamp
            results = scan_copy.get('results')
            if isinstance(results, dict):
                nested_ts = results.get('timestamp')
                if hasattr(nested_ts, 'isoformat'):
                    results['timestamp'] = nested_ts.isoformat()
                elif nested_ts:
                    results['timestamp'] = str(nested_ts)

            scans.append(scan_copy)

        return jsonify({
            'scans': scans,
            'pagination': {
                'total': len(scans),
                'page': 1,
                'per_page': len(scans),
                'pages': 1
            }
        }), 200

    except Exception as e:
        app.logger.error(f"Get scans error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve scans'}), 500

@app.route('/api/scans/<scan_id>', methods=['GET'])
def get_scan_details(scan_id):
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401

        user = validate_token(auth_header)
        if not user:
            return jsonify({'error': 'Invalid token'}), 401

        if 'scans' not in user:
            return jsonify({'error': 'Scan not found'}), 404

        scan = next((s for s in user['scans'] if str(s['_id']) == scan_id), None)
        if not scan:
            return jsonify({'error': 'Scan not found'}), 404

        scan['_id'] = str(scan['_id'])
        scan['timestamp'] = scan['timestamp'].isoformat()
        return jsonify(scan), 200
    except Exception as e:
        app.logger.error(f"Get scan details error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve scan details'}), 500

@app.route('/api/scans/<scan_id>', methods=['DELETE'])
def delete_scan(scan_id):
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401

        user = validate_token(auth_header)
        if not user:
            return jsonify({'error': 'Invalid token'}), 401

        result = users_collection.update_one(
            {'_id': user['_id']},
            {'$pull': {'scans': {'_id': ObjectId(scan_id)}}}
        )

        if result.modified_count == 0:
            return jsonify({'error': 'Scan not found'}), 404

        return jsonify({'message': 'Scan deleted successfully'}), 200
    except Exception as e:
        app.logger.error(f"Delete scan error: {str(e)}")
        return jsonify({'error': 'Failed to delete scan'}), 500

# Admin: List all users
@app.route('/api/admin/users', methods=['GET'])
def admin_get_users():
    users = list(users_collection.find({}))
    for user in users:
        user['_id'] = str(user['_id'])
    return jsonify({'users': users})

# Admin: List all scans (across all users)
@app.route('/api/admin/scans', methods=['GET'])
def admin_get_scans():
    scans = []
    for user in users_collection.find({}):
        for scan in user.get('scans', []):
            scan_copy = scan.copy()
            scan_copy['_id'] = str(scan_copy['_id'])
            scan_copy['user'] = user['username']
            scans.append(scan_copy)
    return jsonify({'scans': scans})

# Admin: Delete a user
@app.route('/api/admin/users/<user_id>', methods=['DELETE'])
def admin_delete_user(user_id):
    result = users_collection.delete_one({'_id': ObjectId(user_id)})
    return jsonify({'success': result.deleted_count == 1})

# Admin: Delete a scan
@app.route('/api/admin/scans/<scan_id>', methods=['DELETE'])
def admin_delete_scan(scan_id):
    result = users_collection.update_many(
        {},
        {'$pull': {'scans': {'_id': ObjectId(scan_id)}}}
    )
    return jsonify({'success': result.modified_count > 0})

# Admin: System stats
@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    users = list(users_collection.find({}))
    user_count = len(users)
    scan_count = 0
    scans_by_language = {}
    findings = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    recent_activity = []
    all_scans = []

    for user in users:
        user_scans = user.get('scans', [])
        scan_count += len(user_scans)
        for scan in user_scans:
            lang = scan.get('language', 'Unknown')
            scans_by_language[lang] = scans_by_language.get(lang, 0) + 1
            # Count findings by severity if present
            results = scan.get('results', {})
            if isinstance(results, dict):
                for finding in results.get('findings', []):
                    sev = finding.get('severity', '').lower()
                    if sev in findings:
                        findings[sev] += 1
            # Collect for recent activity
            all_scans.append({
                "type": "scan",
                "description": f"Scan by {user.get('username', 'unknown')}",
                "date": scan.get('timestamp', datetime.utcnow()).isoformat()
            })
    # Recent user registrations
    for user in users:
        recent_activity.append({
            "type": "user_created",
            "description": f"User registered: {user.get('username', 'unknown')}",
            "date": user.get('created_at', datetime.utcnow()).isoformat()
        })
    # Combine and sort by date (most recent first)
    recent_activity.extend(all_scans)
    recent_activity = sorted(recent_activity, key=lambda x: x['date'], reverse=True)[:10]

    # --- Trends Overview ---
    trends = defaultdict(lambda: {"scans": 0, "findings": 0, "users": set()})
    for user in users:
        username = user.get('username', 'unknown')
        for scan in user.get('scans', []):
            ts = scan.get('timestamp')
            if ts:
                day = ts.date() if hasattr(ts, 'date') else datetime.fromisoformat(str(ts)).date()
                trends[day]["scans"] += 1
                trends[day]["users"].add(username)
                results = scan.get('results', {})
                if isinstance(results, dict):
                    findings_list = results.get('findings', [])
                    trends[day]["findings"] += len(findings_list)
    trendsData = [
        {"date": day.isoformat(), "scans": v["scans"], "findings": v["findings"], "users": len(v["users"])}
        for day, v in sorted(trends.items())
    ]

    # --- User Growth ---
    user_growth = defaultdict(lambda: {"users": 0, "activeUsers": 0})
    for user in users:
        created = user.get('created_at')
        if created:
            month = created.strftime('%Y-%m') if hasattr(created, 'strftime') else str(created)[:7]
            user_growth[month]["users"] += 1
            if user.get('scan_count', 0) > 0:
                user_growth[month]["activeUsers"] += 1
    userGrowth = [
        {"month": month, "users": v["users"], "activeUsers": v["activeUsers"]}
        for month, v in sorted(user_growth.items())
    ]

    # --- Vulnerability Types ---
    vuln_types = defaultdict(int)
    for user in users:
        for scan in user.get('scans', []):
            results = scan.get('results', {})
            if isinstance(results, dict):
                for finding in results.get('findings', []):
                    cat = finding.get('category', 'Unknown')
                    vuln_types[cat] += 1
    vulnerabilityTypes = [
        {"type": cat, "count": count} for cat, count in vuln_types.items()
    ]

    # --- Findings per Scan Distribution ---
    findings_dist = {"0": 0, "1": 0, "2": 0, "3+": 0}
    for user in users:
        for scan in user.get('scans', []):
            results = scan.get('results', {})
            findings_count = 0
            if isinstance(results, dict):
                findings_count = len(results.get('findings', []))
            if findings_count == 0:
                findings_dist["0"] += 1
            elif findings_count == 1:
                findings_dist["1"] += 1
            elif findings_count == 2:
                findings_dist["2"] += 1
            else:
                findings_dist["3+"] += 1
    findingsPerScan = [
        {"range": k, "count": v} for k, v in findings_dist.items()
    ]

    # --- Scans This Week ---
    today = datetime.utcnow()
    start_of_week = today - timedelta(days=today.weekday())
    scans_this_week = 0
    for user in users:
        for scan in user.get('scans', []):
            ts = scan.get('timestamp')
            if ts:
                scan_date = ts if isinstance(ts, datetime) else datetime.fromisoformat(str(ts))
                if scan_date >= start_of_week:
                    scans_this_week += 1

    # --- Weekly Scans (bar graph) ---
    today = datetime.utcnow()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    week_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    daily_counts = {i: 0 for i in range(7)}  # 0=Mon, 6=Sun
    for user in users:
        for scan in user.get('scans', []):
            ts = scan.get('timestamp')
            if ts:
                if isinstance(ts, datetime):
                    if ts.tzinfo is not None:
                        scan_date = ts.astimezone(timezone.utc).replace(tzinfo=None)
                    else:
                        scan_date = ts
                else:
                    scan_date = datetime.fromisoformat(str(ts))
                    if scan_date.tzinfo is not None:
                        scan_date = scan_date.astimezone(timezone.utc).replace(tzinfo=None)
                if scan_date >= start_of_week:
                    day_idx = scan_date.weekday()
                    daily_counts[day_idx] += 1

    weeklyScans = [
        {"day": week_days[i], "count": daily_counts[i]} for i in range(7)
    ]

    stats = {
        "totalUsers": user_count,
        "totalScans": scan_count,
        "findings": findings,
        "scansByLanguage": [{"language": lang, "count": count} for lang, count in scans_by_language.items()],
        "recentActivity": recent_activity,
        "trendsData": trendsData,
        "userGrowth": userGrowth,
        "vulnerabilityTypes": vulnerabilityTypes,
        "findingsPerScan": findingsPerScan,
        "scansThisWeek": scans_this_week,
        "weeklyScans": weeklyScans
    }
    return jsonify(stats)

@app.route('/api/admin/scans/<scan_id>', methods=['GET'])
def admin_get_scan_details(scan_id):
    for user in users_collection.find({}):
        scan = next((s for s in user.get('scans', []) if str(s['_id']) == scan_id), None)
        if scan:
            scan['_id'] = str(scan['_id'])
            scan['timestamp'] = scan['timestamp'].isoformat() if hasattr(scan['timestamp'], 'isoformat') else str(scan['timestamp'])
            scan['user'] = user['username']
            # Always provide findings at the top level
            if 'findings' not in scan or not isinstance(scan['findings'], list):
                scan['findings'] = scan.get('results', {}).get('findings', [])
            # Ensure code_snippet is included
            if 'code_snippet' not in scan:
                scan['code_snippet'] = scan.get('code_snippet', '')
            return jsonify(scan), 200
    return jsonify({'error': 'Scan not found'}), 404

if __name__ == '__main__':
    # Enable debug mode and bind to all interfaces
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
