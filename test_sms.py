import os
import requests
from dotenv import load_dotenv

load_dotenv()

FAST2SMS_API_KEY = os.environ.get("FAST2SMS_API_KEY")

def test_sms():
    url = "https://www.fast2sms.com/dev/bulkV2"
    headers = {
        "authorization": FAST2SMS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "route": "q",
        "message": "Your OTP is 123456",
        "language": "english",
        "flash": 0,
        "numbers": "9019641567"  # User's real test number
    }
    
    print("Testing API Key: <hidden>...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        print("Status Code:", response.status_code)
        print("Response JSON:", response.text)
    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    test_sms()
