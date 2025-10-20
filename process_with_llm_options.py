import json
import os
from typing import Optional

# LLM Import Options - Uncomment the one you want to use:

# Option 1: OpenAI
# from openai import OpenAI

# Option 2: Google Gemini (Direct API)
# import google.generativeai as genai

# Option 3: Anthropic Claude
# import anthropic

# Option 4: Hugging Face (Free, local)
# from transformers import pipeline

class LLMAnalyzer:
    def __init__(self, provider="openai"):
        self.provider = provider
        self.setup_llm()
    
    def setup_llm(self):
        """Setup the chosen LLM provider."""
        if self.provider == "openai":
            try:
                self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                self.model = "gpt-4"
                print("✓ OpenAI GPT-4 initialized")
            except:
                print("❌ OpenAI not available. Set OPENAI_API_KEY environment variable.")
                self.client = None
        
        elif self.provider == "gemini":
            try:
                genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                self.model = genai.GenerativeModel('gemini-pro')
                print("✓ Google Gemini initialized")
            except:
                print("❌ Google Gemini not available. Set GOOGLE_API_KEY environment variable.")
                self.model = None
        
        elif self.provider == "claude":
            try:
                self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                self.model = "claude-3-sonnet-20240229"
                print("✓ Anthropic Claude initialized")
            except:
                print("❌ Anthropic Claude not available. Set ANTHROPIC_API_KEY environment variable.")
                self.client = None
        
        elif self.provider == "huggingface":
            try:
                self.classifier = pipeline("text-classification", 
                                         model="microsoft/DialoGPT-medium")
                print("✓ Hugging Face model initialized")
            except:
                print("❌ Hugging Face not available.")
                self.classifier = None
    
    def analyze(self, prompt: str) -> str:
        """Analyze text using the configured LLM."""
        if self.provider == "openai" and self.client:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=2000
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"OpenAI Error: {e}"
        
        elif self.provider == "gemini" and self.model:
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                return f"Gemini Error: {e}"
        
        elif self.provider == "claude" and self.client:
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            except Exception as e:
                return f"Claude Error: {e}"
        
        elif self.provider == "huggingface" and self.classifier:
            try:
                # For HF, we'll do a simple classification
                result = self.classifier(prompt[:512])  # Limit text length
                return f"Hugging Face Classification: {result}"
            except Exception as e:
                return f"Hugging Face Error: {e}"
        
        return "No LLM provider available"

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

    def process_with_llm(self, llm_provider="openai", output_filepath=None):
        """Process document using specified LLM provider with Vlada's master prompt."""
        if not self.load_json():
            return False
        
        self._organize_content_by_page()
        
        # Initialize LLM
        llm = LLMAnalyzer(provider=llm_provider)
        
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
            output_filepath = f"{self.json_filename.replace('.json', '')}_llm_analysis_{llm_provider}.txt"
        
        try:
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(f"--- LLM Analysis ({llm_provider.upper()}) for {self.json_filename} ---\n")
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
                        # Run LLM analysis
                        result = llm.analyze(full_prompt)
                        f.write(result)
                        f.write("\n\n")
                        
                        print(f"✓ Analyzed page {page_num} with {llm_provider}")
                        
                    except Exception as e:
                        f.write(f"Error running LLM analysis: {e}\n\n")
                        print(f"✗ Error analyzing page {page_num}: {e}")
            
            print(f"LLM analysis saved to: {output_filepath}")
            return True
            
        except Exception as e:
            print(f"Error writing LLM analysis file: {e}")
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

if __name__ == '__main__':
    json_filename = "Personal_Information_1.pdf.json"
    
    # Choose your LLM provider: "openai", "gemini", "claude", or "huggingface"
    llm_provider = "openai"  # Change this to your preferred provider
    
    processor = AzureLayoutProcessor(json_filename)
    
    print(f"Processing document with {llm_provider.upper()}...")
    print("Available providers: openai, gemini, claude, huggingface")
    print("Make sure to set the appropriate API key environment variable!")
    
    success = processor.process_with_llm(llm_provider=llm_provider)
    
    if success:
        print("\n✅ Analysis completed successfully!")
    else:
        print("\n❌ Analysis failed!")


