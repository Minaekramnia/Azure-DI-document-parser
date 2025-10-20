"""
SIMPLE VERSION - Just V2 code with MasterPrompt_V4

This is EXACTLY V2's code (which works) but loads MasterPrompt_V4.md instead of hardcoded prompt.
NO CACHING for now - just get it working first!
"""

import json
import glob
import os
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


class DocumentProcessor:
    """Simple document processor - based on V2."""
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.analyze_result = None
        self.page_content = {}
        self.page_dimensions = {}
        self.document_segments = {}
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
        """Analyze with LLM - EXACTLY like V2."""
        print(f"\n🤖 Running LLM analysis for {segment_id}...")
        
        # V2 approach: Send full prompt + document
        full_prompt = f"{MASTER_PROMPT}\n\nDocument Content to Analyze:\n{document_content}"
        
        try:
            gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
            message = gemini.invoke(full_prompt)
            result = message.content
            print(f"✅ Analysis completed for {segment_id}")
            return result
        except Exception as e:
            print(f"❌ Error: {e}")
            return f"Error: {str(e)}"
    
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
    json_files = glob.glob(f"{data_path}Personal_Information_*.pdf.json")
    
    print("🚀 SIMPLE PROCESSOR")
    print("="*60)
    print(f"Using: MasterPrompt_V4.md")
    print(f"Files: {len(json_files)}")
    print(f"NO CACHING - just get it working first!")
    print("="*60)
    
    for json_file in sorted(json_files):
        print(f"\n{'='*60}")
        print(f"🔍 Processing: {json_file}")
        print(f"{'='*60}")
        
        base_name = os.path.basename(json_file).replace('.pdf.json', '')
        output_filename = f"{data_path}{base_name}_SIMPLE_analysis.txt"
        
        try:
            processor = DocumentProcessor(json_file)
            processor.process_document(output_filepath=output_filename)
            print(f"✅ Done: {output_filename}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n🎯 Complete!")
    print(f"Output files: *_SIMPLE_analysis.txt")


