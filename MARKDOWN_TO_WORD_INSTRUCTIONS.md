# 📄 Markdown to Word Converter

## 🎯 **Purpose:**

Converts existing `.md` files to `.docx` Word documents.

---

## 📋 **Input and Output:**

### **Input:**
**Folder:** `/Volumes/.../PI/`  
**Files:** `Personal_Information_#_WORKING_analysis.md`

### **Output:**
**Folder:** `/Volumes/.../PI/word_reports/`  
**Files:** `Personal_Information_#_WORKING_analysis.docx`

---

## 🚀 **How to Run:**

### **Step 1: Install Pandoc**

On Databricks, run:
```bash
pip install pypandoc
```

Or if pandoc binary is needed:
```bash
# Databricks usually has pandoc pre-installed
# If not, contact admin to install
```

### **Step 2: Upload**
Upload `markdown_to_word.py` to Databricks

### **Step 3: Run**
```python
python markdown_to_word.py
```

---

## 📊 **What It Does:**

1. ✅ Finds all `*_WORKING_analysis.md` files
2. ✅ Creates `word_reports/` folder
3. ✅ Converts each `.md` to `.docx` using pandoc
4. ✅ Saves all Word files in the folder

---

## 📂 **Result:**

```
/Volumes/.../PI/
├── Personal_Information_1_WORKING_analysis.md
├── Personal_Information_2_WORKING_analysis.md
└── word_reports/
    ├── Personal_Information_1_WORKING_analysis.docx
    ├── Personal_Information_2_WORKING_analysis.docx
    └── ...
```

---

## 🔍 **Console Output:**

```
============================================================
🚀 MARKDOWN TO WORD CONVERTER
============================================================
Source: /Volumes/.../PI/
Looking for: *_WORKING_analysis.md
Output: word_reports/ folder
============================================================

✅ Output folder created: /Volumes/.../PI/word_reports

🔄 Markdown to Word Converter
============================================================
Input: /Volumes/.../PI/
Output: /Volumes/.../PI/word_reports/
Found 16 Markdown files to convert
============================================================

📄 Converting: Personal_Information_1_WORKING_analysis.md
   ✅ Created: Personal_Information_1_WORKING_analysis.docx

📄 Converting: Personal_Information_2_WORKING_analysis.md
   ✅ Created: Personal_Information_2_WORKING_analysis.docx

...

============================================================
🎯 Conversion Complete!
============================================================
✅ Successfully converted: 16 files

📁 Output folder: /Volumes/.../PI/word_reports/
📄 Word files: *_WORKING_analysis.docx
============================================================
```

---

## ⚠️ **If Pandoc Not Available:**

Use the alternative script: `json_to_word_converter.py`

This converts **directly from JSON to Word** without needing Markdown files or pandoc.

---

## 🎯 **Summary:**

**Script:** `markdown_to_word.py`  
**Input:** `.md` files  
**Output:** `.docx` files in `word_reports/` folder  
**Requirement:** `pandoc` (usually pre-installed on Databricks)  

**Upload and run!** 📄


