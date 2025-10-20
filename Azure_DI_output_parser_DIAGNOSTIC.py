"""
DIAGNOSTIC VERSION - Shows EXACTLY what's happening with the prompt
"""

import json
import glob
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from itsai.llm_registry import vertex
from itsai.google import load_credentials_from_environment, get_google_credentials
from itsai.mai import llm
from itsai import llm_registry


def load_master_prompt():
    """Load MasterPrompt_V4.md from file."""
    paths = [
        '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/MasterPrompt_V4.md',
        'MasterPrompt_V4.md',
    ]
    
    for path in paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"✅ Loaded MasterPrompt_V4.md from: {path}")
            print(f"   Prompt length: {len(content)} characters")
            print(f"   First 200 chars of prompt:")
            print(f"   {content[:200]}")
            return content
        except:
            continue
    
    print("❌ Could not find MasterPrompt_V4.md")
    return None


# Load prompt
MASTER_PROMPT = load_master_prompt()

if not MASTER_PROMPT:
    print("ERROR: Cannot proceed without prompt file")
    exit(1)

print("\n" + "="*80)
print("DIAGNOSTIC: Checking what's in MASTER_PROMPT variable")
print("="*80)
print(f"MASTER_PROMPT length: {len(MASTER_PROMPT)} chars")
print(f"MASTER_PROMPT first line: {MASTER_PROMPT.split(chr(10))[0]}")
print(f"Contains 'classified_content': {'classified_content' in MASTER_PROMPT}")
print(f"Contains 'extracted_names': {'extracted_names' in MASTER_PROMPT}")
print("="*80 + "\n")


def delete_old_caches():
    """Delete ALL old caches."""
    print("\n🗑️  DELETING ALL OLD CACHES...")
    
    try:
        load_dotenv()
        creds = load_credentials_from_environment()
        g = get_google_credentials()
        
        client = genai.Client(
            vertexai=True, 
            project=creds.project_id, 
            location=g.google_vertex_region, 
            credentials=creds
        )
        
        caches = list(client.caches.list())
        
        if not caches:
            print("✅ No old caches found")
            return True
        
        print(f"   Found {len(caches)} existing cache(s)")
        
        for cache in caches:
            print(f"   Deleting: {cache.display_name}")
            client.caches.delete(name=cache.name)
        
        print(f"✅ Deleted {len(caches)} old cache(s)\n")
        return True
        
    except Exception as e:
        print(f"⚠️  Could not delete old caches: {e}\n")
        return False


def create_cached_model(system_instruction, ttl="600s"):
    """Create cache with diagnostic output."""
    print("🔄 Creating NEW cache...")
    print(f"   System instruction length: {len(system_instruction)} chars")
    print(f"   System instruction first 100 chars:")
    print(f"   {system_instruction[:100]}")
    
    try:
        load_dotenv()
        creds = load_credentials_from_environment()
        g = get_google_credentials()
        
        client = genai.Client(
            vertexai=True, 
            project=creds.project_id, 
            location=g.google_vertex_region, 
            credentials=creds
        )
        
        model = vertex.Gemini.PRO_2_5
        
        print(f"\n   Creating cache with display_name='masterprompt_v4_diagnostic'")
        cache = client.caches.create(
            model=model,
            config=types.CreateCachedContentConfig(
                display_name='masterprompt_v4_diagnostic',
                system_instruction=system_instruction,
                ttl=ttl,
            )
        )
        
        print(f"✅ Cache created: {cache.name}")
        print(f"   Cache display name: {cache.display_name}")
        print(f"   Cache TTL: {ttl}")
        
        # DIAGNOSTIC: Check what's in the cache
        print(f"\n🔍 DIAGNOSTIC: Cache object inspection")
        print(f"   Cache type: {type(cache)}")
        print(f"   Cache attributes: {dir(cache)}")
        if hasattr(cache, 'system_instruction'):
            print(f"   Cache has system_instruction attribute!")
            print(f"   System instruction length: {len(str(cache.system_instruction))}")
        else:
            print(f"   ⚠️  Cache does NOT have system_instruction attribute")
        
        return cache
        
    except Exception as e:
        print(f"❌ Error creating cache: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_cache_usage(cached_model):
    """Test if the cache is actually being used correctly."""
    print("\n" + "="*80)
    print("🧪 TESTING CACHE USAGE")
    print("="*80)
    
    test_content = """
    === PAGE 1 ===
    [Role: title, BBox: 100,200,300,250]
    Employment History
    
    [Role: paragraph, BBox: 100,260,300,300]
    Work Experience at ABC Company from 2020 to 2023.
    """
    
    try:
        gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
        
        print(f"\n   Sending test request with cached_content")
        print(f"   Test content length: {len(test_content)} chars")
        
        message = gemini.invoke(
            f"Document Content to Analyze:\n{test_content}",
            model_kwargs={'cached_content': cached_model}
        )
        
        result = message.content
        
        print(f"\n✅ LLM Response received")
        print(f"   Response length: {len(result)} chars")
        print(f"   Response first 300 chars:")
        print(f"   {result[:300]}")
        
        # Check if response follows MasterPrompt_V4 format
        try:
            json_result = json.loads(result)
            print(f"\n✅ Response is valid JSON")
            print(f"   JSON keys: {list(json_result.keys())}")
            
            if "classified_content" in json_result:
                print(f"   ✅ Has 'classified_content' - CORRECT FORMAT!")
            else:
                print(f"   ❌ Missing 'classified_content' - WRONG FORMAT!")
            
            if "extracted_names" in json_result:
                print(f"   ✅ Has 'extracted_names' - CORRECT FORMAT!")
            else:
                print(f"   ❌ Missing 'extracted_names' - WRONG FORMAT!")
        except:
            print(f"   ⚠️  Response is NOT valid JSON")
        
        print("="*80 + "\n")
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_without_cache():
    """Test sending the full prompt WITHOUT cache."""
    print("\n" + "="*80)
    print("🧪 TESTING WITHOUT CACHE (Full Prompt)")
    print("="*80)
    
    test_content = """
    === PAGE 1 ===
    [Role: title, BBox: 100,200,300,250]
    Employment History
    
    [Role: paragraph, BBox: 100,260,300,300]
    Work Experience at ABC Company from 2020 to 2023.
    """
    
    try:
        gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
        
        full_prompt = f"{MASTER_PROMPT}\n\nDocument Content to Analyze:\n{test_content}"
        
        print(f"\n   Sending full prompt (no cache)")
        print(f"   Full prompt length: {len(full_prompt)} chars")
        print(f"   Content portion: {len(test_content)} chars")
        print(f"   System instruction portion: {len(MASTER_PROMPT)} chars")
        
        message = gemini.invoke(full_prompt)
        result = message.content
        
        print(f"\n✅ LLM Response received")
        print(f"   Response length: {len(result)} chars")
        print(f"   Response first 300 chars:")
        print(f"   {result[:300]}")
        
        # Check format
        try:
            json_result = json.loads(result)
            print(f"\n✅ Response is valid JSON")
            print(f"   JSON keys: {list(json_result.keys())}")
            
            if "classified_content" in json_result:
                print(f"   ✅ Has 'classified_content' - CORRECT FORMAT!")
            else:
                print(f"   ❌ Missing 'classified_content' - WRONG FORMAT!")
        except:
            print(f"   ⚠️  Response is NOT valid JSON")
        
        print("="*80 + "\n")
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    print("\n" + "="*80)
    print("🔬 DIAGNOSTIC MODE - Testing Caching Implementation")
    print("="*80)
    
    # Step 1: Delete old caches
    delete_old_caches()
    
    # Step 2: Create new cache
    cached_model = create_cached_model(MASTER_PROMPT, ttl="600s")
    
    if not cached_model:
        print("\n❌ Cache creation failed - cannot continue")
        exit(1)
    
    # Step 3: Test WITH cache
    print("\n" + "="*80)
    print("TEST 1: Using Cache")
    print("="*80)
    cache_result = test_cache_usage(cached_model)
    
    # Step 4: Test WITHOUT cache
    print("\n" + "="*80)
    print("TEST 2: Without Cache (Full Prompt)")
    print("="*80)
    no_cache_result = test_without_cache()
    
    # Step 5: Compare results
    print("\n" + "="*80)
    print("📊 COMPARISON")
    print("="*80)
    
    if cache_result and no_cache_result:
        print(f"✅ Both methods returned results")
        
        # Check if both have same format
        try:
            cache_json = json.loads(cache_result)
            no_cache_json = json.loads(no_cache_result)
            
            cache_keys = set(cache_json.keys())
            no_cache_keys = set(no_cache_json.keys())
            
            if cache_keys == no_cache_keys:
                print(f"✅ Both have same JSON structure: {cache_keys}")
                print(f"\n🎯 CONCLUSION: Cache is working correctly!")
            else:
                print(f"❌ Different JSON structures:")
                print(f"   With cache: {cache_keys}")
                print(f"   Without cache: {no_cache_keys}")
                print(f"\n🚨 CONCLUSION: Cache is NOT using the prompt correctly!")
        except:
            print(f"⚠️  Could not compare - one or both responses not valid JSON")
    else:
        print(f"❌ One or both tests failed")
    
    print("="*80)


