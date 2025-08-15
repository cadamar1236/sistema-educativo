#!/usr/bin/env python3
"""
Simple server launcher for the educational library system
"""

import sys
import os
import uvicorn

# Add the webapp and src directories to Python path
sys.path.insert(0, '/home/user/webapp')
sys.path.insert(0, '/home/user/webapp/src')

if __name__ == "__main__":
    # Set environment variables
    os.environ['PYTHONPATH'] = '/home/user/webapp'
    
    print("🚀 Starting Educational Library System with Unified Wrapper")
    print("=" * 60)
    print("✅ Library service wrapper is active")
    print("✅ Automatic parameter handling enabled")
    print("✅ Support for 20+ file types")
    print("=" * 60)
    
    # Start the server
    uvicorn.run(
        "src.main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )