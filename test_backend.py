import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def print_result(name, res):
    print(f"\n--- {name} ---")
    print(f"Status: {res.status_code}")
    try:
        print(f"Response: {json.dumps(res.json(), indent=2)}")
    except:
        print(f"Response: {res.text}")

def run_tests():
    print("Checking if backend is up...")
    try:
        res = requests.get(f"{BASE_URL}/")
        print_result("Root Endpoint", res)
    except Exception as e:
        print(f"Backend is not running: {e}")
        return

    # 1. Check DB
    print_result("Check DB", requests.get(f"{BASE_URL}/check-db"))

    # 2. Test Send OTP
    mobile = "9999999999"
    payload = {"mobile": mobile, "isTestMode": True}
    print_result("Send OTP", requests.post(f"{BASE_URL}/send-otp", json=payload))

    # 3. Test Verify OTP (New User)
    verify_payload = {"mobile": mobile, "enteredOtp": "123456"}
    print_result("Verify OTP", requests.post(f"{BASE_URL}/verify-otp", json=verify_payload))

    # 4. Test Register Worker
    register_payload = {
        "phone_number": mobile,
        "role": "worker",
        "name": "Test Worker",
        "categories": ["Cleaning"],
        "location": "Test City",
        "about": "Testing registration",
        "experience": "1 year"
    }
    # Using data instead of json because it uses request.form
    print_result("Register Worker", requests.post(f"{BASE_URL}/register-worker", data=register_payload))

    # 5. Test Verify OTP (Existing User)
    print_result("Verify OTP (Existing)", requests.post(f"{BASE_URL}/verify-otp", json=verify_payload))

    # 6. Test Get Profile
    print_result("Get Profile", requests.get(f"{BASE_URL}/get-profile?phone_number={mobile}"))

    # 7. Test Admin - Get Workers
    print_result("Admin Get Workers", requests.get(f"{BASE_URL}/admin/workers"))

    print("\nAll tests completed.")

if __name__ == "__main__":
    run_tests()
