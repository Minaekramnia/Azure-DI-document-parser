# 📄 JSON to Markdown & Word Converter

## 🎯 **What It Does:**

Converts JSON analysis files to **both Markdown and Word** formats for easy review.

---

## 📋 **Input and Output:**

### **Input:**
**Folder:** `/Volumes/.../PI/`

**Files:**
```
Personal_Information_1_WORKING_analysis.json
Personal_Information_2_WORKING_analysis.json
...
```

### **Output:**
**Folder:** `/Volumes/.../PI/markdown_reports/`

**Files:**
```
Personal_Information_1_WORKING_analysis.md    ← Markdown
Personal_Information_1_WORKING_analysis.docx  ← Word
Personal_Information_2_WORKING_analysis.md
Personal_Information_2_WORKING_analysis.docx
...
```

---

## 📂 **Folder Structure:**

```
PI/
├── Personal_Information_1.pdf.json
├── Personal_Information_1_WORKING_analysis.json
├── Personal_Information_2.pdf.json
├── Personal_Information_2_WORKING_analysis.json
└── markdown_reports/                    ← NEW FOLDER
    ├── Personal_Information_1_WORKING_analysis.md
    ├── Personal_Information_1_WORKING_analysis.docx
    ├── Personal_Information_2_WORKING_analysis.md
    ├── Personal_Information_2_WORKING_analysis.docx
    └── ...
```

---

## 🚀 **How to Run:**

### **Step 1: Install python-docx**
On Databricks, run:
```bash
%pip install python-docx
```

### **Step 2: Upload**
Upload `convert_json_to_markdown.py` to Databricks

### **Step 3: Run**
```python
python convert_json_to_markdown.py
```

---

## 📊 **Console Output:**

```
============================================================
🚀 JSON TO MARKDOWN & WORD CONVERTER
============================================================
Source: /Volumes/.../PI/
Looking for: *_WORKING_analysis.json
Output: *_WORKING_analysis.md + *_WORKING_analysis.docx
============================================================

✅ Output folder created: /Volumes/.../PI/markdown_reports

🔄 JSON to Markdown Converter
============================================================
Input: /Volumes/.../PI/
Output: /Volumes/.../PI/markdown_reports/
Found 16 JSON files to convert
============================================================

📄 Converting: Personal_Information_1_WORKING_analysis.json
   ✅ Created Markdown: Personal_Information_1_WORKING_analysis.md
   ✅ Created Word: Personal_Information_1_WORKING_analysis.docx

📄 Converting: Personal_Information_2_WORKING_analysis.json
   ✅ Created Markdown: Personal_Information_2_WORKING_analysis.md
   ✅ Created Word: Personal_Information_2_WORKING_analysis.docx

...

============================================================
🎯 Conversion Complete!
============================================================
✅ Successfully converted: 16 files

📁 Output folder: /Volumes/.../PI/markdown_reports/
📄 Markdown files: *_WORKING_analysis.md
📄 Word files: *_WORKING_analysis.docx
============================================================

✅ All JSON files converted to Markdown and Word!
   📄 Markdown files (.md) - For GitHub/Databricks viewing
   📄 Word files (.docx) - For sharing/editing in Microsoft Word
```

---

## 📄 **Word Document Features:**

### **Formatting:**
- ✅ **Headings** - Hierarchical structure (H1, H2, H3)
- ✅ **Bullet lists** - For names and items
- ✅ **Bold text** - For emphasis
- ✅ **Colors** - Gray text for classified content
- ✅ **Page breaks** - Between major sections

### **Content:**
- ✅ **Title page** - Document name and metadata
- ✅ **Summary** - Overview with counts
- ✅ **All names** - Alphabetically sorted list
- ✅ **Each segment** - With names and classifications
- ✅ **Each classification** - Category, text, confidence, reason, bounding box

### **Professional:**
- ✅ Ready to share with stakeholders
- ✅ Can be edited in Microsoft Word
- ✅ Can be converted to PDF
- ✅ Can be printed

---

## 🎯 **Summary:**

**Script:** `convert_json_to_markdown.py`  
**Input:** `*_WORKING_analysis.json` (in PI folder)  
**Output:** `*_WORKING_analysis.md` + `*_WORKING_analysis.docx` (in markdown_reports folder)  
**Requires:** `python-docx` library  

**Creates both Markdown and Word formats for maximum flexibility!** ✨


