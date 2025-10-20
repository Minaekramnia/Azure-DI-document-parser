"""
Simple script to find the MasterPrompt_V4.md file in Databricks
"""

import os
import glob

print("="*80)
print("🔍 SEARCHING FOR MasterPrompt_V4.md")
print("="*80)

# Possible locations
search_paths = [
    '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/',
    '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/',
    '/dbfs/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/',
    '/Workspace/Users/',
    '.',
    '..',
]

print("\n1️⃣ Trying specific paths:")
print("-" * 80)
for base_path in search_paths:
    full_path = os.path.join(base_path, 'MasterPrompt_V4.md')
    print(f"Checking: {full_path}")
    if os.path.exists(full_path):
        print(f"✅ FOUND at: {full_path}")
        try:
            with open(full_path, 'r') as f:
                content = f.read()
            print(f"   File size: {len(content)} characters")
            print(f"   First 100 chars: {content[:100]}")
            print(f"\n🎯 USE THIS PATH IN YOUR CODE:")
            print(f"   '{full_path}'")
            break
        except Exception as e:
            print(f"   ⚠️  Found but can't read: {e}")
    else:
        print(f"   ❌ Not found")

print("\n2️⃣ Searching with glob patterns:")
print("-" * 80)
for base_path in search_paths:
    pattern = os.path.join(base_path, '**/MasterPrompt_V4.md')
    print(f"Pattern: {pattern}")
    matches = glob.glob(pattern, recursive=True)
    if matches:
        print(f"✅ Found {len(matches)} match(es):")
        for match in matches:
            print(f"   {match}")
    else:
        print(f"   ❌ No matches")

print("\n3️⃣ Looking for ANY MasterPrompt files:")
print("-" * 80)
for base_path in search_paths:
    pattern = os.path.join(base_path, '**/MasterPrompt*')
    matches = glob.glob(pattern, recursive=True)
    if matches:
        print(f"✅ Found in {base_path}:")
        for match in matches:
            print(f"   {match}")

print("\n4️⃣ Checking current working directory:")
print("-" * 80)
cwd = os.getcwd()
print(f"Current directory: {cwd}")
files = os.listdir(cwd)
master_files = [f for f in files if 'master' in f.lower() or 'prompt' in f.lower()]
if master_files:
    print(f"✅ Found prompt-related files:")
    for f in master_files:
        print(f"   {f}")
else:
    print("❌ No prompt files in current directory")

print("\n5️⃣ Checking the PI directory contents:")
print("-" * 80)
pi_path = '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/'
print(f"Listing: {pi_path}")
try:
    if os.path.exists(pi_path):
        files = os.listdir(pi_path)
        print(f"✅ Directory exists, contains {len(files)} files")
        
        # Show prompt-related files
        prompt_files = [f for f in files if 'prompt' in f.lower() or 'master' in f.lower()]
        if prompt_files:
            print(f"\nPrompt-related files found:")
            for f in sorted(prompt_files):
                full = os.path.join(pi_path, f)
                size = os.path.getsize(full)
                print(f"   {f} ({size} bytes)")
        else:
            print("\n❌ No prompt files found in this directory")
        
        # Show first 20 files
        print(f"\nFirst 20 files in directory:")
        for f in sorted(files)[:20]:
            print(f"   {f}")
    else:
        print(f"❌ Directory does not exist")
except Exception as e:
    print(f"❌ Error accessing directory: {e}")

print("\n" + "="*80)
print("🎯 SUMMARY")
print("="*80)
print("Copy the correct path from above and use it in your code!")
print("="*80)


