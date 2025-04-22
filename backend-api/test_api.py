import requests
import json

BASE_URL = 'http://localhost:5000/api'

def test_api():
    # Test data
    test_user = {
        'username': 'testuser',
        'password': 'Test123!',
        'email': 'test@example.com'
    }
    
    test_code = '''
    API_KEY = "secret123"
    http://example.com
    eval("2 + 2")
    '''
    
    print("🧪 Testing API Endpoints\n")
    
    # 1. Register User
    print("1. Testing Registration")
    print("-" * 50)
    response = requests.post(f'{BASE_URL}/auth/register', json=test_user)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    
    # 2. Login
    print("2. Testing Login")
    print("-" * 50)
    response = requests.post(f'{BASE_URL}/auth/login', 
                           json={'username': test_user['username'], 
                                'password': test_user['password']})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    
    if response.status_code == 200:
        token = response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # 3. Perform Scan
        print("3. Testing Code Scan")
        print("-" * 50)
        response = requests.post(f'{BASE_URL}/scan', 
                               headers=headers,
                               json={'code': test_code, 'language': 'python'})
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
        
        if response.status_code == 200:
            scan_id = response.json()['scan_id']
            
            # 4. Get Scan History
            print("4. Testing Scan History")
            print("-" * 50)
            response = requests.get(f'{BASE_URL}/scans', headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}\n")
            
            # 5. Get Specific Scan
            print("5. Testing Get Specific Scan")
            print("-" * 50)
            response = requests.get(f'{BASE_URL}/scans/{scan_id}', headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}\n")
            
            # 6. Delete Scan
            print("6. Testing Delete Scan")
            print("-" * 50)
            response = requests.delete(f'{BASE_URL}/scans/{scan_id}', headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}\n")

if __name__ == "__main__":
    test_api() 