# Changes Made: Added Page Number Tracking to Classifications

## Summary
Modified `Azure_DI_output_parser_WORKING.py` to include the original page number for each classification in the output JSON.

## Changes Made

### 1. Updated `_get_segment_content()` method (Line 396-415)
- **Before**: Returned only content string
- **After**: Returns both content string AND the list of pages
- This allows downstream functions to know which pages are in the segment

### 2. Updated LLM Format Instructions (Line 417-455)
- **Added** `"page_number": X` field to the expected JSON structure
- **Added** instruction: "IMPORTANT: Include a 'page_number' field in each classification to indicate which page the content was found on."
- This tells the LLM to include page numbers in its response

### 3. Updated `analyze_with_llm()` signature (Line 417)
- **Before**: `def analyze_with_llm(self, document_content, segment_id)`
- **After**: `def analyze_with_llm(self, document_content, segment_id, segment_pages)`
- Now receives the list of pages for the segment

### 4. Updated `process_document()` method (Line 549-550)
- **Before**: `segment_content = self._get_segment_content(pages)`
- **After**: `segment_content, segment_pages = self._get_segment_content(pages)`
- **Before**: `llm_result = self.analyze_with_llm(segment_content, segment_id)`
- **After**: `llm_result = self.analyze_with_llm(segment_content, segment_id, segment_pages)`

### 5. Enhanced CV Merging Logic (Line 578-597)
- **Added** `"page_number": min(pages)` to merged CV classification (first page)
- **Added** `"page_range": f"{min(pages)}-{max(pages)}"` to show full CV page range
- **Added** fallback logic: If LLM doesn't provide page_number, use first page of segment

## Output Format

### Before
```json
{
  "category": "1.1 Personal Information",
  "text": "John Doe's salary is $100,000",
  "bounding_box": [100, 50, 800, 75],
  "confidence_score": 0.98,
  "reason": "Contains salary information"
}
```

### After
```json
{
  "category": "1.1 Personal Information",
  "text": "John Doe's salary is $100,000",
  "bounding_box": [100, 50, 800, 75],
  "page_number": 3,
  "confidence_score": 0.98,
  "reason": "Contains salary information"
}
```

### For Multi-Page CVs
```json
{
  "category": "2.1 CV or Resume Content",
  "text": "Complete CV/Resume spanning pages 2-5...",
  "bounding_box": [0, 0, 10, 12],
  "page_number": 2,
  "page_range": "2-5",
  "confidence_score": 0.99,
  "reason": "Document is a complete CV/Resume spanning 4 pages..."
}
```

## Benefits

1. ✅ **Traceability**: Can now trace each classification back to its source page
2. ✅ **Better Reporting**: Easier to generate page-specific reports
3. ✅ **Audit Trail**: Clear documentation of where sensitive content was found
4. ✅ **CV Handling**: Multi-page CVs show both starting page and full page range
5. ✅ **Fallback Safety**: If LLM forgets to include page_number, code adds it automatically

## Testing

Run the script as normal:
```python
python Azure_DI_output_parser_WORKING.py
```

Check the output JSON files (`*_WORKING_analysis.json`) - each classification should now have a `page_number` field.

## Next Steps

1. Upload the modified script to Databricks
2. Run on your test files
3. Verify that `page_number` appears in all classifications
4. Update the Markdown and Word converters if you want to display page numbers in the reports

