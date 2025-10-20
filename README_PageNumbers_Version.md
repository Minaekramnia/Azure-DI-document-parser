# Azure DI Output Parser - Page Numbers Version

## 📁 File: `Azure_DI_output_parser_WORKING_PageNumbers.py`

### ✨ What's New?

This version includes **page number tracking** for all classifications!

### 🎯 Key Features

1. **Page Number Field**: Every classification now includes `page_number` to show which page the content was found on
2. **Page Range for CVs**: Multi-page CVs include both `page_number` (starting page) and `page_range` (e.g., "2-5")
3. **Automatic Fallback**: If the LLM forgets to include page numbers, the code adds them automatically
4. **Same Functionality**: All other features from the WORKING version remain unchanged

### 📊 Output Format

#### Single Classification
```json
{
  "category": "1.1 Personal Information",
  "text": "John Doe's salary is $100,000",
  "bounding_box": [100, 50, 800, 75],
  "page_number": 3,  ← NEW!
  "confidence_score": 0.98,
  "reason": "Contains salary information"
}
```

#### Multi-Page CV
```json
{
  "category": "2.1 CV or Resume Content",
  "text": "Complete CV/Resume spanning pages 2-5...",
  "bounding_box": [0, 0, 10, 12],
  "page_number": 2,        ← Starting page
  "page_range": "2-5",     ← Full range
  "confidence_score": 0.99,
  "reason": "Document is a complete CV/Resume spanning 4 pages..."
}
```

### 📝 Output Files

The script generates files named:
```
Personal_Information_1_WORKING_PageNumbers_analysis.json
Personal_Information_2_WORKING_PageNumbers_analysis.json
...
```

### 🚀 Usage

Same as the original WORKING version:

```python
python Azure_DI_output_parser_WORKING_PageNumbers.py
```

### 📋 Files Available

- **`Azure_DI_output_parser_WORKING.py`** - Original version (no page numbers)
- **`Azure_DI_output_parser_WORKING_PageNumbers.py`** - NEW version with page numbers ✨

### 💡 When to Use Which Version?

- **Use PageNumbers version** if you need to:
  - Track which page sensitive content appears on
  - Generate page-specific reports
  - Create audit trails with page references
  - Build page-indexed search functionality

- **Use original WORKING version** if you:
  - Don't need page tracking
  - Want slightly smaller output files
  - Have existing tools that expect the old format

### 🔄 Differences from Original

| Feature | WORKING | WORKING_PageNumbers |
|---------|---------|---------------------|
| extracted_names | ✅ | ✅ |
| classifications | ✅ | ✅ |
| page_number field | ❌ | ✅ |
| page_range for CVs | ❌ | ✅ |
| Output filename | `*_WORKING_analysis.json` | `*_WORKING_PageNumbers_analysis.json` |

### 📦 What's Included

Both versions include:
- ✅ Executive Prompt format validation
- ✅ Prompt caching for cost savings
- ✅ Multi-page CV detection and merging
- ✅ Page number sequence detection (1/4, 2/4, etc.)
- ✅ Document boundary detection (3 rules)
- ✅ Bounding box information
- ✅ Confidence scores
- ✅ Classification reasons

### 🎓 Benefits of Page Numbers

1. **Traceability**: Know exactly where sensitive content was found
2. **Compliance**: Better audit trails for regulatory requirements
3. **Efficiency**: Quickly locate content in original documents
4. **Reporting**: Generate page-specific summaries and statistics
5. **Validation**: Easier to verify LLM classifications against source

---

**Recommendation**: Use the **PageNumbers version** for production - the extra metadata is valuable for auditing and reporting! 🚀

