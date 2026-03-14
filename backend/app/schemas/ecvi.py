"""Pydantic schemas matching the PRD Section 6 AI extraction spec and eCVI v3.1 XSD."""

from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, Field


class MovementPurpose(str, Enum):
    RACING = "Racing"
    SALE = "Sale"
    GRAZING = "Grazing"
    TRAINING = "Training"
    SLAUGHTER = "Slaughter"
    MEDICAL_TREATMENT = "Medical Treatment"
    EXHIBITION = "Exhibition/Show/Rodeo"
    BREEDING = "Breeding"
    COMPETITION = "Competition"
    FEEDING_CONDITION = "Feeding to condition"
    FEEDING_SLAUGHTER = "Feeding to slaughter"
    LAYING_HENS = "Laying Hens"
    HUNTING = "Hunting for harvest"
    COMPANION = "Companion Animal"
    TRAVEL = "Personal Travel/Transit"
    RELOCATING = "Owner relocating"
    EVACUATION = "Evacuation from Natural Disaster"
    OTHER = "Other"


class SexType(str, Enum):
    FEMALE = "Female"
    MALE = "Male"
    SPAYED_FEMALE = "Spayed Female"
    NEUTERED_MALE = "Neutered Male"
    TRUE_HERMAPHRODITE = "True Hermaphrodite"
    GENDER_UNKNOWN = "Gender Unknown"
    OTHER = "Other"


# Use _Schema suffix on class names to avoid field name collisions in Python 3.9
class AddressSchema(BaseModel):
    Line1: Optional[str] = None
    Line2: Optional[str] = None
    Town: Optional[str] = None
    County: Optional[str] = None
    State: Optional[str] = None
    ZIP: Optional[str] = None


class VeterinarianSchema(BaseModel):
    FirstName: Optional[str] = None
    LastName: Optional[str] = None
    LicenseNumber: Optional[str] = None
    NationalAccreditationNumber: Optional[str] = None
    Address: Optional[AddressSchema] = None


class MovementPurposesSchema(BaseModel):
    Purpose: Optional[MovementPurpose] = None
    OtherReason: Optional[str] = None


class LocationSchema(BaseModel):
    PremId: Optional[str] = None
    PremName: Optional[str] = None
    Address: Optional[AddressSchema] = None


class AnimalTag(BaseModel):
    TagType: str
    Number: str


class AnimalSchema(BaseModel):
    HeadCount: Optional[int] = 1
    SpeciesCode: Optional[str] = None
    SpeciesOther: Optional[str] = None
    Breed: Optional[str] = None
    Age: Optional[str] = None
    Sex: Optional[str] = None
    InspectionDate: Optional[str] = None
    Tags: List[AnimalTag] = Field(default_factory=list)


class ECVIData(BaseModel):
    CviNumber: Optional[str] = None
    IssueDate: Optional[str] = None
    ExpirationDate: Optional[str] = None
    ShipmentDate: Optional[str] = None
    PageNumber: Optional[int] = None
    TotalPages: Optional[int] = None
    TotalAnimals: Optional[int] = None
    Veterinarian: Optional[VeterinarianSchema] = None
    MovementPurposes: Optional[MovementPurposesSchema] = None
    Origin: Optional[LocationSchema] = None
    Destination: Optional[LocationSchema] = None
    Animals: List[AnimalSchema] = Field(default_factory=list)


class ExtractionMetadata(BaseModel):
    overall_confidence_score: float = 0.0
    low_confidence_fields: List[str] = Field(default_factory=list)
    is_form_readable: bool = True


class ExtractionResult(BaseModel):
    extraction_metadata: ExtractionMetadata
    eCVI: ECVIData
