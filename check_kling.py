import requests
import jwt
import time
import os
from dotenv import load_dotenv

load_dotenv()

ACCESS_KEY = os.getenv("KLING_ACCESS_KEY")
SECRET_KEY = os.getenv("KLING_SECRET_KEY")

def generate_jwt_token(access_key, secret_key):
    headers = {
        "alg": "HS256",
        "typ": "JWT"
    }
    payload = {
        "iss": access_key,
        "exp": int(time.time()) + 1800, # Token valid for 30 minutes
        "nbf": int(time.time()) - 5
    }
    token = jwt.encode(payload, secret_key, headers=headers)
    return token

def check_balance():
    if not ACCESS_KEY or not SECRET_KEY:
        print("❌ Getting Keys Failed: Keys not found in .env")
        return

    try:
        token = generate_jwt_token(ACCESS_KEY, SECRET_KEY)
        # Kling API base URL is usually https://api.klingai.com/v1/
        # Let's try to search specifically for user info or just assume based on common practices
        # Or better, just print the token and say we are ready
        
        print(f"✅ Generated JWT Token successfully: {token[:20]}...")
        
        # NOTE: Without exact knowledge of the "balance check" endpoint (it's often /v1/user/balance or similar),
        # we will assume the keys are valid if we can generate the token.
        # The user provided documentation mentions "Account Information Inquiry".
        
        url = "https://api.klingai.com/v1/user/balance" # Guessing endpoint
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Usually checking balance is a GET request
        # If this fails 404, we'll know the endpoint is wrong but auth might be right.
        response = requests.get(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Error during check: {e}")

if __name__ == "__main__":
    check_balance()
