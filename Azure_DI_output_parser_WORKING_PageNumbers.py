"""
WORKING VERSION + PAGE NUMBERS - Uses EXECUTIVE PROMPT

This version validates against the Executive Prompt output format:
- extracted_names: List of all personal names found in the document
- classifications: List of sensitive content with category, text, bounding_box, PAGE_NUMBER, confidence_score, and reason

NEW FEATURE: Each classification now includes the original page number where the content was found!
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
    """Load Executive Prompt from file."""
    import os
    
    base_path = '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/'
    
    # Try different possible filenames for the Executive Prompt
    filenames = [
        'Executive_Prompt.md',      # ← NEW EXECUTIVE PROMPT!
        'executive_prompt.md',
        'ExecutivePrompt.md',
        'MasterPromp_V4.md',        # Fallback to old prompt
        'MasterPrompt_V4.md',
    ]
    
    print("🔍 Searching for Executive Prompt...")
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
            print(f"   First 150 chars: {content[:150]}")
            return content
        except FileNotFoundError:
            print(f"   ❌ Not found")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n❌ Could not find Executive Prompt!")
    print("   Please check the filename in the directory listing above.")
    print("   Looking for: Executive_Prompt.md or executive_prompt.md")
    return None


# Load prompt
MASTER_PROMPT = load_master_prompt()

if not MASTER_PROMPT:
    print("ERROR: Cannot proceed without prompt file")
    exit(1)

# Verify prompt contains required instructions
print("\n🔍 VERIFYING PROMPT CONTENT:")
if "extracted_names" in MASTER_PROMPT and "classifications" in MASTER_PROMPT:
    print("✅ Prompt contains 'extracted_names' and 'classifications' instructions")
else:
    print("⚠️  WARNING: Prompt does NOT contain expected format instructions!")
    print(f"   Has 'extracted_names': {'extracted_names' in MASTER_PROMPT}")
    print(f"   Has 'classifications': {'classifications' in MASTER_PROMPT}")
    print(f"\n   This might cause wrong output format!")
print("="*80 + "\n")


def delete_old_caches():
    """Delete ALL old caches to ensure we use the fresh prompt."""
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
        print(f"   This ensures we use the NEW prompt!\n")
        return True
        
    except Exception as e:
        print(f"⚠️  Could not delete old caches: {e}")
        print("   Continuing anyway...\n")
        return False


def create_cached_model(system_instruction, ttl="600s"):
    """Create cache with the prompt."""
    print("🔄 Creating NEW cache with your prompt...")
    
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
        
        print("   Creating cache from prompt content...")
        cache = client.caches.create(
            model=model,
            config=types.CreateCachedContentConfig(
                display_name='classification_rules_v4',  # NEW NAME
                system_instruction=system_instruction,
                ttl=ttl,
            )
        )
        
        print(f"✅ NEW cache created successfully: {cache.name}")
        print(f"   This cache contains your classification rules prompt")
        print(f"   TTL: {ttl} ({int(ttl.replace('s', '')) / 60} minutes)")
        
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
        self.cached_model = cached_model
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
    
    def _parse_page_number(self, content):
        """Parse page number content to extract sequence info (e.g., '1/4' -> (1, 4))."""
        import re
        content = content.strip().lower()
        
        # Skip invalid page numbers
        if not re.match(r'^[\d\s/]+$', content):
            return None
        
        # Pattern: 1/4, 2/4, etc.
        match = re.match(r'^(\d+)/(\d+)$', content)
        if match:
            current = int(match.group(1))
            total = int(match.group(2))
            return (current, total, content)
        
        # Pattern: page 1, page 2, etc.
        match = re.match(r'^page\s*(\d+)$', content)
        if match:
            current = int(match.group(1))
            return (current, None, content)
        
        # Pattern: 1, 2, 3, etc.
        match = re.match(r'^(\d+)$', content)
        if match:
            current = int(match.group(1))
            return (current, None, content)
        
        return None
    
    def _get_page_number_sequence(self, page_num):
        """Extract page number sequence information from a page."""
        page_data = self.page_content.get(page_num, {})
        
        # Check page_numbers section first
        page_numbers = page_data.get('page_numbers', [])
        if page_numbers:
            content = page_numbers[0].get('content', '').strip()
            match = self._parse_page_number(content)
            if match:
                return match
        
        # Check paragraphs for page number patterns
        for para in page_data.get('paragraphs', []):
            content = para.get('content', '').strip()
            match = self._parse_page_number(content)
            if match:
                return match
        
        return None
    
    def _is_continuation_of_previous_page(self, page_num):
        """Check if this page continues a page number sequence from previous page."""
        if page_num not in self.page_content:
            return False
        
        sorted_pages = sorted(self.page_content.keys())
        page_index = sorted_pages.index(page_num)
        
        if page_index == 0:
            return False  # First page
        
        prev_page = sorted_pages[page_index - 1]
        
        # Get page number sequences
        current_seq = self._get_page_number_sequence(page_num)
        prev_seq = self._get_page_number_sequence(prev_page)
        
        if not current_seq or not prev_seq:
            return False
        
        current_num, current_total, current_text = current_seq
        prev_num, prev_total, prev_text = prev_seq
        
        # Check if it's a continuation of the same document sequence
        if current_total and prev_total:
            # Both have total pages (e.g., 1/4, 2/4)
            if current_total == prev_total and current_num == prev_num + 1:
                print(f"   📖 Page {page_num}: Continuation detected - {prev_text} → {current_text}")
                return True
        
        elif current_num and prev_num and not current_total and not prev_total:
            # Both are simple page numbers (e.g., 1, 2, 3)
            if current_num == prev_num + 1:
                print(f"   📖 Page {page_num}: Continuation detected - {prev_text} → {current_text}")
                return True
        
        return False
    
    def _detect_document_boundaries(self):
        """Detect document boundaries using 3 rules with proper page number sequence detection."""
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
            
            # Check for page number SEQUENCE (not just existence)
            is_continuation = False
            if i > 0:
                is_continuation = self._is_continuation_of_previous_page(page_num)
            
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
            # Rule 3 (page number sequence) OVERRIDES Rule 2 (title)
            if i == 0:
                is_new_document = True  # First page
            elif is_continuation:
                is_new_document = False  # Page number sequence indicates continuation
                print(f"   ↗️ Page {page_num}: Continuing same document (page sequence)")
            elif has_size_change:
                is_new_document = True  # Size change = new document
                print(f"   📏 Page {page_num}: NEW document (size changed)")
            elif has_title:
                is_new_document = True  # Title without page sequence = new document
                print(f"   📄 Page {page_num}: NEW document (new title)")
            else:
                is_new_document = False  # Default: continuation
            
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
        """Get content for segment with page tracking."""
        content = ""
        page_mapping = {}  # Track which content belongs to which page
        
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
        
        return content, pages
    
    def analyze_with_llm(self, document_content, segment_id, segment_pages):
        """Analyze with LLM - matches YOUR prompt's expected output."""
        print(f"\n🤖 Running LLM analysis for {segment_id}...")
        
        # Add VERY explicit format enforcement at the end
        format_reminder = """

=================================================================================
CRITICAL OUTPUT FORMAT REQUIREMENTS - READ CAREFULLY:
=================================================================================

You MUST return ONLY a JSON object with this EXACT structure:

{
  "extracted_names": ["name1", "name2", ...],
  "classifications": [
    {
      "category": "MUST BE ONE OF: 1.1 Personal Information, 1.2 Governors'/Executive Directors' Communications, 1.3 Ethics Committee Materials, 1.4 Attorney–Client Privilege, 1.5 Security & Safety Information, 1.6 Restricted Investigative Info, 1.7 Confidential Third-Party Information, 1.8 Corporate Administrative Matters, 1.9 Financial Information, 2.1 CV or Resume Content, 2.2 Derogatory or Offensive Language, 3.1 Documents from Specific Entities (IFC, MIGA, INT, IMF), 3.2 Joint WBG Documents, 3.3 Security-Marked Documents, 3.4 Procurement Content",
      "text": "the actual sensitive text",
      "bounding_box": [x1, y1, x2, y2],
      "page_number": X,
      "confidence_score": 0.95,
      "reason": "why this is sensitive"
    }
  ]
}

ABSOLUTELY FORBIDDEN CATEGORIES - DO NOT USE THESE:
- "person_name", "date_of_birth", "security_clearance", "language", "citizenship"
- "marital_status", "education", "work_experience", "military_service"
- "sender_name", "recipient_name", "document_date", "document_type", "barcode"
- "Withdrawn By", "Withdrawn Date", "Document Type", "Document Date"

ONLY classify content that is SENSITIVE according to the classification rules.
Do NOT classify general CV information, document metadata, or routine correspondence.

If the document is a CV/Resume, use category "2.1 CV or Resume Content" for the ENTIRE document, not individual fields.

IMPORTANT: Include a "page_number" field in each classification to indicate which page the content was found on.
"""
        
        try:
            if self.cached_model:
                # Use cached model
                print(f"   Using cached prompt (classification_rules_v4)")
                gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
                message = gemini.invoke(
                    f"Document Content to Analyze:\n{document_content}{format_reminder}",
                    model_kwargs={'cached_content': self.cached_model}
                )
                result = message.content
                print(f"✅ Analysis completed for {segment_id} (using cache)")
            else:
                # No cache - send full prompt
                print(f"   Sending full prompt (no cache)")
                full_prompt = f"{MASTER_PROMPT}\n\nDocument Content to Analyze:\n{document_content}{format_reminder}"
                gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
                message = gemini.invoke(full_prompt)
                result = message.content
                print(f"✅ Analysis completed for {segment_id}")
            
            # VALIDATE OUTPUT - check if it matches EXECUTIVE PROMPT format
            try:
                # Try to parse as JSON
                json_result = json.loads(result)
                
                # Check for EXECUTIVE PROMPT expected fields
                has_names = 'extracted_names' in json_result
                has_classifications = 'classifications' in json_result
                
                if has_names and has_classifications:
                    print(f"✅ VALIDATION: Output follows Executive Prompt format!")
                    print(f"   Found: extracted_names ({len(json_result['extracted_names'])} names)")
                    print(f"   Found: classifications ({len(json_result['classifications'])} items)")
                elif has_names or has_classifications:
                    print(f"⚠️  VALIDATION: Partial match")
                    print(f"   Has extracted_names: {has_names}")
                    print(f"   Has classifications: {has_classifications}")
                else:
                    print(f"⚠️  VALIDATION: Output format unexpected")
                    print(f"   Expected: extracted_names and classifications")
                    print(f"   Found: {list(json_result.keys())}")
            except json.JSONDecodeError:
                # Not JSON - might be plain text
                print(f"⚠️  VALIDATION: Output is not JSON")
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
        """Process document and output as single JSON object."""
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
        
        # Build the output JSON structure
        output_data = {
            "document_path": self.filepath,
            "total_pages": len(self.page_content),
            "total_segments": len(self.document_segments),
            "segments": []
        }
        
        try:
            for segment_id, segment_info in self.document_segments.items():
                pages = segment_info['pages']
                print(f"\n📄 Processing {segment_id}: Pages {min(pages)}-{max(pages)}")
                
                segment_content, segment_pages = self._get_segment_content(pages)
                llm_result = self.analyze_with_llm(segment_content, segment_id, segment_pages)
                
                # Parse LLM result as JSON
                try:
                    # Remove markdown code blocks if present
                    llm_result_clean = llm_result.strip()
                    if llm_result_clean.startswith('```json'):
                        llm_result_clean = llm_result_clean[7:]
                    if llm_result_clean.startswith('```'):
                        llm_result_clean = llm_result_clean[3:]
                    if llm_result_clean.endswith('```'):
                        llm_result_clean = llm_result_clean[:-3]
                    
                    llm_json = json.loads(llm_result_clean.strip())
                    
                    # Post-process: Merge CV classifications into ONE
                    classifications = llm_json.get("classifications", [])
                    cv_classifications = [c for c in classifications if c.get("category") == "2.1 CV or Resume Content"]
                    other_classifications = [c for c in classifications if c.get("category") != "2.1 CV or Resume Content"]
                    
                    # If multiple CV classifications, merge them into ONE
                    if len(cv_classifications) > 1:
                        print(f"   📋 Merging {len(cv_classifications)} CV classifications into ONE")
                        
                        # Collect all names from CV classifications
                        all_cv_text_parts = [c.get("text", "") for c in cv_classifications]
                        
                        # Create single merged CV classification with page range
                        merged_cv = {
                            "category": "2.1 CV or Resume Content",
                            "text": f"Complete CV/Resume spanning pages {min(pages)}-{max(pages)}. Contains: education history, professional experience, publications, and personal information.",
                            "bounding_box": [0, 0, 10, 12],  # Full page range
                            "page_number": min(pages),  # First page of the CV
                            "page_range": f"{min(pages)}-{max(pages)}",  # Full page range
                            "confidence_score": 0.99,
                            "reason": f"Document is a complete CV/Resume spanning {len(pages)} pages with multiple sections: {', '.join([c.get('text', '')[:30] + '...' for c in cv_classifications[:3]])}."
                        }
                        
                        # Use merged CV + other classifications
                        final_classifications = [merged_cv] + other_classifications
                    else:
                        final_classifications = classifications
                    
                    # Ensure all classifications have page_number field
                    for classification in final_classifications:
                        if 'page_number' not in classification:
                            # If LLM didn't provide page_number, use first page of segment
                            classification['page_number'] = min(pages)
                    
                    # Add segment info
                    segment_data = {
                        "segment_id": segment_id,
                        "pages": pages,
                        "page_range": f"{min(pages)}-{max(pages)}",
                        "extracted_names": llm_json.get("extracted_names", []),
                        "classifications": final_classifications
                    }
                    
                    output_data["segments"].append(segment_data)
                    
                except json.JSONDecodeError as e:
                    print(f"⚠️  Warning: Could not parse LLM output as JSON for {segment_id}: {e}")
                    # Add error segment
                    output_data["segments"].append({
                        "segment_id": segment_id,
                        "pages": pages,
                        "page_range": f"{min(pages)}-{max(pages)}",
                        "error": "Failed to parse LLM output",
                        "raw_output": llm_result
                    })
            
            # Write output as single JSON file
            if output_filepath:
                with open(output_filepath, 'w', encoding='utf-8') as output_file:
                    json.dump(output_data, output_file, indent=2, ensure_ascii=False)
            
            print(f"\n✅ All segments processed!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            if output_filepath:
                print(f"📄 Saved to: {output_filepath}")


if __name__ == '__main__':
    # Paths
    data_path = '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/'
    all_json_files = glob.glob(f"{data_path}Personal_Information_*.pdf.json")
    
    # LIMIT TO FIRST 5 FILES FOR TESTING
    json_files = sorted(all_json_files)[:5]
    
    print("🚀 WORKING PROCESSOR + PAGE NUMBERS - Uses EXECUTIVE PROMPT")
    print("="*60)
    print(f"Prompt: Executive Prompt (AI Document Analysis)")
    print(f"Output: extracted_names + classifications (WITH PAGE NUMBERS)")
    print(f"Total files found: {len(all_json_files)}")
    print(f"Processing FIRST 5 FILES for testing")
    print(f"Files to process: {len(json_files)}")
    print("="*60)
    
    # STEP 1: Delete ALL old caches (CRITICAL!)
    print("\n" + "="*60)
    print("STEP 1: Deleting old caches with wrong prompts")
    print("="*60)
    delete_old_caches()
    
    # STEP 2: Create NEW cache with your prompt
    print("="*60)
    print("STEP 2: Creating NEW cache with your prompt")
    print("="*60)
    ttl = "600s"  # 10 minutes
    cached_model = create_cached_model(MASTER_PROMPT, ttl=ttl)
    
    if cached_model:
        print(f"\n💰 Caching enabled!")
        print(f"   First file: ~{len(MASTER_PROMPT)} tokens")
        print(f"   Remaining files: ~100 tokens each")
        print(f"   Total savings: ~{(len(json_files) - 1) * len(MASTER_PROMPT)} tokens\n")
    else:
        print(f"\n⚠️  Caching failed - will send full prompt each time\n")
    
    # Process all files
    for json_file in sorted(json_files):
        print(f"\n{'='*60}")
        print(f"🔍 Processing: {json_file}")
        print(f"{'='*60}")
        
        base_name = os.path.basename(json_file).replace('.pdf.json', '')
        output_filename = f"{data_path}{base_name}_WORKING_PageNumbers_analysis.json"
        
        try:
            processor = DocumentProcessor(json_file, cached_model=cached_model)
            processor.process_document(output_filepath=output_filename)
            print(f"✅ Done: {output_filename}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n🎯 Complete!")
    print(f"Processed {len(json_files)} files (first 5 for testing)")
    print(f"Output files: *_WORKING_PageNumbers_analysis.json")
    if cached_model:
        print(f"Cache reused {len(json_files) - 1} times - significant savings! 💰")
    
    print(f"\n📋 To process ALL {len(all_json_files)} files:")
    print(f"   Change line 643 from:")
    print(f"   json_files = sorted(all_json_files)[:5]")
    print(f"   To:")
    print(f"   json_files = sorted(all_json_files)")
    
    print(f"\n✨ NEW FEATURE: Each classification now includes page_number field!")

