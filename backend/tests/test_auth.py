#!/usr/bin/env python3
"""Authentication API Test Script"""

import requests
import json
import sys
import os

BASE_URL = "http://localhost:8000"


def test_health():
    """Test server health"""
    print("\n[INFO] Testing server health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("[PASS] Server is running")
            return True
        else:
            print(f"[FAIL] Server returned {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Server not reachable: {e}")
        print("[INFO] Make sure backend is running: uvicorn main:app --reload")
        return False


def test_register():
    """Test user registration"""
    print("\n[TEST] POST /auth/register")
    
    user_data = {
        "email": "test@example.com",
        "password": "Test123!",
        "first_name": "Test",
        "last_name": "User",
        "tc_identity_no": "12345678901",
        "phone": "05551234567",
        "role": "volunteer",
        "expertise_area": "medikal",
        "organization": "Test Org",
        "city": "İstanbul",
        "district": "Kadıköy",
        "profile_photo_url": "https://example.com/photo.png"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data, timeout=10)
        
        if response.status_code == 201:
            data = response.json()
            print("[PASS] Registration successful")
            print(f"       Token: {data['access_token'][:30]}...")
            print(f"       User: {data['user']['first_name']} {data['user']['last_name']}")
            print(f"       Role: {data['user']['role']}")
            return data['access_token']
        else:
            print(f"[FAIL] Registration failed")
            print(f"       Response: {response.json()}")
            return None
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return None


def test_login():
    """Test user login"""
    print("\n[TEST] POST /auth/login")
    
    credentials = {
        "email": "test@example.com",
        "password": "Test123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=credentials, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("[PASS] Login successful")
            print(f"       Token: {data['access_token'][:30]}...")
            print(f"       User: {data['user']['first_name']} {data['user']['last_name']}")
            return data['access_token']
        else:
            print(f"[FAIL] Login failed")
            print(f"       Response: {response.json()}")
            return None
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return None


def test_get_me(token):
    """Test get current user"""
    print("\n[TEST] GET /auth/me")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("[PASS] Get user successful")
            print(f"       Name: {data['first_name']} {data['last_name']}")
            print(f"       Email: {data['email']}")
            print(f"       Role: {data['role']}")
            print(f"       Organization: {data['organization']}")
            return True
        else:
            print(f"[FAIL] Get user failed")
            print(f"       Response: {response.json()}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def cleanup_test_user():
    """Clean up test user from database"""
    print("\n[INFO] Cleaning up test user...")
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from database import SessionLocal
        from models import User
        
        db = SessionLocal()
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if test_user:
            db.delete(test_user)
            db.commit()
            print("[PASS] Test user deleted")
        else:
            print("[INFO] No test user found")
        db.close()
    except Exception as e:
        print(f"[WARN] Cleanup failed: {e}")


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from routers.auth import get_password_hash, verify_password


def test_password_hashing():
    print("Testing password hashing logic...")
    password = "MySecurePassword123!"
    
    # Hash oluşturma
    hashed = get_password_hash(password)
    print(f"Password: {password}")
    print(f"Hashed: {hashed}")
    
    # Doğrulama (Başarılı durum)
    is_valid = verify_password(password, hashed)
    print(f"Verification (Correct password): {'PASS' if is_valid else 'FAIL'}")
    
    # Doğrulama (Yanlış durum)
    is_invalid = verify_password("WrongPassword", hashed)
    print(f"Verification (Wrong password): {'PASS' if not is_invalid else 'FAIL'}")
    
    if is_valid and not is_invalid:
        print("\nSUCCESS: Password hashing and verification are working correctly with bcrypt!")
        return True
    else:
        print("\nFAILURE: Password hashing or verification failed.")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("AUTHENTICATION API TEST SUITE")
    print("=" * 60)
    
    if not test_health():
        sys.exit(1)
    
    cleanup_test_user()
    success = test_password_hashing()
    if not success:
        sys.exit(1)

    token = test_register()
    if not token:
        print("\n[FAIL] Registration test failed. Stopping tests.")
        sys.exit(1)
    
    test_get_me(token)
    
    token = test_login()
    if not token:
        print("\n[FAIL] Login test failed. Stopping tests.")
        sys.exit(1)
    
    test_get_me(token)
    
    cleanup_test_user()
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)


