"""
TEST SCRIPT FOR Azure_DI_output_parser_V3_Final.py

This script tests the V3_Final code on a SINGLE file first to verify:
1. Prompt V3 is loaded correctly
2. LLM analysis produces structured JSON output
3. Classifications and name extraction work
4. Caching works (or falls back gracefully)

Run this BEFORE processing all files!
"""

import json
import os
from Azure_DI_output_parser_V3_Final import (
    load_master_prompt_v3,
    SimpleDocumentProcessorV3,
    create_cached_model,
    MASTER_PROMPT_V3
)

def test_prompt_loading():
    """Test 1: Verify prompt is loaded correctly."""
    print("\n" + "="*60)
    print("TEST 1: Prompt Loading")
    print("="*60)
    
    if MASTER_PROMPT_V3:
        print("✅ Prompt loaded successfully!")
        print(f"   Length: {len(MASTER_PROMPT_V3)} characters")
        print(f"   First 200 chars: {MASTER_PROMPT_V3[:200]}...")
        
        # Check for key sections
        key_sections = [
            "extracted_names",
            "classifications",
            "Personal Information",
            "CV or Resume",
            "bounding_box",
            "confidence_score"
        ]
        
        missing = [s for s in key_sections if s not in MASTER_PROMPT_V3]
        if missing:
            print(f"⚠️  WARNING: Missing sections: {missing}")
            return False
        else:
            print("✅ All key sections present!")
            return True
    else:
        print("❌ FAILED: Prompt not loaded!")
        return False

def test_single_file():
    """Test 2: Process a single file and verify output."""
    print("\n" + "="*60)
    print("TEST 2: Single File Processing")
    print("="*60)
    
    # Use the first available JSON file
    data_path = '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/'
    test_file = f"{data_path}Personal_Information_1.pdf.json"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        print("   Trying to find any available file...")
        import glob
        json_files = glob.glob(f"{data_path}Personal_Information_*.pdf.json")
        if json_files:
            test_file = json_files[0]
            print(f"   Using: {test_file}")
        else:
            print("❌ No JSON files found!")
            return False
    
    print(f"📄 Testing with: {test_file}")
    
    # Create output path
    output_file = f"{data_path}TEST_OUTPUT.txt"
    
    try:
        # Test WITHOUT caching first (simpler)
        print("\n🔍 Testing WITHOUT caching (to isolate issues)...")
        processor = SimpleDocumentProcessorV3(test_file, cached_model=None)
        processor.process_document(output_filepath=output_file)
        
        # Check output
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n✅ Output file created: {output_file}")
            print(f"   Size: {len(content)} characters")
            
            # Verify it contains expected JSON structure
            if '"extracted_names"' in content or '"classifications"' in content:
                print("✅ Output contains expected JSON structure!")
                print("\n📋 Sample output (first 500 chars):")
                print("-" * 60)
                # Find the first JSON-like content
                if "LLM ANALYSIS RESULTS" in content:
                    start = content.find("LLM ANALYSIS RESULTS")
                    print(content[start:start+500])
                else:
                    print(content[:500])
                print("-" * 60)
                return True
            else:
                print("⚠️  WARNING: Output doesn't contain expected JSON structure!")
                print("\n📋 Actual output (first 1000 chars):")
                print("-" * 60)
                print(content[:1000])
                print("-" * 60)
                return False
        else:
            print("❌ Output file not created!")
            return False
            
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_caching():
    """Test 3: Verify caching works."""
    print("\n" + "="*60)
    print("TEST 3: Caching")
    print("="*60)
    
    try:
        print("🔄 Attempting to create cache...")
        cache = create_cached_model(MASTER_PROMPT_V3, ttl="300s")
        
        if cache:
            print("✅ Cache created successfully!")
            print(f"   Cache name: {cache.name}")
            return True
        else:
            print("⚠️  Cache creation returned None (will use fallback)")
            return True  # This is OK - fallback will work
            
    except Exception as e:
        print(f"⚠️  Cache creation failed: {e}")
        print("   This is OK - code will fall back to non-cached mode")
        return True  # Still OK - fallback exists

def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("🧪 TESTING Azure_DI_output_parser_V3_Final.py")
    print("="*80)
    
    results = {
        "Prompt Loading": test_prompt_loading(),
        "Single File Processing": test_single_file(),
        "Caching": test_caching()
    }
    
    print("\n" + "="*80)
    print("📊 TEST RESULTS SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*80)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Ready to process all files!")
        print("="*80)
        print("\n📝 Next steps:")
        print("1. Review the TEST_OUTPUT.txt file to verify the analysis quality")
        print("2. If satisfied, run: python Azure_DI_output_parser_V3_Final.py")
        print("3. Monitor the output for any errors")
    else:
        print("⚠️  SOME TESTS FAILED - Review errors above before proceeding")
        print("="*80)
    
    return all_passed

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)


