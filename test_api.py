#!/usr/bin/env python3
"""
Test script for AI Profile Evaluation Platform
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/profile"

def test_profile_initiate():
    """Test profile initiation endpoint"""
    print("🔹 Testing Profile Initiation...")
    
    profile_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "countries": ["United States", "Canada", "United Kingdom"],
        "degree": "Master of Science",
        "fields": ["Computer Science", "Data Science", "Artificial Intelligence"],
        "cgpa": "3.75",
        "grad_year": "2023",
        "budget_lakh": 50
    }
    
    response = requests.post(f"{BASE_URL}/initiate/", json=profile_data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()
        return {
            'success': True,
            'phone': profile_data['phone'],
            'otp_code': data.get('details')  # For development mode
        }
    else:
        return {'success': False}

def test_profile_verify(phone, otp_code):
    """Test profile verification endpoint"""
    print(f"\n🔹 Testing Profile Verification with OTP: {otp_code}")
    
    verify_data = {
        "phone": phone,
        "otp": otp_code
    }
    
    response = requests.post(f"{BASE_URL}/verify/", json=verify_data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        data = response.json()
        return {
            'success': True,
            'profile': data.get('profile'),
            'evaluation': data.get('evaluation')
        }
    else:
        return {'success': False}

def test_profile_detail(phone):
    """Test profile detail endpoint"""
    print(f"\n🔹 Testing Profile Detail...")
    
    response = requests.get(f"{BASE_URL}/detail/{phone}/")
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def main():
    """Run complete test flow"""
    print("🚀 Starting AI Profile Evaluation Tests")
    print("=" * 60)
    
    # Step 1: Initiate Profile
    initiate_result = test_profile_initiate()
    
    if not initiate_result['success']:
        print("❌ Profile initiation failed")
        return
    
    # Step 2: Verify Profile
    otp_code = initiate_result.get('otp_code', '123456')  # Fallback for testing
    verify_result = test_profile_verify(
        initiate_result['phone'], 
        otp_code
    )
    
    if not verify_result['success']:
        print("❌ Profile verification failed")
        return
    
    print("✅ Profile created and evaluated successfully!")
    
    # Step 3: Get Profile Detail
    if test_profile_detail(initiate_result['phone']):
        print("✅ Profile detail retrieved successfully!")
    
    print("\n" + "=" * 60)
    print("🏁 AI Profile Evaluation Tests Completed!")

if __name__ == "__main__":
    main()