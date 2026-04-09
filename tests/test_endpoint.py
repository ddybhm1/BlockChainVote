import httpx
import sys
import logging

def check_endpoint():
    try:
        # Check running server
        client = httpx.Client()
        res = client.get('http://localhost:8000/api/admin/voters-count?election_address=test')
        print(f"Status Code: {res.status_code}")
        print(res.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_endpoint()
