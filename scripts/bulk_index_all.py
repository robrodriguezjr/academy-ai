#!/usr/bin/env python3
"""
Efficiently index all documents from data/raw to Railway production
"""

import os
import glob
import requests
import time
import json
from pathlib import Path

# Configuration
RAILWAY_API_URL = "https://academy-ai-production.up.railway.app"
ADMIN_TOKEN = "supersecret123"
RAW_DIR = "data/raw"
BATCH_SIZE = 10  # Files per batch
DELAY_BETWEEN_BATCHES = 3  # seconds
MAX_FILE_SIZE = 1024 * 1024  # 1MB limit

def get_all_markdown_files():
    """Get all markdown files from data/raw"""
    pattern = os.path.join(RAW_DIR, "**", "*.md")
    all_files = glob.glob(pattern, recursive=True)
    
    # Filter out very large files and sort by size (smaller first)
    valid_files = []
    for file_path in all_files:
        try:
            size = os.path.getsize(file_path)
            if size < MAX_FILE_SIZE:
                valid_files.append((file_path, size))
            else:
                print(f"⚠️  Skipping large file: {os.path.basename(file_path)} ({size/1024:.1f}KB)")
        except:
            continue
    
    # Sort by size (smaller files first for faster initial progress)
    valid_files.sort(key=lambda x: x[1])
    return [f[0] for f in valid_files]

def upload_file(file_path: str) -> dict:
    """Upload a single file and return result"""
    try:
        headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        filename = os.path.basename(file_path)
        
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f, 'text/plain')}
            
            response = requests.post(
                f"{RAILWAY_API_URL}/admin/upload-document",
                headers=headers,
                files=files,
                timeout=120  # 2 minute timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "filename": filename,
                    "chunks": result.get("chunks", 0),
                    "title": result.get("title", filename)
                }
            else:
                return {
                    "status": "error",
                    "filename": filename,
                    "error": f"HTTP {response.status_code}: {response.text[:100]}"
                }
                
    except Exception as e:
        return {
            "status": "error", 
            "filename": os.path.basename(file_path),
            "error": str(e)[:100]
        }

def get_current_status():
    """Get current indexing status"""
    try:
        response = requests.get(f"{RAILWAY_API_URL}/index-status")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {"vector_count": 0, "status": "unknown"}

def main():
    print("🚀 BULK INDEXING ALL DOCUMENTS TO RAILWAY")
    print("=" * 60)
    
    # Get initial status
    initial_status = get_current_status()
    print(f"📊 Starting vector count: {initial_status.get('vector_count', 0)}")
    
    # Get all files
    files_to_upload = get_all_markdown_files()
    total_files = len(files_to_upload)
    
    print(f"📋 Found {total_files} markdown files to index")
    print(f"⚙️  Batch size: {BATCH_SIZE} files")
    print(f"⏱️  Delay between batches: {DELAY_BETWEEN_BATCHES}s")
    print(f"🎯 Estimated time: {(total_files/BATCH_SIZE * DELAY_BETWEEN_BATCHES)/60:.1f} minutes")
    
    # Process in batches
    total_uploaded = 0
    total_failed = 0
    total_chunks = 0
    
    for i in range(0, total_files, BATCH_SIZE):
        batch = files_to_upload[i:i+BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (total_files + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"\n📦 Batch {batch_num}/{total_batches} ({len(batch)} files)")
        print("-" * 50)
        
        batch_success = 0
        batch_chunks = 0
        
        for file_path in batch:
            result = upload_file(file_path)
            
            if result["status"] == "success":
                chunks = result["chunks"]
                print(f"✅ {result['filename']} ({chunks} chunks)")
                total_uploaded += 1
                batch_success += 1
                batch_chunks += chunks
                total_chunks += chunks
            else:
                print(f"❌ {result['filename']}: {result['error']}")
                total_failed += 1
        
        # Batch summary
        print(f"   📈 Batch: {batch_success}/{len(batch)} success, {batch_chunks} chunks")
        print(f"   📊 Total: {total_uploaded}/{total_uploaded+total_failed} files, {total_chunks} chunks")
        
        # Progress update
        progress = ((i + len(batch)) / total_files) * 100
        print(f"   🎯 Progress: {progress:.1f}% complete")
        
        # Check current vector count
        if batch_num % 5 == 0:  # Every 5 batches
            current_status = get_current_status()
            current_vectors = current_status.get("vector_count", 0)
            print(f"   📊 Current vectors in database: {current_vectors}")
        
        # Delay between batches (except for the last one)
        if i + BATCH_SIZE < total_files:
            print(f"   ⏱️  Waiting {DELAY_BETWEEN_BATCHES}s before next batch...")
            time.sleep(DELAY_BETWEEN_BATCHES)
    
    # Final summary
    print(f"\n" + "=" * 60)
    print(f"🏁 INDEXING COMPLETE!")
    print(f"=" * 60)
    print(f"✅ Successfully indexed: {total_uploaded} documents")
    print(f"❌ Failed: {total_failed} documents")
    print(f"📈 Success rate: {(total_uploaded/(total_uploaded+total_failed)*100):.1f}%")
    print(f"🧩 Total chunks created: {total_chunks}")
    
    # Final status check
    final_status = get_current_status()
    final_vectors = final_status.get("vector_count", 0)
    print(f"📊 Final vector count: {final_vectors}")
    print(f"📈 Vectors added: {final_vectors - initial_status.get('vector_count', 0)}")
    
    if total_failed > 0:
        print(f"\n⚠️  {total_failed} files failed to upload. Check logs above for details.")

if __name__ == "__main__":
    main()




