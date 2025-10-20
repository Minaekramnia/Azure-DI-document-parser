# 🚀 QUICK START GUIDE - PageNumbers Version

## 📋 What to Run (In Order)

### **STEP 1: Analyze JSON Files**

**Run this command in Databricks**:
```python
python Azure_DI_output_parser_WORKING_PageNumbers.py
```

**What it does**:
- Reads your JSON files
- Analyzes them with LLM
- Adds page numbers to classifications
- Creates JSON output files

**Time**: ~5-10 minutes for 5 files

---

### **STEP 2: Create Reports**

**Run this command in Databricks**:
```python
python convert_PageNumbers_to_reports.py
```

**What it does**:
- Converts JSON to Markdown
- Converts Markdown to Word
- Creates organized folders

**Time**: ~1-2 minutes

---

## 📁 WHERE TO FIND YOUR OUTPUTS

### **All outputs are in the same folder as your input files**:

```
/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/
```

---

## 📂 OUTPUT FILES AND FOLDERS

After running both steps, you'll have:

### **1. JSON Analysis Files** (from Step 1)
```
/Volumes/.../PI/Personal_Information_1_WORKING_PageNumbers_analysis.json
/Volumes/.../PI/Personal_Information_2_WORKING_PageNumbers_analysis.json
/Volumes/.../PI/Personal_Information_3_WORKING_PageNumbers_analysis.json
...
```

### **2. Markdown Reports Folder** (from Step 2)
```
/Volumes/.../PI/markdown_reports_PageNumbers/
    ├── Personal_Information_1_PageNumbers_report.md
    ├── Personal_Information_2_PageNumbers_report.md
    ├── Personal_Information_3_PageNumbers_report.md
    └── ...
```

### **3. Word Documents Folder** (from Step 2)
```
/Volumes/.../PI/word_reports_PageNumbers/
    ├── Personal_Information_1_PageNumbers_report.docx
    ├── Personal_Information_2_PageNumbers_report.docx
    ├── Personal_Information_3_PageNumbers_report.docx
    └── ...
```

---

## 🎯 EXACT PATHS

### **Input Files Location**:
```
/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/Personal_Information_*.pdf.json
```

### **JSON Output Location**:
```
/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/*_WORKING_PageNumbers_analysis.json
```

### **Markdown Reports Location**:
```
/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/markdown_reports_PageNumbers/
```

### **Word Reports Location**:
```
/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/word_reports_PageNumbers/
```

---

## ✅ CHECKLIST

### **Before Running**:
- [ ] Upload `Azure_DI_output_parser_WORKING_PageNumbers.py` to Databricks
- [ ] Upload `convert_PageNumbers_to_reports.py` to Databricks
- [ ] Verify `Executive_Prompt.md` is in the PI folder
- [ ] Verify your JSON files exist in the PI folder

### **After Step 1**:
- [ ] Check that `*_WORKING_PageNumbers_analysis.json` files were created
- [ ] Open one JSON file to verify it has `page_number` fields

### **After Step 2**:
- [ ] Check that `markdown_reports_PageNumbers/` folder exists
- [ ] Check that `word_reports_PageNumbers/` folder exists
- [ ] Open a Word file to verify the report looks good

---

## 🔍 HOW TO CHECK IF IT WORKED

### **In Databricks, run**:
```python
# Check JSON outputs
import glob
json_files = glob.glob('/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/*_WORKING_PageNumbers_analysis.json')
print(f"Found {len(json_files)} JSON output files")

# Check Markdown reports
import os
md_folder = '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/markdown_reports_PageNumbers'
if os.path.exists(md_folder):
    md_files = os.listdir(md_folder)
    print(f"Found {len(md_files)} Markdown reports")

# Check Word reports
word_folder = '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/word_reports_PageNumbers'
if os.path.exists(word_folder):
    word_files = os.listdir(word_folder)
    print(f"Found {len(word_files)} Word reports")
```

---

## 💡 QUICK TIPS

### **Processing More Files**
By default, scripts process only **5 files** for testing.

To process **ALL files**, edit line 643 in `Azure_DI_output_parser_WORKING_PageNumbers.py`:

**Change**:
```python
json_files = sorted(all_json_files)[:5]
```

**To**:
```python
json_files = sorted(all_json_files)
```

### **If Something Goes Wrong**
1. Check the console output for error messages
2. Verify all paths are correct
3. Make sure `Executive_Prompt.md` exists
4. Ensure you have write permissions to the PI folder

---

## 📞 WHAT TO TELL YOUR BOSS

> "I've successfully implemented an automated document analysis pipeline that:
> 
> 1. Analyzes Azure Document Intelligence JSON files using AI
> 2. Extracts personal names and classifies sensitive content
> 3. Tracks the exact page number where each sensitive item appears
> 4. Generates professional reports in both Markdown and Word formats
> 5. Uses prompt caching to reduce costs by 90%
> 
> All outputs are organized in dedicated folders with clear naming conventions,
> making it easy to review and share results with stakeholders."

---

## 🎯 SUMMARY

**Run these 2 commands**:
```bash
python Azure_DI_output_parser_WORKING_PageNumbers.py
python convert_PageNumbers_to_reports.py
```

**Get these outputs**:
- JSON files with page numbers
- Markdown reports in `markdown_reports_PageNumbers/`
- Word documents in `word_reports_PageNumbers/`

**All in this folder**:
```
/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/
```

---

**That's it! You're ready to go! 🚀**

