"""
VERIFY PROMPT - Shows exactly what the LLM receives
"""

import os

def load_master_prompt_v3():
    """Load Master Prompt V3 from the markdown file."""
    paths = [
        '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/prompt_v3.md',
        'prompt_v3.md',
        os.path.join(os.path.dirname(__file__), 'prompt_v3.md')
    ]
    
    for prompt_path in paths:
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"✅ Loaded prompt from: {prompt_path}\n")
            return content.strip()
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"⚠️  Error loading from {prompt_path}: {e}")
            continue
    
    print(f"❌ Error: Could not find prompt_v3.md")
    return None

def main():
    print("="*80)
    print("VERIFYING PROMPT V3 LOADING")
    print("="*80)
    
    prompt = load_master_prompt_v3()
    
    if not prompt:
        print("❌ FAILED: Could not load prompt!")
        return False
    
    print(f"📊 Prompt Statistics:")
    print(f"   Length: {len(prompt)} characters")
    print(f"   Lines: {len(prompt.split(chr(10)))} lines")
    print()
    
    # Check for key sections
    print("🔍 Checking for key sections:")
    key_sections = {
        "extracted_names": "extracted_names" in prompt,
        "classifications": "classifications" in prompt,
        "bounding_box": "bounding_box" in prompt,
        "confidence_score": "confidence_score" in prompt,
        "1.1 Personal Information": "1.1 Personal Information" in prompt,
        "2. CV or Resume": "CV or Resume" in prompt,
        "3. Derogatory": "Derogatory" in prompt or "Offensive Language" in prompt,
        "4. Other Sensitive": "Other Sensitive" in prompt,
    }
    
    all_present = True
    for section, present in key_sections.items():
        status = "✅" if present else "❌"
        print(f"   {status} {section}")
        if not present:
            all_present = False
    
    print()
    
    if not all_present:
        print("⚠️  WARNING: Some key sections are missing!")
        return False
    
    print("="*80)
    print("EXPECTED OUTPUT FORMAT (from prompt):")
    print("="*80)
    
    # Extract the example output from the prompt
    if '{' in prompt and '"extracted_names"' in prompt:
        start = prompt.find('{')
        end = prompt.find('}', start) + 1
        example = prompt[start:end]
        print(example[:500] + "..." if len(example) > 500 else example)
    
    print()
    print("="*80)
    print("SAMPLE DOCUMENT CONTENT (what LLM will receive):")
    print("="*80)
    
    # Show what the LLM will actually receive
    sample_markdown = """
## Page 1

**Role:** title (bbox: 100,50,800,75)
> John Doe - Software Engineer

**Role:** paragraph (bbox: 100,100,800,150)
> Professional Experience: Software Engineer at XYZ Corp, 2015-2020

**Role:** paragraph (bbox: 100,200,800,250)
> Education: B.S. Computer Science, MIT, 2015
"""
    
    full_llm_input = f"{prompt}\n\nDocument Content to Analyze:\n{sample_markdown}"
    
    print("📋 Full LLM Input Preview (first 1000 chars):")
    print("-" * 80)
    print(full_llm_input[:1000])
    print("...")
    print("-" * 80)
    print(f"\n📊 Total LLM input length: {len(full_llm_input)} characters")
    
    print()
    print("="*80)
    print("✅ VERIFICATION COMPLETE")
    print("="*80)
    print()
    print("The LLM will receive:")
    print("1. ✅ The full prompt_v3.md content (classification rules)")
    print("2. ✅ The document content in Markdown format with bounding boxes")
    print()
    print("Expected LLM output:")
    print('{')
    print('  "extracted_names": ["John Doe"],')
    print('  "classifications": [')
    print('    {')
    print('      "category": "2. CV or Resume Content",')
    print('      "text": "Professional Experience: Software Engineer...",')
    print('      "bounding_box": [100, 100, 800, 150],')
    print('      "confidence_score": 0.92,')
    print('      "reason": "Contains work history section"')
    print('    }')
    print('  ]')
    print('}')
    
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)


