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

class AzureLayoutProcessor:
    def __init__(self, json_filename):
        self.json_filename = json_filename
        self.analyze_result = None
        self.page_content = {}
        self.page_dimensions = {}
        
    def load_json(self):
        """Load the Azure Document Intelligence JSON file."""
        try:
            with open(self.json_filename, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            # Handle nested structure - data might be under 'analyzeResult'
            if 'analyzeResult' in raw_data:
                self.analyze_result = raw_data['analyzeResult']
            else:
                self.analyze_result = raw_data
                
            print(f"Successfully loaded JSON file: {self.json_filename}")
            return True
        except FileNotFoundError:
            print(f"Error: JSON file '{self.json_filename}' not found.")
            return False
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format in '{self.json_filename}': {e}")
            return False
        except Exception as e:
            print(f"Error loading JSON file: {e}")
            return False
    
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

    def process_document(self, output_filepath=None):
        """Process the document and generate formatted output."""
        if not self.load_json():
            return False
        
        self._organize_content_by_page()
        
        if not output_filepath:
            output_filepath = f"{self.json_filename.replace('.json', '')}_analysis_output.txt"
        
        try:
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(f"--- Document Analysis for {self.json_filename} ---\n")
                f.write(f"Found {len(self.page_content)} pages\n\n")
                
                for page_num in sorted(self.page_content.keys()):
                    f.write(f"{'='*80}\n")
                    f.write(f"PAGE {page_num}\n")
                    f.write(f"{'='*80}\n\n")
                    
                    # Write page content
                    page_data = self.page_content[page_num]
                    
                    # Page numbers
                    if page_data['page_numbers']:
                        f.write("## Page Numbers\n\n")
                        for page_num_info in page_data['page_numbers']:
                            f.write(f"**BoundingBox:** {', '.join(map(str, page_num_info['boundingBox']))}\n")
                            f.write(f"> {page_num_info['content']}\n\n")
                        f.write("---\n\n")
                    
                    # Paragraphs
                    if page_data['paragraphs']:
                        f.write("## Paragraphs\n\n")
                        for para in page_data['paragraphs']:
                            f.write(f"**Role:** {para['role']}\n")
                            f.write(f"**BoundingBox:** {', '.join(map(str, para['boundingBox']))}\n")
                            f.write(f"> {para['content']}\n\n")
                            f.write("---\n\n")
                    
                    # Tables
                    if page_data['tables']:
                        f.write("## Tables\n\n")
                        for table in page_data['tables']:
                            f.write(self._format_table(table))
                            f.write("\n---\n\n")
            
            print(f"Document analysis saved to: {output_filepath}")
            return True
            
        except Exception as e:
            print(f"Error writing output file: {e}")
            return False
    
    def _format_table(self, table):
        """Format a table for markdown output."""
        if not table.get('cells'):
            return ""
        
        # Group cells by row
        rows = {}
        for cell in table['cells']:
            row_index = cell.get('rowIndex', 0)
            col_index = cell.get('columnIndex', 0)
            
            if row_index not in rows:
                rows[row_index] = {}
            rows[row_index][col_index] = cell.get('content', '')
        
        # Create markdown table
        markdown_table = []
        for row_idx in sorted(rows.keys()):
            row_data = rows[row_idx]
            max_col = max(row_data.keys()) if row_data else 0
            
            # Create row with all columns
            row_content = []
            for col_idx in range(max_col + 1):
                row_content.append(row_data.get(col_idx, ''))
            
            markdown_table.append('| ' + ' | '.join(row_content) + ' |')
        
        return '\n'.join(markdown_table)
    
    def process_with_vlada_prompt(self, output_filepath=None):
        """Process document using Vlada's master prompt for content classification."""
        if not self.load_json():
            return False
        
        self._organize_content_by_page()
        
        # Vlada's master prompt
        vlada_prompt = '''System Role   You are an Archivist reviewing documents for declassification. Follow the rules and policies below to identify content that should be flagged for restriction.     

Master Prompt    

Please review/search page of the document and identify any content falling under the following categories:     

Access to Information Exceptions (World Bank Access to Information Policy)   
Certain categories of information are restricted from disclosure. These include:   
Personal Information  – personal staff records, HR details (staff appointment, promotion, selection, performance evaluation), Information relating to investigations of allegations of staff misconduct and personal conflicts of interest, information relating to proceedings of the Bank's internal conflict resolution mechanisms, personal medical data.   
Information about the consideration of a person for a post with the name of the person, specific position and title, and any evaluation of person's ability and expertise.    
Information related to promotions, grading of specific positions, and the hiring and selection process if the name of a staff member is included.     
Information on a staff member or consultant/contractor salary, fees, honorarium and/or remuneration.     
Letters of recommendations concerning training, professional affiliation and other professional development activities of Bank staff and external people at the World Bank, if they include the following information: name of the person and specific position/title and any evaluation of person's ability and/or expertise.     
Bank staff UPI numbers or passport numbers including UN Passport or laissez-passer     
Communications of Governors and/or Executive Directors' Offices – Communications within and between individual Governors and/or Executive Directors' offices, communications between individual Governors and/or Executive Directors' offices and the member country or countries they represent, communications between individual Governors and/or Executive Directors' offices and third parties.   
Ethics Committee  – Proceedings or documentation from the Ethics Committee, unless explicitly authorized.    
Attorney–Client Privilege  – communications provided and/or received by the General Counsel, in-house Bank counsel, and other legal advisors.  This includes:   
Written legal opinions, notes, and memoranda of the General Counsel in response to a request for legal advice or assistance by the President, the Board, an Executive Director, or other client of the General Counsel, including such request for legal advice or assistance.    
Spoken legal advice provided by the General Counsel or in-house Bank counsel at meetings of the Board or Board Committees, or legal advice of the General Counsel or in-house Bank counsel that is discussed at meetings of the Board or Board Committees, including the recording or transcription of such in any format or media.    
Written legal notes and legal memoranda of in-house Bank counsel or other legal advisors in response to a request by a client for legal advice or assistance    
Spoken legal advice provided by in-house Bank counsel or other legal advisors at meetings with clients, or legal advice of in-house Bank counsel or other legal advisors that is discussed at meetings between clients, including recordings or transcriptions in any format or media.    
Legal strategy discussions by WB attorneys.    
Legal views/strategies/positions set out by WB attorney.    
Legal staff comments on draft Bank documents.    
Explanation by legal staff of what constitutes a default under Loan Agreements and Bank Guidelines.    
Security and Safety Information  –  Information  whose disclosure would compromise the security of Bank staff and their families, contractors, other individuals, and Bank assets, information about logistical and transport arrangements related to the Bank's shipments of its assets and documents and the shipment of staff's personal effects, information whose disclosure is likely to endanger the life, health, or safety of any individual, or the environment (e.g., travel, logistics, building layouts or blueprints, protective measures).   
Information Restricted Under Separate Disclosure Regimes and Other Investigative Information  –  Information  restricted by IEG, IP, INT, the Bank's Sanctions process, or investigative frameworks. This includes information gathered, received, or generated by INT  in connection with  or related to inquiries, investigations, audits, or any other types of INT reviews, programs, products, or outputs, and any other information gathered, received, or generated by INT on a confidential basis, and information whose disclosure is restricted under the Sanctions Board Statute and the Sanctions Procedures.   
Confidential Third-Party Information  –  Information  shared by member countries, clients, contractors, or third parties in confidence.  Confidentiality is determined by the nature and content of the information in the main body of the record.   
Corporate Administrative Matters  – Information relating to the Bank's corporate administrative matters, including corporate expenses, procurement, facilities, real estate, the pension and other retirement benefit plans of the World Bank Group, which are governed by the Pension Finance Committee and the Pension Benefit Administration Committee, procurement information resulting from Bank  executed  Trust Funds, which are funds that support the Bank's work program and other activities.   
Financial Information  – Banking account and billing information of World Bank entities, member countries, clients, donors, recipients, vendors, or consultants including account number, routing number and SWIFT number.   
CV or Resume Identification   
Flag a document as a CV/resume if it contains two or more of these:   
Personal contact info (name, phone, email, address, LinkedIn)   
Professional summary or objective   
Work history (employers, titles, dates, responsibilities, achievements)   
Education (degrees, institutions, graduation dates)   
Skills (technical, language, soft skills)   
Extras like awards, publications, projects, or certifications   
Structured layout with headings such as  Education, Experience, Skills   
Derogatory/Offensive Language Detection   
Identify and flag any words, phrases, or expressions that are:   
Derogatory, offensive, or profane   
Slurs, insults, hate speech, or crude language   
Targeting individuals or groups based on race, gender, sexuality, religion, nationality, disability, or appearance   
Documents prepared by other WBG entities  such as IFC, MIGA, INT and IMF.     
Documents prepared jointly with partners  – Information prepared jointly by the Bank and other WBG entities such as IFC, MIGA, INT.     
Documents with any security classification marking  including Confidential, Strictly Confidential, Official Use Only, Personal, Private, Secret, For Your Eyes Only, Not for Public Use, Restricted and Deliberative.        
Information related to procurement   of goods and consultant services  under Bank-Financed projects including contracts, bid evaluations, and procurement complaints including  mis -procurement.       

Instructions:   
For each text snippet that matches a category, provide:   
text: the exact text identified   
category: category number (1–9)   
bounding_box : coordinates of the text on the page (format: [x1, y1, x2, y2])   
confidence: confidence score (0–1) indicating how sure you are that this text belongs to the category   
reason: brief explanation of why the text falls under the category (20 tokens)   

If no classified content is found on this page, output:   

Output example:   
{     
 "classified_content": [     
    {     
      "text": "Staff medical record for John Doe",     
      "category": "Disclosure Exception",     
      "subcategory": "Personal Information",     
      "bounding_box": [100, 200, 300, 250],     
      "confidence": 0.95,     
      "reason": "Contains personal medical details of an employee"     
    },     
    {     
      "text": "Work Experience: Software Engineer at XYZ Corp, 2015–2020",     
      "category": "CV/Resume",     
      "subcategory": "Work History",     
      "bounding_box": [50, 400, 500, 450],     
      "confidence": 0.92,     
      "reason": "Chronological listing of past employment history"     
    }     
 ]   
}'''
        
        if not output_filepath:
            output_filepath = f"{self.json_filename.replace('.json', '')}_vlada_analysis.txt"
        
        try:
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(f"--- Vlada Master Prompt Analysis for {self.json_filename} ---\n")
                f.write(f"Analyzing {len(self.page_content)} pages for classified content\n\n")
                
                for page_num in sorted(self.page_content.keys()):
                    f.write(f"{'='*80}\n")
                    f.write(f"PAGE {page_num} ANALYSIS\n")
                    f.write(f"{'='*80}\n\n")
                    
                    # Format page content for LLM analysis
                    page_data = self.page_content[page_num]
                    page_content_formatted = self._format_page_for_llm(page_data, page_num)
                    
                    # Create full prompt with page content
                    full_prompt = f"{vlada_prompt}\n\nDocument Content:\n{page_content_formatted}"
                    
                    f.write("LLM Analysis Results:\n")
                    f.write("-" * 50 + "\n")
                    
                    try:
                        # Save the prompt for manual LLM analysis
                        prompt_filename = f"page_{page_num}_vlada_prompt.txt"
                        with open(prompt_filename, 'w', encoding='utf-8') as pf:
                            pf.write(f"VLADA MASTER PROMPT ANALYSIS - PAGE {page_num}\n")
                            pf.write("="*50 + "\n\n")
                            pf.write(full_prompt)
                        
                        f.write(f"Prompt saved to: {prompt_filename}\n")
                        f.write("To run LLM analysis, uncomment the LLM lines and run:\n")
                        f.write("# gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)\n")
                        f.write("# message = gemini.invoke(full_prompt)\n")
                        f.write("# print(message.content)\n\n")
                        
                        print(f"✓ Prepared prompt for page {page_num} -> {prompt_filename}")
                        
                    except Exception as e:
                        f.write(f"Error preparing LLM prompt: {e}\n\n")
                        print(f"✗ Error preparing page {page_num}: {e}")
            
            print(f"Vlada master prompt analysis saved to: {output_filepath}")
            return True
            
        except Exception as e:
            print(f"Error writing Vlada analysis file: {e}")
            return False
    
    def _format_page_for_llm(self, page_data, page_num):
        """Format page data for LLM analysis with bounding boxes."""
        formatted_content = f"Page {page_num}:\n\n"
        
        # Add paragraphs with bounding boxes
        for para in page_data['paragraphs']:
            bbox = para['boundingBox']
            formatted_content += f"Text: {para['content']}\n"
            formatted_content += f"Role: {para['role']}\n"
            formatted_content += f"Bounding Box: [{bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}]\n\n"
        
        # Add tables
        for table in page_data['tables']:
            formatted_content += "Table:\n"
            formatted_content += self._format_table(table)
            formatted_content += "\n\n"
        
        return formatted_content

if __name__ == '__main__':
    json_filename = "Personal_Information_1.pdf.json"
    processor = AzureLayoutProcessor(json_filename)
    
    print("Processing document with Vlada's Master Prompt...")
    success = processor.process_with_vlada_prompt()
    
    if success:
        print("\n✅ Analysis completed successfully!")
    else:
        print("\n❌ Analysis failed!")
