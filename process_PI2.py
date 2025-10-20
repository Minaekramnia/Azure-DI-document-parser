import json
from itsai.mai import llm
from itsai import llm_registry

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
    """
    Processes an Azure Document Intelligence Layout JSON file to extract
    and format content page by page.
    """
    def __init__(self, filepath):
        """
        Initializes the processor by loading and parsing the JSON file.
        """
        self.filepath = filepath
        self.analyze_result = None
        self.page_content = {}
        self.page_dimensions = {}
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
        
        output_file = None
        try:
            if output_filepath:
                output_file = open(output_filepath, 'w', encoding='utf-8')
                output_file.write(f"--- Document Analysis Output for {self.filepath} ---\n\n")

            previous_dimensions = None
            for page_num in sorted(self.page_content.keys()):
                # Check for dimension changes
                current_dimensions = self.page_dimensions.get(page_num)
                if previous_dimensions and current_dimensions and (
                    current_dimensions['width'] != previous_dimensions['width'] or
                    current_dimensions['height'] != previous_dimensions['height']
                ):
                    print(f"WARNING: Page {page_num} dimensions ({current_dimensions['width']}x{current_dimensions['height']}) "
                          f"differ from previous page ({previous_dimensions['width']}x{previous_dimensions['height']}).\n")
                previous_dimensions = current_dimensions

                # Check if page starts with a title
                paragraphs = self.page_content[page_num].get('paragraphs', [])
                if paragraphs and paragraphs[0].get('role') == 'title':
                    print(f"INFO: Page {page_num} starts with a title.\n")

                # Format and process content
                markdown_output = self._format_page_as_markdown(page_num)
                print(markdown_output)
                
                if output_file:
                    output_file.write(markdown_output)
                    output_file.write("\n" + "="*80 + "\n\n")

                check_content(markdown_output, page_num)

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
    json_filename = "Personal_Information_2.pdf.json"
    output_filename = 'Personal_Information_2_analysis_output.txt'
    processor = AzureLayoutProcessor(json_filename)
    processor.process_document(output_filepath=output_filename)
    # Get the document content for CV analysis
    print("\n" + "="*80)
    print("CV/RESUME CLASSIFICATION ANALYSIS")
    print("="*80)
    
    # Read the output file to get the formatted content
    try:
        with open(output_filename, 'r', encoding='utf-8') as f:
            document_content = f.read()
        
        # Create the CV classification prompt with the actual document content
        cv_analysis_prompt = f'''Instruction: Determine whether the following document is a resume/CV. The document is provided in Markdown format, and each text block 
    includes metadata: role (e.g., header, footer, paragraph) and bounding box coordinates (x0, y0, x1, y1). Use both content and layout information to make your decision. 
        Return a JSON object with the following fields: 
        - is_resume: true/false 
        - confidence: number between 0 and 1 
        - reason: short explanation (1-2 sentences) 
        - probable_sections: list of any detected resume sections bounding box (e.g., ["Header", "Work Experience", "Education", "Skills"]) 
        
        Markdown Document: 
        {document_content}'''
        
        print("CV Classification Prompt Created:")
        print("-" * 50)
        print(cv_analysis_prompt[:500] + "..." if len(cv_analysis_prompt) > 500 else cv_analysis_prompt)
        print("-" * 50)
        
        # Save the prompt to a file for analysis
        prompt_filename = 'Personal_Information_2_CV_analysis_prompt.txt'
        with open(prompt_filename, 'w', encoding='utf-8') as f:
            f.write("CV/RESUME CLASSIFICATION PROMPT\n")
            f.write("="*50 + "\n\n")
            f.write(cv_analysis_prompt)
        
        print(f"\nCV analysis prompt saved to: {prompt_filename}")
        
        # Run LLM analysis
        print("Running LLM analysis...")
        gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
        message = gemini.invoke(cv_analysis_prompt)
        
        print("\n" + "="*80)
        print("LLM ANALYSIS RESULTS")
        print("="*80)
        print(message.content)
        
        # Save LLM results to file
        llm_results_filename = 'Personal_Information_2_LLM_analysis_results.txt'
        with open(llm_results_filename, 'w', encoding='utf-8') as f:
            f.write("LLM ANALYSIS RESULTS\n")
            f.write("="*50 + "\n\n")
            f.write(message.content)
        
        print(f"\nLLM analysis results saved to: {llm_results_filename}")
        
    except FileNotFoundError:
        print(f"Error: Could not read output file {output_filename}")
    except Exception as e:
        print(f"Error processing document for CV analysis: {e}")

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

        

        output_file = None

        try:

            if output_filepath:

                output_file = open(output_filepath, 'w', encoding='utf-8')

                output_file.write(f"--- Document Analysis Output for {self.filepath} ---\n\n")



            previous_dimensions = None

            for page_num in sorted(self.page_content.keys()):

                # Check for dimension changes

                current_dimensions = self.page_dimensions.get(page_num)

                if previous_dimensions and current_dimensions and (

                    current_dimensions['width'] != previous_dimensions['width'] or

                    current_dimensions['height'] != previous_dimensions['height']

                ):

                    print(f"WARNING: Page {page_num} dimensions ({current_dimensions['width']}x{current_dimensions['height']}) "

                          f"differ from previous page ({previous_dimensions['width']}x{previous_dimensions['height']}).\n")

                previous_dimensions = current_dimensions



                # Check if page starts with a title

                paragraphs = self.page_content[page_num].get('paragraphs', [])

                if paragraphs and paragraphs[0].get('role') == 'title':

                    print(f"INFO: Page {page_num} starts with a title.\n")



                # Format and process content

                markdown_output = self._format_page_as_markdown(page_num)

                print(markdown_output)

                

                if output_file:

                    output_file.write(markdown_output)

                    output_file.write("\n" + "="*80 + "\n\n")



                check_content(markdown_output, page_num)



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

    json_filename = "Personal_Information_2.pdf.json"
    output_filename = 'Personal_Information_2_analysis_output.txt'
    processor = AzureLayoutProcessor(json_filename)

    processor.process_document(output_filepath=output_filename)

    # Get the document content for CV analysis
    print("\n" + "="*80)
    print("CV/RESUME CLASSIFICATION ANALYSIS")
    print("="*80)
    
    # Read the output file to get the formatted content
    try:
        with open(output_filename, 'r', encoding='utf-8') as f:
            document_content = f.read()
        
        # Create the CV classification prompt with the actual document content
        cv_analysis_prompt = f'''Instruction: Determine whether the following document is a resume/CV. The document is provided in Markdown format, and each text block 
    includes metadata: role (e.g., header, footer, paragraph) and bounding box coordinates (x0, y0, x1, y1). Use both content and layout information to make your decision. 

        Return a JSON object with the following fields: 
        - is_resume: true/false 
        - confidence: number between 0 and 1 
        - reason: short explanation (1-2 sentences) 
        - probable_sections: list of any detected resume sections bounding box (e.g., ["Header", "Work Experience", "Education", "Skills"]) 
        
        Markdown Document: 
        {document_content}'''
        
        print("CV Classification Prompt Created:")
        print("-" * 50)
        print(cv_analysis_prompt[:500] + "..." if len(cv_analysis_prompt) > 500 else cv_analysis_prompt)
        print("-" * 50)
        
        # Save the prompt to a file for analysis
        prompt_filename = 'Personal_Information_2_CV_analysis_prompt.txt'
        with open(prompt_filename, 'w', encoding='utf-8') as f:
            f.write("CV/RESUME CLASSIFICATION PROMPT\n")
            f.write("="*50 + "\n\n")
            f.write(cv_analysis_prompt)
        
        print(f"\nCV analysis prompt saved to: {prompt_filename}")
        print("To run with LLM, uncomment the lines below:")
        print("# gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)")
        print("# message = gemini.invoke(cv_analysis_prompt)")
        print("# print(message.content)")
        
    except FileNotFoundError:
        print(f"Error: Could not read output file {output_filename}")
    except Exception as e:
        print(f"Error processing document for CV analysis: {e}")

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

        

        output_file = None

        try:

            if output_filepath:

                output_file = open(output_filepath, 'w', encoding='utf-8')

                output_file.write(f"--- Document Analysis Output for {self.filepath} ---\n\n")



            previous_dimensions = None

            for page_num in sorted(self.page_content.keys()):

                # Check for dimension changes

                current_dimensions = self.page_dimensions.get(page_num)

                if previous_dimensions and current_dimensions and (

                    current_dimensions['width'] != previous_dimensions['width'] or

                    current_dimensions['height'] != previous_dimensions['height']

                ):

                    print(f"WARNING: Page {page_num} dimensions ({current_dimensions['width']}x{current_dimensions['height']}) "

                          f"differ from previous page ({previous_dimensions['width']}x{previous_dimensions['height']}).\n")

                previous_dimensions = current_dimensions



                # Check if page starts with a title

                paragraphs = self.page_content[page_num].get('paragraphs', [])

                if paragraphs and paragraphs[0].get('role') == 'title':

                    print(f"INFO: Page {page_num} starts with a title.\n")



                # Format and process content

                markdown_output = self._format_page_as_markdown(page_num)

                print(markdown_output)

                

                if output_file:

                    output_file.write(markdown_output)

                    output_file.write("\n" + "="*80 + "\n\n")



                check_content(markdown_output, page_num)



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

    json_filename = "Personal_Information_2.pdf.json"
    output_filename = 'Personal_Information_2_analysis_output.txt'
    processor = AzureLayoutProcessor(json_filename)

    processor.process_document(output_filepath=output_filename)

    # Get the document content for CV analysis
    print("\n" + "="*80)
    print("CV/RESUME CLASSIFICATION ANALYSIS")
    print("="*80)
    
    # Read the output file to get the formatted content
    try:
        with open(output_filename, 'r', encoding='utf-8') as f:
            document_content = f.read()
        
        # Create the CV classification prompt with the actual document content
        cv_analysis_prompt = f'''Instruction: Determine whether the following document is a resume/CV. The document is provided in Markdown format, and each text block 
    includes metadata: role (e.g., header, footer, paragraph) and bounding box coordinates (x0, y0, x1, y1). Use both content and layout information to make your decision. 

        Return a JSON object with the following fields: 
        - is_resume: true/false 
        - confidence: number between 0 and 1 
        - reason: short explanation (1-2 sentences) 
        - probable_sections: list of any detected resume sections bounding box (e.g., ["Header", "Work Experience", "Education", "Skills"]) 
        
        Markdown Document: 
        {document_content}'''
        
        print("CV Classification Prompt Created:")
        print("-" * 50)
        print(cv_analysis_prompt[:500] + "..." if len(cv_analysis_prompt) > 500 else cv_analysis_prompt)
        print("-" * 50)
        
        # Save the prompt to a file for analysis
        prompt_filename = 'Personal_Information_2_CV_analysis_prompt.txt'
        with open(prompt_filename, 'w', encoding='utf-8') as f:
            f.write("CV/RESUME CLASSIFICATION PROMPT\n")
            f.write("="*50 + "\n\n")
            f.write(cv_analysis_prompt)
        
        print(f"\nCV analysis prompt saved to: {prompt_filename}")
        print("To run with LLM, uncomment the lines below:")
        print("# gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)")
        print("# message = gemini.invoke(cv_analysis_prompt)")
        print("# print(message.content)")
        
    except FileNotFoundError:
        print(f"Error: Could not read output file {output_filename}")
    except Exception as e:
        print(f"Error processing document for CV analysis: {e}")