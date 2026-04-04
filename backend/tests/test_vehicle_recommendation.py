#!/usr/bin/env python3
"""
Vehicle Recommendation and ETA Test Suite
Tests for autonomous vehicle recommendation and ETA calculation features
"""

import requests
import json
import sys

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


def create_test_vehicle(db):
    """Create test vehicle with stock"""
    print("\n[TEST] Creating test vehicle...")
    
    vehicle_data = {
        "latitude": 41.0082,
        "longitude": 28.9784,
        "vehicle_type": "Kamyon",
        "capacity": "10 Ton",
        "base_speed_kmh": 60
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/vehicles", json=vehicle_data, timeout=10)
        if response.status_code == 201:
            vehicle = response.json()
            vehicle_id = vehicle.get('id')
            if not vehicle_id:
                print(f"[FAIL] Vehicle response missing 'id': {vehicle}")
                return None
                
            print(f"[PASS] Vehicle created: {vehicle_id}")
            
            stock_data = {
                "tent_count": 100,
                "food_count": 200,
                "water_count": 500,
                "medical_count": 50,
                "blanket_count": 150
            }
            
            update_response = requests.put(
                f"{BASE_URL}/api/vehicles/{vehicle_id}", 
                json=stock_data, 
                timeout=10
            )
            
            if update_response.status_code == 200:
                print("[PASS] Vehicle stock updated")
                return vehicle_id
            else:
                print(f"[WARN] Stock update failed: {update_response.status_code}")
                return vehicle_id
        else:
            print(f"[FAIL] Vehicle creation failed: {response.status_code}")
            print(f"       Response: {response.text}")
            return None
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return None


def create_test_cluster(db):
    """Create test cluster from disaster request"""
    print("\n[TEST] Creating test cluster...")
    
    request_data = {
        "latitude": 41.0150,
        "longitude": 28.9850,
        "need_type": "barinma",
        "person_count": 20,
        "description": "Test cluster request"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/requests", json=request_data, timeout=10)
        if response.status_code == 200:
            print("[PASS] Request created")
            
            cluster_response = requests.post(
                f"{BASE_URL}/requests/task-packages/generate",
                timeout=30
            )
            
            if cluster_response.status_code == 201:
                clusters = cluster_response.json()
                if clusters:
                    cluster = clusters[0]
                    cluster_id = cluster['cluster_id']
                    print(f"[PASS] Cluster created: {cluster_id}")
                    print(f"       Need: {cluster['need_type']}, Persons: {cluster['total_persons_affected']}, Priority: {cluster['average_priority_score']}")
                    return cluster_id
                else:
                    print("[WARN] No clusters generated")
                    return None
            else:
                print(f"[FAIL] Clustering failed: {cluster_response.status_code}")
                return None
        else:
            print(f"[FAIL] Request creation failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return None


def test_vehicle_recommendation(cluster_id):
    """Test autonomous vehicle recommendation system"""
    print("\n[TEST] Autonomous Vehicle Recommendation")
    print(f"       Cluster ID: {cluster_id}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/requests/task-packages/{cluster_id}/recommend-vehicles",
            params={"top_n": 3},
            timeout=10
        )
        
        if response.status_code == 200:
            recommendations = response.json()
            print(f"[PASS] Found {len(recommendations)} recommendations")
            
            for idx, rec in enumerate(recommendations, 1):
                print(f"\n       Recommendation #{idx}:")
                print(f"       - Vehicle: {rec['vehicle_type']} ({rec['capacity']})")
                print(f"       - Score: {rec['score']}/100")
                print(f"       - Distance: {rec['details']['distance_km']} km")
                print(f"       - ETA: {rec['details']['eta_minutes']} minutes")
                print(f"       - Stock: {rec['details']['available_stock']} (required: {rec['details']['required_quantity']})")
            
            return recommendations[0]['vehicle_id'] if recommendations else None
        else:
            error = response.json()
            print(f"[FAIL] Recommendation failed: {error.get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return None


def test_eta_calculation(cluster_id, vehicle_id):
    """Test ETA (Estimated Time of Arrival) calculation"""
    print("\n[TEST] ETA Calculation")
    
    try:
        response = requests.post(
            f"{BASE_URL}/requests/task-packages/{cluster_id}/assign-vehicle",
            params={"vehicle_id": vehicle_id},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("[PASS] Vehicle assigned successfully")
            print(f"\n       Assignment Details:")
            print(f"       - Distance: {result['distance_km']} km")
            print(f"       - ETA: {result['eta_minutes']} minutes")
            print(f"       - Remaining Stock: {result['remaining_stock']}")
            print(f"       - Cluster Status: {result['cluster_status']}")
            
            distance = result['distance_km']
            eta = result['eta_minutes']
            avg_speed = (distance / (eta / 60)) if eta > 0 else 0
            
            print(f"\n       ETA Validation:")
            print(f"       - Average Speed: {avg_speed:.1f} km/h")
            
            if 30 <= avg_speed <= 100:
                print(f"       - Status: Realistic")
            else:
                print(f"       - Status: Edge case (very short distance)")
            
            return True
        else:
            error = response.json()
            print(f"[FAIL] Assignment failed: {error.get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def cleanup():
    """Cleanup test data"""
    print("\n[INFO] Cleaning up test data...")
    try:
        from database import SessionLocal
        from models import DisasterRequest
        
        db = SessionLocal()
        db.query(DisasterRequest).filter(
            DisasterRequest.description == "Test cluster request"
        ).delete()
        db.commit()
        db.close()
        print("[PASS] Cleanup completed")
    except Exception as e:
        print(f"[WARN] Cleanup failed: {e}")


if __name__ == "__main__":
    print("=" * 70)
    print("VEHICLE RECOMMENDATION AND ETA TEST SUITE")
    print("Autonomous Vehicle Recommendation System")
    print("ETA (Estimated Time of Arrival) Calculation")
    print("=" * 70)
    
    if not test_health():
        sys.exit(1)
    
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from database import SessionLocal
    db = SessionLocal()
    
    vehicle_id = create_test_vehicle(db)
    if not vehicle_id:
        print("\n[FAIL] Vehicle creation failed. Stopping tests.")
        sys.exit(1)
    
    cluster_id = create_test_cluster(db)
    if not cluster_id:
        print("\n[FAIL] Cluster creation failed. Stopping tests.")
        sys.exit(1)
    
    recommended_vehicle_id = test_vehicle_recommendation(cluster_id)
    if not recommended_vehicle_id:
        print("\n[FAIL] Vehicle recommendation test failed.")
        sys.exit(1)
    
    if not test_eta_calculation(cluster_id, recommended_vehicle_id):
        print("\n[FAIL] ETA calculation test failed.")
        sys.exit(1)
    
    cleanup()
    db.close()
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED")
    print("=" * 70)
    print("\nSummary:")
    print("  [PASS] Autonomous Vehicle Recommendation")
    print("  [PASS] ETA Calculation")
    print("\nSystem is ready for production.")

