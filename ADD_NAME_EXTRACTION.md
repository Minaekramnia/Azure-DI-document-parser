# 📋 How to Add Name Extraction

## 🎯 **Current Situation:**

Your current prompt (`MasterPromp_V4.md`) does **NOT** extract names.

**Current output:**
```json
{
  "file_title": "...",
  "barcode_no": "...",
  "document_type": "...",
  "exceptions": "..."
}
```

**Missing:** `extracted_names` field

---

## ✅ **Solution:**

I created an **updated prompt** that includes name extraction:

**File:** `MasterPrompt_V4_WITH_NAMES.md`

---

## 📊 **What's Added:**

### **Section 4: Name Extraction**

```markdown
### **4. Name Extraction**

Extract all personal names mentioned in the document including:
- Full names (first name, middle name, last name)
- Professional titles with names (Dr. John Smith, Professor Jane Doe, Mr. Walter Rill)
- Names in signatures, letterheads, or contact information
- Names in CV/resume sections
- Names in correspondence (sender, recipient, cc'd individuals)
- Names in routing slips or memoranda

For each name extracted, provide:
- `name`: The full name as it appears
- `context`: Where the name appears
- `bounding_box`: The coordinates where the name appears
```

### **Updated Output Format:**

```json
{
  "file_title": "...",
  "barcode_no": "...",
  "document_type": "...",
  "exceptions": "...",
  "extracted_names": [
    {
      "name": "Donna Jenloz",
      "context": "mentioned in telegram",
      "bounding_box": [100, 200, 300, 250]
    },
    {
      "name": "Edward V.K. Jaycox",
      "context": "sender",
      "bounding_box": [50, 100, 250, 120]
    }
  ]
}
```

---

## 🚀 **How to Use:**

### **Option 1: Replace Your Current Prompt**

1. **On Databricks**, rename your current file:
   ```
   MasterPromp_V4.md  →  MasterPromp_V4_OLD.md
   ```

2. **Upload** the new file:
   ```
   MasterPrompt_V4_WITH_NAMES.md  →  MasterPromp_V4.md
   ```

3. **Run** `Azure_DI_output_parser_WORKING.py` again

4. **Check output** - should now include `extracted_names`

---

### **Option 2: Test Side-by-Side**

1. **Upload** `MasterPrompt_V4_WITH_NAMES.md` to Databricks

2. **Update the code** to use the new prompt:
   ```python
   # In Azure_DI_output_parser_WORKING.py, line 30:
   filenames = [
       'MasterPrompt_V4_WITH_NAMES.md',  # ← NEW
       'MasterPromp_V4.md',
       ...
   ]
   ```

3. **Run** and compare outputs

---

## 📋 **Expected Output After Update:**

### **Before (current):**
```json
{
  "file_title": "Boke Extension...",
  "document_type": "Incoming wire",
  "exceptions": "Personal Information"
}
```

### **After (with name extraction):**
```json
{
  "file_title": "Boke Extension...",
  "document_type": "Incoming wire",
  "exceptions": "Personal Information",
  "extracted_names": [
    {
      "name": "Donna Jenloz",
      "context": "mentioned in telegram",
      "bounding_box": [100, 200, 300, 250]
    }
  ]
}
```

---

## 🔍 **Validation Update:**

The WORKING version will automatically detect the `extracted_names` field and validate it:

```python
expected_fields = ['file_title', 'document_type', 'exceptions', 'extracted_names']
```

---

## 🎯 **Summary:**

1. ✅ **Created:** `MasterPrompt_V4_WITH_NAMES.md`
2. ✅ **Adds:** Name extraction with context and bounding boxes
3. ✅ **Compatible:** Works with existing classification rules
4. ✅ **Ready:** Upload to Databricks and use

**Upload the new prompt file and run the WORKING version!** 🚀


