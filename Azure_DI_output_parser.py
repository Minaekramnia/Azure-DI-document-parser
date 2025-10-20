import json
# from itsai.mai import llm
# from itsai import llm_registry

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
    and format content page by page, with document segmentation capabilities.
    """
    def __init__(self, filepath):
        """
        Initializes the processor by loading and parsing the JSON file.
        """
        self.filepath = filepath
        self.analyze_result = None
        self.page_content = {}
        self.page_dimensions = {}
        self.document_segments = {}  # Store detected document segments
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

    def detect_document_boundaries(self):
        """
        Detect where one document ends and another begins within the JSON file.
        Returns a list of page numbers where new documents start.
        """
        if not self.page_content:
            return []
        
        boundaries = [1]  # Always start with page 1
        pages = sorted(self.page_content.keys())
        
        for i in range(1, len(pages)):
            prev_page = pages[i-1]
            curr_page = pages[i]
            
            # Check for document boundary indicators
            if self._is_document_boundary(prev_page, curr_page):
                boundaries.append(curr_page)
                print(f"Document boundary detected at page {curr_page}")
        
        return boundaries

    def _is_document_boundary(self, prev_page, curr_page):
        """
        Enhanced document boundary detection with multiple heuristics.
        """
        boundary_score = 0
        
        # 1. Check for significant page number gap (e.g., page 1, then page 15)
        if curr_page - prev_page > 3:
            boundary_score += 3
            print(f"  -> Large page gap detected: {prev_page} to {curr_page}")
        
        # 2. Check if current page starts with a title (common document start pattern)
        curr_paragraphs = self.page_content[curr_page].get('paragraphs', [])
        if curr_paragraphs and curr_paragraphs[0].get('role') == 'title':
            boundary_score += 2
            print(f"  -> Title detected at page {curr_page}")
        
        # 3. Check for dimension changes (different document types/sources)
        prev_dims = self.page_dimensions.get(prev_page)
        curr_dims = self.page_dimensions.get(curr_page)
        if prev_dims and curr_dims:
            width_diff = abs(prev_dims.get('width', 0) - curr_dims.get('width', 0))
            height_diff = abs(prev_dims.get('height', 0) - curr_dims.get('height', 0))
            
            # If dimensions differ significantly (more than 10%)
            if (width_diff > 0.1 or height_diff > 0.1):
                boundary_score += 2
                print(f"  -> Dimension change detected: {prev_dims} vs {curr_dims}")
        
        # 4. Check for content pattern changes (header/footer changes)
        if self._content_pattern_changed(prev_page, curr_page):
            boundary_score += 1
            print(f"  -> Content pattern change detected at page {curr_page}")
        
        # 5. Check for document type indicators in first paragraph
        if self._has_document_type_indicators(curr_page):
            boundary_score += 1
            print(f"  -> Document type indicators detected at page {curr_page}")
        
        # 6. Check for layout structure changes
        if self._layout_structure_changed(prev_page, curr_page):
            boundary_score += 1
            print(f"  -> Layout structure change detected at page {curr_page}")
        
        # 7. Check for language changes
        if self._language_changed(prev_page, curr_page):
            boundary_score += 2
            print(f"  -> Language change detected at page {curr_page}")
        
        # Return True if boundary score is above threshold
        return boundary_score >= 2

    def _content_pattern_changed(self, prev_page, curr_page):
        """Check if content patterns suggest a document boundary."""
        prev_content = self.page_content.get(prev_page, {})
        curr_content = self.page_content.get(curr_page, {})
        
        # Check if page headers/footers are different
        prev_headers = [p for p in prev_content.get('paragraphs', []) 
                       if p.get('role') in ['pageHeader', 'header']]
        curr_headers = [p for p in curr_content.get('paragraphs', []) 
                       if p.get('role') in ['pageHeader', 'header']]
        
        if prev_headers and curr_headers:
            prev_header_text = prev_headers[0].get('content', '').lower().strip()
            curr_header_text = curr_headers[0].get('content', '').lower().strip()
            
            # If headers are completely different, likely different documents
            if prev_header_text and curr_header_text and prev_header_text != curr_header_text:
                return True
        
        return False

    def segment_documents(self):
        """
        Segment the JSON content into individual documents based on detected boundaries.
        """
        boundaries = self.detect_document_boundaries()
        
        if not boundaries:
            print("No document boundaries detected. Treating entire file as one document.")
            return {1: {'start_page': 1, 'end_page': max(self.page_content.keys()) if self.page_content else 1}}
        
        segments = {}
        for i, start_page in enumerate(boundaries):
            end_page = boundaries[i + 1] - 1 if i + 1 < len(boundaries) else max(self.page_content.keys())
            segment_id = i + 1
            
            segments[segment_id] = {
                'start_page': start_page,
                'end_page': end_page,
                'pages': list(range(start_page, end_page + 1))
            }
            
            print(f"Document Segment {segment_id}: Pages {start_page}-{end_page}")
        
        self.document_segments = segments
        return segments

    def get_document_content(self, segment_id):
        """
        Get the complete content for a specific document segment.
        """
        if segment_id not in self.document_segments:
            raise ValueError(f"Segment {segment_id} not found")
        
        segment = self.document_segments[segment_id]
        document_lines = []
        
        for page_num in sorted(segment['pages']):
            if page_num in self.page_content:
                page_markdown = self._format_page_as_markdown(page_num)
                document_lines.append(page_markdown)
                document_lines.append("\n" + "="*80 + "\n")
        
        return "\n".join(document_lines)

    def classify_document_type(self, segment_id):
        """
        Comprehensive document classification for World Bank archives including
        CVs, letters, articles, professional history, agreements, notes, and WB documents.
        Returns tuple of (document_type, confidence_score)
        """
        if segment_id not in self.document_segments:
            return ("unknown", 0.0)
        
        segment = self.document_segments[segment_id]
        content = self.get_document_content(segment_id)
        
        # Get content analysis
        content_lower = content.lower()
        content_words = content_lower.split()
        word_count = len(content_words)
        
        # Detect language (basic heuristic)
        detected_language = self._detect_language(content)
        
        # World Bank specific documents
        wb_doc_type, wb_confidence = self._classify_worldbank_document_with_confidence(content_lower)
        if wb_doc_type != "unknown":
            return (f"worldbank_{wb_doc_type}", wb_confidence)
        
        # Professional History Statement
        if self._is_professional_history(content_lower, content_words):
            confidence = self._calculate_professional_history_confidence(content_lower, content_words)
            return ("professional_history", confidence)
        
        # Legal/Agreement documents
        if self._is_legal_agreement(content_lower):
            confidence = self._calculate_legal_agreement_confidence(content_lower)
            return ("legal_agreement", confidence)
        
        # CV/Resume indicators (enhanced)
        if self._is_cv_resume(content_lower, word_count):
            confidence = self._calculate_cv_confidence(content_lower, word_count)
            return ("cv", confidence)
        
        # Letter indicators (enhanced for informal letters)
        if self._is_letter(content_lower, word_count):
            confidence = self._calculate_letter_confidence(content_lower, word_count)
            return ("letter", confidence)
        
        # Article indicators (enhanced)
        if self._is_article(content_lower, word_count):
            confidence = self._calculate_article_confidence(content_lower, word_count)
            return ("article", confidence)
        
        # Note/Memo indicators
        if self._is_note_memo(content_lower, word_count):
            confidence = self._calculate_note_confidence(content_lower, word_count)
            return ("note", confidence)
        
        # Report indicators
        if self._is_report(content_lower):
            confidence = self._calculate_report_confidence(content_lower)
            return ("report", confidence)
        
        # Meeting minutes/transcript
        if self._is_meeting_transcript(content_lower):
            confidence = self._calculate_meeting_confidence(content_lower)
            return ("meeting_transcript", confidence)
        
        # Presentation/Slides
        if self._is_presentation(content_lower, word_count):
            confidence = self._calculate_presentation_confidence(content_lower, word_count)
            return ("presentation", confidence)
        
        # Financial Document
        if self._is_financial_document(content_lower):
            confidence = self._calculate_financial_confidence(content_lower)
            return ("financial_document", confidence)
        
        # Technical Specification
        if self._is_technical_specification(content_lower, word_count):
            confidence = self._calculate_technical_confidence(content_lower, word_count)
            return ("technical_specification", confidence)
        
        # Administrative Document
        if self._is_administrative_document(content_lower):
            confidence = self._calculate_administrative_confidence(content_lower)
            return ("administrative_document", confidence)
        
        # Return unknown with low confidence
        return (f"unknown_{detected_language}", 0.1)

    def _detect_language(self, content):
        """Basic language detection based on common words and patterns."""
        content_lower = content.lower()
        
        # English indicators
        english_words = ['the', 'and', 'of', 'to', 'in', 'for', 'is', 'are', 'was', 'were', 'be', 'been']
        english_count = sum(1 for word in english_words if word in content_lower)
        
        # Spanish indicators
        spanish_words = ['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le']
        spanish_count = sum(1 for word in spanish_words if word in content_lower)
        
        # French indicators
        french_words = ['le', 'la', 'de', 'et', 'à', 'un', 'il', 'que', 'ne', 'se', 'ce', 'pas']
        french_count = sum(1 for word in french_words if word in content_lower)
        
        # Portuguese indicators
        portuguese_words = ['o', 'a', 'de', 'e', 'do', 'da', 'em', 'um', 'para', 'com', 'não', 'uma']
        portuguese_count = sum(1 for word in portuguese_words if word in content_lower)
        
        # Arabic indicators (basic)
        arabic_chars = sum(1 for char in content if '\u0600' <= char <= '\u06FF')
        
        if arabic_chars > 10:
            return "arabic"
        elif spanish_count > english_count and spanish_count > french_count:
            return "spanish"
        elif french_count > english_count:
            return "french"
        elif portuguese_count > english_count:
            return "portuguese"
        else:
            return "english"

    def _classify_worldbank_document(self, content_lower):
        """Classify specific World Bank document types."""
        # World Bank project documents
        wb_project_keywords = ['project appraisal document', 'project information document', 
                              'implementation completion report', 'project completion report',
                              'environmental assessment', 'social assessment', 'resettlement plan']
        if any(keyword in content_lower for keyword in wb_project_keywords):
            return "project_document"
        
        # World Bank policy documents
        wb_policy_keywords = ['operational policy', 'bank procedures', 'directive', 
                             'guidelines', 'policy framework', 'safeguard policy']
        if any(keyword in content_lower for keyword in wb_policy_keywords):
            return "policy_document"
        
        # World Bank research/analysis
        wb_research_keywords = ['world development report', 'global economic prospects',
                               'country economic memorandum', 'public expenditure review',
                               'poverty assessment', 'economic sector work']
        if any(keyword in content_lower for keyword in wb_research_keywords):
            return "research_document"
        
        # World Bank correspondence
        wb_correspondence_keywords = ['international bank for reconstruction', 'world bank group',
                                    'executive director', 'country director', 'sector manager']
        if any(keyword in content_lower for keyword in wb_correspondence_keywords):
            return "wb_correspondence"
        
        # World Bank forms/templates
        wb_form_keywords = ['form', 'template', 'checklist', 'questionnaire', 'survey']
        if any(keyword in content_lower for keyword in wb_form_keywords):
            return "wb_form"
        
        return "unknown"

    def _is_professional_history(self, content_lower, content_words):
        """Enhanced professional history detection."""
        history_keywords = ['professional history', 'career history', 'employment history',
                           'work history', 'professional background', 'career summary',
                           'employment record', 'work record', 'professional experience',
                           'career progression', 'work experience', 'employment background',
                           'professional development', 'career timeline', 'work timeline']
        
        # Check for history-specific patterns
        if any(keyword in content_lower for keyword in history_keywords):
            return True
        
        # Enhanced chronological work patterns
        date_patterns = ['19', '20', 'jan', 'feb', 'mar', 'apr', 'may', 'jun',
                        'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'present',
                        'ongoing', 'current', 'since']
        position_keywords = ['manager', 'director', 'analyst', 'consultant', 'advisor',
                           'specialist', 'officer', 'coordinator', 'supervisor',
                           'economist', 'researcher', 'professor', 'lecturer',
                           'coordinator', 'lead', 'senior', 'junior', 'assistant']
        
        # Enhanced date and position detection
        date_count = sum(1 for word in content_words if any(date in word for date in date_patterns))
        position_count = sum(1 for word in content_words if word in position_keywords)
        
        # Check for chronological sequence patterns
        chronological_patterns = ['to', 'until', 'from', 'between', 'during',
                                'worked at', 'employed by', 'served as']
        sequence_count = sum(1 for word in content_words if word in chronological_patterns)
        
        # If document has many dates, positions, and sequence indicators
        if (date_count > 3 and position_count > 2) or (date_count > 2 and sequence_count > 3):
            return True
        
        # Check for education + experience pattern
        education_keywords = ['university', 'college', 'degree', 'phd', 'mba', 'master', 'bachelor']
        education_count = sum(1 for word in content_words if word in education_keywords)
        
        if education_count > 1 and position_count > 2:
            return True
        
        return False

    def _is_legal_agreement(self, content_lower):
        """Detect legal agreements and contracts."""
        legal_keywords = ['agreement', 'contract', 'memorandum of understanding', 'mou',
                         'terms and conditions', 'whereas', 'hereby', 'party', 'parties',
                         'clause', 'section', 'article', 'signature', 'signatory',
                         'effective date', 'termination', 'liability', 'indemnification']
        
        legal_count = sum(1 for keyword in legal_keywords if keyword in content_lower)
        
        # Check for legal document structure
        structure_indicators = ['whereas', 'therefore', 'hereby agrees', 'shall', 'will',
                              'party of the first part', 'party of the second part']
        
        if legal_count > 3 or any(indicator in content_lower for indicator in structure_indicators):
            return True
        
        return False

    def _is_cv_resume(self, content_lower, word_count):
        """Enhanced CV/Resume detection."""
        cv_keywords = ['curriculum vitae', 'cv', 'resume', 'résumé', 'work experience', 
                      'education', 'professional experience', 'skills', 'employment history',
                      'personal information', 'contact information', 'references',
                      'objective', 'summary', 'qualifications', 'achievements']
        
        if any(keyword in content_lower for keyword in cv_keywords):
            return True
        
        # Check for CV structure patterns
        cv_sections = ['education', 'experience', 'skills', 'languages', 'certifications',
                      'publications', 'awards', 'honors', 'activities']
        
        section_count = sum(1 for section in cv_sections if section in content_lower)
        
        # Check for contact info patterns
        contact_patterns = ['email', 'phone', 'address', 'mobile', 'tel', 'fax']
        contact_count = sum(1 for pattern in contact_patterns if pattern in content_lower)
        
        if section_count > 2 or (contact_count > 1 and word_count < 1000):
            return True
        
        return False

    def _is_letter(self, content_lower, word_count):
        """Enhanced letter detection including informal letters."""
        # Formal letter indicators
        formal_letter_keywords = ['dear', 'sincerely', 'yours', 'letter', 'correspondence',
                                 'regarding', 're:', 'subject:', 'to whom it may concern']
        
        # Informal letter indicators
        informal_letter_keywords = ['hi', 'hello', 'thanks', 'thank you', 'best regards',
                                   'kind regards', 'warm regards', 'take care', 'all the best']
        
        # Check for letter structure
        if any(keyword in content_lower for keyword in formal_letter_keywords + informal_letter_keywords):
            return True
        
        # Check for letter-like patterns (short, personal tone)
        if word_count < 500:  # Letters are typically shorter
            personal_pronouns = ['i', 'you', 'we', 'us', 'your', 'our']
            pronoun_count = sum(1 for pronoun in personal_pronouns if pronoun in content_lower)
            
            if pronoun_count > 5:  # High personal pronoun usage suggests letter
                return True
        
        return False

    def _is_article(self, content_lower, word_count):
        """Enhanced article detection."""
        article_keywords = ['abstract', 'introduction', 'conclusion', 'references', 
                           'methodology', 'results', 'discussion', 'literature review',
                           'data analysis', 'findings', 'implications', 'recommendations']
        
        if any(keyword in content_lower for keyword in article_keywords):
            return True
        
        # Academic paper structure
        academic_indicators = ['figure', 'table', 'equation', 'hypothesis', 'research question',
                              'sample size', 'statistical', 'correlation', 'regression']
        
        academic_count = sum(1 for indicator in academic_indicators if indicator in content_lower)
        
        # Long documents with academic indicators
        if word_count > 1000 and academic_count > 2:
            return True
        
        return False

    def _is_note_memo(self, content_lower, word_count):
        """Detect notes, memos, and informal documents."""
        note_keywords = ['note', 'memo', 'memorandum', 'brief', 'summary', 'update',
                        'status update', 'progress report', 'action items', 'follow-up']
        
        if any(keyword in content_lower for keyword in note_keywords):
            return True
        
        # Check for informal document characteristics
        if word_count < 300:  # Short documents
            informal_indicators = ['urgent', 'asap', 'fyi', 'update', 'status', 'next steps']
            if any(indicator in content_lower for indicator in informal_indicators):
                return True
        
        return False

    def _is_report(self, content_lower):
        """Detect various types of reports."""
        report_keywords = ['report', 'analysis', 'assessment', 'evaluation', 'review',
                          'study', 'survey', 'findings', 'recommendations', 'conclusions']
        
        report_count = sum(1 for keyword in report_keywords if keyword in content_lower)
        
        # Check for report structure
        if report_count > 2:
            return True
        
        # Executive summary pattern
        if 'executive summary' in content_lower or 'summary' in content_lower:
            return True
        
        return False

    def _is_meeting_transcript(self, content_lower):
        """Detect meeting minutes and transcripts."""
        meeting_keywords = ['meeting', 'minutes', 'transcript', 'agenda', 'attendees',
                           'participants', 'discussion', 'decision', 'action item',
                           'next meeting', 'chair', 'secretary']
        
        meeting_count = sum(1 for keyword in meeting_keywords if keyword in content_lower)
        
        # Check for transcript patterns
        transcript_patterns = ['speaker:', 'participant:', 'q:', 'a:', 'question:', 'answer:']
        
        if meeting_count > 2 or any(pattern in content_lower for pattern in transcript_patterns):
            return True
        
        return False

    def _is_presentation(self, content_lower, word_count):
        """Detect presentation or slide documents."""
        presentation_keywords = ['slide', 'presentation', 'agenda', 'overview', 'summary',
                               'introduction', 'conclusion', 'next steps', 'key points',
                               'bullet points', 'chart', 'graph', 'figure']
        
        if any(keyword in content_lower for keyword in presentation_keywords):
            return True
        
        # Short documents with bullet-like structure
        if word_count < 500 and ('•' in content_lower or '-' in content_lower):
            return True
        
        return False

    def _is_financial_document(self, content_lower):
        """Detect financial documents."""
        financial_keywords = ['budget', 'expense', 'revenue', 'cost', 'payment', 'invoice',
                            'financial statement', 'balance sheet', 'income statement',
                            'cash flow', 'profit', 'loss', 'assets', 'liabilities',
                            'audit', 'accounting', 'fiscal year', 'quarterly report']
        
        financial_count = sum(1 for keyword in financial_keywords if keyword in content_lower)
        return financial_count > 2

    def _is_technical_specification(self, content_lower, word_count):
        """Detect technical specifications or manuals."""
        technical_keywords = ['specification', 'technical', 'requirements', 'system',
                            'architecture', 'implementation', 'design', 'protocol',
                            'interface', 'api', 'software', 'hardware', 'database',
                            'algorithm', 'framework', 'methodology']
        
        technical_count = sum(1 for keyword in technical_keywords if keyword in content_lower)
        
        # Long documents with technical content
        if technical_count > 3 and word_count > 1000:
            return True
        
        return False

    def _is_administrative_document(self, content_lower):
        """Detect administrative documents."""
        admin_keywords = ['administrative', 'procedure', 'policy', 'guideline',
                         'standard operating procedure', 'sop', 'workflow',
                         'process', 'approval', 'authorization', 'clearance',
                         'compliance', 'regulatory', 'governance']
        
        admin_count = sum(1 for keyword in admin_keywords if keyword in content_lower)
        return admin_count > 2

    def _calculate_presentation_confidence(self, content_lower, word_count):
        """Calculate confidence for presentation classification."""
        presentation_keywords = ['slide', 'presentation', 'agenda', 'overview']
        matches = sum(1 for keyword in presentation_keywords if keyword in content_lower)
        base_confidence = min(0.8, 0.3 + (matches * 0.15))
        
        # Bonus for short documents with bullet points
        if word_count < 500:
            base_confidence += 0.1
        
        return max(0.1, min(0.9, base_confidence))

    def _calculate_financial_confidence(self, content_lower):
        """Calculate confidence for financial document classification."""
        financial_keywords = ['budget', 'expense', 'revenue', 'cost', 'payment', 'invoice']
        matches = sum(1 for keyword in financial_keywords if keyword in content_lower)
        return max(0.1, min(0.9, 0.3 + (matches * 0.1)))

    def _calculate_technical_confidence(self, content_lower, word_count):
        """Calculate confidence for technical specification classification."""
        technical_keywords = ['specification', 'technical', 'requirements', 'system']
        matches = sum(1 for keyword in technical_keywords if keyword in content_lower)
        base_confidence = min(0.8, 0.3 + (matches * 0.1))
        
        # Bonus for long technical documents
        if word_count > 1000:
            base_confidence += 0.1
        
        return max(0.1, min(0.9, base_confidence))

    def _calculate_administrative_confidence(self, content_lower):
        """Calculate confidence for administrative document classification."""
        admin_keywords = ['administrative', 'procedure', 'policy', 'guideline']
        matches = sum(1 for keyword in admin_keywords if keyword in content_lower)
        return max(0.1, min(0.9, 0.3 + (matches * 0.1)))

    def _has_document_type_indicators(self, page_num):
        """Check if page has strong document type indicators."""
        content = self.page_content.get(page_num, {})
        paragraphs = content.get('paragraphs', [])
        
        if not paragraphs:
            return False
        
        # Get first few paragraphs for analysis
        first_paragraphs = paragraphs[:3]
        combined_text = " ".join([p.get('content', '') for p in first_paragraphs]).lower()
        
        # Strong document type indicators
        strong_indicators = [
            'curriculum vitae', 'resume', 'cv', 'personal information',
            'record removal notice', 'confidential', 'memorandum',
            'agreement', 'contract', 'terms and conditions',
            'project appraisal', 'implementation completion',
            'operational policy', 'bank procedures',
            'world development report', 'economic memorandum'
        ]
        
        return any(indicator in combined_text for indicator in strong_indicators)

    def _layout_structure_changed(self, prev_page, curr_page):
        """Check if layout structure significantly changed between pages."""
        prev_content = self.page_content.get(prev_page, {})
        curr_content = self.page_content.get(curr_page, {})
        
        # Compare table counts
        prev_tables = len(prev_content.get('tables', []))
        curr_tables = len(curr_content.get('tables', []))
        
        # Compare paragraph counts
        prev_paragraphs = len(prev_content.get('paragraphs', []))
        curr_paragraphs = len(curr_content.get('paragraphs', []))
        
        # Significant structure change if table/paragraph ratio changes dramatically
        if abs(prev_tables - curr_tables) > 2:
            return True
        
        if prev_paragraphs > 0 and curr_paragraphs > 0:
            ratio_change = abs(prev_paragraphs - curr_paragraphs) / max(prev_paragraphs, curr_paragraphs)
            if ratio_change > 0.5:  # 50% change in paragraph count
                return True
        
        return False

    def _language_changed(self, prev_page, curr_page):
        """Check if language changed between pages."""
        prev_content = self.page_content.get(prev_page, {})
        curr_content = self.page_content.get(curr_page, {})
        
        # Get text from first few paragraphs of each page
        prev_text = " ".join([p.get('content', '') for p in prev_content.get('paragraphs', [])[:2]])
        curr_text = " ".join([p.get('content', '') for p in curr_content.get('paragraphs', [])[:2]])
        
        prev_lang = self._detect_language(prev_text)
        curr_lang = self._detect_language(curr_text)
        
        return prev_lang != curr_lang and prev_lang != 'english' and curr_lang != 'english'

    def _classify_worldbank_document_with_confidence(self, content_lower):
        """Classify World Bank documents with confidence scoring."""
        # World Bank project documents
        wb_project_keywords = ['project appraisal document', 'project information document', 
                              'implementation completion report', 'project completion report',
                              'environmental assessment', 'social assessment', 'resettlement plan']
        project_matches = sum(1 for keyword in wb_project_keywords if keyword in content_lower)
        if project_matches > 0:
            confidence = min(0.9, 0.5 + (project_matches * 0.1))
            return ("project_document", confidence)
        
        # World Bank policy documents
        wb_policy_keywords = ['operational policy', 'bank procedures', 'directive', 
                             'guidelines', 'policy framework', 'safeguard policy']
        policy_matches = sum(1 for keyword in wb_policy_keywords if keyword in content_lower)
        if policy_matches > 0:
            confidence = min(0.9, 0.5 + (policy_matches * 0.1))
            return ("policy_document", confidence)
        
        # World Bank research/analysis
        wb_research_keywords = ['world development report', 'global economic prospects',
                               'country economic memorandum', 'public expenditure review',
                               'poverty assessment', 'economic sector work']
        research_matches = sum(1 for keyword in wb_research_keywords if keyword in content_lower)
        if research_matches > 0:
            confidence = min(0.9, 0.5 + (research_matches * 0.1))
            return ("research_document", confidence)
        
        # World Bank correspondence
        wb_correspondence_keywords = ['international bank for reconstruction', 'world bank group',
                                    'executive director', 'country director', 'sector manager']
        correspondence_matches = sum(1 for keyword in wb_correspondence_keywords if keyword in content_lower)
        if correspondence_matches > 0:
            confidence = min(0.8, 0.4 + (correspondence_matches * 0.1))
            return ("wb_correspondence", confidence)
        
        # World Bank forms/templates
        wb_form_keywords = ['form', 'template', 'checklist', 'questionnaire', 'survey']
        form_matches = sum(1 for keyword in wb_form_keywords if keyword in content_lower)
        if form_matches > 0:
            confidence = min(0.7, 0.3 + (form_matches * 0.1))
            return ("wb_form", confidence)
        
        return ("unknown", 0.0)

    def _calculate_cv_confidence(self, content_lower, word_count):
        """Calculate confidence for CV/Resume classification."""
        cv_keywords = ['curriculum vitae', 'cv', 'resume', 'résumé', 'work experience', 
                      'education', 'professional experience', 'skills', 'employment history']
        keyword_matches = sum(1 for keyword in cv_keywords if keyword in content_lower)
        
        # Base confidence from keywords
        base_confidence = min(0.8, 0.3 + (keyword_matches * 0.1))
        
        # Check for CV structure patterns
        cv_sections = ['education', 'experience', 'skills', 'languages', 'certifications']
        section_matches = sum(1 for section in cv_sections if section in content_lower)
        structure_bonus = min(0.2, section_matches * 0.05)
        
        # Check for contact info patterns
        contact_patterns = ['email', 'phone', 'address', 'mobile', 'tel', 'fax']
        contact_matches = sum(1 for pattern in contact_patterns if pattern in content_lower)
        contact_bonus = min(0.1, contact_matches * 0.02)
        
        # Length penalty for very long documents (unlikely to be CVs)
        length_penalty = 0.0
        if word_count > 2000:
            length_penalty = 0.1
        
        final_confidence = base_confidence + structure_bonus + contact_bonus - length_penalty
        return max(0.1, min(0.95, final_confidence))

    def _calculate_letter_confidence(self, content_lower, word_count):
        """Calculate confidence for letter classification."""
        # Formal letter indicators
        formal_keywords = ['dear', 'sincerely', 'yours', 'letter', 'correspondence']
        formal_matches = sum(1 for keyword in formal_keywords if keyword in content_lower)
        
        # Informal letter indicators
        informal_keywords = ['hi', 'hello', 'thanks', 'thank you', 'best regards']
        informal_matches = sum(1 for keyword in informal_keywords if keyword in content_lower)
        
        total_matches = formal_matches + informal_matches
        
        # Base confidence from greeting/closing patterns
        base_confidence = min(0.7, 0.2 + (total_matches * 0.15))
        
        # Length bonus for short documents (typical of letters)
        length_bonus = 0.0
        if word_count < 500:
            length_bonus = 0.2
        elif word_count < 1000:
            length_bonus = 0.1
        
        # Personal pronoun bonus
        personal_pronouns = ['i', 'you', 'we', 'us', 'your', 'our']
        pronoun_count = sum(1 for pronoun in personal_pronouns if pronoun in content_lower)
        pronoun_bonus = min(0.1, pronoun_count * 0.01)
        
        final_confidence = base_confidence + length_bonus + pronoun_bonus
        return max(0.1, min(0.9, final_confidence))

    def _calculate_professional_history_confidence(self, content_lower, content_words):
        """Calculate confidence for professional history classification."""
        history_keywords = ['professional history', 'career history', 'employment history',
                           'work history', 'professional background', 'career summary']
        keyword_matches = sum(1 for keyword in history_keywords if keyword in content_lower)
        
        # Base confidence from explicit keywords
        base_confidence = min(0.8, 0.4 + (keyword_matches * 0.2))
        
        # Date pattern analysis
        date_patterns = ['19', '20', 'jan', 'feb', 'mar', 'apr', 'may', 'jun',
                        'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        date_count = sum(1 for word in content_words if any(date in word for date in date_patterns))
        date_bonus = min(0.2, date_count * 0.02)
        
        # Position keyword analysis
        position_keywords = ['manager', 'director', 'analyst', 'consultant', 'advisor']
        position_count = sum(1 for word in content_words if word in position_keywords)
        position_bonus = min(0.2, position_count * 0.03)
        
        final_confidence = base_confidence + date_bonus + position_bonus
        return max(0.1, min(0.95, final_confidence))

    # Simplified confidence methods for other document types
    def _calculate_legal_agreement_confidence(self, content_lower):
        """Calculate confidence for legal agreement classification."""
        legal_keywords = ['agreement', 'contract', 'memorandum of understanding', 'mou',
                         'terms and conditions', 'whereas', 'hereby', 'party', 'parties']
        matches = sum(1 for keyword in legal_keywords if keyword in content_lower)
        return max(0.1, min(0.9, 0.3 + (matches * 0.1)))

    def _calculate_article_confidence(self, content_lower, word_count):
        """Calculate confidence for article classification."""
        article_keywords = ['abstract', 'introduction', 'conclusion', 'references', 
                           'methodology', 'results', 'discussion']
        matches = sum(1 for keyword in article_keywords if keyword in content_lower)
        base_confidence = min(0.8, 0.3 + (matches * 0.1))
        
        # Bonus for long documents (typical of articles)
        length_bonus = 0.0
        if word_count > 1000:
            length_bonus = 0.1
        
        return max(0.1, min(0.9, base_confidence + length_bonus))

    def _calculate_note_confidence(self, content_lower, word_count):
        """Calculate confidence for note/memo classification."""
        note_keywords = ['note', 'memo', 'memorandum', 'brief', 'summary', 'update']
        matches = sum(1 for keyword in note_keywords if keyword in content_lower)
        base_confidence = min(0.7, 0.2 + (matches * 0.15))
        
        # Bonus for short documents (typical of notes)
        length_bonus = 0.0
        if word_count < 300:
            length_bonus = 0.2
        
        return max(0.1, min(0.8, base_confidence + length_bonus))

    def _calculate_report_confidence(self, content_lower):
        """Calculate confidence for report classification."""
        report_keywords = ['report', 'analysis', 'assessment', 'evaluation', 'review']
        matches = sum(1 for keyword in report_keywords if keyword in content_lower)
        return max(0.1, min(0.9, 0.3 + (matches * 0.1)))

    def _calculate_meeting_confidence(self, content_lower):
        """Calculate confidence for meeting transcript classification."""
        meeting_keywords = ['meeting', 'minutes', 'transcript', 'agenda', 'attendees']
        matches = sum(1 for keyword in meeting_keywords if keyword in content_lower)
        return max(0.1, min(0.8, 0.3 + (matches * 0.1)))

    def process_with_master_prompt(self, output_filepath=None):
        """
        Process documents using a comprehensive master prompt for all document types.
        This method provides a unified approach to document analysis.
        """
        if not self.analyze_result:
            print("Processing stopped due to loading errors.")
            return

        # First, organize content and detect segments
        self._organize_content_by_page()
        if not self.page_content:
            print("No pages with content were found.")
            return
        
        # Segment documents
        segments = self.segment_documents()
        
        if not segments:
            print("No document segments found.")
            return
        
        # Process each segment with master prompt
        results = {}
        output_file = None
        
        try:
            if output_filepath:
                output_file = open(output_filepath, 'w', encoding='utf-8')
                output_file.write(f"--- Master Prompt Document Analysis for {self.filepath} ---\n")
                output_file.write(f"Found {len(segments)} document segments\n\n")
            
            for segment_id, segment_info in segments.items():
                print(f"\n{'='*60}")
                print(f"Processing Document Segment {segment_id} with Master Prompt")
                print(f"Pages: {segment_info['start_page']}-{segment_info['end_page']}")
                print(f"{'='*60}")
                
                # Get complete document content
                document_content = self.get_document_content(segment_id)
                
                # Process with master prompt
                result = self.process_with_master_prompt_llm(document_content, segment_id)
                results[segment_id] = {
                    'pages': segment_info['pages'],
                    'result': result
                }
                
                # Write to output file
                if output_file:
                    output_file.write(f"\n{'='*80}\n")
                    output_file.write(f"DOCUMENT SEGMENT {segment_id}\n")
                    output_file.write(f"Pages: {segment_info['start_page']}-{segment_info['end_page']}\n")
                    output_file.write(f"{'='*80}\n\n")
                    output_file.write(document_content)
                    output_file.write(f"\n\nMASTER PROMPT ANALYSIS:\n{result}\n")
                
        except IOError as e:
            print(f"Error writing to file {output_filepath}: {e}")
        finally:
            if output_file:
                output_file.close()
                print(f"\n--- Output successfully saved to {output_filepath} ---")
        
        return results

    def process_with_master_prompt_llm(self, document_content, segment_id):
        """
        Process document content with comprehensive master prompt.
        """
        print(f"\n>>> Processing document with Master Prompt (Segment {segment_id})")
        print(f"Content size: {len(document_content)} characters")
        
        # Comprehensive master prompt for all document types
        master_prompt = f"""
INSTRUCTION: Analyze this document comprehensively and provide a detailed classification.

Return a JSON object with the following fields:

1. **document_type**: Primary classification (cv, letter, article, professional_history, legal_agreement, worldbank_project_document, worldbank_policy_document, worldbank_research_document, worldbank_wb_correspondence, worldbank_wb_form, note, report, meeting_transcript, unknown)

2. **confidence**: Confidence score (0.0-1.0) for the classification

3. **reason**: Detailed explanation of why this classification was chosen

4. **language**: Detected language (english, spanish, french, portuguese, arabic, other)

5. **document_characteristics**:
   - length_category: (short/medium/long)
   - has_tables: (true/false)
   - has_headers_footers: (true/false)
   - primary_content_type: (text/tabular/mixed)

6. **key_entities**: Important names, organizations, dates, locations found

7. **document_purpose**: What is this document meant to accomplish?

8. **world_bank_relevance**: If this is a WB document, specify the relevance (high/medium/low/none)

9. **personal_information**: Does this contain personal/confidential information? (true/false)

10. **suggested_actions**: Recommended next steps for processing this document

11. **alternative_classifications**: Other possible document types with confidence scores

12. **content_summary**: Brief summary of the document's main content

DOCUMENT CONTENT:
{document_content}

Please provide a comprehensive analysis focusing on accurate classification and detailed reasoning.
"""
        
        # For now, return a placeholder - you can uncomment the LLM code below
        result = f"PLACEHOLDER: Master prompt analysis for segment {segment_id}\n"
        result += f"Document length: {len(document_content)} characters\n"
        result += f"Would use comprehensive master prompt for detailed analysis"
        
        # Uncomment these lines when you want to use the actual LLM:
        # gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
        # message = gemini.invoke(master_prompt)
        # result = message.content
        
        print(f"Master Prompt Result: {result}")
        return result

    def process_segmented_documents(self, output_filepath=None):
        """
        Process each detected document segment individually with appropriate classification.
        """
        if not self.analyze_result:
            print("Processing stopped due to loading errors.")
            return

        # First, organize content and detect segments
        self._organize_content_by_page()
        if not self.page_content:
            print("No pages with content were found.")
            return
        
        # Segment documents
        segments = self.segment_documents()
        
        if not segments:
            print("No document segments found.")
            return
        
        # Process each segment as a separate document
        results = {}
        output_file = None
        
        try:
            if output_filepath:
                output_file = open(output_filepath, 'w', encoding='utf-8')
                output_file.write(f"--- Document Analysis Output for {self.filepath} ---\n")
                output_file.write(f"Found {len(segments)} document segments\n\n")
            
            for segment_id, segment_info in segments.items():
                print(f"\n{'='*60}")
                print(f"Processing Document Segment {segment_id}")
                print(f"Pages: {segment_info['start_page']}-{segment_info['end_page']}")
                print(f"{'='*60}")
                
                # Get complete document content
                document_content = self.get_document_content(segment_id)
                
                # Classify document type with confidence
                doc_type, confidence = self.classify_document_type(segment_id)
                print(f"Classified as: {doc_type.upper()} (Confidence: {confidence:.2f})")
                
                # Process with appropriate prompt based on document type
                result = self.process_with_llm(document_content, doc_type, segment_id)
                results[segment_id] = {
                    'type': doc_type,
                    'confidence': confidence,
                    'pages': segment_info['pages'],
                    'result': result
                }
                
                # Write to output file
                if output_file:
                    output_file.write(f"\n{'='*80}\n")
                    output_file.write(f"DOCUMENT SEGMENT {segment_id} - TYPE: {doc_type.upper()}\n")
                    output_file.write(f"CONFIDENCE: {confidence:.2f}\n")
                    output_file.write(f"Pages: {segment_info['start_page']}-{segment_info['end_page']}\n")
                    output_file.write(f"{'='*80}\n\n")
                    output_file.write(document_content)
                    output_file.write(f"\n\nLLM ANALYSIS:\n{result}\n")
                
        except IOError as e:
            print(f"Error writing to file {output_filepath}: {e}")
        finally:
            if output_file:
                output_file.close()
                print(f"\n--- Output successfully saved to {output_filepath} ---")
        
        return results

    def process_with_llm(self, document_content, doc_type, segment_id):
        """
        Process document content with LLM using comprehensive type-specific prompts.
        """
        print(f"\n>>> Processing {doc_type.upper()} document (Segment {segment_id})")
        print(f"Content size: {len(document_content)} characters")
        
        # Define comprehensive type-specific prompts
        prompts = {
            # CV/Resume
            'cv': '''Instruction: Analyze this document to determine if it's a CV/Resume. 
            Return a JSON object with: is_resume (true/false), confidence (0-1), 
            reason (explanation), probable_sections (list of detected sections),
            and language (detected language).''',
            
            # Letters (formal and informal)
            'letter': '''Instruction: Analyze this document to determine if it's a letter or correspondence. 
            Return a JSON object with: is_letter (true/false), confidence (0-1), 
            reason (explanation), letter_type (business/personal/formal/informal),
            language (detected language), and sender_recipient_info (if identifiable).''',
            
            # Articles
            'article': '''Instruction: Analyze this document to determine if it's an academic or journal article. 
            Return a JSON object with: is_article (true/false), confidence (0-1), 
            reason (explanation), article_type (research/academic/news/opinion),
            language (detected language), and academic_discipline (if identifiable).''',
            
            # Professional History
            'professional_history': '''Instruction: Analyze this professional history statement. 
            Return a JSON object with: is_professional_history (true/false), confidence (0-1),
            reason (explanation), career_summary (brief summary), key_positions (list),
            language (detected language), and time_span (date range if identifiable).''',
            
            # Legal Agreements
            'legal_agreement': '''Instruction: Analyze this legal document or agreement. 
            Return a JSON object with: is_legal_document (true/false), confidence (0-1),
            reason (explanation), document_type (contract/mou/agreement/etc),
            language (detected language), parties_involved (if identifiable),
            and key_terms (main legal concepts).''',
            
            # World Bank Documents
            'worldbank_project_document': '''Instruction: Analyze this World Bank project document. 
            Return a JSON object with: is_wb_project_doc (true/false), confidence (0-1),
            reason (explanation), project_type (PAD/PID/ICR/etc), language,
            country_region (if identifiable), and project_sector (if identifiable).''',
            
            'worldbank_policy_document': '''Instruction: Analyze this World Bank policy document. 
            Return a JSON object with: is_wb_policy_doc (true/false), confidence (0-1),
            reason (explanation), policy_type (OP/BP/Directive/etc), language,
            and policy_area (safeguards/procurement/etc).''',
            
            'worldbank_research_document': '''Instruction: Analyze this World Bank research document. 
            Return a JSON object with: is_wb_research_doc (true/false), confidence (0-1),
            reason (explanation), research_type (WDR/CEM/PER/etc), language,
            country_focus (if identifiable), and research_topic (main subject).''',
            
            'worldbank_wb_correspondence': '''Instruction: Analyze this World Bank correspondence. 
            Return a JSON object with: is_wb_correspondence (true/false), confidence (0-1),
            reason (explanation), correspondence_type (internal/external), language,
            sender_level (ED/CD/SM/etc), and subject_matter (main topic).''',
            
            'worldbank_wb_form': '''Instruction: Analyze this World Bank form or template. 
            Return a JSON object with: is_wb_form (true/false), confidence (0-1),
            reason (explanation), form_type (checklist/questionnaire/survey/etc),
            language, and purpose (what the form is for).''',
            
            # Notes and Memos
            'note': '''Instruction: Analyze this note or memo. 
            Return a JSON object with: is_note_memo (true/false), confidence (0-1),
            reason (explanation), note_type (brief/summary/update/etc), language,
            urgency_level (urgent/routine/etc), and main_topic (subject matter).''',
            
            # Reports
            'report': '''Instruction: Analyze this report document. 
            Return a JSON object with: is_report (true/false), confidence (0-1),
            reason (explanation), report_type (assessment/evaluation/study/etc),
            language, and report_focus (main subject area).''',
            
            # Meeting Transcripts
            'meeting_transcript': '''Instruction: Analyze this meeting transcript or minutes. 
            Return a JSON object with: is_meeting_transcript (true/false), confidence (0-1),
            reason (explanation), meeting_type (board/staff/project/etc), language,
            participants_count (if identifiable), and main_decisions (key outcomes).''',
            
            # Unknown documents with language detection
            'unknown_english': '''Instruction: Analyze this unknown document in English. 
            Return a JSON object with: document_type (best guess), confidence (0-1),
            reason (explanation), language (confirmed), key_characteristics (main features),
            and suggested_classification (recommended category).''',
            
            'unknown_spanish': '''Instruction: Analyze this unknown document in Spanish. 
            Return a JSON object with: document_type (best guess), confidence (0-1),
            reason (explanation), language (confirmed), key_characteristics (main features),
            and suggested_classification (recommended category).''',
            
            'unknown_french': '''Instruction: Analyze this unknown document in French. 
            Return a JSON object with: document_type (best guess), confidence (0-1),
            reason (explanation), language (confirmed), key_characteristics (main features),
            and suggested_classification (recommended category).''',
            
            'unknown_arabic': '''Instruction: Analyze this unknown document in Arabic. 
            Return a JSON object with: document_type (best guess), confidence (0-1),
            reason (explanation), language (confirmed), key_characteristics (main features),
            and suggested_classification (recommended category).''',
            
            # Default fallback
            'unknown': '''Instruction: Analyze this document and classify its type and content. 
            Return a JSON object with: document_type (best guess), confidence (0-1), 
            reason (explanation), language (detected), key_characteristics (main features),
            and suggested_classification (recommended category).'''
        }
        
        # Get the appropriate prompt for the document type
        prompt = prompts.get(doc_type, prompts['unknown'])
        full_prompt = f"{prompt}\n\nDocument Content:\n{document_content}"
        
        # For now, just return a placeholder - you can uncomment the LLM code below
        result = f"PLACEHOLDER: Would process {doc_type} document with LLM\nPrompt type: {doc_type}"
        
        # Uncomment these lines when you want to use the actual LLM:
        # gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
        # message = gemini.invoke(full_prompt)
        # result = message.content
        
        print(f"LLM Result: {result}")
        return result

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
    json_filename = "Personal_Information_13.pdf.json"
    output_filename = 'segmented_documents_output.txt'
    master_prompt_filename = 'master_prompt_output.txt'
    
    # Process with document segmentation
    processor = AzureLayoutProcessor(json_filename)
    
    print("="*80)
    print("PROCESSING WITH DOCUMENT SEGMENTATION")
    print("="*80)
    
    # Use the segmented processing method
    results = processor.process_segmented_documents(output_filepath=output_filename)
    
    print("\n" + "="*80)
    print("PROCESSING WITH MASTER PROMPT")
    print("="*80)
    
    # Use the master prompt processing method
    master_results = processor.process_with_master_prompt(output_filepath=master_prompt_filename)
    
    # Print comprehensive summary
    print(f"\n{'='*80}")
    print("COMPREHENSIVE DOCUMENT ANALYSIS SUMMARY")
    print(f"{'='*80}")
    
    # Group by document type
    type_counts = {}
    for segment_id, result in results.items():
        doc_type = result['type']
        if doc_type not in type_counts:
            type_counts[doc_type] = []
        type_counts[doc_type].append((segment_id, result))
    
    print(f"Total documents processed: {len(results)}")
    print(f"Document types found: {len(type_counts)}")
    print("\nDetailed breakdown:")
    print("-" * 60)
    
    for doc_type, segments in sorted(type_counts.items()):
        print(f"\n{doc_type.upper().replace('_', ' ')} ({len(segments)} document{'s' if len(segments) > 1 else ''}):")
        for segment_id, result in segments:
            page_range = f"{result['pages'][0]}-{result['pages'][-1]}"
            confidence = result.get('confidence', 0.0)
            print(f"  • Segment {segment_id}: Pages {page_range} (Confidence: {confidence:.2f})")
    
    print(f"\n{'='*80}")
    print("DOCUMENT TYPE LEGEND")
    print(f"{'='*80}")
    print("• CV: Curriculum Vitae/Resume")
    print("• LETTER: Formal or informal correspondence")
    print("• ARTICLE: Academic or journal articles")
    print("• PROFESSIONAL_HISTORY: Professional history statements")
    print("• LEGAL_AGREEMENT: Contracts, MOUs, legal documents")
    print("• WORLDBANK_*: World Bank specific documents")
    print("  - PROJECT_DOCUMENT: PADs, PIDs, ICRs, etc.")
    print("  - POLICY_DOCUMENT: OPs, BPs, Directives, etc.")
    print("  - RESEARCH_DOCUMENT: WDRs, CEMs, PERs, etc.")
    print("  - WB_CORRESPONDENCE: Internal/external WB correspondence")
    print("  - WB_FORM: Forms, templates, checklists")
    print("• NOTE: Notes, memos, briefs, updates")
    print("• REPORT: Various types of reports and assessments")
    print("• MEETING_TRANSCRIPT: Meeting minutes and transcripts")
    print("• UNKNOWN_*: Documents that couldn't be classified (with language)")
    
    # Show confidence analysis
    print(f"\n{'='*80}")
    print("CONFIDENCE ANALYSIS")
    print(f"{'='*80}")
    
    high_confidence = [(seg_id, result) for seg_id, result in results.items() if result.get('confidence', 0) > 0.7]
    medium_confidence = [(seg_id, result) for seg_id, result in results.items() if 0.4 <= result.get('confidence', 0) <= 0.7]
    low_confidence = [(seg_id, result) for seg_id, result in results.items() if result.get('confidence', 0) < 0.4]
    
    print(f"High Confidence (>0.7): {len(high_confidence)} documents")
    for seg_id, result in high_confidence:
        print(f"  • Segment {seg_id}: {result['type']} ({result.get('confidence', 0):.2f})")
    
    print(f"\nMedium Confidence (0.4-0.7): {len(medium_confidence)} documents")
    for seg_id, result in medium_confidence:
        print(f"  • Segment {seg_id}: {result['type']} ({result.get('confidence', 0):.2f})")
    
    print(f"\nLow Confidence (<0.4): {len(low_confidence)} documents")
    for seg_id, result in low_confidence:
        print(f"  • Segment {seg_id}: {result['type']} ({result.get('confidence', 0):.2f})")
    
    print(f"\nOutput saved to: {output_filename}")
    print("\nTo enable LLM processing, uncomment the lines in process_with_llm method")
    print("and ensure you have the proper LLM setup configured.")
    print("\nCONFIDENCE USAGE:")
    print("• High confidence (>0.7): Trust the classification")
    print("• Medium confidence (0.4-0.7): Review classification, may need manual verification")
    print("• Low confidence (<0.4): Requires manual review or additional analysis")