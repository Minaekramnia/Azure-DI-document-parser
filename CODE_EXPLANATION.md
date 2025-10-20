# 🔍 What The Code Does - Step by Step

## 📋 **Overview:**

The code takes JSON files from Azure Document Intelligence, splits them into document segments, and uses an LLM to extract names and classify sensitive information.

---

## 🎯 **Main Process (5 Steps):**

### **STEP 1: Load the Executive Prompt**
```python
def load_master_prompt()
```

**What it does:**
1. Looks for `Executive_Prompt.md` in the Databricks volume
2. Reads the entire prompt file into memory
3. Shows you what it found (file path, length, first 150 characters)

**Output:**
```
🔍 Searching for Executive Prompt...
   Base path: /Volumes/.../PI/
   Found 3 prompt-related files:
      - Executive_Prompt.md
      - MasterPromp_V4.md
      - prompt_v3.md

   Trying: /Volumes/.../PI/Executive_Prompt.md
   ✅ FOUND! Loaded from: /Volumes/.../PI/Executive_Prompt.md
   Prompt length: 6842 characters
```

**Why:** This prompt tells the LLM exactly how to analyze documents (what to extract, what format to use).

---

### **STEP 2: Delete Old Caches**
```python
def delete_old_caches()
```

**What it does:**
1. Connects to Google Vertex AI
2. Lists all existing cached prompts
3. Deletes each one

**Output:**
```
🗑️  DELETING ALL OLD CACHES (IMPORTANT!)...
   Found 2 existing cache(s)
   Deleting: classification_rules_v4
   Deleting: sensitive_data_classifier
✅ Deleted 2 old cache(s)
```

**Why:** Old caches might have wrong prompts. Deleting them ensures we use the fresh Executive Prompt.

---

### **STEP 3: Create New Cache**
```python
def create_cached_model(system_instruction, ttl="600s")
```

**What it does:**
1. Connects to Google Vertex AI
2. Creates a new cache with the Executive Prompt
3. Sets it to expire in 10 minutes (600 seconds)

**Output:**
```
🔄 Creating NEW cache with your prompt...
   Creating cache from prompt content...
✅ NEW cache created successfully: projects/.../cachedContents/abc123
   This cache contains your classification rules prompt
   TTL: 600s (10.0 minutes)
```

**Why:** Caching saves money! 
- **First file:** Sends full prompt (~6,842 tokens) = Normal cost
- **Next files:** Sends only document (~100 tokens) = 60% cheaper!
- **Total savings:** ~90% cost reduction for batch processing

---

### **STEP 4: Process Each JSON File**

#### **4A. Load JSON File**
```python
def _load_data(self)
```

**What it does:**
1. Opens the `.pdf.json` file
2. Finds the `analyzeResult` section
3. Loads all pages, paragraphs, and tables

**Output:**
```
✅ Loaded: /Volumes/.../Personal_Information_1.pdf.json
```

---

#### **4B. Organize Content by Page**
```python
def _organize_content_by_page(self)
```

**What it does:**
1. Creates a dictionary for each page
2. Assigns paragraphs to their pages (based on bounding regions)
3. Assigns tables to their pages
4. Stores page dimensions (width, height)

**Result:**
```python
self.page_content = {
    1: {
        'paragraphs': [
            {'content': 'Hello World', 'role': 'title', 'boundingBox': [100, 200, 300, 250]},
            {'content': 'This is text', 'role': 'paragraph', 'boundingBox': [100, 260, 300, 300]}
        ],
        'tables': [],
        'page_numbers': []
    },
    2: { ... }
}
```

---

#### **4C. Detect Document Boundaries**
```python
def _detect_document_boundaries(self)
```

**What it does:**
Splits the pages into separate documents based on 3 rules:

**Rule 1: Page Size Change**
- If width or height changes by >5% → New document

**Rule 2: New Title**
- If page starts with a title role → New document (unless there's a page number)

**Rule 3: Page Number**
- If page has a page number → Continuation of previous document

**Output:**
```
📚 Found 2 document segments
   segment_1: Pages 1-1 (1 pages)
   segment_2: Pages 2-3 (2 pages)
```

**Example:**
```
Page 1: Title "Report" → NEW DOCUMENT (segment_1)
Page 2: Page number "2/3" → CONTINUATION (still segment_1)
Page 3: Size changed → NEW DOCUMENT (segment_2)
```

---

#### **4D. Format Content for LLM**
```python
def _get_segment_content(self, pages)
```

**What it does:**
1. Takes all pages in a segment
2. Formats them into text with bounding boxes
3. Creates a single string for the LLM

**Example Output:**
```
=== PAGE 1 ===
[Role: title, BBox: 100,200,300,250]
Employment History

[Role: paragraph, BBox: 100,260,300,300]
Work Experience at ABC Company from 2020 to 2023.

[Page Number, BBox: 100,800,150,820]
1/3
```

---

#### **4E. Send to LLM for Analysis**
```python
def analyze_with_llm(self, document_content, segment_id)
```

**What it does:**

**If cache exists:**
1. Uses the cached prompt (saves money!)
2. Sends only the document content
3. Gets response from LLM

**If no cache:**
1. Sends full prompt + document content
2. Gets response from LLM

**Output:**
```
🤖 Running LLM analysis for segment_1...
   Using cached prompt (classification_rules_v4)
✅ Analysis completed for segment_1 (using cache)
```

**LLM Response Format:**
```json
{
  "extracted_names": [
    "John Doe",
    "Dr. Jane Smith"
  ],
  "classifications": [
    {
      "category": "1.1 Personal Information",
      "text": "Work Experience at ABC Company from 2020 to 2023.",
      "bounding_box": [100, 260, 300, 300],
      "confidence_score": 0.85,
      "reason": "Contains employment history linked to a named individual."
    }
  ]
}
```

---

#### **4F. Validate Output**
```python
# VALIDATE OUTPUT - check if it matches EXECUTIVE PROMPT format
```

**What it does:**
1. Tries to parse the LLM response as JSON
2. Checks if it has `extracted_names` field
3. Checks if it has `classifications` field
4. Counts how many names and classifications found

**Output:**
```
✅ VALIDATION: Output follows Executive Prompt format!
   Found: extracted_names (3 names)
   Found: classifications (2 items)
```

**Or if wrong:**
```
⚠️  VALIDATION: Output format unexpected
   Expected: extracted_names and classifications
   Found: ['file_title', 'barcode_no']
```

---

#### **4G. Save to File**
```python
if output_file:
    output_file.write(f"\n{'='*60}\n")
    output_file.write(f"SEGMENT: {segment_id}\n")
    output_file.write(f"Pages: {min(pages)}-{max(pages)}\n")
    output_file.write(f"{'='*60}\n\n")
    output_file.write("LLM ANALYSIS:\n")
    output_file.write(llm_result)
    output_file.write("\n\n")
```

**What it does:**
Writes the LLM analysis to a text file

**Example File Content:**
```
=== Document Analysis: /Volumes/.../Personal_Information_1.pdf.json ===
Prompt: Executive Prompt (AI Document Analysis)
Total Pages: 2
Segments: 2


============================================================
SEGMENT: segment_1
Pages: 1-1
============================================================

LLM ANALYSIS:
{
  "extracted_names": ["Donna Jenloz"],
  "classifications": [
    {
      "category": "1.1 Personal Information",
      "text": "Donna Jenloz is wife of Peace Corps member...",
      "bounding_box": [100, 200, 300, 250],
      "confidence_score": 0.92,
      "reason": "Contains personal information about employment and relationships."
    }
  ]
}


============================================================
SEGMENT: segment_2
Pages: 2-2
============================================================

LLM ANALYSIS:
{
  "extracted_names": ["Edward V.K. Jaycox", "Walter Rill"],
  "classifications": [...]
}
```

---

### **STEP 5: Process All Files**

**What it does:**
1. Finds all `Personal_Information_*.pdf.json` files
2. Takes the first 5 (for testing)
3. Processes each one using Steps 4A-4G
4. Reuses the same cache for all files (saves money!)

**Output:**
```
🎯 Complete!
Processed 5 files (first 5 for testing)
Output files: *_WORKING_analysis.txt
Cache reused 4 times - significant savings! 💰
```

---

## 💰 **Cost Breakdown:**

| File | Tokens Sent | Cost |
|------|-------------|------|
| **File 1** (creates cache) | 6,842 (prompt) + 500 (doc) = 7,342 | 100% |
| **File 2** (uses cache) | 0 (cached) + 500 (doc) = 500 | ~7% |
| **File 3** (uses cache) | 0 (cached) + 500 (doc) = 500 | ~7% |
| **File 4** (uses cache) | 0 (cached) + 500 (doc) = 500 | ~7% |
| **File 5** (uses cache) | 0 (cached) + 500 (doc) = 500 | ~7% |
| **Total for 5 files** | 9,342 tokens | ~25% cost |
| **Without caching** | 36,710 tokens | 100% cost |
| **Savings** | 27,368 tokens | **75% cheaper!** |

---

## 📊 **Data Flow:**

```
JSON File
    ↓
[Load & Parse]
    ↓
Organize by Page
    ↓
Detect Document Boundaries
    ↓
Split into Segments
    ↓
Format as Text + Bounding Boxes
    ↓
Send to LLM (with cached prompt)
    ↓
Get Response (names + classifications)
    ↓
Validate Format
    ↓
Save to Output File
```

---

## 🎯 **Summary:**

**Input:** Azure Document Intelligence JSON files
**Process:** 
1. Load Executive Prompt
2. Delete old caches
3. Create new cache (saves money)
4. For each JSON file:
   - Split into document segments
   - Send each segment to LLM
   - Extract names and classify sensitive info
5. Save results

**Output:** Text files with:
- All personal names found
- All sensitive content classified (with categories, bounding boxes, confidence scores)

**Key Feature:** Caching saves ~75% of LLM costs for batch processing!


