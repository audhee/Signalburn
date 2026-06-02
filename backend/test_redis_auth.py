import os
import sys

# Add backend directory to sys.path so app imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
# Now we can import from app.services.auth
from app.services.auth.auth_service import generate_otp, verify_otp, redis_client

def run_tests():
    try:
        redis_client.ping()
        print("✅ Connected to Redis")
    except Exception as e:
        print("❌ Cannot connect to Redis:", e)
        return

    test_phone = "9999999999"  # should be standardized to +91... and hit dev bypass
    print(f"\n--- Testing Generate OTP for {test_phone} ---")
    otp = generate_otp(test_phone)
    print(f"Generated OTP: {otp}")

    # Check standardize format in redis
    expected_formatted = "+919999999999"
    attempts = redis_client.get(f"{expected_formatted}:attempts")
    otp_stored = redis_client.get(f"{expected_formatted}:otp")
    print(f"Stored Attempts: {attempts}")
    print(f"Stored OTP: {otp_stored}")

    print("\n--- Testing Invalid Verification (Attempt 1) ---")
    try:
        verify_otp(test_phone, "000000")
        print("❌ Should have failed verification")
    except ValueError as e:
        print("✅ ValueError caught:", e)
    except Exception as e:
        print("❌ Unexpected exception:", e)

    attempts = redis_client.get(f"{expected_formatted}:attempts")
    print(f"Stored Attempts after 1 failure: {attempts}")

    print("\n--- Testing Valid Verification ---")
    try:
        res = verify_otp(test_phone, "123456")
        print("✅ Verification successful:", res)
    except Exception as e:
        print("❌ Unexpected exception:", e)

    # Check keys are deleted
    attempts_after = redis_client.get(f"{expected_formatted}:attempts")
    otp_after = redis_client.get(f"{expected_formatted}:otp")
    if not attempts_after and not otp_after:
        print("✅ Keys successfully deleted from Redis")
    else:
        print("❌ Keys were not deleted")

if __name__ == "__main__":
    run_tests()
