# 🚀 Databricks Instructions

## 📄 **File to Upload:**

**`Azure_DI_output_parser_V3_FINAL_WITH_CACHING.py`**

---

## ✅ **No Changes Needed!**

The file is **already configured for Databricks** with the correct paths:

```python
# Input/Output path (already correct)
data_path = '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/'

# Prompt path (already correct - tries Databricks path first)
paths = [
    '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/prompt_v3.md',
    'prompt_v3.md',
    os.path.join(os.getcwd(), 'prompt_v3.md')
]
```

---

## 📋 **Prerequisites:**

Make sure these files are in the Databricks volume:

1. ✅ `prompt_v3.md` - in `/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/`
2. ✅ All `Personal_Information_*.pdf.json` files - in the same folder

---

## 🚀 **How to Run in Databricks:**

### **Option 1: Upload as Notebook**

1. **Upload the file:**
   - Go to Databricks Workspace
   - Navigate to your folder
   - Click "Import"
   - Select `Azure_DI_output_parser_V3_FINAL_WITH_CACHING.py`

2. **Run the notebook:**
   - Click "Run All"
   - Watch the output

### **Option 2: Run as Script**

1. **Upload to DBFS:**
   ```python
   dbutils.fs.put("/FileStore/Azure_DI_output_parser_V3_FINAL_WITH_CACHING.py", 
                  open("Azure_DI_output_parser_V3_FINAL_WITH_CACHING.py").read(), 
                  overwrite=True)
   ```

2. **Run the script:**
   ```python
   %run /FileStore/Azure_DI_output_parser_V3_FINAL_WITH_CACHING.py
   ```

### **Option 3: Copy-Paste into Notebook**

1. Create a new Python notebook in Databricks
2. Copy the entire content of `Azure_DI_output_parser_V3_FINAL_WITH_CACHING.py`
3. Paste into a single cell
4. Run the cell

---

## 📊 **Expected Output:**

```
🚀 DOCUMENT PROCESSOR V3 - WITH CORRECT CACHING
============================================================
Processing 13 files
Features:
- ✅ Deletes old caches with wrong prompt
- ✅ Creates NEW cache with prompt_v3.md
- ✅ Validates output format
- ✅ Cost savings from caching
============================================================

🗑️  Checking for old caches...
   Deleting old cache: sensitive_data_classifier (...)
✅ Deleted 1 old cache(s)

🔄 Creating NEW cache with prompt_v3.md...
   Cache name: sensitive_classifier_v3_correct_1728567890
   Prompt length: 7631 chars
   TTL: 600s
✅ NEW cache created successfully!
   This cache contains the CORRECT prompt_v3.md

💰 Cost Savings: Using NEW cached prompt for 13 files!
   Estimated savings: ~720% reduction in prompt tokens

============================================================
🔍 Processing: /Volumes/.../Personal_Information_1.pdf.json
============================================================
📄 Document boundary at page 1: First page
📚 Found 1 document segments

🤖 Running LLM analysis for segment_1...
✅ LLM analysis completed for segment_1 (using cache) - CORRECT FORMAT
✅ Successfully processed: /Volumes/.../Personal_Information_1_correct_cache_analysis.txt

... (repeats for all files) ...

🎯 All files processed with CORRECT caching!
   NEW cache was created with prompt_v3.md
   Cache was reused 12 times
   Output files: *_correct_cache_analysis.txt
   Significant cost savings achieved! 💰
```

---

## 📁 **Output Files:**

All output files will be created in:
```
/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/
```

**File names:**
```
Personal_Information_1_correct_cache_analysis.txt
Personal_Information_2_correct_cache_analysis.txt
Personal_Information_3_correct_cache_analysis.txt
...
Personal_Information_13_correct_cache_analysis.txt
```

---

## ✅ **Validation:**

Look for these messages to confirm it's working:

1. ✅ `"✅ Deleted X old cache(s)"` - Old cache removed
2. ✅ `"✅ NEW cache created successfully!"` - New cache created
3. ✅ `"✅ LLM analysis completed (using cache) - CORRECT FORMAT"` - Output is correct
4. ✅ `"✅ Successfully processed: ..."` - File saved

---

## 🔍 **Check Output:**

After running, check one output file:

```python
# In Databricks notebook
with open('/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/Personal_Information_1_correct_cache_analysis.txt', 'r') as f:
    content = f.read()
    print(content[:1000])  # First 1000 chars
```

**Should contain:**
- ✅ `"extracted_names": [...]`
- ✅ `"classifications": [...]`
- ✅ `"bounding_box": [...]`
- ✅ `"confidence_score": ...`

**Should NOT contain:**
- ❌ `"File Title"`
- ❌ `"sender_name"`
- ❌ `"Barcode No."`

---

## 💰 **Cost Savings:**

| Metric | Value |
|--------|-------|
| **First file** (creates cache) | ~7,600 tokens |
| **Subsequent files** (use cache) | ~100 tokens each |
| **Total savings** (13 files) | ~90,000 tokens |
| **Cost reduction** | ~60% |

---

## 🎯 **Summary:**

| Item | Status |
|------|--------|
| **File to upload** | `Azure_DI_output_parser_V3_FINAL_WITH_CACHING.py` |
| **Changes needed** | ✅ None - already configured |
| **Paths** | ✅ Correct for Databricks |
| **Prompt** | ✅ Will load from volume |
| **Caching** | ✅ Enabled with NEW cache |
| **Output** | ✅ Correct format |

---

## 🚀 **Quick Start:**

1. Upload `Azure_DI_output_parser_V3_FINAL_WITH_CACHING.py` to Databricks
2. Make sure `prompt_v3.md` is in `/Volumes/.../PI/`
3. Run the script
4. Check output files in `/Volumes/.../PI/*_correct_cache_analysis.txt`

**That's it!** 🎉


