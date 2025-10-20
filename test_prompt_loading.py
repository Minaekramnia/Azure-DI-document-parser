"""
Test that prompt loading works without __file__ error
"""
import os

def load_master_prompt_v3():
    """Load Master Prompt V3 from the markdown file."""
    paths = [
        '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/prompt_v3.md',
        'prompt_v3.md',
        os.path.join(os.getcwd(), 'prompt_v3.md')
    ]
    
    for prompt_path in paths:
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"✅ Loaded prompt from: {prompt_path}")
            return content.strip()
        except FileNotFoundError:
            print(f"⚠️  Not found: {prompt_path}")
            continue
        except Exception as e:
            print(f"⚠️  Error loading from {prompt_path}: {e}")
            continue
    
    print(f"❌ Error: Could not find prompt_v3.md")
    return None

if __name__ == '__main__':
    print("Testing prompt loading (no __file__ error)...")
    print("="*60)
    
    prompt = load_master_prompt_v3()
    
    if prompt:
        print(f"\n✅ SUCCESS!")
        print(f"   Prompt length: {len(prompt)} chars")
        print(f"   Contains 'extracted_names': {'extracted_names' in prompt}")
        print(f"   Contains 'classifications': {'classifications' in prompt}")
        print(f"\n✅ No __file__ error!")
    else:
        print(f"\n❌ FAILED to load prompt")


