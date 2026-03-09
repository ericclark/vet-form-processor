"""AI extraction service - Vertex AI Gemini or mock mode for local dev."""


import json
import logging
import random

from app.config import settings
from app.schemas.ecvi import ExtractionResult

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """You are an expert data extraction agent for the Indiana Board of Animal Health (BOAH).
You are given a scanned image or PDF of a handwritten Certificate of Veterinary Inspection (CVI) form.

Your task is to extract ALL data from this form into the exact JSON structure below.

RULES:
1. Extract every legible field. Use null for fields you cannot read.
2. Dates must be in YYYY-MM-DD format.
3. For MovementPurpose, map to EXACTLY one of: "Racing", "Sale", "Grazing", "Training", "Slaughter", "Medical Treatment", "Exhibition/Show/Rodeo", "Breeding", "Competition", "Feeding to condition", "Feeding to slaughter", "Laying Hens", "Hunting for harvest", "Companion Animal", "Personal Travel/Transit", "Owner relocating", "Evacuation from Natural Disaster", "Other".
4. For SpeciesCode, use official 3-letter USDA codes: AQU, BEF, BIS, CAM, CAN, CAP, CER, CHI, DAI, EQU, FEL, OVI, POR, TUR. If the species doesn't match, leave SpeciesCode null and put the species name in SpeciesOther.
5. For Sex, use exactly: "Female", "Male", "Spayed Female", "Neutered Male", "True Hermaphrodite", "Gender Unknown", or "Other".
6. For animal tags, classify each tag:
   - AIN: starts with "840" followed by 12 digits (15 digits total)
   - NUES9: 2-letter state abbreviation followed by 7 digits (9 characters total)
   - NUES8: 2-letter state abbreviation followed by 6 digits (8 characters total)
   - MfrRFID: starts with "900"-"999" (not 999) followed by 12 digits
   - OtherOfficialID: any other official government ID
   - ManagementID: farm/ranch management tags
7. Evaluate overall legibility. Set is_form_readable to false only if the form is mostly illegible.
8. Score your confidence 0.0-1.0 in overall_confidence_score.
9. List JSON paths of any field where handwriting is ambiguous in low_confidence_fields (e.g., "eCVI.Veterinarian.LastName").
10. State codes must be 2-letter US postal abbreviations (e.g., "IN" for Indiana).

Return ONLY valid JSON matching this structure:
{
  "extraction_metadata": {
    "overall_confidence_score": <float 0.0-1.0>,
    "low_confidence_fields": ["<json path>", ...],
    "is_form_readable": <boolean>
  },
  "eCVI": {
    "CviNumber": "<string or null>",
    "IssueDate": "<YYYY-MM-DD or null>",
    "ExpirationDate": "<YYYY-MM-DD or null>",
    "ShipmentDate": "<YYYY-MM-DD or null>",
    "Veterinarian": {
      "FirstName": "<string or null>",
      "LastName": "<string or null>",
      "LicenseNumber": "<string or null>",
      "NationalAccreditationNumber": "<string or null>",
      "Address": {
        "Line1": "<string or null>",
        "Town": "<string or null>",
        "State": "<2-letter code or null>",
        "ZIP": "<5-digit or null>"
      }
    },
    "MovementPurposes": {
      "Purpose": "<ENUM VALUE or null>",
      "OtherReason": "<string or null>"
    },
    "Origin": {
      "PremId": "<string or null>",
      "PremName": "<string or null>",
      "Address": {
        "Line1": "<string or null>",
        "Town": "<string or null>",
        "State": "<2-letter code or null>",
        "ZIP": "<5-digit or null>"
      }
    },
    "Destination": {
      "PremId": "<string or null>",
      "PremName": "<string or null>",
      "Address": {
        "Line1": "<string or null>",
        "Town": "<string or null>",
        "State": "<2-letter code or null>",
        "ZIP": "<5-digit or null>"
      }
    },
    "Animals": [
      {
        "SpeciesCode": "<3-letter code or null>",
        "SpeciesOther": "<string or null>",
        "Breed": "<string or null>",
        "Age": "<age string or null>",
        "Sex": "<ENUM VALUE or null>",
        "InspectionDate": "<YYYY-MM-DD or null>",
        "Tags": [
          {
            "TagType": "AIN|NUES9|NUES8|MfrRFID|OtherOfficialID|ManagementID",
            "Number": "<string>"
          }
        ]
      }
    ]
  }
}
"""


def _mock_extraction() -> ExtractionResult:
    """Return realistic mock data for local testing."""
    mock_data = {
        "extraction_metadata": {
            "overall_confidence_score": round(random.uniform(0.72, 0.95), 2),
            "low_confidence_fields": [
                "eCVI.Veterinarian.LicenseNumber",
                "eCVI.Animals.0.Tags.0.Number",
            ],
            "is_form_readable": True,
        },
        "eCVI": {
            "CviNumber": f"IN-2026-{random.randint(100000, 999999)}",
            "IssueDate": "2026-03-01",
            "ExpirationDate": "2026-03-31",
            "ShipmentDate": "2026-03-05",
            "Veterinarian": {
                "FirstName": "James",
                "LastName": "Herriot",
                "LicenseNumber": "VET-12345",
                "NationalAccreditationNumber": None,
                "Address": {
                    "Line1": "123 Veterinary Lane",
                    "Town": "Indianapolis",
                    "State": "IN",
                    "ZIP": "46204",
                },
            },
            "MovementPurposes": {
                "Purpose": "Sale",
                "OtherReason": None,
            },
            "Origin": {
                "PremId": "IN1234A",
                "PremName": "Smith Family Farm",
                "Address": {
                    "Line1": "4567 County Road 200 N",
                    "Town": "Lebanon",
                    "State": "IN",
                    "ZIP": "46052",
                },
            },
            "Destination": {
                "PremId": "OH5678B",
                "PremName": "Buckeye Livestock Auction",
                "Address": {
                    "Line1": "890 Market Street",
                    "Town": "Columbus",
                    "State": "OH",
                    "ZIP": "43215",
                },
            },
            "Animals": [
                {
                    "SpeciesCode": "BEF",
                    "SpeciesOther": None,
                    "Breed": "Angus",
                    "Age": "2a",
                    "Sex": "Female",
                    "InspectionDate": "2026-03-01",
                    "Tags": [
                        {"TagType": "AIN", "Number": "840003212345678"},
                        {"TagType": "ManagementID", "Number": "F-201"},
                    ],
                },
                {
                    "SpeciesCode": "BEF",
                    "SpeciesOther": None,
                    "Breed": "Angus",
                    "Age": "3a",
                    "Sex": "Female",
                    "InspectionDate": "2026-03-01",
                    "Tags": [
                        {"TagType": "AIN", "Number": "840003212345679"},
                    ],
                },
                {
                    "SpeciesCode": "BEF",
                    "SpeciesOther": None,
                    "Breed": "Hereford",
                    "Age": "18mo",
                    "Sex": "Male",
                    "InspectionDate": "2026-03-01",
                    "Tags": [
                        {"TagType": "NUES9", "Number": "IN1234567"},
                    ],
                },
            ],
        },
    }
    return ExtractionResult.model_validate(mock_data)


async def extract_from_document(file_bytes: bytes, mime_type: str) -> ExtractionResult:
    """Extract data from a scanned form. Uses mock data in local dev mode."""
    if settings.use_mock_extraction:
        logger.info("Using mock extraction (USE_MOCK_EXTRACTION=true)")
        return _mock_extraction()

    import vertexai
    from vertexai.generative_models import GenerativeModel, Part

    vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)
    model = GenerativeModel(
        settings.gemini_model,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.1,
            "max_output_tokens": 8192,
        },
    )

    document_part = Part.from_data(data=file_bytes, mime_type=mime_type)
    response = model.generate_content([EXTRACTION_PROMPT, document_part])

    raw_text = response.text
    logger.info("Gemini raw response length: %d", len(raw_text))

    parsed = json.loads(raw_text)
    return ExtractionResult.model_validate(parsed)
