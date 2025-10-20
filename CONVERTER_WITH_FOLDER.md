# ✅ UPDATED: Markdown Converter with Output Folder

## 📁 **Input and Output:**

### **Input:**
**Location:** `/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/`

**Files:**
```
Personal_Information_1_WORKING_analysis.json
Personal_Information_2_WORKING_analysis.json
Personal_Information_3_WORKING_analysis.json
...
```

### **Output:**
**Location:** `/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/markdown_reports/`

**Files:**
```
Personal_Information_1_WORKING_analysis.md
Personal_Information_2_WORKING_analysis.md
Personal_Information_3_WORKING_analysis.md
...
```

---

## 📂 **Folder Structure:**

```
/Volumes/.../PI/
├── Personal_Information_1.pdf.json              (original)
├── Personal_Information_1_WORKING_analysis.json (JSON output)
├── Personal_Information_2.pdf.json
├── Personal_Information_2_WORKING_analysis.json
├── ...
└── markdown_reports/                            (NEW FOLDER)
    ├── Personal_Information_1_WORKING_analysis.md
    ├── Personal_Information_2_WORKING_analysis.md
    ├── Personal_Information_3_WORKING_analysis.md
    └── ...
```

---

## 🚀 **How to Run:**

### **Step 1: Upload**
Upload `convert_json_to_markdown.py` to Databricks

### **Step 2: Run**
```python
python convert_json_to_markdown.py
```

### **Step 3: Check Output**
Navigate to:
```
/Volumes/.../PI/markdown_reports/
```

---

## 📊 **Console Output:**

```
============================================================
🚀 JSON TO MARKDOWN CONVERTER
============================================================
Source: /Volumes/.../PI/
Looking for: *_WORKING_analysis.json
Output: *_WORKING_analysis.md
============================================================

✅ Output folder created: /Volumes/.../PI/markdown_reports

🔄 JSON to Markdown Converter
============================================================
Input: /Volumes/.../PI/
Output: /Volumes/.../PI/markdown_reports/
Found 16 JSON files to convert
============================================================

📄 Converting: Personal_Information_1_WORKING_analysis.json
   ✅ Created: Personal_Information_1_WORKING_analysis.md

📄 Converting: Personal_Information_2_WORKING_analysis.json
   ✅ Created: Personal_Information_2_WORKING_analysis.md

...

============================================================
🎯 Conversion Complete!
============================================================
✅ Successfully converted: 16 files

📁 Output folder: /Volumes/.../PI/markdown_reports/
📄 Markdown files: *_WORKING_analysis.md
============================================================
```

---

## 🎯 **Summary:**

**Input Folder:** `/Volumes/.../PI/` (JSON files)  
**Output Folder:** `/Volumes/.../PI/markdown_reports/` (Markdown files)  
**Folder Name:** `markdown_reports` (automatically created)  

**All Markdown files will be organized in the new folder!** ✨

---

## 📋 **To Change Folder Name:**

If you want a different folder name, edit line 230:

```python
# Current:
convert_all_json_files(data_path, output_folder_name='markdown_reports')

# Change to:
convert_all_json_files(data_path, output_folder_name='analysis_reports')
# or
convert_all_json_files(data_path, output_folder_name='sensitive_info_reports')
```

**Upload and run!** 🚀

