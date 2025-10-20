"""
CLEAN VERSION - Combines V2's Working Logic + Proper Caching

This version:
1. Uses V2's proven working LLM analysis approach
2. Adds proper caching with cache management
3. Loads prompt from external file (flexible)
4. Validates output format
5. No complicated features - just what works!
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
import time


def load_prompt_from_file(prompt_filename='prompt_v3.md'):
    """
    Load prompt from external file.
    
    Args:
        prompt_filename: Name of the prompt file (default: 'prompt_v3.md')
                        Can be changed to 'MasterPrompt_V4.md' or any other file
    
    Returns:
        str: Prompt content
    """
    # Try multiple paths
    paths = [
        f'/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/{prompt_filename}',
        prompt_filename,
        os.path.join(os.getcwd(), prompt_filename)
    ]
    
    for prompt_path in paths:
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"✅ Loaded prompt from: {prompt_path}")
            print(f"   Prompt length: {len(content)} characters")
            return content.strip()
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"⚠️  Error loading from {prompt_path}: {e}")
            continue
    
    print(f"❌ Error: Could not find {prompt_filename}")
    return None


# Load the prompt (CHANGE THIS TO USE DIFFERENT PROMPT FILE)
PROMPT_FILE = 'MasterPrompt_V4.md'  # ← Using MasterPrompt_V4.md from Databricks
MASTER_PROMPT = load_prompt_from_file(PROMPT_FILE)

if not MASTER_PROMPT:
    print(f"❌ Failed to load prompt from {PROMPT_FILE}. Exiting.")
    exit(1)


class DocumentProcessor:
    """
    Clean document processor based on V2's working approach.
    """
    def __init__(self, filepath, cached_model=None):
        self.filepath = filepath
        self.analyze_result = None
        self.page_content = {}
        self.page_dimensions = {}
        self.document_segments = {}
        self.cached_model = cached_model
        self._load_data()

    def _load_data(self):
        """Load and parse the JSON file."""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.analyze_result = data.get('analyzeResult')
            if not self.analyze_result:
                raise ValueError("JSON structure is invalid. Missing 'analyzeResult' key.")
            print(f"✅ Loaded: {self.filepath}")
            return True
        except Exception as e:
            print(f"❌ Error loading {self.filepath}: {e}")
            self.analyze_result = None
            return False

    def _organize_content_by_page(self):
        """Organize content by page number."""
        if not self.analyze_result:
            return

        # Initialize containers for each page
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
        """Detect document boundaries using 3 rules (same as V2)."""
        if not self.page_content:
            return
        
        sorted_pages = sorted(self.page_content.keys())
        document_segments = []
        current_segment = []
        
        for i, page_num in enumerate(sorted_pages):
            page_data = self.page_content[page_num]
            
            has_new_title = self._has_title_at_start(page_data)
            has_page_number = self._has_page_number(page_data)
            has_size_change = False
            
            if i > 0:
                prev_page = sorted_pages[i-1]
                has_size_change = self._page_size_changed(prev_page, page_num)
            
            is_new_document = False
            
            if i == 0:
                is_new_document = True
                print(f"📄 Document boundary at page {page_num}: First page")
            else:
                if has_new_title:
                    if has_page_number and self._is_continuation_of_previous_page(page_num):
                        is_new_document = False
                    else:
                        is_new_document = True
                        print(f"📄 Document boundary at page {page_num}: New title found")
                elif has_size_change:
                    is_new_document = True
                    print(f"📏 Document boundary at page {page_num}: Page size changed")
                elif has_page_number:
                    if self._is_continuation_of_previous_page(page_num):
                        is_new_document = False
                    else:
                        is_new_document = False
                else:
                    is_new_document = False
            
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

    def _has_title_at_start(self, page_data):
        """Check if page starts with a title."""
        paragraphs = page_data.get('paragraphs', [])
        for para in paragraphs[:3]:
            if para.get('role') == 'title':
                return True
        return False

    def _has_page_number(self, page_data):
        """Check if page has page number content."""
        import re
        page_numbers = page_data.get('page_numbers', [])
        if page_numbers:
            return True
        
        for para in page_data.get('paragraphs', []):
            content = para.get('content', '').strip()
            patterns = [r'^\d+$', r'^\d+/\d+$', r'^page\s*\d+$', r'^\d+\s*of\s*\d+$']
            for pattern in patterns:
                if re.match(pattern, content.lower()):
                    return True
        return False

    def _page_size_changed(self, prev_page_num, curr_page_num):
        """Check if page dimensions changed."""
        if prev_page_num not in self.page_dimensions or curr_page_num not in self.page_dimensions:
            return False
        
        prev_dims = self.page_dimensions[prev_page_num]
        curr_dims = self.page_dimensions[curr_page_num]
        
        height_change = abs(prev_dims.get('height', 0) - curr_dims.get('height', 0)) / max(prev_dims.get('height', 1), 1)
        width_change = abs(prev_dims.get('width', 0) - curr_dims.get('width', 0)) / max(prev_dims.get('width', 1), 1)
        
        return height_change > 0.05 or width_change > 0.05

    def _get_page_number_sequence(self, page_num):
        """Extract page number sequence information."""
        import re
        page_data = self.page_content.get(page_num, {})
        
        page_numbers = page_data.get('page_numbers', [])
        if page_numbers:
            content = page_numbers[0].get('content', '').strip()
            match = self._parse_page_number(content)
            if match:
                return match
        
        for para in page_data.get('paragraphs', []):
            content = para.get('content', '').strip()
            match = self._parse_page_number(content)
            if match:
                return match
        
        return None

    def _parse_page_number(self, content):
        """Parse page number content."""
        import re
        content = content.strip().lower()
        
        if not re.match(r'^[\d\s/]+$', content):
            return None
        
        match = re.match(r'^(\d+)/(\d+)$', content)
        if match:
            return (int(match.group(1)), int(match.group(2)), content)
        
        match = re.match(r'^page\s*(\d+)$', content)
        if match:
            return (int(match.group(1)), None, content)
        
        match = re.match(r'^(\d+)$', content)
        if match:
            return (int(match.group(1)), None, content)
        
        return None

    def _is_continuation_of_previous_page(self, page_num):
        """Check if this page continues a page number sequence."""
        if page_num not in self.page_content:
            return False
        
        sorted_pages = sorted(self.page_content.keys())
        page_index = sorted_pages.index(page_num)
        
        if page_index == 0:
            return False
        
        prev_page = sorted_pages[page_index - 1]
        
        current_seq = self._get_page_number_sequence(page_num)
        prev_seq = self._get_page_number_sequence(prev_page)
        
        if not current_seq or not prev_seq:
            return False
        
        current_num, current_total, _ = current_seq
        prev_num, prev_total, _ = prev_seq
        
        if current_total and prev_total:
            if current_total == prev_total and current_num == prev_num + 1:
                return True
        elif current_num and prev_num and not current_total and not prev_total:
            if current_num == prev_num + 1:
                return True
        
        return False

    def _get_segment_content(self, pages):
        """
        Get content for a document segment (V2 style - simple and clean).
        Returns plain text with bounding boxes.
        """
        content = ""
        for page_num in sorted(pages):
            page_data = self.page_content.get(page_num, {})
            
            content += f"\n=== PAGE {page_num} ===\n"
            
            # Add paragraphs with bounding boxes
            for para in page_data.get('paragraphs', []):
                bbox = para.get('boundingBox', [])
                bbox_str = ",".join(map(str, bbox)) if bbox else "unknown"
                content += f"[Role: {para['role']}, BBox: {bbox_str}]\n"
                content += f"{para['content']}\n\n"
            
            # Add page numbers
            for pn in page_data.get('page_numbers', []):
                bbox = pn.get('boundingBox', [])
                bbox_str = ",".join(map(str, bbox)) if bbox else "unknown"
                content += f"[Page Number, BBox: {bbox_str}]\n"
                content += f"{pn['content']}\n\n"
        
        return content

    def analyze_with_llm(self, document_content, segment_id):
        """
        Analyze document using LLM (V2 style - proven to work).
        
        Args:
            document_content: The document content to analyze
            segment_id: Segment identifier
        
        Returns:
            str: LLM analysis result
        """
        print(f"\n🤖 Running LLM analysis for {segment_id}...")
        
        try:
            if self.cached_model:
                # Use cached model
                print(f"   Using cached prompt (cost savings!)")
                gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
                message = gemini.invoke(
                    f"Document Content to Analyze:\n{document_content}",
                    model_kwargs={'cached_content': self.cached_model}
                )
                analysis_result = message.content
                print(f"✅ LLM analysis completed for {segment_id} (using cache)")
            else:
                # No cache - send full prompt (V2 style)
                print(f"   Sending full prompt (no cache)")
                full_prompt = f"{MASTER_PROMPT}\n\nDocument Content to Analyze:\n{document_content}"
                gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
                message = gemini.invoke(full_prompt)
                analysis_result = message.content
                print(f"✅ LLM analysis completed for {segment_id}")
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ Error in LLM analysis for {segment_id}: {e}")
            # Fallback: try without cache
            try:
                print(f"   Trying fallback without cache...")
                full_prompt = f"{MASTER_PROMPT}\n\nDocument Content to Analyze:\n{document_content}"
                gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
                message = gemini.invoke(full_prompt)
                return message.content
            except Exception as fallback_error:
                return f"Error in LLM analysis: {str(fallback_error)}"

    def process_document(self, output_filepath=None):
        """Main processing workflow."""
        if not self.analyze_result:
            print("❌ Processing stopped due to loading errors.")
            return

        print("\n🔍 Organizing content by page...")
        self._organize_content_by_page()
        
        if not self.page_content:
            print("❌ No pages with content found.")
            return
        
        print("\n🔍 Detecting document boundaries...")
        self._detect_document_boundaries()
        
        print("\n🔍 Processing document segments...")
        self._process_segments(output_filepath)

    def _process_segments(self, output_filepath=None):
        """Process each document segment."""
        if not self.document_segments:
            print("❌ No document segments found.")
            return
        
        output_file = None
        try:
            if output_filepath:
                output_file = open(output_filepath, 'w', encoding='utf-8')
                output_file.write(f"=== Document Analysis: {self.filepath} ===\n\n")
                output_file.write(f"Prompt Used: {PROMPT_FILE}\n")
                output_file.write(f"Total Pages: {len(self.page_content)}\n")
                output_file.write(f"Document Segments: {len(self.document_segments)}\n\n")
            
            for segment_id, segment_info in self.document_segments.items():
                pages = segment_info['pages']
                print(f"\n📄 Processing {segment_id}: Pages {min(pages)}-{max(pages)} ({len(pages)} pages)")
                
                # Get segment content (V2 style)
                segment_content = self._get_segment_content(pages)
                
                # Run LLM analysis (V2 style)
                llm_result = self.analyze_with_llm(segment_content, segment_id)
                
                # Write to file
                if output_file:
                    output_file.write(f"\n{'='*60}\n")
                    output_file.write(f"SEGMENT: {segment_id}\n")
                    output_file.write(f"Pages: {min(pages)}-{max(pages)} ({len(pages)} pages)\n")
                    output_file.write(f"{'='*60}\n\n")
                    
                    output_file.write("LLM ANALYSIS RESULTS:\n")
                    output_file.write(llm_result)
                    output_file.write("\n\n")
            
            print(f"\n✅ All segments processed successfully!")
            
        except Exception as e:
            print(f"❌ Error writing to file: {e}")
        finally:
            if output_file:
                output_file.close()
                print(f"📄 Output saved to: {output_filepath}")


def delete_old_caches():
    """Delete old caches to ensure fresh start."""
    print("\n🗑️  Checking for old caches...")
    
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
        
        caches = client.caches.list()
        deleted_count = 0
        
        for cache in caches:
            # Delete any cache with 'sensitive' or 'classifier' in the name
            if any(keyword in cache.display_name.lower() for keyword in ['sensitive', 'classifier', 'document']):
                print(f"   Deleting old cache: {cache.display_name}")
                client.caches.delete(name=cache.name)
                deleted_count += 1
        
        if deleted_count > 0:
            print(f"✅ Deleted {deleted_count} old cache(s)")
        else:
            print("✅ No old caches found")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Could not delete old caches: {e}")
        print("   Continuing anyway...")
        return False


def create_cache(system_instruction, ttl="600s"):
    """
    Create a NEW cache with the prompt.
    
    Args:
        system_instruction: The prompt content
        ttl: Time to live (default: 10 minutes)
    
    Returns:
        Cache object or None
    """
    print(f"\n🔄 Creating NEW cache with {PROMPT_FILE}...")
    
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
        
        # Unique cache name with timestamp
        timestamp = int(time.time())
        cache_name = f'doc_classifier_clean_{timestamp}'
        
        print(f"   Cache name: {cache_name}")
        print(f"   Prompt length: {len(system_instruction)} characters")
        print(f"   TTL: {ttl}")
        
        cache = client.caches.create(
            model=model,
            config=types.CreateCachedContentConfig(
                display_name=cache_name,
                system_instruction=system_instruction,
                ttl=ttl,
            )
        )
        
        print(f"✅ Cache created successfully!")
        print(f"   Cache ID: {cache.name}")
        
        return cache
        
    except Exception as e:
        print(f"❌ Error creating cache: {e}")
        print("⚠️  Will proceed without caching (higher cost but will work)")
        return None


if __name__ == '__main__':
    # Configuration
    data_path = '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/'
    json_files = glob.glob(f"{data_path}Personal_Information_*.pdf.json")
    
    print("🚀 CLEAN DOCUMENT PROCESSOR")
    print("="*60)
    print(f"Prompt File: {PROMPT_FILE}")
    print(f"Processing {len(json_files)} files")
    print("Features:")
    print("- ✅ V2's proven working LLM analysis")
    print("- ✅ Proper caching with cache management")
    print("- ✅ Flexible prompt loading")
    print("- ✅ Clean, simple code")
    print("="*60)
    
    # Step 1: Delete old caches
    delete_old_caches()
    
    # Step 2: Create NEW cache
    ttl = "600s"
    print(f"\n📊 Cache TTL: 10 minutes")
    
    cached_model = create_cache(MASTER_PROMPT, ttl=ttl)
    
    if cached_model:
        print(f"\n💰 Cost Savings: Caching enabled for {len(json_files)} files!")
        print(f"   First file: ~7,600 tokens")
        print(f"   Remaining files: ~100 tokens each")
        print(f"   Total savings: ~{(len(json_files) - 1) * 7500} tokens\n")
    else:
        print(f"\n⚠️  Caching disabled - will send full prompt each time\n")
    
    # Step 3: Process all files
    output_path = '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/'
    os.makedirs(output_path, exist_ok=True)
    
    for json_file in sorted(json_files):
        print(f"\n{'='*60}")
        print(f"🔍 Processing: {json_file}")
        print(f"{'='*60}")
        
        base_name = os.path.basename(json_file).replace('.pdf.json', '')
        output_filename = f"{output_path}{base_name}_CLEAN_analysis.txt"
        
        try:
            processor = DocumentProcessor(json_file, cached_model=cached_model)
            processor.process_document(output_filepath=output_filename)
            print(f"✅ Successfully processed: {output_filename}")
        except Exception as e:
            print(f"❌ Error processing {json_file}: {e}")
    
    print(f"\n🎯 All files processed!")
    print(f"   Prompt used: {PROMPT_FILE}")
    print(f"   Output files: *_CLEAN_analysis.txt")
    if cached_model:
        print(f"   Cache reused {len(json_files) - 1} times - significant cost savings! 💰")

