# 🔍 Function-by-Function Analysis

## 📚 **Table of Contents:**
1. [Module-Level Code](#module-level)
2. [Global Functions](#global-functions)
3. [DocumentProcessor Class](#documentprocessor-class)
4. [Main Execution Block](#main-execution)

---

## 🌐 **MODULE-LEVEL CODE**

### **Lines 1-18: Imports**
```python
import json
import glob
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from itsai.llm_registry import vertex
from itsai.google import load_credentials_from_environment, get_google_credentials
from itsai.mai import llm
from itsai import llm_registry
```

**Purpose:** Import required libraries
- `json`: Parse JSON files and LLM responses
- `glob`: Find files matching patterns
- `os`: File system operations
- `google.genai`: Google's Generative AI SDK for caching
- `dotenv`: Load environment variables
- `itsai`: World Bank's internal LLM wrapper library

---

## 🔧 **GLOBAL FUNCTIONS**

### **Function 1: `load_master_prompt()` (Lines 21-72)**

**Purpose:** Find and load the Executive Prompt file

**Parameters:** None

**Returns:** `str` (prompt content) or `None` (if not found)

**Logic Flow:**
1. **Define search path** (line 25):
   ```python
   base_path = '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/'
   ```

2. **Define possible filenames** (lines 28-34):
   ```python
   filenames = [
       'Executive_Prompt.md',      # Primary
       'executive_prompt.md',      # Lowercase variant
       'ExecutivePrompt.md',       # No underscore
       'MasterPromp_V4.md',        # Fallback (with typo)
       'MasterPrompt_V4.md',       # Fallback (correct)
   ]
   ```

3. **List directory contents** (lines 40-51):
   - Shows all prompt-related files in the directory
   - Helps debug if file is missing

4. **Try each filename** (lines 54-67):
   - Opens file with UTF-8 encoding
   - Reads entire content
   - Shows first 150 characters
   - Returns content if successful

5. **Error handling**:
   - `FileNotFoundError`: File doesn't exist (continue trying)
   - `Exception`: Other errors (continue trying)
   - Returns `None` if all attempts fail

**Example Output:**
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
   First 150 chars: AI Document Analysis Prompt 

You are an expert AI assistant specializing in document analysis...
```

---

### **Lines 75-80: Load Prompt and Validate**
```python
MASTER_PROMPT = load_master_prompt()

if not MASTER_PROMPT:
    print("ERROR: Cannot proceed without prompt file")
    exit(1)
```

**Purpose:** Load prompt into global variable, exit if not found

**Why global?** 
- Prompt is needed by all document processors
- Only loaded once at startup (efficient)
- Shared across all files being processed

---

### **Function 2: `delete_old_caches()` (Lines 83-124)**

**Purpose:** Delete all existing caches to ensure fresh prompt is used

**Parameters:** None

**Returns:** `bool` (True if successful, False if error)

**Logic Flow:**

1. **Load credentials** (lines 88-90):
   ```python
   load_dotenv()                              # Load .env file
   creds = load_credentials_from_environment() # World Bank credentials
   g = get_google_credentials()               # Google Cloud credentials
   ```

2. **Create Vertex AI client** (lines 92-97):
   ```python
   client = genai.Client(
       vertexai=True,                  # Use Vertex AI (not standard Gemini)
       project=creds.project_id,        # Your GCP project
       location=g.google_vertex_region, # e.g., 'us-central1'
       credentials=creds                # Authentication
   )
   ```

3. **List all caches** (line 100):
   ```python
   caches = list(client.caches.list())
   ```
   Returns all cached prompts for this project/location

4. **Delete each cache** (lines 109-115):
   ```python
   for cache in caches:
       client.caches.delete(name=cache.name)
   ```
   - Deletes by `name` (full resource path)
   - Catches errors for individual deletions

5. **Error handling**:
   - Individual deletion errors: Warn but continue
   - Overall errors: Warn and return False (continues execution)

**Why delete?**
- Old caches might have wrong/outdated prompts
- Ensures clean slate for new prompt
- Prevents confusion from multiple cached versions

**Example Output:**
```
🗑️  DELETING ALL OLD CACHES (IMPORTANT!)...
   Found 2 existing cache(s)
   Deleting: classification_rules_v4
   Deleting: sensitive_data_classifier
✅ Deleted 2 old cache(s)
   This ensures we use the NEW prompt!
```

---

### **Function 3: `create_cached_model()` (Lines 127-164)**

**Purpose:** Create a new cache containing the prompt

**Parameters:**
- `system_instruction` (str): The prompt content to cache
- `ttl` (str, default="600s"): Time-to-live (how long cache lasts)

**Returns:** `CachedContent` object or `None` (if error)

**Logic Flow:**

1. **Load credentials** (same as delete_old_caches)

2. **Select model** (line 143):
   ```python
   model = vertex.Gemini.PRO_2_5
   ```
   Uses Gemini 2.0 Pro model

3. **Create cache** (lines 146-153):
   ```python
   cache = client.caches.create(
       model=model,
       config=types.CreateCachedContentConfig(
           display_name='classification_rules_v4',  # Name for this cache
           system_instruction=system_instruction,   # The prompt content
           ttl=ttl,                                 # "600s" = 10 minutes
       )
   )
   ```

4. **Return cache object** (line 159):
   - Returns the cache itself (not a model)
   - Cache will be passed to LLM via `model_kwargs`

**How caching works:**
```
WITHOUT CACHE:
Request 1: Prompt (6,842 tokens) + Document (500 tokens) = 7,342 tokens
Request 2: Prompt (6,842 tokens) + Document (500 tokens) = 7,342 tokens
Request 3: Prompt (6,842 tokens) + Document (500 tokens) = 7,342 tokens
Total: 22,026 tokens

WITH CACHE:
Request 1: Prompt (6,842 tokens) + Document (500 tokens) = 7,342 tokens [Creates cache]
Request 2: Cached (0 tokens) + Document (500 tokens) = 500 tokens [Uses cache]
Request 3: Cached (0 tokens) + Document (500 tokens) = 500 tokens [Uses cache]
Total: 8,342 tokens → 62% cost reduction!
```

**Example Output:**
```
🔄 Creating NEW cache with your prompt...
   Creating cache from prompt content...
✅ NEW cache created successfully: projects/my-project/locations/us-central1/cachedContents/abc123def456
   This cache contains your classification rules prompt
   TTL: 600s (10.0 minutes)
```

---

## 📦 **DOCUMENTPROCESSOR CLASS**

### **Class: `DocumentProcessor` (Lines 167-414)**

**Purpose:** Process a single JSON file through all stages

**Attributes:**
- `filepath`: Path to JSON file
- `analyze_result`: Parsed JSON data
- `page_content`: Dictionary of pages and their content
- `page_dimensions`: Dictionary of page sizes
- `document_segments`: Dictionary of detected document segments
- `cached_model`: The cache object (if caching enabled)

---

### **Method 1: `__init__()` (Lines 170-177)**

**Purpose:** Initialize the processor

**Parameters:**
- `filepath` (str): Path to JSON file
- `cached_model` (CachedContent, optional): Cache object

**Logic:**
1. Store filepath and cached_model
2. Initialize empty dictionaries
3. Call `_load_data()` immediately

**Example:**
```python
processor = DocumentProcessor('file.json', cached_model=cache)
```

---

### **Method 2: `_load_data()` (Lines 179-190)**

**Purpose:** Load and parse the JSON file

**Parameters:** None (uses `self.filepath`)

**Returns:** None (sets `self.analyze_result`)

**Logic:**
1. **Open file** (line 182):
   ```python
   with open(self.filepath, 'r', encoding='utf-8') as f:
       data = json.load(f)
   ```

2. **Extract analyzeResult** (line 184):
   ```python
   self.analyze_result = data.get('analyzeResult')
   ```
   This is the main section with all document data

3. **Validate** (lines 185-186):
   - Raises error if 'analyzeResult' missing
   - Sets to `None` on error

**JSON Structure:**
```json
{
  "analyzeResult": {
    "pages": [...],
    "paragraphs": [...],
    "tables": [...]
  }
}
```

---

### **Method 3: `_organize_content_by_page()` (Lines 192-228)**

**Purpose:** Group all content by page number

**Parameters:** None

**Returns:** None (populates `self.page_content` and `self.page_dimensions`)

**Logic:**

**Step 1: Initialize page containers** (lines 198-206):
```python
for page in self.analyze_result.get('pages', []):
    page_number = page.get('pageNumber')  # 1, 2, 3...
    self.page_content[page_number] = {
        'paragraphs': [],
        'tables': [],
        'page_numbers': []
    }
    self.page_dimensions[page_number] = {
        'width': page.get('width'),    # e.g., 612
        'height': page.get('height'),  # e.g., 792
        'unit': page.get('unit')       # e.g., 'pixel'
    }
```

**Step 2: Assign paragraphs to pages** (lines 209-221):
```python
for paragraph in self.analyze_result.get('paragraphs', []):
    # Get page number from boundingRegions
    page_number = paragraph['boundingRegions'][0].get('pageNumber')
    
    # Create paragraph info
    para_info = {
        'content': paragraph.get('content', ''),        # Text
        'role': paragraph.get('role', 'paragraph'),     # title/paragraph/etc
        'boundingBox': paragraph['boundingRegions'][0].get('polygon', [])  # [x1,y1,x2,y2,...]
    }
    
    # Categorize by role
    if para_info['role'] == 'pageNumber':
        self.page_content[page_number]['page_numbers'].append(para_info)
    else:
        self.page_content[page_number]['paragraphs'].append(para_info)
```

**Step 3: Assign tables to pages** (lines 224-228):
```python
for table in self.analyze_result.get('tables', []):
    # Get page number from first cell
    page_number = table['cells'][0]['boundingRegions'][0].get('pageNumber')
    self.page_content[page_number]['tables'].append(table)
```

**Result:**
```python
self.page_content = {
    1: {
        'paragraphs': [
            {'content': 'Title', 'role': 'title', 'boundingBox': [...]},
            {'content': 'Text', 'role': 'paragraph', 'boundingBox': [...]}
        ],
        'tables': [],
        'page_numbers': []
    },
    2: {...}
}
```

---

### **Method 4: `_detect_document_boundaries()` (Lines 230-279)**

**Purpose:** Split pages into separate document segments

**Parameters:** None

**Returns:** None (populates `self.document_segments`)

**Logic:**

**3 Detection Rules:**

**Rule 1: Page Size Change** (lines 250-257):
```python
height_change = abs(prev_height - curr_height) / max(prev_height, 1)
width_change = abs(prev_width - curr_width) / max(prev_width, 1)
has_size_change = height_change > 0.05 or width_change > 0.05  # >5% change
```
If dimensions change by >5% → New document

**Rule 2: New Title** (line 244):
```python
has_title = any(p.get('role') == 'title' for p in paragraphs[:3])
```
If first 3 paragraphs include a title → New document (unless Rule 3 overrides)

**Rule 3: Page Number** (line 247):
```python
has_page_num = bool(page_data.get('page_numbers', []))
```
If page has page number → Continuation of document

**Decision Logic** (line 260):
```python
is_new_document = (i == 0) or (has_title and not has_page_num) or has_size_change
```
- First page is always new document
- OR title without page number
- OR size changed

**Segment Creation** (lines 262-269):
```python
if is_new_document and current_segment:
    document_segments.append(current_segment)  # Save previous segment
    current_segment = []                        # Start new segment

current_segment.append(page_num)  # Add current page to segment
```

**Final Storage** (lines 271-277):
```python
for i, segment in enumerate(document_segments):
    self.document_segments[f"segment_{i+1}"] = {
        'pages': segment,            # [1, 2, 3]
        'start_page': min(segment),  # 1
        'end_page': max(segment),    # 3
        'page_count': len(segment)   # 3
    }
```

**Example:**
```
Input: 5 pages
Page 1: Title "Report A" → NEW (Rule 2)
Page 2: Page number "2/3" → CONTINUATION (Rule 3)
Page 3: Page number "3/3" → CONTINUATION (Rule 3)
Page 4: Size changed → NEW (Rule 1)
Page 5: No indicators → CONTINUATION

Output:
segment_1: [1, 2, 3]
segment_2: [4, 5]
```

---

### **Method 5: `_get_segment_content()` (Lines 281-298)**

**Purpose:** Format segment pages into text for LLM

**Parameters:**
- `pages` (list): List of page numbers in segment

**Returns:** `str` (formatted content with bounding boxes)

**Logic:**

**For each page** (lines 284-296):
1. Add page header
2. Format paragraphs with role and bounding box
3. Format page numbers with bounding box

**Example Output:**
```
=== PAGE 1 ===
[Role: title, BBox: 100,200,300,250]
Employment History

[Role: paragraph, BBox: 100,260,300,300]
Work Experience at ABC Company from 2020 to 2023.

[Page Number, BBox: 100,800,150,820]
1/3

=== PAGE 2 ===
[Role: paragraph, BBox: 50,100,550,150]
Continued experience description...

[Page Number, BBox: 100,800,150,820]
2/3
```

**Why include bounding boxes?**
- Executive Prompt requires them
- LLM extracts them for `classifications` output
- Shows exact location of sensitive content

---

### **Method 6: `analyze_with_llm()` (Lines 300-362)**

**Purpose:** Send document to LLM for analysis

**Parameters:**
- `document_content` (str): Formatted text from `_get_segment_content()`
- `segment_id` (str): e.g., "segment_1"

**Returns:** `str` (LLM response, should be JSON)

**Logic:**

**Branch 1: With Cache** (lines 305-314):
```python
if self.cached_model:
    gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
    message = gemini.invoke(
        f"Document Content to Analyze:\n{document_content}",
        model_kwargs={'cached_content': self.cached_model}  # Use cache!
    )
    result = message.content
```
- Sends ONLY document content (~500 tokens)
- Prompt comes from cache (0 tokens)
- **Cost: ~93% cheaper than without cache**

**Branch 2: Without Cache** (lines 316-322):
```python
else:
    full_prompt = f"{MASTER_PROMPT}\n\nDocument Content to Analyze:\n{document_content}"
    gemini = llm.select_model(llm_registry.vertex.Gemini.PRO_2_5)
    message = gemini.invoke(full_prompt)
    result = message.content
```
- Sends prompt + document (~7,342 tokens)
- **Cost: Normal (no savings)**

**Validation** (lines 325-348):
```python
json_result = json.loads(result)

has_names = 'extracted_names' in json_result
has_classifications = 'classifications' in json_result

if has_names and has_classifications:
    print("✅ VALIDATION: Output follows Executive Prompt format!")
    print(f"   Found: extracted_names ({len(json_result['extracted_names'])} names)")
    print(f"   Found: classifications ({len(json_result['classifications'])} items)")
```

Checks if LLM response matches expected format:
- ✅ Has both fields → Success
- ⚠️ Has one field → Partial match
- ❌ Has neither → Wrong format

**Fallback** (lines 354-362):
If error occurs, tries again without cache

---

### **Method 7: `process_document()` (Lines 364-414)**

**Purpose:** Orchestrate the entire processing workflow

**Parameters:**
- `output_filepath` (str, optional): Where to save results

**Returns:** None

**Logic Flow:**

**Step 1: Organize content** (lines 370-375):
```python
self._organize_content_by_page()
if not self.page_content:
    return  # Exit if no content
```

**Step 2: Detect boundaries** (lines 377-378):
```python
self._detect_document_boundaries()
```

**Step 3: Open output file** (lines 384-389):
```python
output_file = open(output_filepath, 'w', encoding='utf-8')
output_file.write(f"=== Document Analysis: {self.filepath} ===\n")
output_file.write(f"Prompt: Executive Prompt (AI Document Analysis)\n")
output_file.write(f"Total Pages: {len(self.page_content)}\n")
output_file.write(f"Segments: {len(self.document_segments)}\n\n")
```

**Step 4: Process each segment** (lines 391-405):
```python
for segment_id, segment_info in self.document_segments.items():
    pages = segment_info['pages']
    
    # Get formatted content
    segment_content = self._get_segment_content(pages)
    
    # Send to LLM
    llm_result = self.analyze_with_llm(segment_content, segment_id)
    
    # Write to file
    output_file.write(f"\nSEGMENT: {segment_id}\n")
    output_file.write(f"Pages: {min(pages)}-{max(pages)}\n")
    output_file.write("LLM ANALYSIS:\n")
    output_file.write(llm_result)
```

**Step 5: Close file** (lines 411-414):
```python
finally:
    if output_file:
        output_file.close()
```
Always closes file, even if error occurs

---

## 🚀 **MAIN EXECUTION BLOCK**

### **Lines 417-481: Main Program**

**Purpose:** Process all JSON files with caching

**Flow:**

**1. Find files** (lines 419-423):
```python
all_json_files = glob.glob(f"{data_path}Personal_Information_*.pdf.json")
json_files = sorted(all_json_files)[:5]  # First 5 for testing
```

**2. Delete old caches** (lines 434-438):
```python
delete_old_caches()
```

**3. Create new cache** (lines 440-453):
```python
cached_model = create_cached_model(MASTER_PROMPT, ttl="600s")
```

**4. Process each file** (lines 456-469):
```python
for json_file in sorted(json_files):
    processor = DocumentProcessor(json_file, cached_model=cached_model)
    processor.process_document(output_filepath=output_filename)
```
- Creates one processor per file
- Reuses same `cached_model` (saves money!)

**5. Summary** (lines 471-481):
```python
print(f"Processed {len(json_files)} files")
print(f"Cache reused {len(json_files) - 1} times")
```

---

## 📊 **COMPLETE DATA FLOW**

```
1. Load Executive Prompt (global)
2. Delete old caches
3. Create new cache with prompt
4. For each JSON file:
   ├─ Load JSON → extract analyzeResult
   ├─ Organize content by page
   │  ├─ Assign paragraphs to pages
   │  ├─ Assign tables to pages
   │  └─ Store page dimensions
   ├─ Detect document boundaries
   │  ├─ Check for size changes (Rule 1)
   │  ├─ Check for titles (Rule 2)
   │  ├─ Check for page numbers (Rule 3)
   │  └─ Split into segments
   ├─ For each segment:
   │  ├─ Format content with bounding boxes
   │  ├─ Send to LLM (with cached prompt)
   │  ├─ Validate response format
   │  └─ Write to output file
   └─ Close file
5. Print summary
```

---

## 🎯 **KEY TAKEAWAYS**

**Efficiency:**
- Prompt loaded once (line 76)
- Cache created once (line 445)
- Cache reused for all files (line 465)
- **Result: 75% cost reduction**

**Robustness:**
- File not found? Lists directory contents
- Cache fails? Falls back to non-cached
- LLM error? Tries again without cache
- Wrong format? Validates and reports

**Modularity:**
- Each method has single responsibility
- Easy to modify one part without breaking others
- Clear separation of concerns

**Debugging:**
- Extensive print statements
- Shows progress at each step
- Validates output format
- Reports errors clearly


