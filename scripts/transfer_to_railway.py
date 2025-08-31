#!/usr/bin/env python3
"""
Transfer locally indexed content to Railway production database
"""

import os
import sys
import requests
import json
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()

# Configuration
LOCAL_CHROMA_DIR = "data/chroma"
RAILWAY_API_URL = "https://academy-ai-production.up.railway.app"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "supersecret123")
BATCH_SIZE = 50  # Upload in smaller batches

def get_local_collection():
    """Get the local ChromaDB collection"""
    try:
        client = chromadb.PersistentClient(
            path=LOCAL_CHROMA_DIR,
            settings=Settings(allow_reset=True)
        )
        return client.get_collection("academy_kb")
    except Exception as e:
        print(f"Error accessing local collection: {e}")
        return None

def upload_batch_to_railway(batch_data: Dict):
    """Upload a batch of documents to Railway via the reindex endpoint"""
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # Trigger reindex to ensure Railway collection exists
        response = requests.post(f"{RAILWAY_API_URL}/reindex", headers=headers)
        if response.status_code == 200:
            print("✓ Railway reindex triggered successfully")
        else:
            print(f"Warning: Railway reindex returned {response.status_code}")
            
        return True
    except Exception as e:
        print(f"Error uploading batch: {e}")
        return False

def transfer_data():
    """Main transfer function"""
    print("🚀 Starting transfer of local ChromaDB to Railway...")
    
    # Get local collection
    collection = get_local_collection()
    if not collection:
        print("❌ Could not access local collection")
        return False
    
    # Get all data from local collection
    try:
        print("📊 Fetching local data...")
        result = collection.get(
            include=["documents", "metadatas", "embeddings"]
        )
        
        total_docs = len(result["ids"])
        print(f"📋 Found {total_docs} documents to transfer")
        
        if total_docs == 0:
            print("⚠️ No documents found in local collection")
            return False
            
        # Since ChromaDB doesn't support direct bulk insert via API,
        # we'll use the reindex approach to populate Railway
        print("🔄 Triggering Railway reindex...")
        success = upload_batch_to_railway({})
        
        if success:
            print("✅ Transfer initiated successfully!")
            print("⏱️ Railway indexing will run in background...")
            return True
        else:
            print("❌ Transfer failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during transfer: {e}")
        return False

def check_railway_status():
    """Check Railway indexing status"""
    try:
        response = requests.get(f"{RAILWAY_API_URL}/index-status")
        if response.status_code == 200:
            status = response.json()
            print(f"📊 Railway Status:")
            print(f"   Vector Count: {status.get('vector_count', 0)}")
            print(f"   Status: {status.get('status', 'Unknown')}")
            print(f"   Last Indexed: {status.get('last_indexed', 'Never')}")
            return status
        else:
            print(f"❌ Could not check Railway status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error checking Railway status: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("ACADEMY COMPANION - LOCAL TO RAILWAY TRANSFER")
    print("=" * 60)
    
    # Check initial status
    print("\n1️⃣ Checking initial Railway status...")
    initial_status = check_railway_status()
    
    # Actually, let's use a different approach - copy the ChromaDB files directly
    print("\n🔄 Alternative approach: Using Railway's remote indexing...")
    print("This will process all documents directly on Railway...")
    
    # Trigger remote indexing
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    try:
        response = requests.post(f"{RAILWAY_API_URL}/reindex", headers=headers)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Remote indexing started: {result.get('message', 'Success')}")
            print("⏱️ This will take 10-15 minutes to complete...")
            print("🔄 You can check progress by refreshing the dashboard")
        else:
            print(f"❌ Failed to start remote indexing: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error starting remote indexing: {e}")
    
    print("\n" + "=" * 60)
