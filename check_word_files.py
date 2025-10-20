"""
Check Word Files in word_reports folder

This script helps diagnose issues with Word file processing.
"""

import glob
import os

def main():
    """Check what's in the word_reports folder."""
    
    # Path
    data_path = '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/'
    word_folder = os.path.join(data_path, 'word_reports')
    
    print("="*60)
    print("🔍 CHECKING WORD FILES")
    print("="*60)
    print(f"Looking in: {word_folder}")
    print("="*60)
    
    # Check if folder exists
    if not os.path.exists(word_folder):
        print(f"❌ Folder does not exist: {word_folder}")
        print("\n💡 Solution: Run convert_to_word_fixed.py first to create Word documents")
        return
    
    # List all files in folder
    try:
        all_files = os.listdir(word_folder)
        print(f"📁 All files in folder ({len(all_files)} total):")
        for file in sorted(all_files):
            print(f"   - {file}")
    except Exception as e:
        print(f"❌ Cannot list folder contents: {e}")
        return
    
    print()
    
    # Find Word files
    word_files = glob.glob(f"{word_folder}/*.docx")
    print(f"📄 Word files found ({len(word_files)} total):")
    
    if not word_files:
        print("   ❌ No .docx files found!")
        print("\n💡 Possible issues:")
        print("   1. Word documents not created yet")
        print("   2. Files have different extension")
        print("   3. Files in subfolder")
        return
    
    for word_file in sorted(word_files):
        filename = os.path.basename(word_file)
        file_size = os.path.getsize(word_file)
        print(f"   ✅ {filename} ({file_size:,} bytes)")
    
    print()
    print("="*60)
    print("🎯 SUMMARY")
    print("="*60)
    print(f"Folder exists: ✅")
    print(f"Total files: {len(all_files)}")
    print(f"Word files (.docx): {len(word_files)}")
    
    if len(word_files) > 0:
        print(f"\n✅ Ready to run: python remove_names_from_word_FIXED.py")
    else:
        print(f"\n⚠️  No Word files found. Run convert_to_word_fixed.py first")

if __name__ == '__main__':
    main()
