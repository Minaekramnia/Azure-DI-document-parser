# 🔍 STEP 1: Find the Prompt File Location

## 📋 **Instructions:**

### **1. Upload `find_prompt.py` to Databricks**

### **2. Run it:**
```python
%run /Workspace/Users/your_username/find_prompt.py
```

Or just:
```python
python find_prompt.py
```

---

## 📊 **What It Will Show You:**

```
================================================================================
🔍 SEARCHING FOR MasterPrompt_V4.md
================================================================================

1️⃣ Trying specific paths:
--------------------------------------------------------------------------------
Checking: /Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/MasterPrompt_V4.md
✅ FOUND at: /Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/MasterPrompt_V4.md
   File size: 7631 characters
   First 100 chars: System Role 
You are an Archivist reviewing documents for declassification. Follow the ru

🎯 USE THIS PATH IN YOUR CODE:
   '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/MasterPrompt_V4.md'

2️⃣ Searching with glob patterns:
...

3️⃣ Looking for ANY MasterPrompt files:
✅ Found in /Volumes/qa_datascience_convaiqa/.../PI/:
   /Volumes/.../PI/MasterPrompt_V4.md
   /Volumes/.../PI/MasterPrompt_V3.md
   /Volumes/.../PI/prompt_v3.md

4️⃣ Checking current working directory:
Current directory: /Workspace/Users/your_username
✅ Found prompt-related files:
   prompt_v3.md
   MasterPrompt_V4.md

5️⃣ Checking the PI directory contents:
Listing: /Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/
✅ Directory exists, contains 25 files

Prompt-related files found:
   MasterPrompt_V4.md (7631 bytes)
   prompt_v3.md (8200 bytes)

First 20 files in directory:
   MasterPrompt_V4.md
   Personal_Information_1.pdf.json
   Personal_Information_2.pdf.json
   ...

================================================================================
🎯 SUMMARY
================================================================================
Copy the correct path from above and use it in your code!
================================================================================
```

---

## 🎯 **What to Do Next:**

### **Once you find the path, send me:**

1. The **exact path** where `MasterPrompt_V4.md` was found
2. The **file size** (in characters)
3. The **first 100 characters** of the file

Then I'll update the code to use the correct path!

---

## 🔍 **Common Scenarios:**

### **Scenario 1: File is in the volume path**
```
✅ FOUND at: /Volumes/.../PI/MasterPrompt_V4.md
```
**→ This is the expected path, code should work!**

### **Scenario 2: File is in workspace**
```
✅ FOUND at: /Workspace/Users/your_user/MasterPrompt_V4.md
```
**→ I'll update the code to check workspace path**

### **Scenario 3: File has different name**
```
✅ Found in /Volumes/.../PI/:
   prompt_v3.md (8200 bytes)
   MasterPrompt_V3.md (7500 bytes)
```
**→ Tell me which file to use and I'll update the code**

### **Scenario 4: File not found anywhere**
```
❌ No prompt files found in this directory
```
**→ We need to upload MasterPrompt_V4.md to Databricks first**

---

## 🚀 **Quick Start:**

1. Upload `find_prompt.py` to Databricks
2. Run it
3. Look for the line that says: **"🎯 USE THIS PATH IN YOUR CODE:"**
4. Copy that path
5. Send it to me
6. I'll fix the FINAL.py code

**This will take 30 seconds and solve the path issue!** ✅


