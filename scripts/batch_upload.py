#!/usr/bin/env python3
"""
Batch upload documents to Railway via the upload API
"""

import os
import glob
import requests
import time
from pathlib import Path

# Configuration
RAILWAY_API_URL = "https://academy-ai-production.up.railway.app"
ADMIN_TOKEN = "supersecret123"
RAW_DIR = "data/raw"
BATCH_SIZE = 5  # Upload 5 files at a time to avoid timeouts
DELAY_BETWEEN_BATCHES = 2  # seconds

def upload_file(file_path: str) -> bool:
    """Upload a single file to Railway"""
    try:
        headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'text/plain')}
            
            print(f"📤 Uploading: {os.path.basename(file_path)}...", end=" ")
            response = requests.post(
                f"{RAILWAY_API_URL}/admin/upload-document",
                headers=headers,
                files=files,
                timeout=60  # 60 second timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success! ({result.get('chunks', 0)} chunks)")
                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                if response.text:
                    print(f"   Error: {response.text[:100]}...")
                return False
                
    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}...")
        return False

def get_sample_files(limit: int = 20) -> list:
    """Get a sample of markdown files to upload"""
    pattern = os.path.join(RAW_DIR, "**", "*.md")
    all_files = glob.glob(pattern, recursive=True)
    
    # Prioritize certain types of content
    priority_patterns = [
        "**/blog/robertrodriguezjr.com/**",
        "**/ls transcripts/**", 
        "**/creativepathworkshops/**"
    ]
    
    priority_files = []
    for pattern in priority_patterns:
        matches = glob.glob(os.path.join(RAW_DIR, pattern), recursive=True)
        priority_files.extend([f for f in matches if f.endswith('.md')])
    
    # Remove duplicates and take sample
    unique_files = list(set(priority_files))
    return unique_files[:limit]

def main():
    """Main upload function"""
    print("🚀 Starting batch upload to Railway...")
    print(f"📡 Target: {RAILWAY_API_URL}")
    
    # Get sample files to upload
    files_to_upload = get_sample_files(20)  # Start with 20 files
    
    if not files_to_upload:
        print("❌ No files found to upload")
        return
    
    print(f"📋 Found {len(files_to_upload)} files to upload")
    
    # Upload in batches
    total_uploaded = 0
    total_failed = 0
    
    for i in range(0, len(files_to_upload), BATCH_SIZE):
        batch = files_to_upload[i:i+BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        
        print(f"\n📦 Batch {batch_num}/{(len(files_to_upload) + BATCH_SIZE - 1) // BATCH_SIZE}")
        print("-" * 50)
        
        for file_path in batch:
            if upload_file(file_path):
                total_uploaded += 1
            else:
                total_failed += 1
        
        # Delay between batches
        if i + BATCH_SIZE < len(files_to_upload):
            print(f"⏱️ Waiting {DELAY_BETWEEN_BATCHES}s before next batch...")
            time.sleep(DELAY_BETWEEN_BATCHES)
    
    print(f"\n" + "=" * 60)
    print(f"📊 UPLOAD SUMMARY")
    print(f"=" * 60)
    print(f"✅ Successful uploads: {total_uploaded}")
    print(f"❌ Failed uploads: {total_failed}")
    print(f"📈 Success rate: {(total_uploaded/(total_uploaded+total_failed)*100):.1f}%")
    
    # Check final status
    print(f"\n🔍 Checking final status...")
    try:
        response = requests.get(f"{RAILWAY_API_URL}/index-status")
        if response.status_code == 200:
            status = response.json()
            print(f"📊 Vector count: {status.get('vector_count', 0)}")
            print(f"📅 Last indexed: {status.get('last_indexed', 'Never')}")
        else:
            print(f"❌ Could not check status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking status: {e}")

if __name__ == "__main__":
    main()
