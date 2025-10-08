import json
from itsai.mai import llm
from itsai import llm_registry

def load_master_prompt_v3():
    """Load Master Prompt V3 from the markdown file."""
    try:
        with open('prompt_v3.md', 'r', encoding='utf-8') as f:
            content = f.read()
        return content.strip()
    except Exception as e:
        print(f"❌ Error loading prompt_v3.md: {e}")
        return None

# Load Master Prompt V3 for sensitive information analysis with name extraction
MASTER_PROMPT_V3 = load_master_prompt_v3()

class SimpleDocumentProcessorV3:
    def __init__(self, filepath):
        self.filepath = filepath
        self.analyze_result = None
        self.page_content = {}
        self.page_dimensions = {}
        self.document_segments = {}
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
        """Organize content by page number."""
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
        """Analyze document segment using Master Prompt V3 and LLM."""
        print(f"\n🤖 Running LLM analysis for {segment_id}...")
        
        full_prompt = f"{MASTER_PROMPT_V3}\n\nDocument Content to Analyze:\n{markdown_content}"
        
        try:
            gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
            message = gemini.invoke(full_prompt)
            analysis_result = message.content
            
            print(f"✅ LLM analysis completed for {segment_id}")
            return analysis_result
            
        except Exception as e:
            print(f"❌ Error in LLM analysis for {segment_id}: {e}")
            return f"Error in LLM analysis: {str(e)}"

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
                output_file.write(f"=== Document Analysis V3: {self.filepath} ===\n\n")
                output_file.write(f"Total Pages: {len(self.page_content)}\n")
                output_file.write(f"Document Segments: {len(self.document_segments)}\n\n")
            
            for segment_id, segment_info in self.document_segments.items():
                pages = segment_info['pages']
                print(f"\n📄 Processing {segment_id}: Pages {min(pages)}-{max(pages)} ({len(pages)} pages)")
                
                # Get segment content as Markdown
                markdown_content = self._get_segment_content_as_markdown(pages)
                
                # Run LLM analysis
                llm_result = self.analyze_document_with_llm(markdown_content, segment_id)
                
                # Write to file
                if output_file:
                    output_file.write(f"\n{'='*60}\n")
                    output_file.write(f"SEGMENT: {segment_id}\n")
                    output_file.write(f"Pages: {min(pages)}-{max(pages)} ({len(pages)} pages)\n")
                    output_file.write(f"{'='*60}\n\n")
                    
                    output_file.write("LLM ANALYSIS RESULTS (V3):\n")
                    output_file.write(llm_result)
                    output_file.write("\n\n")
            
            print(f"\n✅ All segments processed successfully!")
            
        except Exception as e:
            print(f"❌ Error writing to file: {e}")
        finally:
            if output_file:
                output_file.close()
                print(f"📄 Output saved to: {output_filepath}")


if __name__ == '__main__':
    import glob
    
    # Process all Personal_Information_#.pdf.json files
    json_files = glob.glob("Personal_Information_*.pdf.json")
    
    print("🚀 SIMPLE DOCUMENT PROCESSOR V3 WITH LLM ANALYSIS")
    print("="*60)
    print(f"Processing {len(json_files)} files")
    print("Features:")
    print("- Document segmentation with 3-rule boundary detection")
    print("- LLM analysis using Master Prompt V3")
    print("- Markdown-formatted content processing")
    print("- Character-range based location tracking")
    print("- Sensitive information detection")
    print("- Name extraction with context")
    print("="*60)
    
    for json_file in sorted(json_files):
        print(f"\n🔍 Processing: {json_file}")
        
        # Create output filename
        base_name = json_file.replace('.pdf.json', '')
        output_filename = f"{base_name}_Final_analysis.txt"
        
        try:
            processor = SimpleDocumentProcessorV3(json_file)
            processor.process_document(output_filepath=output_filename)
            print(f"✅ Successfully processed: {output_filename}")
        except Exception as e:
            print(f"❌ Error processing {json_file}: {e}")
    
    print(f"\n🎯 All files processed with V3!")
