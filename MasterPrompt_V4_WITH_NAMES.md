## CLASSIFICATION RULES

### **1. Core Information Types**

#### **1.1 Personal Information**

A document is flagged as **Personal Information** only if it contains a **sensitive data type** that is **explicitly linked** to a specific, identifiable person (e.g., by name or unique ID).

* **Exclusion**: A standalone name, or a name combined only with a physical address, is **not** considered Personal Information on its own. It must be linked to one of the sensitive data types below to be flagged.
* **Human Resources (HR) Actions**: Content detailing specific employment actions (e.g., promotions, performance evaluations, hiring decisions) for a named individual.
* **Internal Investigations & Disputes**: Records concerning a specific misconduct allegation, investigation, or conflict resolution case involving named individuals.
* **Medical and Health Data**: Any information about a named individual's physical or mental health or medical history.
* **Individual Remuneration**: Specific details about a named individual's salary, fees, benefits, or other payments.
* **Evaluative Recommendations**: A formal recommendation or reference that includes evaluative commentary about a named person's performance or character.
* **Unique Personal Identifiers**: The presence of non-public identification numbers such as a UPI (Unique Personal Identifier), Passport number, or UN Laissez-Passer.

#### **1.2 Governors'/Executive Directors' Communications**

* **Rule**: Classify communications to or from a Governor or Executive Director **only if** the content contains explicit markers of sensitivity (e.g., "Confidential," "For Internal Discussion Only," "Embargoed") or discusses non-public negotiations or sensitive policy deliberations.

#### **1.3 Ethics Committee Materials**

* **Rule**: Flag documents that are explicitly titled or labeled as "Ethics Committee Meeting Minutes," "Agenda: Ethics Committee," or contain phrases referring to specific, non-public ethics deliberations or case numbers.

#### **1.4 Attorney–Client Privilege**

* **Rule**: Classify content as privileged if it is sent to/from a designated legal counsel's office **and** contains keywords such as "attorney-client privilege," "legal opinion," "confidential legal advice," or "litigation strategy."

#### **1.5 Security & Safety Information**

* **Rule**: Flag only **specific and non-public** security details, such as travel itineraries linking a person's name to flight numbers or hotel confirmations, or blueprints and access codes for secure, non-public areas.

#### **1.6 Restricted Investigative Info**

* **Rule**: Classify documents explicitly identified by source or title as originating from a restricted unit. Look for labels like "**INT Investigation Report**," "**IEG Final Audit**," or "**Sanctions Committee Finding**."

#### **1.7 Confidential Third-Party Information**

* **Rule**: Flag documents that contain explicit confidentiality markers or legal notices, such as "**Confidential**," "**Under Non-Disclosure Agreement (NDA)**," or "**Third-Party Proprietary Information**."

#### **1.8 Corporate Administrative Matters**

* **Rule**: Target non-public, specific instances of administrative matters, such as an individual's expense report with names and amounts, internal bid evaluations, or a person's private pension statement.

#### **1.9 Financial Information**

* **Rule**: Use pattern matching (regular expressions) to detect the precise, known formats of **Bank Account Numbers (IBAN), SWIFT/BIC codes, and credit card numbers**. Flag specific invoices containing a unique invoice number, a vendor name, and line-item amounts.

---

### **2. Document-Level Classifications**

#### **2.1 CV or Resume Content**

* **Rule**: Flag the document as a CV/Resume if at least two of the following distinct sections are present: personal contact information (email, phone, address); a work history or professional experience section; an education section; a skills or certifications section. The presence of structured headings (e.g., '## Experience') strongly indicates a CV.

#### **2.2 Derogatory or Offensive Language**

* **Rule**: Flag any text that contains unambiguous profanity, slurs, hate speech, or malicious language targeting individuals or groups based on race, gender, sexuality, religion, nationality, appearance, or disability.

---

### **3. Other Sensitive Categories**

#### **3.1 Documents from Specific Entities (IFC, MIGA, INT, IMF)**

* **Rule**: Flag a document if its header, footer, or title explicitly states it is an official, non-public document originating from IFC, MIGA, INT, or IMF (e.g., "IFC Internal Report," "MIGA Board Document"). Do not flag simple mentions of these entities in the body text.

#### **3.2 Joint WBG Documents**

* **Rule**: Flag a document if its title page or header explicitly names multiple World Bank Group entities as co-authors.

#### **3.3 Security-Marked Documents**

* **Rule**: Flag any document containing explicit security markings such as: 'Confidential', 'Strictly Confidential', 'Private', 'Personal', 'Restricted', 'For Your Eyes Only', 'Not for Public Use', 'Official Use Only', 'Secret', or 'Deliberative'.

#### **3.4 Procurement Content**

* **Rule**: Flag specific, non-public procurement documents such as 'Contract Agreement', 'Bid Evaluation Report', 'Procurement Complaint', or official 'Mis-procurement Finding'. Do not flag general discussions of procurement.

---

### **4. Name Extraction**

Extract all personal names mentioned in the document including:
- Full names (first name, middle name, last name)
- Professional titles with names (Dr. John Smith, Professor Jane Doe, Mr. Walter Rill)
- Names in signatures, letterheads, or contact information
- Names in CV/resume sections
- Names in references or endorsements
- Names in legal documents or contracts
- Names in correspondence (sender, recipient, cc'd individuals)
- Names in meeting minutes or attendance lists
- Names in project teams or committee memberships
- Names in routing slips or memoranda

For each name extracted, provide:
- `name`: The full name as it appears
- `context`: Where the name appears (e.g., "signature", "sender", "recipient", "CV header", "routing slip")
- `bounding_box`: The coordinates where the name appears in the document

---

## OUTPUT FORMAT

Return a JSON object with the following structure:

```json
{
  "file_title": "Document title or subject",
  "barcode_no": "Barcode number if present",
  "document_date": "Date in YYYY-MM-DD format",
  "document_type": "Type of document (e.g., CV, Letter, Memorandum, etc.)",
  "correspondents_participants": {
    "from": "Sender name or entity",
    "to": "Recipient name or entity",
    "cc": ["List of CC'd individuals"]
  },
  "subject_title": "Subject or title of the communication",
  "exceptions": "Comma-separated list of exception categories that apply (e.g., 'Personal Information, Attorney-Client Privilege')",
  "withdrawn_by": "Name of person who withdrew/reviewed the document",
  "withdrawal_date": "Date in YYYY-MM-DD format",
  "extracted_names": [
    {
      "name": "Full name as it appears",
      "context": "Where the name appears (e.g., signature, sender, recipient)",
      "bounding_box": [x1, y1, x2, y2]
    }
  ]
}
```

If any field is not applicable or not found, use `null` or an empty array `[]` as appropriate.


