import json
#from itsai.mai import llm
#from itsai import llm_registry

def check_content(llm_input: str, page_num: int):
    """
    Placeholder for processing a page's content, e.g., with an LLM.

    Args:
        llm_input (str): The formatted string content of a single page.
        page_num (int): The page number being processed.
    """
    separator = "=" * 50
    print(f"\n{separator}")
    print(f">>> Processing Page {page_num} Content (Size: {len(llm_input)} chars)")
    # In a real implementation, an LLM API call would be made here.
    # For example: result = process_with_llm(llm_input)
    # print(f">>> LLM Result: {result}")
    print(f"{separator}\n")

def process_document_segment(segment_content: str, segment_id: str, page_range: str):
    """
    Process an entire document segment (multiple pages) with clear boundaries.
    
    Args:
        segment_content (str): The concatenated content of all pages in the segment.
        segment_id (str): The identifier for this document segment.
        page_range (str): The page range (e.g., "Pages 1-3").
    """
    separator = "=" * 80
    print(f"\n{separator}")
    print(f">>> DOCUMENT SEGMENT: {segment_id}")
    print(f">>> {page_range}")
    print(f">>> Content Size: {len(segment_content)} chars")
    print(f"{separator}")
    
    # Add clear document boundary separator
    print(f"\n{'='*80}")
    print(f"📄 DOCUMENT BOUNDARY - {segment_id.upper()}")
    print(f"{'='*80}")
    
    # In a real implementation, an LLM API call would be made here for the entire document segment.
    # For example: result = process_with_llm(segment_content)
    # print(f">>> LLM Result for entire document: {result}")
    
    print(f"{'='*80}")
    print(f"END OF DOCUMENT SEGMENT: {segment_id}")
    print(f"{'='*80}\n")


class AzureLayoutProcessor:
    """
    Processes an Azure Document Intelligence Layout JSON file to extract
    and format content page by page with document splitting functionality.
    """
    def __init__(self, filepath):
        """
        Initializes the processor by loading and parsing the JSON file.
        """
        self.filepath = filepath
        self.analyze_result = None
        self.page_content = {}
        self.page_dimensions = {}
        self.document_segments = {}  # New: stores document segments
        self._load_data()

    def _load_data(self):
        """Loads and validates the JSON file."""
        print(f"--- Loading and processing file: {self.filepath} ---\n")
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.analyze_result = data.get('analyzeResult')
            if not self.analyze_result:
                raise ValueError("JSON structure is invalid. Missing 'analyzeResult' key.")
        except FileNotFoundError:
            print(f"Error: The file '{self.filepath}' was not found.")
            self.analyze_result = None
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error: {e}")
            self.analyze_result = None

    def _organize_content_by_page(self):
        """Extracts and organizes all content from the JSON into a page-centric dictionary."""
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
        
        # Process and assign paragraphs
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

        # Process and assign tables
        for table in self.analyze_result.get('tables', []):
            if table.get('cells') and table['cells'][0].get('boundingRegions'):
                page_number = table['cells'][0]['boundingRegions'][0].get('pageNumber')
                if page_number in self.page_content:
                    self.page_content[page_number]['tables'].append(table)

    def _detect_document_boundaries(self):
        """
        Detects document boundaries using the 3 rules with improved logic:
        1. Page size change (height/width) - creates new boundary
        2. New title at page start - creates new boundary  
        3. Page number indicates continuation - only within same document type
        """
        if not self.page_content:
            return
        
        # Sort pages by page number
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
            
            # Decision logic: New document vs Continuation
            is_new_document = False
            decision_reason = ""
            
            if i == 0:
                # First page is always a new document start
                is_new_document = True
                decision_reason = "First page"
                print(f"📄 Document boundary detected at page {page_num}: {decision_reason}")
            else:
                # For subsequent pages, check the rules
                if has_new_title:
                    # Rule 2: New title creates boundary UNLESS it's part of a page number sequence
                    if has_page_number and self._is_continuation_of_previous_page(page_num):
                        # Page number sequence takes priority over new title
                        is_new_document = False
                        decision_reason = "Page number sequence overrides new title"
                        # Don't print here as _is_continuation_of_previous_page already prints
                    else:
                        # New title creates new boundary
                        is_new_document = True
                        decision_reason = "New title found"
                        print(f"📄 Document boundary detected at page {page_num}: {decision_reason}")
                elif has_size_change:
                    # Rule 1: Size change creates new boundary
                    # Size change is a strong indicator of new document regardless of page numbers
                    is_new_document = True
                    decision_reason = "Page size changed - strong indicator of new document"
                    print(f"📏 Document boundary detected at page {page_num}: {decision_reason}")
                elif has_page_number:
                    # Rule 3: Check if page number indicates continuation of previous page
                    if self._is_continuation_of_previous_page(page_num):
                        # This is a continuation of the previous page's sequence
                        is_new_document = False
                        decision_reason = "Page number sequence indicates continuation"
                        # Don't print here as _is_continuation_of_previous_page already prints
                    else:
                        # Page number exists but doesn't form a sequence - treat as continuation anyway
                        is_new_document = False
                        decision_reason = "Page number indicates continuation"
                        print(f"📖 Page {page_num}: {decision_reason}")
                else:
                    # No clear indicators - assume continuation
                    is_new_document = False
                    decision_reason = "No clear boundary indicators - assuming continuation"
                    print(f"📄 Page {page_num}: {decision_reason}")
            
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
        
        print(f"\n📚 Document splitting complete:")
        print(f"   Found {len(document_segments)} document segments")
        for segment_id, segment_info in self.document_segments.items():
            pages = segment_info['pages']
            print(f"   {segment_id}: Pages {min(pages)}-{max(pages)} ({len(pages)} pages)")
    
    def _page_size_changed(self, prev_page_num, curr_page_num):
        """Check if page dimensions changed between pages."""
        if prev_page_num not in self.page_dimensions or curr_page_num not in self.page_dimensions:
            return False
        
        prev_dims = self.page_dimensions[prev_page_num]
        curr_dims = self.page_dimensions[curr_page_num]
        
        # Check if height or width changed significantly (more than 5% difference)
        height_change = abs(prev_dims.get('height', 0) - curr_dims.get('height', 0)) / max(prev_dims.get('height', 1), 1)
        width_change = abs(prev_dims.get('width', 0) - curr_dims.get('width', 0)) / max(prev_dims.get('width', 1), 1)
        
        return height_change > 0.05 or width_change > 0.05
    
    def _has_title_at_start(self, page_data):
        """Check if page starts with a title role."""
        paragraphs = page_data.get('paragraphs', [])
        if not paragraphs:
            return False
        
        # Check first few paragraphs for title role
        for para in paragraphs[:3]:  # Check first 3 paragraphs
            if para.get('role') == 'title':
                return True
        return False
    
    def _has_page_number(self, page_data):
        """Check if page has page number content."""
        page_numbers = page_data.get('page_numbers', [])
        paragraphs = page_data.get('paragraphs', [])
        
        # Check page_numbers section
        if page_numbers:
            return True
        
        # Check paragraphs for page number patterns (e.g., "1/4", "Page 1", etc.)
        for para in paragraphs:
            content = para.get('content', '').strip()
            if self._looks_like_page_number(content):
                return True
        
        return False
    
    def _looks_like_page_number(self, content):
        """Check if content looks like a page number."""
        import re
        # Common page number patterns
        patterns = [
            r'^\d+$',  # Just a number
            r'^\d+/\d+$',  # 1/4 format
            r'^page\s*\d+$',  # Page 1 format
            r'^\d+\s*of\s*\d+$',  # 1 of 4 format
        ]
        
        content_lower = content.lower().strip()
        for pattern in patterns:
            if re.match(pattern, content_lower):
                return True
        return False

    def _get_page_number_sequence(self, page_num):
        """Extract page number sequence information (e.g., '1/4' -> (1, 4))."""
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
        
        # Skip invalid page numbers (non-numeric characters, symbols, etc.)
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
                print(f"📖 Page {page_num}: Continuation detected - {prev_text} → {current_text}")
                return True
        
        elif current_num and prev_num and not current_total and not prev_total:
            # Both are simple page numbers (e.g., 1, 2, 3)
            if current_num == prev_num + 1:
                print(f"📖 Page {page_num}: Continuation detected - {prev_text} → {current_text}")
                return True
        
        return False

    def _format_markdown_table(self, table_data):
        """Formats a single table dictionary into a Markdown string."""
        row_count = table_data.get('rowCount', 0)
        col_count = table_data.get('columnCount', 0)
        if row_count == 0 or col_count == 0:
            return ""

        grid = [["" for _ in range(col_count)] for _ in range(row_count)]
        for cell in table_data.get('cells', []):
            grid[cell['rowIndex']][cell['columnIndex']] = cell.get('content', '')

        lines = []
        header = [str(h).replace('|', '\\|') for h in grid[0]]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "---|"*len(header))
        for row in grid[1:]:
            row_safe = [str(r).replace('|', '\\|') for r in row]
            lines.append("| " + " | ".join(row_safe) + " |")
        return "\n".join(lines)

    def _format_page_as_markdown_with_details(self, page_num):
        """Enhanced version that includes page dimensions and boundary indicators."""
        content = self.page_content.get(page_num, {})
        dims = self.page_dimensions.get(page_num, {})
        
        # Page header with dimensions
        lines = [f"# Page {page_num}"]
        lines.append(f"**📏 Dimensions:** {dims.get('width', 'Unknown')} x {dims.get('height', 'Unknown')} {dims.get('unit', 'Unknown')}")
        
        # Check if this page starts a new document segment
        if page_num in [min(segment['pages']) for segment in self.document_segments.values()]:
            lines.append("**🆕 DOCUMENT START**")
            lines.append("**🔥 NEW DOCUMENT DETECTED**")
        
        # Check for page numbers (continuation indicator)
        page_numbers = content.get('page_numbers', [])
        if page_numbers:
            page_nums = [pn['content'] for pn in page_numbers]
            lines.append(f"**📖 Page Numbers:** {page_nums} (Continuation indicator)")
            lines.append("**↗️ DOCUMENT CONTINUATION**")
        
        # Check for titles (document start indicator)
        titles = [p for p in content.get('paragraphs', []) if p.get('role') == 'title']
        if titles:
            lines.append(f"**🎯 TITLE FOUND:** '{titles[0]['content']}'")
        
        # Check for dimension changes from previous page
        sorted_pages = sorted(self.page_content.keys())
        page_index = sorted_pages.index(page_num)
        if page_index > 0:
            prev_page = sorted_pages[page_index - 1]
            prev_dims = self.page_dimensions.get(prev_page, {})
            if (prev_dims.get('width') != dims.get('width') or 
                prev_dims.get('height') != dims.get('height')):
                lines.append(f"**📏 SIZE CHANGED FROM PREVIOUS PAGE**")
                lines.append(f"**🔄 DIMENSION CHANGE DETECTED**")
        
        lines.append("")  # Empty line

        # Format Page Numbers
        if page_numbers:
            lines.append("## Page Numbers")
            for item in page_numbers:
                bbox_str = ",".join(map(str, item.get('boundingBox', [])))
                lines.extend([f"**BoundingBox:** {bbox_str}", f"> {item['content']}\n", "---\n"])

        # Format Paragraphs
        if content.get('paragraphs'):
            lines.append("## Paragraphs")
            for item in content['paragraphs']:
                bbox_str = ",".join(map(str, item.get('boundingBox', [])))
                role = item.get('role', 'paragraph')
                if role == 'title':
                    lines.append(f"**🎯 TITLE DETECTED:** {role}")
                lines.extend([f"**Role:** {role}", f"**BoundingBox:** {bbox_str}", f"> {item['content']}\n", "---\n"])
        
        # Format Tables
        if content.get('tables'):
            lines.append("## Tables")
            for table in content['tables']:
                lines.append(self._format_markdown_table(table))
                lines.append("\n---\n")

        return "\n".join(lines)

    def _format_page_as_markdown(self, page_num):
        """Formats all content of a single page into a Markdown string."""
        content = self.page_content.get(page_num, {})
        lines = [f"# Page {page_num}\n"]

        # Format Page Numbers
        if content.get('page_numbers'):
            lines.append("## Page Numbers\n")
            for item in content['page_numbers']:
                bbox_str = ",".join(map(str, item.get('boundingBox', [])))
                lines.extend([f"**BoundingBox:** {bbox_str}", f"> {item['content']}\n", "---\n"])

        # Format Paragraphs
        if content.get('paragraphs'):
            lines.append("## Paragraphs\n")
            for item in content['paragraphs']:
                bbox_str = ",".join(map(str, item.get('boundingBox', [])))
                lines.extend([f"**Role:** {item['role']}", f"**BoundingBox:** {bbox_str}", f"> {item['content']}\n", "---\n"])
        
        # Format Tables
        if content.get('tables'):
            lines.append("## Tables\n")
            for table in content['tables']:
                lines.append(self._format_markdown_table(table))
                lines.append("\n---\n")

        return "\n".join(lines)

    def process_document(self, output_filepath=None):
        """
        Orchestrates the document processing workflow: organizing, formatting,
        and calling the content check for each page. Writes output to a file.
        """
        if not self.analyze_result:
            print("Processing stopped due to loading errors.")
            return

        self._organize_content_by_page()
        if not self.page_content:
            print("No pages with content were found.")
            return
        
        # NEW: Detect document boundaries and split into segments
        print("\n" + "="*60)
        print("🔍 DOCUMENT BOUNDARY DETECTION")
        print("="*60)
        self._detect_document_boundaries()
        
        # Process each document segment separately
        self._process_document_segments(output_filepath)

    def _process_document_segments(self, output_filepath=None):
        """
        Process each document segment separately and write output with detailed page information.
        """
        if not self.document_segments:
            print("No document segments found. Processing as single document.")
            return
        
        output_file = None
        try:
            if output_filepath:
                output_file = open(output_filepath, 'w', encoding='utf-8')
                output_file.write(f"--- Document Analysis with Segmentation for {self.filepath} ---\n\n")
                
                # Write page dimension summary
                output_file.write("📏 PAGE DIMENSIONS SUMMARY:\n")
                output_file.write("-" * 50 + "\n")
                for page_num in sorted(self.page_content.keys()):
                    dims = self.page_dimensions.get(page_num, {})
                    width = dims.get('width', 'Unknown')
                    height = dims.get('height', 'Unknown')
                    unit = dims.get('unit', 'Unknown')
                    output_file.write(f"Page {page_num}: {width} x {height} {unit}\n")
                output_file.write("\n")
                
                # Write document change summary
                output_file.write("🔄 DOCUMENT CHANGE SUMMARY:\n")
                output_file.write("=" * 60 + "\n")
                output_file.write(f"Total Pages: {len(self.page_content)}\n")
                output_file.write(f"Document Segments Found: {len(self.document_segments)}\n")
                output_file.write(f"Document Changes Detected: {len(self.document_segments) - 1}\n\n")
                
                # Show each document change point
                sorted_pages = sorted(self.page_content.keys())
                for i, page_num in enumerate(sorted_pages):
                    if i > 0:
                        prev_page = sorted_pages[i-1]
                        page_data = self.page_content[page_num]
                        prev_dims = self.page_dimensions.get(prev_page, {})
                        curr_dims = self.page_dimensions.get(page_num, {})
                        
                        # Check for dimension changes
                        dim_change = ""
                        if (prev_dims.get('width') != curr_dims.get('width') or 
                            prev_dims.get('height') != curr_dims.get('height')):
                            dim_change = f"📏 SIZE CHANGE: {prev_dims.get('width', '?')}x{prev_dims.get('height', '?')} → {curr_dims.get('width', '?')}x{curr_dims.get('height', '?')}"
                        
                        # Check for titles
                        titles = [p for p in page_data.get('paragraphs', []) if p.get('role') == 'title']
                        title_change = ""
                        if titles:
                            title_change = f"📄 NEW TITLE: '{titles[0]['content']}'"
                        
                        # Check for page numbers
                        page_numbers = page_data.get('page_numbers', [])
                        page_num_change = ""
                        if page_numbers:
                            page_num_change = f"📖 PAGE NUMBER: {page_numbers[0]['content']} (Continuation)"
                        
                        if dim_change or title_change:
                            output_file.write(f"🔄 CHANGE DETECTED AT PAGE {page_num}:\n")
                            if dim_change:
                                output_file.write(f"   {dim_change}\n")
                            if title_change:
                                output_file.write(f"   {title_change}\n")
                            if page_num_change:
                                output_file.write(f"   {page_num_change}\n")
                            output_file.write(f"   → Decision: {'NEW DOCUMENT' if title_change and not page_numbers else 'CONTINUATION' if page_numbers else 'SIZE CHANGE ONLY'}\n\n")
                
                output_file.write("=" * 60 + "\n\n")

            print("\n" + "="*60)
            print("📄 PROCESSING DOCUMENT SEGMENTS")
            print("="*60)

            for segment_id, segment_info in self.document_segments.items():
                pages = segment_info['pages']
                print(f"\n🔍 Processing {segment_id}: Pages {min(pages)}-{max(pages)} ({len(pages)} pages)")
                
                if output_file:
                    output_file.write(f"\n{'='*80}\n")
                    output_file.write(f"DOCUMENT SEGMENT: {segment_id}\n")
                    output_file.write(f"Pages: {min(pages)}-{max(pages)} ({len(pages)} pages)\n")
                    
                    # Write segment analysis
                    output_file.write(f"\n🔍 SEGMENT ANALYSIS:\n")
                    output_file.write("-" * 30 + "\n")
                    for page_num in sorted(pages):
                        page_data = self.page_content[page_num]
                        dims = self.page_dimensions.get(page_num, {})
                        width = dims.get('width', 'Unknown')
                        height = dims.get('height', 'Unknown')
                        unit = dims.get('unit', 'Unknown')
                        
                        # Check for page numbers
                        page_numbers = page_data.get('page_numbers', [])
                        page_number_text = ""
                        if page_numbers:
                            page_number_text = f" | Page Numbers: {[pn['content'] for pn in page_numbers]}"
                        
                        # Check for titles
                        titles = [p for p in page_data.get('paragraphs', []) if p.get('role') == 'title']
                        title_text = ""
                        if titles:
                            title_text = f" | Titles: {[t['content'] for t in titles]}"
                        
                        output_file.write(f"Page {page_num}: {width} x {height} {unit}{page_number_text}{title_text}\n")
                    
                    output_file.write(f"{'='*80}\n\n")
                    
                    # Add clear document boundary separator to output file
                    output_file.write(f"\n{'='*80}\n")
                    output_file.write(f"📄 DOCUMENT BOUNDARY - {segment_id.upper()}\n")
                    output_file.write(f"{'='*80}\n\n")

                # Concatenate all pages in the segment and process as one document
                segment_content = ""
                page_range = f"Pages {min(pages)}-{max(pages)} ({len(pages)} pages)"
                
                for page_num in sorted(pages):
                    print(f"  📖 Concatenating page {page_num}")
                    
                    # Format page content
                    markdown_output = self._format_page_as_markdown_with_details(page_num)
                    
                    if output_file:
                        output_file.write(markdown_output)
                        output_file.write("\n" + "-"*40 + "\n\n")
                    
                    # Add to segment content
                    segment_content += markdown_output + "\n" + "-"*40 + "\n\n"
                
                # Process entire document segment with clear boundaries
                process_document_segment(segment_content, segment_id, page_range)
                
                # Add end separator to output file
                if output_file:
                    output_file.write(f"\n{'='*80}\n")
                    output_file.write(f"END OF DOCUMENT SEGMENT: {segment_id}\n")
                    output_file.write(f"{'='*80}\n\n")

            print(f"\n✅ All document segments processed successfully!")
            
                 # Document processing complete

        except IOError as e:
            print(f"Error writing to file {output_filepath}: {e}")
        finally:
            if output_file:
                output_file.close()
                print(f"\n--- Output successfully saved to {output_filepath} ---")


# def check_content(llm_input: str) -> str:
#     gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
#     message = message.invoke(llm_input)
#     message_content = message.content
#     print (message_content)
if __name__ == '__main__':
    import glob
    
    # Process all Personal_Information JSON files with FINAL improved boundary detection
    json_files = glob.glob("Personal_Information_*.pdf.json")
    
    print("🚀 PROCESSING ALL FILES WITH FINAL IMPROVED BOUNDARY DETECTION")
    print("="*80)
    print("Final improvements:")
    print("- New titles ALWAYS create boundaries")
    print("- Page size changes ALWAYS create boundaries")
    print("- Page number sequences take PRIORITY over new titles")
    print("- Intelligent page number sequence detection (1/4 → 2/4 → 3/4 → 4/4)")
    print("- Invalid page numbers (like '·') are ignored")
    print("="*80)
    
    for json_file in sorted(json_files):
        print(f"\n🔍 Processing: {json_file}")
        
        # Create output filename with the requested naming convention
        base_name = json_file.replace('.pdf.json', '')
        output_filename = f"{base_name}_seperatedDocs.txt"
        
        try:
            processor = AzureLayoutProcessor(json_file)
            processor.process_document(output_filepath=output_filename)
            print(f"✅ Successfully processed: {output_filename}")
        except Exception as e:
            print(f"❌ Error processing {json_file}: {e}")
    
    print(f"\n🎯 All files processed with FINAL improved boundary detection!")
    print(f"   Output files named: Personal_Information_#_seperatedDocs.txt")
    prmpt = '''Instruction: Determine whether the following document is a resume/CV. The document is provided in Markdown format, and each text block 
    includes metadata: role (e.g., header, footer, paragraph) and bounding box coordinates (x0, y0, x1, y1). Use both content and layout information to make your decision. 
    Return a JSON object with the following fields: - is_resume: true/false - confidence: number between 0 and 1 
    - reason: short explanation (1-2 sentences) - probable_sections: list of any detected resume sections bounding box (e.g., ["Header", "Work Experience", "Education", "Skills"]) 
    
    Markdown Document: > 2/4 --- **Role:** pageHeader **BoundingBox:** 1.269,0.5785,2.3474,0.5757,2.3478,0.7248,1.2693,0.7276 > Markus Kostner --- **Role:** sectionHeading **BoundingBox:** 3.7051,1.1112,5.2624,1.1107,5.2625,1.29,3.7051,1.2906 > Professional Experience --- **Role:** paragraph **BoundingBox:** 1.1627,1.3666,2.5853,1.3575,2.5853,1.9014,1.1627,1.9014 > 10/1993- --- **Role:** paragraph **BoundingBox:** 2.5853,1.3575,7.6775,1.3666,7.6775,1.9014,2.5853,1.9014 > Vienna University of Economics and Business Administration. Lecturer in Economics. --- **Role:** paragraph **BoundingBox:** 2.5853,1.9014,7.6775,1.9014,7.6775,2.7987,2.5853,2.7987 > Teaching courses on 'Structural Adjustment in Developing Countries'; supervising students on Master's theses in development economics; Guest Lecturer at the University of Szczecin, Poland, on structural adjustment in economies in transition. --- **Role:** paragraph **BoundingBox:** 1.1627,2.7987,2.5853,2.7987,2.5762,3.3515,1.1537,3.3515 > 03/1993- --- **Role:** paragraph **BoundingBox:** 2.5853,2.7987,7.6775,2.7987,7.6685,3.3515,2.5762,3.3515 > World Bank. Short-term consultant for AFTHR, AF2PH, AF3CO, and AF6PH (human resources economist). --- **Role:** paragraph **BoundingBox:** 2.5762,3.3515,7.6685,3.3515,7.6685,4.7745,2.5762,4.7836 > Participation in identification and supervision missions for poverty/human resources (demobilization/reintegration) projects in Malawi, Rwanda, Uganda, and Mozambique (forthcoming); design of safety net components and monitoring and evaluation systems; preparations for staff training at ministries and universities for undertaking poverty- and policy-related analysis; preparing a poverty-impact study covering the agriculture, education, and health sectors. --- **Role:** paragraph **BoundingBox:** 1.1537,4.7836,2.5762,4.7836,2.5762,5.5087,1.1537,5.5178 > 01/1993- --- **Role:** paragraph **BoundingBox:** 2.5762,4.7836,7.6685,4.7745,7.6594,5.4996,2.5762,5.5087 > Association for Development and Cooperation Austria, Vienna. Assistant to the Director/Project Officer; UN Adviser on secondment to the Ministry of Foreign Affairs. --- **Role:** paragraph **BoundingBox:** 2.5762,5.5087,7.6594,5.4996,7.6504,7.8381,2.5581,7.8653 > Development of salary scheme, design of internal reporting system, preparation of standard contract agreements, development of controlling instruments for short- to medium-term planning. UN Adviser: Advising Austria's permanent representatives to UNIDO on pertinent issues; preparation of policy papers and statements; participation in meetings, conferences, and negotiations with member states; coordination and cooperation with member states of the European Union; general activities in multilateral development cooperation (negotiations, counselling, coordination). --- **Role:** paragraph **BoundingBox:** 1.1446,7.8653,2.5581,7.8653,2.5581,8.2369,1.1446,8.2369 > 03/1989- --- **Role:** paragraph **BoundingBox:** 2.5581,7.8653,7.6504,7.8381,7.6504,8.2097,2.5581,8.2369 > Webster University, Vienna campus. Adjunct Professor in Economics. --- **Role:** paragraph **BoundingBox:** 2.5581,8.2369,7.6504,8.2097,7.6504,8.9257,2.5581,8.9438 > Teaching graduate and undergraduate courses in economics (development economics, comparative economic systems); advising students on curriculum. --- **Role:** paragraph **BoundingBox:** 1.1356,8.9529,2.5581,8.9438,2.5581,9.5058,1.1356,9.5148 > 10/1990-10/1992 --- **Role:** paragraph **BoundingBox:** 2.5581,8.9438,7.6504,8.9257,7.6413,9.4877,2.5581,9.5058 > World Bank, Washington D.C. Economist in the Poverty and Social Policy Division, Africa Technical Department. --- **Role:** paragraph **BoundingBox:** 2.5581,9.5058,7.6413,9.4877,7.6413,10.1856,2.5491,10.2037 > Coordinator of the macromodelling component of the Cameroon SDA project; coordinator of the SDA Study Funds/Poverty Analysis Components in Malawi and Uganda; organization of courses in "Social --- ## Tables | 10/1993- | Vienna University of Economics and Business Administration. Lecturer in Economics. | |---|---| | | Teaching courses on 'Structural Adjustment in Developing Countries'; supervising students on Master's theses in development economics; Guest Lecturer at the University of Szczecin, Poland, on structural adjustment in economies in transition. | | 03/1993- | World Bank. Short-term consultant for AFTHR, AF2PH, AF3CO, and AF6PH (human resources economist). | | | Participation in identification and supervision missions for poverty/human resources (demobilization/reintegration) projects in Malawi, Rwanda, Uganda, and Mozambique (forthcoming); design of safety net components and monitoring and evaluation systems; preparations for staff training at ministries and universities for undertaking poverty- and policy-related analysis; preparing a poverty-impact study covering the agriculture, education, and health sectors. | | 01/1993- | Association for Development and Cooperation Austria, Vienna. Assistant to the Director/Project Officer; UN Adviser on secondment to the Ministry of Foreign Affairs. | | | Development of salary scheme, design of internal reporting system, preparation of standard contract agreements, development of controlling instruments for short- to medium-term planning. UN Adviser: Advising Austria's permanent representatives to UNIDO on pertinent issues; preparation of policy papers and statements; participation in meetings, conferences, and negotiations with member states; coordination and cooperation with member states of the European Union; general activities in multilateral development cooperation (negotiations, counselling, coordination). | | 03/1989- | Webster University, Vienna campus. Adjunct Professor in Economics. | | | Teaching graduate and undergraduate courses in economics (development economics, comparative economic systems); advising students on curriculum. | | 10/1990-10/1992 | World Bank, Washington D.C. Economist in the Poverty and Social Policy Division, Africa Technical Department. | | | Coordinator of the macromodelling component of the Cameroon SDA project; coordinator of the SDA Study Funds/Poverty Analysis Components in Malawi and Uganda; organization of courses in "Social |'''

    # gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
    # message = gemini.invoke(prmpt)
    # print(message.content)