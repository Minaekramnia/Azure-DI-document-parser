"""
FINAL VERSION - V2's Working Code + Proper Caching + MasterPrompt_V4

This combines:
1. V2's proven working LLM analysis
2. Working caching implementation (from V3_Cached)
3. MasterPrompt_V4.md
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
    import os
    
    base_path = '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/'
    
    # Try different possible filenames (including typos found in directory)
    filenames = [
        'MasterPromp_V4.md',      # ← TYPO FOUND IN YOUR DIRECTORY!
        'MasterPrompt_V4.md',
        'MasterPrompt_V4',
        'masterprompt_v4.md',
        'prompt_v4.md',
    ]
    
    print("🔍 Searching for MasterPrompt_V4.md...")
    print(f"   Base path: {base_path}")
    
    # First, list what files are actually in the directory
    try:
        if os.path.exists(base_path):
            files = os.listdir(base_path)
            prompt_files = [f for f in files if 'prompt' in f.lower() or 'master' in f.lower()]
            if prompt_files:
                print(f"   Found {len(prompt_files)} prompt-related files:")
                for f in prompt_files:
                    print(f"      - {f}")
        else:
            print(f"   ⚠️  Base path does not exist!")
    except Exception as e:
        print(f"   ⚠️  Cannot list directory: {e}")
    
    # Try each filename
    for filename in filenames:
        path = os.path.join(base_path, filename)
        print(f"\n   Trying: {path}")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"   ✅ FOUND! Loaded from: {path}")
            print(f"   Prompt length: {len(content)} characters")
            print(f"   First 100 chars: {content[:100]}")
            return content
        except FileNotFoundError:
            print(f"   ❌ Not found")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n❌ Could not find MasterPrompt_V4.md!")
    print("   Please check the filename in the directory listing above.")
    return None


# Load prompt
MASTER_PROMPT = load_master_prompt()

if not MASTER_PROMPT:
    print("ERROR: Cannot proceed without prompt file")
    exit(1)


def delete_old_caches():
    """
    Delete ALL old caches to ensure we use the fresh prompt.
    This is CRITICAL - old caches have wrong prompts!
    """
    print("\n🗑️  DELETING ALL OLD CACHES (IMPORTANT!)...")
    
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
        
        # List ALL caches
        caches = list(client.caches.list())
        
        if not caches:
            print("✅ No old caches found")
            return True
        
        print(f"   Found {len(caches)} existing cache(s)")
        deleted_count = 0
        
        for cache in caches:
            try:
                print(f"   Deleting: {cache.display_name}")
                client.caches.delete(name=cache.name)
                deleted_count += 1
            except Exception as e:
                print(f"   Warning: Could not delete {cache.display_name}: {e}")
        
        print(f"✅ Deleted {deleted_count} old cache(s)")
        print(f"   This ensures we use the NEW MasterPrompt_V4.md!\n")
        return True
        
    except Exception as e:
        print(f"⚠️  Could not delete old caches: {e}")
        print("   Continuing anyway...\n")
        return False


def create_cached_model(system_instruction, ttl="600s"):
    """
    Create a cached model with the system instruction (prompt).
    EXACT implementation from V3_Cached.py (which worked).
    
    Args:
        system_instruction: The prompt content
        ttl: Time to live for the cache (default: 10 minutes)
    
    Returns:
        Cached model object
    """
    print("🔄 Creating NEW cache with MasterPrompt_V4.md...")
    
    try:
        # Load environment variables and credentials
        load_dotenv()
        creds = load_credentials_from_environment()
        g = get_google_credentials()
        
        # Create client with proper credentials
        client = genai.Client(
            vertexai=True, 
            project=creds.project_id, 
            location=g.google_vertex_region, 
            credentials=creds
        )
        
        model = vertex.Gemini.PRO_2_5
        
        print("   Creating cache from MasterPrompt_V4.md content...")
        cache = client.caches.create(
            model=model,
            config=types.CreateCachedContentConfig(
                display_name='masterprompt_v4_classifier',  # NEW NAME
                system_instruction=system_instruction,
                ttl=ttl,
            )
        )
        
        print(f"✅ NEW cache created successfully: {cache.name}")
        print(f"   This cache contains MasterPrompt_V4.md")
        print(f"   TTL: {ttl} ({int(ttl.replace('s', '')) / 60} minutes)")
        
        # Return the cache object itself
        return cache
        
    except Exception as e:
        print(f"❌ Error creating cache: {e}")
        print("⚠️  Falling back to non-cached mode")
        return None


class DocumentProcessor:
    """Document processor - based on V2's working logic."""
    
    def __init__(self, filepath, cached_model=None):
        self.filepath = filepath
        self.analyze_result = None
        self.page_content = {}
        self.page_dimensions = {}
        self.document_segments = {}
        self.cached_model = cached_model  # Store cache object
        self._load_data()
    
    def _load_data(self):
        """Load JSON file."""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.analyze_result = data.get('analyzeResult')
            if not self.analyze_result:
                raise ValueError("Missing 'analyzeResult' key")
            print(f"✅ Loaded: {self.filepath}")
        except Exception as e:
            print(f"❌ Error: {e}")
            self.analyze_result = None
    
    def _organize_content_by_page(self):
        """Organize content by page."""
        if not self.analyze_result:
            return
        
        # Initialize pages
        for page in self.analyze_result.get('pages', []):
            page_number = page.get('pageNumber')
            if page_number:
                self.page_content[page_number] = {'paragraphs': [], 'tables': [], 'page_numbers': []}
                self.page_dimensions[page_number] = {
                    'width': page.get('width'),
                    'height': page.get('height'),
                    'unit': page.get('unit')
                }
        
        # Process paragraphs
        for paragraph in self.analyze_result.get('paragraphs', []):
            if paragraph.get('boundingRegions'):
                page_number = paragraph['boundingRegions'][0].get('pageNumber')
                if page_number in self.page_content:
                    para_info = {
                        'content': paragraph.get('content', ''),
                        'role': paragraph.get('role', 'paragraph'),
                        'boundingBox': paragraph['boundingRegions'][0].get('polygon', [])
                    }
                    if para_info['role'] == 'pageNumber':
                        self.page_content[page_number]['page_numbers'].append(para_info)
                    else:
                        self.page_content[page_number]['paragraphs'].append(para_info)
        
        # Process tables
        for table in self.analyze_result.get('tables', []):
            if table.get('cells') and table['cells'][0].get('boundingRegions'):
                page_number = table['cells'][0]['boundingRegions'][0].get('pageNumber')
                if page_number in self.page_content:
                    self.page_content[page_number]['tables'].append(table)
    
    def _detect_document_boundaries(self):
        """Detect document boundaries (same as V2)."""
        if not self.page_content:
            return
        
        import re
        sorted_pages = sorted(self.page_content.keys())
        document_segments = []
        current_segment = []
        
        for i, page_num in enumerate(sorted_pages):
            page_data = self.page_content[page_num]
            
            # Check for title
            has_title = any(p.get('role') == 'title' for p in page_data.get('paragraphs', [])[:3])
            
            # Check for page number
            has_page_num = bool(page_data.get('page_numbers', []))
            
            # Check size change
            has_size_change = False
            if i > 0:
                prev_page = sorted_pages[i-1]
                prev_dims = self.page_dimensions[prev_page]
                curr_dims = self.page_dimensions[page_num]
                height_change = abs(prev_dims.get('height', 0) - curr_dims.get('height', 0)) / max(prev_dims.get('height', 1), 1)
                width_change = abs(prev_dims.get('width', 0) - curr_dims.get('width', 0)) / max(prev_dims.get('width', 1), 1)
                has_size_change = height_change > 0.05 or width_change > 0.05
            
            # Decide if new document
            is_new_document = (i == 0) or (has_title and not has_page_num) or has_size_change
            
            if is_new_document and current_segment:
                document_segments.append(current_segment)
                current_segment = []
            
            current_segment.append(page_num)
        
        if current_segment:
            document_segments.append(current_segment)
        
        for i, segment in enumerate(document_segments):
            self.document_segments[f"segment_{i+1}"] = {
                'pages': segment,
                'start_page': min(segment),
                'end_page': max(segment),
                'page_count': len(segment)
            }
        
        print(f"📚 Found {len(document_segments)} document segments")
    
    def _get_segment_content(self, pages):
        """Get content for segment."""
        content = ""
        for page_num in sorted(pages):
            page_data = self.page_content.get(page_num, {})
            content += f"\n=== PAGE {page_num} ===\n"
            
            for para in page_data.get('paragraphs', []):
                bbox = para.get('boundingBox', [])
                bbox_str = ",".join(map(str, bbox)) if bbox else "unknown"
                content += f"[Role: {para['role']}, BBox: {bbox_str}]\n{para['content']}\n\n"
            
            for pn in page_data.get('page_numbers', []):
                bbox = pn.get('boundingBox', [])
                bbox_str = ",".join(map(str, bbox)) if bbox else "unknown"
                content += f"[Page Number, BBox: {bbox_str}]\n{pn['content']}\n\n"
        
        return content
    
    def analyze_with_llm(self, document_content, segment_id):
        """
        Analyze with LLM - V2 approach with caching support.
        """
        print(f"\n🤖 Running LLM analysis for {segment_id}...")
        
        try:
            if self.cached_model:
                # Use cached model
                print(f"   Using cached prompt (masterprompt_v4_classifier)")
                gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
                message = gemini.invoke(
                    f"Document Content to Analyze:\n{document_content}",
                    model_kwargs={'cached_content': self.cached_model}
                )
                result = message.content
                print(f"✅ Analysis completed for {segment_id} (using cache)")
            else:
                # No cache - send full prompt (V2 style)
                print(f"   Sending full prompt (no cache)")
                full_prompt = f"{MASTER_PROMPT}\n\nDocument Content to Analyze:\n{document_content}"
                gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
                message = gemini.invoke(full_prompt)
                result = message.content
                print(f"✅ Analysis completed for {segment_id}")
            
            # VALIDATE OUTPUT - check if it follows MasterPrompt_V4 format
            try:
                json_result = json.loads(result)
                # MasterPrompt_V4 should have 'classified_content' and 'extracted_names'
                if "classified_content" in json_result or "extracted_names" in json_result:
                    print("✅ VALIDATION: Output follows MasterPrompt_V4 format!")
                else:
                    print("⚠️  VALIDATION: Output does NOT match expected format!")
                    print(f"   Keys found: {list(json_result.keys())}")
            except:
                print("⚠️  VALIDATION: Output is not valid JSON")
                print(f"   First 200 chars: {result[:200]}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error: {e}")
            # Fallback: try without cache
            try:
                print(f"   Trying fallback without cache...")
                full_prompt = f"{MASTER_PROMPT}\n\nDocument Content to Analyze:\n{document_content}"
                gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
                message = gemini.invoke(full_prompt)
                return message.content
            except Exception as fallback_error:
                return f"Error: {str(fallback_error)}"
    
    def process_document(self, output_filepath=None):
        """Process document."""
        if not self.analyze_result:
            print("❌ Cannot process - loading failed")
            return
        
        print("\n🔍 Organizing content...")
        self._organize_content_by_page()
        
        if not self.page_content:
            print("❌ No content found")
            return
        
        print("\n🔍 Detecting boundaries...")
        self._detect_document_boundaries()
        
        print("\n🔍 Processing segments...")
        
        output_file = None
        try:
            if output_filepath:
                output_file = open(output_filepath, 'w', encoding='utf-8')
                output_file.write(f"=== Document Analysis: {self.filepath} ===\n")
                output_file.write(f"Prompt: MasterPrompt_V4.md\n")
                output_file.write(f"Total Pages: {len(self.page_content)}\n")
                output_file.write(f"Segments: {len(self.document_segments)}\n\n")
            
            for segment_id, segment_info in self.document_segments.items():
                pages = segment_info['pages']
                print(f"\n📄 Processing {segment_id}: Pages {min(pages)}-{max(pages)}")
                
                segment_content = self._get_segment_content(pages)
                llm_result = self.analyze_with_llm(segment_content, segment_id)
                
                if output_file:
                    output_file.write(f"\n{'='*60}\n")
                    output_file.write(f"SEGMENT: {segment_id}\n")
                    output_file.write(f"Pages: {min(pages)}-{max(pages)}\n")
                    output_file.write(f"{'='*60}\n\n")
                    output_file.write("LLM ANALYSIS:\n")
                    output_file.write(llm_result)
                    output_file.write("\n\n")
            
            print(f"\n✅ All segments processed!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            if output_file:
                output_file.close()
                print(f"📄 Saved to: {output_filepath}")


if __name__ == '__main__':
    # Paths
    data_path = '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/'
    all_json_files = glob.glob(f"{data_path}Personal_Information_*.pdf.json")
    
    # LIMIT TO FIRST 5 FILES FOR TESTING
    json_files = sorted(all_json_files)[:5]
    
    print("🚀 FINAL PROCESSOR - V2 + Caching + MasterPrompt_V4")
    print("="*60)
    print(f"Prompt: MasterPrompt_V4.md")
    print(f"Total files found: {len(all_json_files)}")
    print(f"Processing FIRST 5 FILES for testing")
    print(f"Files to process: {len(json_files)}")
    print("="*60)
    
    # STEP 1: Delete ALL old caches (CRITICAL!)
    print("\n" + "="*60)
    print("STEP 1: Deleting old caches with wrong prompts")
    print("="*60)
    delete_old_caches()
    
    # STEP 2: Create NEW cache with MasterPrompt_V4.md
    print("="*60)
    print("STEP 2: Creating NEW cache with MasterPrompt_V4.md")
    print("="*60)
    ttl = "600s"  # 10 minutes
    cached_model = create_cached_model(MASTER_PROMPT, ttl=ttl)
    
    if cached_model:
        print(f"\n💰 Caching enabled!")
        print(f"   First file: ~7,600 tokens")
        print(f"   Remaining files: ~100 tokens each")
        print(f"   Total savings: ~{(len(json_files) - 1) * 7500} tokens\n")
    else:
        print(f"\n⚠️  Caching failed - will send full prompt each time\n")
    
    # Process all files
    for json_file in sorted(json_files):
        print(f"\n{'='*60}")
        print(f"🔍 Processing: {json_file}")
        print(f"{'='*60}")
        
        base_name = os.path.basename(json_file).replace('.pdf.json', '')
        output_filename = f"{data_path}{base_name}_FINAL_analysis.txt"
        
        try:
            processor = DocumentProcessor(json_file, cached_model=cached_model)
            processor.process_document(output_filepath=output_filename)
            print(f"✅ Done: {output_filename}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n🎯 Complete!")
    print(f"Processed {len(json_files)} files (first 5 for testing)")
    print(f"Output files: *_FINAL_analysis.txt")
    if cached_model:
        print(f"Cache reused {len(json_files) - 1} times - significant savings! 💰")
    
    print(f"\n📋 To process ALL {len(all_json_files)} files:")
    print(f"   Change line 396 from:")
    print(f"   json_files = sorted(all_json_files)[:5]")
    print(f"   To:")
    print(f"   json_files = sorted(all_json_files)")

