# 📄 OUTPUT FILES - What Gets Created

## 🧪 **Test Script Output:**

### **File:** `test_v3_final.py`

**Creates:**
```
/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/TEST_OUTPUT.txt
```

**Purpose:** Tests on ONE file to verify the LLM analysis works correctly

**Content Example:**
```
=== Document Analysis V3 (Prompt V3): Personal_Information_1.pdf.json ===

Total Pages: 3
Document Segments: 2

============================================================
SEGMENT: segment_1
Pages: 1-1 (1 pages)
============================================================

LLM ANALYSIS RESULTS (Prompt V3):
{
  "extracted_names": [
    "John Doe",
    "Dr. Jane Smith"
  ],
  "classifications": [
    {
      "category": "1.1 Personal Information",
      "text": "Staff medical record for John Doe",
      "bounding_box": [100, 200, 300, 250],
      "confidence_score": 0.95,
      "reason": "Contains personal medical details of an employee"
    },
    {
      "category": "2. CV or Resume Content",
      "text": "Work Experience: Software Engineer at XYZ Corp, 2015–2020",
      "bounding_box": [50, 400, 500, 450],
      "confidence_score": 0.92,
      "reason": "Chronological job history listed"
    }
  ]
}

============================================================
SEGMENT: segment_2
Pages: 2-3 (2 pages)
============================================================

LLM ANALYSIS RESULTS (Prompt V3):
{
  "extracted_names": ["Robert Johnson"],
  "classifications": [...]
}
```

---

## 🚀 **Main Script Output:**

### **File:** `Azure_DI_output_parser_V3_Final.py`

**Creates ONE file per input JSON:**

### **Input Files:**
```
/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/Personal_Information_1.pdf.json
/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/Personal_Information_2.pdf.json
/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/Personal_Information_3.pdf.json
...
/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/Personal_Information_N.pdf.json
```

### **Output Files Created:**
```
/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/Personal_Information_1_final_analysis.txt
/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/Personal_Information_2_final_analysis.txt
/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/Personal_Information_3_final_analysis.txt
...
/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/Personal_Information_N_final_analysis.txt
```

---

## 📋 **Output File Structure:**

Each `*_final_analysis.txt` file contains:

### **1. Header Section:**
```
=== Document Analysis V3 (Prompt V3): [filename] ===

Total Pages: X
Document Segments: Y
```

### **2. For Each Document Segment:**
```
============================================================
SEGMENT: segment_1
Pages: 1-2 (2 pages)
============================================================

LLM ANALYSIS RESULTS (Prompt V3):
{
  "extracted_names": [
    "Full Name 1",
    "Full Name 2",
    ...
  ],
  "classifications": [
    {
      "category": "1.1 Personal Information",
      "text": "The exact sensitive text found",
      "bounding_box": [x1, y1, x2, y2, ...],
      "confidence_score": 0.95,
      "reason": "Brief explanation why this is sensitive"
    },
    {
      "category": "2. CV or Resume Content",
      "text": "Work experience section...",
      "bounding_box": [x1, y1, x2, y2, ...],
      "confidence_score": 0.92,
      "reason": "Contains resume sections"
    },
    ...
  ]
}
```

---

## 🗂️ **Complete Output Summary:**

### **From Test Script:**
- **1 file:** `TEST_OUTPUT.txt` (in PI folder)

### **From Main Script:**
- **N files:** One `*_final_analysis.txt` for each input JSON file (in PI folder)

### **Example:**
If you have 13 JSON files (`Personal_Information_1.pdf.json` through `Personal_Information_13.pdf.json`):

**You'll get 13 output files:**
```
Personal_Information_1_final_analysis.txt
Personal_Information_2_final_analysis.txt
Personal_Information_3_final_analysis.txt
Personal_Information_4_final_analysis.txt
Personal_Information_5_final_analysis.txt
Personal_Information_6_final_analysis.txt
Personal_Information_7_final_analysis.txt
Personal_Information_8_final_analysis.txt
Personal_Information_9_final_analysis.txt
Personal_Information_10_final_analysis.txt
Personal_Information_11_final_analysis.txt
Personal_Information_12_final_analysis.txt
Personal_Information_13_final_analysis.txt
```

---

## 📊 **What Each Output Contains:**

### ✅ **Extracted Names:**
- All personal names found in the document
- Full names (first, middle, last)
- Names with titles (Dr., Professor, etc.)
- Names from signatures, headers, correspondence

### ✅ **Classifications:**
- **Category:** What type of sensitive content (1.1, 1.2, 2, 3, 4.1, etc.)
- **Text:** The exact sensitive text snippet
- **Bounding Box:** Location coordinates `[x1, y1, x2, y2, ...]`
- **Confidence Score:** 0.0 to 1.0 (how certain the LLM is)
- **Reason:** Brief explanation (~20 words)

### ✅ **Document Segments:**
- Each document is split based on 3 rules:
  1. Page size changes
  2. New titles
  3. Page number sequences
- Each segment is analyzed separately

---

## 🎯 **Quick Reference:**

| Script | Output Location | Output Name | Purpose |
|--------|----------------|-------------|---------|
| `test_v3_final.py` | `/Volumes/.../PI/` | `TEST_OUTPUT.txt` | Test on 1 file |
| `Azure_DI_output_parser_V3_Final.py` | `/Volumes/.../PI/` | `Personal_Information_#_final_analysis.txt` | Process all files |

---

## 🔍 **How to Check Outputs:**

### **After running test:**
```bash
cat /Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/TEST_OUTPUT.txt
```

### **After running main script:**
```bash
ls -lh /Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/*_final_analysis.txt
```

### **View one output:**
```bash
cat /Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/Personal_Information_1_final_analysis.txt
```

---

## ✅ **Summary:**

**Test Script:** Creates `TEST_OUTPUT.txt` (1 file)  
**Main Script:** Creates `Personal_Information_#_final_analysis.txt` (N files, one per input)  
**Location:** All in `/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/`

**Each output contains JSON with:**
- ✅ Extracted names
- ✅ Classified sensitive content
- ✅ Bounding boxes
- ✅ Confidence scores
- ✅ Reasoning


