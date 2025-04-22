from scanner import scan_code

def test_scanner():
    """Test the vulnerability scanner with various code patterns"""
    
    # Test cases with different vulnerability types
    test_cases = [
        {
            "name": "Credentials Test",
            "code": """
API_KEY = "secret123"
password = "admin123"
TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGc"
""",
            "expected_findings": 3
        },
        {
            "name": "Network Security Test",
            "code": """
url = "http://example.com/api"
backup_url = "http://internal.server/backup"
""",
            "expected_findings": 2
        },
        {
            "name": "Code Execution Test",
            "code": """
user_input = input("Enter command: ")
eval(user_input)
os.system("ls")
""",
            "expected_findings": 3
        },
        {
            "name": "Configuration Test",
            "code": """
DEBUG = True
DEVELOPMENT_MODE = True
""",
            "expected_findings": 2
        }
    ]

    print("🧪 Running Vulnerability Scanner Tests\n")
    
    for test in test_cases:
        print(f"Testing: {test['name']}")
        print("-" * 50)
        
        results = scan_code(test['code'])
        
        # Print findings
        if results['findings']:
            print(f"\nFound {results['total_findings']} vulnerabilities:")
            for finding in results['findings']:
                print(f"\n▶ {finding['severity']} - {finding['category']}")
                print(f"  ↳ {finding['description']}")
                print(f"  ↳ Line {finding['line']}: {finding['code']}")
        else:
            print("No vulnerabilities found.")
            
        # Print severity statistics
        print("\nSeverity Statistics:")
        for severity, count in results['stats']['severity_counts'].items():
            if count > 0:
                print(f"- {severity}: {count}")
                
        print("\nTotal lines scanned:", results['stats']['total_lines_scanned'])
        print("-" * 50 + "\n")

if __name__ == "__main__":
    test_scanner() 