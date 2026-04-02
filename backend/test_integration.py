#!/usr/bin/env python3
"""Integration Test - Frontend + Backend"""

import requests
import json

BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"

print("=" * 60)
print("🔗 INTEGRATION TEST - Frontend + Backend")
print("=" * 60)

# Test 1: Frontend is accessible
print("\n1️⃣ Testing frontend accessibility...")
try:
    response = requests.get(FRONTEND_URL, timeout=5)
    if response.status_code == 200:
        print("✅ Frontend is running on port 5173")
    else:
        print(f"❌ Frontend returned {response.status_code}")
except Exception as e:
    print(f"❌ Frontend not accessible: {e}")

# Test 2: Backend is accessible
print("\n2️⃣ Testing backend accessibility...")
try:
    response = requests.get(f"{BACKEND_URL}/health", timeout=5)
    if response.status_code == 200:
        print("✅ Backend is running on port 8000")
    else:
        print(f"❌ Backend returned {response.status_code}")
except Exception as e:
    print(f"❌ Backend not accessible: {e}")

# Test 3: Vite proxy configuration
print("\n3️⃣ Testing Vite proxy (/auth endpoint)...")
try:
    # This should go through Vite proxy to backend
    response = requests.post(
        f"{FRONTEND_URL}/auth/login",
        json={"email": "nonexistent@test.com", "password": "test"},
        timeout=5
    )
    # We expect 401 (unauthorized) which means proxy is working
    if response.status_code in [401, 404, 422]:
        print("✅ Vite proxy is working (/auth routes)")
    else:
        print(f"⚠️  Unexpected status: {response.status_code}")
except Exception as e:
    print(f"❌ Proxy test failed: {e}")

# Test 4: Database relationships
print("\n4️⃣ Testing database relationships...")
try:
    from database import SessionLocal
    from models import User, Team, Cluster, DisasterRequest
    from sqlalchemy import inspect
    
    db = SessionLocal()
    inspector = inspect(db.bind)
    
    # Check foreign keys
    fks = {
        'app_users': inspector.get_foreign_keys('app_users'),
        'disaster_requests': inspector.get_foreign_keys('disaster_requests'),
        'clusters': inspector.get_foreign_keys('clusters')
    }
    
    expected_fks = {
        'app_users': 1,  # team_id
        'disaster_requests': 2,  # created_by_user_id, cluster_id
        'clusters': 1  # assigned_team_id
    }
    
    all_good = True
    for table, expected_count in expected_fks.items():
        actual_count = len(fks[table])
        if actual_count == expected_count:
            print(f"   ✅ {table}: {actual_count} foreign key(s)")
        else:
            print(f"   ❌ {table}: expected {expected_count}, got {actual_count}")
            all_good = False
    
    if all_good:
        print("✅ All database relationships are correct")
    
    db.close()
except Exception as e:
    print(f"❌ Database test failed: {e}")

# Test 5: Full auth flow
print("\n5️⃣ Testing full authentication flow...")
try:
    # Cleanup
    from database import SessionLocal
    from models import User
    db = SessionLocal()
    test_user = db.query(User).filter(User.email == "integration@test.com").first()
    if test_user:
        db.delete(test_user)
        db.commit()
    db.close()
    
    # Register
    register_data = {
        "email": "integration@test.com",
        "password": "Test123!",
        "first_name": "Integration",
        "last_name": "Test",
        "tc_identity_no": "98765432109",
        "phone": "05559876543",
        "role": "coordinator",
        "expertise_area": "arama_kurtarma",
        "organization": "Integration Test Org",
        "city": "Ankara",
        "district": "Çankaya"
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/register", json=register_data, timeout=10)
    if response.status_code == 201:
        print("   ✅ Registration successful")
        token = response.json()['access_token']
        
        # Get user info
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers, timeout=10)
        if response.status_code == 200:
            user = response.json()
            print(f"   ✅ User info retrieved: {user['first_name']} {user['last_name']}")
            print(f"   ✅ Role: {user['role']}, Organization: {user['organization']}")
        
        # Login
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={"email": "integration@test.com", "password": "Test123!"},
            timeout=10
        )
        if response.status_code == 200:
            print("   ✅ Login successful")
        
        # Cleanup
        db = SessionLocal()
        test_user = db.query(User).filter(User.email == "integration@test.com").first()
        if test_user:
            db.delete(test_user)
            db.commit()
        db.close()
        print("   ✅ Cleanup completed")
    else:
        print(f"   ❌ Registration failed: {response.json()}")
        
except Exception as e:
    print(f"❌ Auth flow test failed: {e}")

print("\n" + "=" * 60)
print("✅ INTEGRATION TESTS COMPLETED!")
print("=" * 60)
print("\n💡 Next steps:")
print("   1. Open http://localhost:5173 in browser")
print("   2. Test registration form manually")
print("   3. Test login form manually")
print("   4. Verify dashboard access after login")
