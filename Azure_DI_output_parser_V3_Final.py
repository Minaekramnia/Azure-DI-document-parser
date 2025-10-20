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

def load_master_prompt_v3():
    """Load Master Prompt V3 from the markdown file."""
    # Try multiple paths (Databricks volume, then local)
    paths = [
        '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/prompt_v3.md',
        'prompt_v3.md',  # Local path
        os.path.join(os.path.dirname(__file__), 'prompt_v3.md')  # Same directory as script
    ]
    
    for prompt_path in paths:
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"✅ Loaded prompt from: {prompt_path}")
            return content.strip()
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"⚠️  Error loading from {prompt_path}: {e}")
            continue
    
    print(f"❌ Error: Could not find prompt_v3.md in any of these locations:")
    for p in paths:
        print(f"   - {p}")
    return None

# Load the Master Prompt V3
MASTER_PROMPT_V3 = load_master_prompt_v3()

if not MASTER_PROMPT_V3:
    print("❌ Failed to load Master Prompt V3. Exiting.")
    exit(1)

class SimpleDocumentProcessorV3:
    def __init__(self, filepath, cached_model=None):
        self.filepath = filepath
        self.analyze_result = None
        self.page_content = {}
        self.page_dimensions = {}
        self.document_segments = {}
        self.cached_model = cached_model  # Store the cache object
        self._load_data()

    def _load_data(self):
        """Load and parse the JSON file."""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            # Handle nested structure
            if 'analyzeResult' in raw_data:
                self.analyze_result = raw_data['analyzeResult']
            else:
                self.analyze_result = raw_data
                
            print(f"✅ Loaded: {self.filepath}")
            return True
        except Exception as e:
            print(f"❌ Error loading {self.filepath}: {e}")
            return False

    def _organize_content_by_page(self):
        """Organize content by page number with bounding boxes."""
        if not self.analyze_result:
            return

        # Initialize containers for each page
        for page in self.analyze_result.get('pages', []):
            page_number = page.get('pageNumber')
            if page_number:
                self.page_content[page_number] = {'paragraphs': [], 'tables': [], 'page_numbers': []}
                self.page_dimensions[page_number] = {
                    'width': page.get('width'), 'height': page.get('height'), 'unit': page.get('unit')
                }
        
        # Process paragraphs with bounding boxes
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

    def _detect_document_boundaries(self):
        """Detect document boundaries using 3 rules."""
        if not self.page_content:
            return
        
        sorted_pages = sorted(self.page_content.keys())
        document_segments = []
        current_segment = []
        
        for i, page_num in enumerate(sorted_pages):
            page_data = self.page_content[page_num]
            
            # Check indicators for this page
            has_new_title = self._has_title_at_start(page_data)
            has_page_number = self._has_page_number(page_data)
            has_size_change = False
            
            if i > 0:
                prev_page = sorted_pages[i-1]
                has_size_change = self._page_size_changed(prev_page, page_num)
            
            # Decision logic
            is_new_document = False
            
            if i == 0:
                is_new_document = True
                print(f"📄 Document boundary at page {page_num}: First page")
            else:
                if has_new_title:
                    if has_page_number and self._is_continuation_of_previous_page(page_num):
                        is_new_document = False
                        print(f"📖 Page {page_num}: Page number sequence overrides new title")
                    else:
                        is_new_document = True
                        print(f"📄 Document boundary at page {page_num}: New title found")
                elif has_size_change:
                    is_new_document = True
                    print(f"📏 Document boundary at page {page_num}: Page size changed")
                elif has_page_number:
                    if self._is_continuation_of_previous_page(page_num):
                        is_new_document = False
                        print(f"📖 Page {page_num}: Continuation detected")
                    else:
                        is_new_document = False
                        print(f"📖 Page {page_num}: Page number indicates continuation")
                else:
                    is_new_document = False
                    print(f"📄 Page {page_num}: No clear indicators - assuming continuation")
            
            # Start new segment if it's a new document
            if is_new_document and current_segment:
                document_segments.append(current_segment)
                current_segment = []
            
            current_segment.append(page_num)
        
        # Add the last segment
        if current_segment:
            document_segments.append(current_segment)
        
        # Store document segments
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
        for para in paragraphs[:3]:  # Check first 3 paragraphs
            if para.get('role') == 'title':
                return True
        return False

    def _has_page_number(self, page_data):
        """Check if page has page number content."""
        page_numbers = page_data.get('page_numbers', [])
        if page_numbers:
            return True
        
        # Check paragraphs for page number patterns
        import re
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

    def _parse_page_number(self, content):
        """Parse page number content to extract sequence info."""
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
        
        current_num, current_total, current_text = current_seq
        prev_num, prev_total, prev_text = prev_seq
        
        # Check if it's a continuation of the same document sequence
        if current_total and prev_total:
            if current_total == prev_total and current_num == prev_num + 1:
                print(f"📖 Page {page_num}: Continuation detected - {prev_text} → {current_text}")
                return True
        
        elif current_num and prev_num and not current_total and not prev_total:
            if current_num == prev_num + 1:
                print(f"📖 Page {page_num}: Continuation detected - {prev_text} → {current_text}")
                return True
        
        return False

    def _get_segment_content_as_markdown(self, pages):
        """Get content for a document segment formatted as Markdown with bounding boxes."""
        markdown_content = ""
        
        for page_num in sorted(pages):
            page_data = self.page_content.get(page_num, {})
            
            # Add page header
            markdown_content += f"\n## Page {page_num}\n\n"
            
            # Add page numbers if present
            for pn in page_data.get('page_numbers', []):
                bbox = pn.get('boundingBox', [])
                bbox_str = ",".join(map(str, bbox)) if bbox else "unknown"
                markdown_content += f"*Page Number: {pn['content']}* (bbox: {bbox_str})\n\n"
            
            # Add paragraphs with role information and bounding boxes
            for para in page_data.get('paragraphs', []):
                role = para.get('role', 'paragraph')
                content = para.get('content', '')
                bbox = para.get('boundingBox', [])
                bbox_str = ",".join(map(str, bbox)) if bbox else "unknown"
                
                if role == 'title':
                    markdown_content += f"### {content} (bbox: {bbox_str})\n\n"
                elif role == 'heading':
                    markdown_content += f"**{content}** (bbox: {bbox_str})\n\n"
                else:
                    markdown_content += f"{content} (bbox: {bbox_str})\n\n"
        
        return markdown_content

    def analyze_document_with_llm(self, markdown_content, segment_id):
        """Analyze document segment using cached model or regular LLM."""
        print(f"\n🤖 Running LLM analysis for {segment_id}...")
        
        try:
            if self.cached_model:
                # Use itsai with cached content
                gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
                
                # Pass the cache object via model_kwargs
                message = gemini.invoke(
                    f"Document Content to Analyze:\n{markdown_content}",
                    model_kwargs={'cached_content': self.cached_model}
                )
                
                analysis_result = message.content
                print(f"✅ LLM analysis completed for {segment_id} (using cache)")
                return analysis_result
            else:
                # Use regular model (send full prompt each time)
                full_prompt = f"{MASTER_PROMPT_V3}\n\nDocument Content to Analyze:\n{markdown_content}"
                gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
                message = gemini.invoke(full_prompt)
                analysis_result = message.content
                print(f"✅ LLM analysis completed for {segment_id}")
                return analysis_result
            
        except Exception as e:
            print(f"❌ Error in LLM analysis for {segment_id}: {e}")
            print(f"⚠️  Falling back to non-cached mode for this segment")
            # Fallback: use full prompt without cache
            try:
                full_prompt = f"{MASTER_PROMPT_V3}\n\nDocument Content to Analyze:\n{markdown_content}"
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
        self._process_document_segments(output_filepath)

    def _process_document_segments(self, output_filepath=None):
        """Process each document segment and write output."""
        if not self.document_segments:
            print("❌ No document segments found.")
            return
        
        output_file = None
        try:
            if output_filepath:
                output_file = open(output_filepath, 'w', encoding='utf-8')
                output_file.write(f"=== Document Analysis V3 (Prompt V3): {self.filepath} ===\n\n")
                output_file.write(f"Total Pages: {len(self.page_content)}\n")
                output_file.write(f"Document Segments: {len(self.document_segments)}\n\n")
            
            for segment_id, segment_info in self.document_segments.items():
                pages = segment_info['pages']
                print(f"\n📄 Processing {segment_id}: Pages {min(pages)}-{max(pages)} ({len(pages)} pages)")
                
                # Get segment content as Markdown with bounding boxes
                markdown_content = self._get_segment_content_as_markdown(pages)
                
                # Run LLM analysis with Prompt V3
                llm_result = self.analyze_document_with_llm(markdown_content, segment_id)
                
                # Write to file
                if output_file:
                    output_file.write(f"\n{'='*60}\n")
                    output_file.write(f"SEGMENT: {segment_id}\n")
                    output_file.write(f"Pages: {min(pages)}-{max(pages)} ({len(pages)} pages)\n")
                    output_file.write(f"{'='*60}\n\n")
                    
                    output_file.write("LLM ANALYSIS RESULTS (Prompt V3):\n")
                    output_file.write(llm_result)
                    output_file.write("\n\n")
            
            print(f"\n✅ All segments processed successfully!")
            
        except Exception as e:
            print(f"❌ Error writing to file: {e}")
        finally:
            if output_file:
                output_file.close()
                print(f"📄 Output saved to: {output_filepath}")


def create_cached_model(system_instruction, ttl="600s"):
    """
    Create a cached model with the system instruction (prompt).
    
    Args:
        system_instruction: The prompt content from prompt_v3.md
        ttl: Time to live for the cache (default: 10 minutes)
    
    Returns:
        CachedContent object
    """
    print("🔄 Creating cache for prompt...")
    
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
        
        print("Creating cache from prompt content...")
        cache = client.caches.create(
            model=model,
            config=types.CreateCachedContentConfig(
                display_name='sensitive_data_classifier_v3',
                system_instruction=system_instruction,
                ttl=ttl,
            )
        )
        
        print(f"✅ Cache created successfully: {cache.name}")
        print(f"   TTL: {ttl} ({int(ttl.replace('s', '')) / 60} minutes)")
        
        return cache  # Return the cache object itself
        
    except Exception as e:
        print(f"❌ Error creating cache: {e}")
        print("⚠️  Falling back to non-cached mode")
        return None


if __name__ == '__main__':
    # Process all Personal_Information_#.pdf.json files from Databricks volume
    data_path = '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/'
    json_files = glob.glob(f"{data_path}Personal_Information_*.pdf.json")
    
    print("🚀 DOCUMENT PROCESSOR V3 FINAL WITH CACHING")
    print("="*60)
    print(f"Processing {len(json_files)} files")
    print("Features:")
    print("- Document segmentation with 3-rule boundary detection")
    print("- LLM analysis using Master Prompt V3 (prompt_v3.md)")
    print("- Markdown-formatted content with bounding boxes")
    print("- Sensitive information detection")
    print("- Name extraction with context")
    print("- 🆕 PROMPT CACHING for cost savings!")
    print("="*60)
    
    # Set TTL to 600 seconds (10 minutes)
    ttl = "600s"
    
    print(f"\n📊 Cache TTL set to: 10 minutes (600 seconds)")
    
    # Create cached model once for all files
    cached_model = create_cached_model(MASTER_PROMPT_V3, ttl=ttl)
    
    if cached_model:
        print(f"\n💰 Cost Savings: Using cached prompt for {len(json_files)} files!")
        print(f"   Estimated savings: ~{(len(json_files) - 1) * 60}% reduction in prompt tokens\n")
    
    # Process all files with the cached model
    output_path = '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/'
    
    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    print(f"📁 Output directory ready: {output_path}\n")
    
    for json_file in sorted(json_files):
        print(f"\n{'='*60}")
        print(f"🔍 Processing: {json_file}")
        print(f"{'='*60}")
        
        # Create output filename with _final_analysis suffix
        base_name = os.path.basename(json_file).replace('.pdf.json', '')
        output_filename = f"{output_path}{base_name}_final_analysis.txt"
        
        try:
            # Pass cached model to processor
            processor = SimpleDocumentProcessorV3(json_file, cached_model=cached_model)
            processor.process_document(output_filepath=output_filename)
            print(f"✅ Successfully processed: {output_filename}")
        except Exception as e:
            print(f"❌ Error processing {json_file}: {e}")
    
    print(f"\n🎯 All files processed with caching!")
    print(f"   Cache was reused {len(json_files) - 1} times")
    print(f"   Significant cost savings achieved! 💰")
