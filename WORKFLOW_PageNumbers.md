# Complete Workflow: PageNumbers Version

## 📋 Overview

This workflow processes Azure Document Intelligence JSON files and generates comprehensive reports with page number tracking.

---

## 🔄 Three-Step Process

### **Step 1: Analyze JSON Files** 
**Script**: `Azure_DI_output_parser_WORKING_PageNumbers.py`

**What it does**:
- Reads Azure DI JSON files
- Detects document boundaries (CVs, letters, etc.)
- Analyzes with LLM using Executive Prompt
- Extracts names and classifies sensitive content
- **Includes page numbers for each classification**

**Input**:
```
/Volumes/.../PI/Personal_Information_*.pdf.json
```

**Output**:
```
/Volumes/.../PI/Personal_Information_*_WORKING_PageNumbers_analysis.json
```

**Run**:
```python
python Azure_DI_output_parser_WORKING_PageNumbers.py
```

---

### **Step 2: Convert to Markdown & Word**
**Script**: `convert_PageNumbers_to_reports.py`

**What it does**:
- Converts JSON to human-readable Markdown
- Converts Markdown to Word documents
- Creates organized output folders
- **Displays page numbers prominently in reports**

**Input**:
```
/Volumes/.../PI/Personal_Information_*_WORKING_PageNumbers_analysis.json
```

**Output**:
```
/Volumes/.../PI/markdown_reports_PageNumbers/Personal_Information_*_PageNumbers_report.md
/Volumes/.../PI/word_reports_PageNumbers/Personal_Information_*_PageNumbers_report.docx
```

**Run**:
```python
python convert_PageNumbers_to_reports.py
```

---

## 📂 Directory Structure After All Steps

```
/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/
│
├── Personal_Information_1.pdf.json                                    (original input)
├── Personal_Information_1_WORKING_PageNumbers_analysis.json           (Step 1 output)
│
├── Personal_Information_2.pdf.json
├── Personal_Information_2_WORKING_PageNumbers_analysis.json
│
├── ... (more files)
│
├── markdown_reports_PageNumbers/                                      (Step 2 output)
│   ├── Personal_Information_1_PageNumbers_report.md
│   ├── Personal_Information_2_PageNumbers_report.md
│   └── ...
│
├── word_reports_PageNumbers/                                          (Step 2 output)
│   ├── Personal_Information_1_PageNumbers_report.docx
│   ├── Personal_Information_2_PageNumbers_report.docx
│   └── ...
│
└── Executive_Prompt.md                                                (prompt file)
```

---

## 🎯 Output Formats

### **JSON Output** (Step 1)
```json
{
  "document_path": "...",
  "total_pages": 5,
  "segments": [
    {
      "segment_id": "segment_1",
      "pages": [1, 2, 3],
      "extracted_names": ["John Doe", "Jane Smith"],
      "classifications": [
        {
          "category": "1.1 Personal Information",
          "text": "Salary information...",
          "page_number": 2,
          "bounding_box": [100, 50, 800, 75],
          "confidence_score": 0.98,
          "reason": "Contains salary details"
        }
      ]
    }
  ]
}
```

### **Markdown Output** (Step 2)
```markdown
# Document Analysis Report (with Page Numbers)

## Segment: segment_1
**Pages**: 1-3

### 📋 Extracted Names
- John Doe
- Jane Smith

### 🔍 Sensitive Content Classifications

#### Classification 1
**Category**: `1.1 Personal Information`
**Page**: 2
**Confidence Score**: 0.98

**Content**:
> Salary information...

**Reason**:
> Contains salary details
```

### **Word Output** (Step 2)
Professional Word document with:
- Formatted headers and sections
- Page number references
- Easy-to-read layout
- Editable for stakeholders

---

## ⚙️ Requirements

### **Python Packages**
```bash
pip install python-dotenv
pip install google-genai
pip install pypandoc
```

### **System Requirements**
- **Pandoc**: Required for Word conversion
  - Install: `pip install pypandoc`
  - Or: https://pandoc.org/installing.html

### **Databricks**
- Access to `/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/`
- `itsai` library available
- Vertex AI credentials configured

---

## 🚀 Quick Start

### **Run Everything**

```python
# Step 1: Analyze JSON files
python Azure_DI_output_parser_WORKING_PageNumbers.py

# Step 2: Generate reports
python convert_PageNumbers_to_reports.py
```

### **Check Results**

```python
# View JSON outputs
ls /Volumes/.../PI/*_WORKING_PageNumbers_analysis.json

# View Markdown reports
ls /Volumes/.../PI/markdown_reports_PageNumbers/

# View Word reports
ls /Volumes/.../PI/word_reports_PageNumbers/
```

---

## 📊 What You Get

### **For Each Document**:
1. ✅ **JSON Analysis** - Structured data with page numbers
2. ✅ **Markdown Report** - Human-readable with page references
3. ✅ **Word Document** - Professional format for sharing

### **Key Features**:
- ✅ Page number tracking for all classifications
- ✅ Multi-page CV detection and merging
- ✅ Page ranges for documents spanning multiple pages
- ✅ Name extraction with page context
- ✅ Confidence scores and reasoning
- ✅ Bounding box coordinates
- ✅ Summary statistics

---

## 💡 Tips

### **Processing All Files**
By default, scripts process only the first 5 files for testing.

To process ALL files, edit line 643 in `Azure_DI_output_parser_WORKING_PageNumbers.py`:

**Change**:
```python
json_files = sorted(all_json_files)[:5]  # First 5 only
```

**To**:
```python
json_files = sorted(all_json_files)  # All files
```

### **Caching**
- First file: ~30,000 tokens
- Remaining files: ~100 tokens each
- Significant cost savings with caching!

### **Output Folders**
- Folders are created automatically
- Named with `_PageNumbers` suffix for easy identification
- Organized and ready for distribution

---

## 🎓 Benefits of This Workflow

1. **Traceability**: Every classification linked to its source page
2. **Compliance**: Full audit trail with page references
3. **Efficiency**: Automated conversion to multiple formats
4. **Sharing**: Word documents ready for stakeholders
5. **Analysis**: JSON for programmatic processing
6. **Review**: Markdown for quick human review

---

## 📞 Support

If you encounter issues:
1. Check that all input files exist
2. Verify Vertex AI credentials
3. Ensure pandoc is installed for Word conversion
4. Check output folders have write permissions

---

**Ready to process your documents with full page tracking!** 🚀

