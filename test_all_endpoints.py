#!/usr/bin/env python3
"""
Test script to verify all library endpoints are working
"""

import requests
import json
import tempfile
import os

BASE_URL = "http://localhost:8000"

def test_library_stats():
    """Test library stats endpoint"""
    print("\n🔍 Testing /api/library/stats...")
    response = requests.get(f"{BASE_URL}/api/library/stats")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Success: {data.get('total_documents', 0)} documents")
    else:
        print(f"   ❌ Error: {response.text}")
    return response.status_code == 200

def test_library_documents():
    """Test library documents endpoint"""
    print("\n📚 Testing /api/library/documents...")
    response = requests.get(f"{BASE_URL}/api/library/documents")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Success: {data.get('total_documents', 0)} documents found")
    else:
        print(f"   ❌ Error: {response.text}")
    return response.status_code == 200

def test_library_upload():
    """Test library upload endpoint"""
    print("\n📤 Testing /api/library/upload...")
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document for the library system.")
        temp_file = f.name
    
    try:
        with open(temp_file, 'rb') as f:
            files = {'file': ('test_document.txt', f, 'text/plain')}
            data = {'subject': 'Testing', 'topic': 'API Test'}
            response = requests.post(f"{BASE_URL}/api/library/upload", files=files, data=data)
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: Document ID {data.get('document_id')}")
        else:
            print(f"   ❌ Error: {response.text}")
        return response.status_code == 200
    finally:
        os.unlink(temp_file)

def test_educational_rag_stats():
    """Test educational RAG stats endpoint"""
    print("\n📊 Testing /api/agents/educational-rag/library-stats/test-user...")
    response = requests.get(f"{BASE_URL}/api/agents/educational-rag/library-stats/test-user")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Success: {data.get('stats', {}).get('total_documents', 0)} documents")
    else:
        print(f"   ❌ Error: {response.text}")
    return response.status_code == 200

def main():
    print("=" * 60)
    print("🧪 TESTING LIBRARY ENDPOINTS")
    print("=" * 60)
    
    results = []
    
    # Test all endpoints
    results.append(("Library Stats", test_library_stats()))
    results.append(("Library Documents", test_library_documents()))
    results.append(("Library Upload", test_library_upload()))
    results.append(("Educational RAG Stats", test_educational_rag_stats()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {name}: {status}")
    
    total_passed = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    print("\n" + "=" * 60)
    if total_passed == total_tests:
        print(f"✅ ALL TESTS PASSED ({total_passed}/{total_tests})")
    else:
        print(f"⚠️ SOME TESTS FAILED ({total_passed}/{total_tests})")
    print("=" * 60)

if __name__ == "__main__":
    main()