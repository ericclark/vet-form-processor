# Product Requirements Document: AutoExtract Agent for INBOAH

**Version:** 1.1 (MVP Focus)
**Target Platform:** Google Cloud Platform (GCP)
**AI Engine:** Vertex AI (Gemini 2.5 GA / Gemini 3.1 Preview)

## 1. Executive Summary

**Objective:** Automate the manual data entry process for the Indiana Board of Animal Health (BOAH) by leveraging state-of-the-art multimodal AI to extract data from handwritten scanned forms.


**Solution Goal:** A centralized, serverless web application that ingests manually uploaded batches of scanned forms, extracts data using Vertex AI, allows human verification via a Human-in-the-Loop (HITL) interface, and generates compliant XML files for federal reporting based on the eCVI Version 3.1 schema.

## 2. User Personas

* **Data Entry Specialist (Primary):** Uploads daily batches, reviews AI extraction alongside the original scan, corrects errors, and approves forms.
* **System Administrator:** Manages IAP access, monitors Cloud Run health, and handles system exceptions.
* **Compliance Officer:** Searches past records, audits historical batches, and ensures XML output integrity.

## 3. Functional Requirements

### 3.1. Document Ingestion (MVP - Web Upload)

* **Batch Upload UI:** The web interface must provide a secure drag-and-drop zone for users to upload scanned files.
* **Supported Formats:** Individual files (PDF, JPEG, PNG) or a single compressed `.zip` archive.
* **Archive Processing:** If a `.zip` is uploaded, the backend must unpack it, validate MIME types, and reject unsupported files.
* **Batching:** Files uploaded together are grouped into a defined "Batch" (e.g., `Batch_YYYYMMDD_HHMM`) for organized queue management.
* *Note for AI Developer: Email inbox monitoring (MS 365) is explicitly deferred to v2. Do not build email ingestion pipelines.*

### 3.2. AI Extraction Engine

* **Model Integration:** Utilize Vertex AI, specifically targeting `gemini-2.5-pro` (or `gemini-3.1-pro` if available in the project environment) for high-fidelity handwriting recognition.
* **Structured Output:** The model must be configured to return strict `application/json` output matching the eCVI mapping defined in Section 6.
* **Confidence Scoring:** The AI must evaluate handwriting legibility and return an array of JSON paths for fields with low confidence to flag them for human review.

### 3.3. Human-in-the-Loop (HITL) Interface

* **Side-by-Side View:** The UI must render the scanned document (PDF/Image) on the left and the extracted editable data fields on the right.
* **Exception Highlighting:** Any field identified in the AI's `low_confidence_fields` array must be visually highlighted (e.g., red border/background) to force user attention.
* **Workflow:** Users can edit fields, mark a document as "Unreadable" (flagging it for manual offline review), or click "Approve".

### 3.4. XML Generation & eCVI Compliance

* 
**Transformation:** Upon user approval, the backend must transform the JSON payload into an XML document strictly adhering to the `http://www.usaha.org/xmlns/ecvi2` schema.


* 
**Root Element:** The document must wrap the data in the `<eCVI>` root element.


* **Export:** Approved forms are compiled into the required XML format and stored securely for federal transmission.

### 3.5. Repository & Search

* **Central Storage:** All original scans, intermediate JSON, and final XMLs must be retained.
* **Search Portal:** Users can search historical records by `CviNumber`, dates, Veterinarian name, or federal tag IDs.

---

## 4. Technical Architecture (GCP-Native)

The solution must be built using a serverless, event-driven architecture to ensure low maintenance overhead and high scalability.

* **Frontend / UI:** React (or similar modern framework) hosted on **Cloud Run**.
* **Backend API:** Node.js or Python API hosted on **Cloud Run**.
* **Security & Access:** **Cloud Identity-Aware Proxy (IAP)** securing the Cloud Run services, restricting access to authorized state employees via Google Workspace/Cloud Identity.
* **Storage (Files):** **Cloud Storage (GCS)**.
* `boah-staging`: Temporary holding for UI uploads and `.zip` unpacking.
* `boah-raw-forms`: Unpacked, individual PDFs/Images ready for AI.
* `boah-archive`: Final XMLs and historical PDFs.


* **Storage (Relational Data):** **Cloud SQL (PostgreSQL)**. Stores document metadata, user audit logs, batch statuses, and the structured JSON extracted by Gemini to power the search UI.
* **Event Orchestration:** **Eventarc** to trigger Cloud Functions/Cloud Run endpoints when new files land in GCS buckets.

---

## 5. Schema Rules & Data Mapping Constraints

The AI extraction prompt and backend XML generator must strictly enforce these rules based on the provided XSD:

* 
**Veterinarian:** Must represent a natural person  (split into First/Last name). Include `LicenseNumber` if available.


* 
**Addresses (Origin/Destination):** `Origin` and `Destination` elements must be physical (911) addresses.


* 
**Movement Purposes:** Must map to the exact enumerated list: "Racing", "Sale", "Grazing", "Training", "Slaughter", "Medical Treatment", "Exhibition/Show/Rodeo", "Breeding", "Competition", "Feeding to condition", "Feeding to slaughter", "Laying Hens", "Hunting for harvest", "Companion Animal", "Personal Travel/Transit", "Owner relocating", "Evacuation from Natural Disaster", or "Other".


* 
**Species:** Map to official 3-letter codes where possible (e.g., "BEF", "EQU", "POR"). Use `SpeciesOther` if an official code is not applicable.


* **Animal Tags:** Must be extracted and categorized. Recognize AIN (840 + 12 digits) , NUES9 , NUES8 , or categorize as `OtherOfficialID`/`ManagementID`. Up to six IDs per animal are typical, though the schema supports more.



---

## 6. AI Extraction Specification (Vertex AI)

The backend must prompt Gemini 2.5/3.1 using `responseMimeType: "application/json"` and the following required JSON schema structure to ensure deterministic, parsable outputs.

```json
{
  "extraction_metadata": {
    "overall_confidence_score": "float",
    "low_confidence_fields": ["array of string JSON paths"],
    "is_form_readable": "boolean"
  },
  "eCVI": {
    "CviNumber": "string | null",
    "IssueDate": "YYYY-MM-DD | null",
    "Veterinarian": {
      "FirstName": "string | null",
      "LastName": "string | null",
      "LicenseNumber": "string | null",
      "Address": {
        "Line1": "string | null",
        "Town": "string | null",
        "State": "string | null",
        "ZIP": "string | null"
      }
    },
    "MovementPurposes": {
      "Purpose": "ENUM VALUE | null",
      "OtherReason": "string | null"
    },
    "Origin": {
      "Address": {
        "Line1": "string | null",
        "Town": "string | null",
        "State": "string | null",
        "ZIP": "string | null"
      }
    },
    "Destination": {
      "Address": {
        "Line1": "string | null",
        "Town": "string | null",
        "State": "string | null",
        "ZIP": "string | null"
      }
    },
    "Animals": [
      {
        "SpeciesCode": "string | null",
        "SpeciesOther": "string | null",
        "Age": "string | null",
        "Sex": "ENUM VALUE | null",
        "InspectionDate": "YYYY-MM-DD | null",
        "Tags": [
          {
            "TagType": "AIN | NUES9 | NUES8 | OtherOfficialID | ManagementID",
            "Number": "string"
          }
        ]
      }
    ]
  }
}

```
