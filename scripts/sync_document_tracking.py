#!/usr/bin/env python3
"""
Sync the document tracking database with what's actually in ChromaDB
"""

import requests
import json

RAILWAY_API_URL = "https://academy-ai-production.up.railway.app"
ADMIN_TOKEN = "supersecret123"

def sync_documents():
    """Create an endpoint to sync document tracking with ChromaDB contents"""
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    try:
        print("🔄 Triggering document tracking sync...")
        response = requests.post(f"{RAILWAY_API_URL}/admin/sync-documents", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Sync completed: {result}")
        else:
            print(f"❌ Sync failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    sync_documents()
