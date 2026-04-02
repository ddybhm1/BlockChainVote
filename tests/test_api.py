import requests
import json

# Test login
response = requests.post(
    'http://localhost:8000/api/auth/login',
    json={'student_id': '2025001', 'password': '123456'}
)
print("Login Response:")
print(json.dumps(response.json(), indent=2))

# Extract token
if response.status_code == 200:
    token = response.json().get('token')  # Note: field name is 'token', not 'access_token'
    
    # Test my-elections endpoint
    headers = {'Authorization': f'Bearer {token}'}
    elections_response = requests.get(
        'http://localhost:8000/api/auth/my-elections',
        headers=headers
    )
    print("\nMy Elections Response:")
    elections_data = elections_response.json()
    print(json.dumps(elections_data, indent=2))
    
    # Count the results
    if isinstance(elections_data, list):
        print(f"\nTotal elections returned: {len(elections_data)}")
else:
    print(f"Login failed with status {response.status_code}")

