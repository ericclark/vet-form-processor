"""Generate eCVI v3.1 compliant XML from approved extraction data."""


from lxml import etree

from app.schemas.ecvi import ECVIData

ECVI_NS = "http://www.usaha.org/xmlns/ecvi2"
SCHEMA_VERSION = "3.1"
NSMAP = {None: ECVI_NS}


def _el(parent, tag, text=None, **attribs):
    """Create a child element with optional text and attributes."""
    elem = etree.SubElement(parent, tag, **{k: v for k, v in attribs.items() if v is not None})
    if text is not None:
        elem.text = text
    return elem


def _build_us_address(parent, addr):
    """Build a USAddress complex type under parent."""
    if addr is None:
        return
    addr_el = _el(parent, "Address")
    if addr.Line1:
        _el(addr_el, "Line1", addr.Line1)
    if addr.Town:
        _el(addr_el, "Town", addr.Town)
    if addr.County:
        _el(addr_el, "County", addr.County)
    if addr.State:
        _el(addr_el, "State", addr.State)
    if addr.ZIP:
        _el(addr_el, "ZIP", addr.ZIP)


def _build_international_address(parent, addr):
    """Build an InternationalAddress complex type under parent (used for Veterinarian)."""
    if addr is None:
        return
    addr_el = _el(parent, "Address")
    if addr.Line1:
        _el(addr_el, "Line1", addr.Line1)
    if addr.Town:
        _el(addr_el, "Town", addr.Town)
    if addr.State:
        _el(addr_el, "State", addr.State)
    if addr.ZIP:
        _el(addr_el, "ZIP", addr.ZIP)


def generate_ecvi_xml(data: ECVIData) -> str:
    """Transform approved ECVIData into an eCVI v3.1 XML string."""

    # Compute ExpirationDate: default to 30 days after IssueDate if not provided
    expiration = data.ExpirationDate
    if not expiration and data.IssueDate:
        from datetime import datetime, timedelta
        try:
            issue_dt = datetime.strptime(data.IssueDate, "%Y-%m-%d")
            expiration = (issue_dt + timedelta(days=30)).strftime("%Y-%m-%d")
        except ValueError:
            expiration = data.IssueDate

    # Root eCVI element
    root = etree.Element(
        "eCVI",
        nsmap=NSMAP,
        XMLSchemaVersion=SCHEMA_VERSION,
        CviNumber=data.CviNumber or "UNKNOWN",
        IssueDate=data.IssueDate or "1900-01-01",
        ExpirationDate=expiration or "1900-01-01",
    )
    if data.ShipmentDate:
        root.set("ShipmentDate", data.ShipmentDate)

    # Veterinarian (required)
    vet = data.Veterinarian
    vet_el = _el(root, "Veterinarian")
    if vet and vet.LicenseNumber:
        vet_el.set("LicenseNumber", vet.LicenseNumber)
    if vet and vet.NationalAccreditationNumber:
        vet_el.set("NationalAccreditationNumber", vet.NationalAccreditationNumber)

    person_el = _el(vet_el, "Person")
    name_parts = _el(person_el, "NameParts")
    _el(name_parts, "FirstName", (vet.FirstName if vet else None) or "Unknown")
    _el(name_parts, "LastName", (vet.LastName if vet else None) or "Unknown")

    if vet and vet.Address:
        _build_international_address(vet_el, vet.Address)

    # MovementPurposes (required, can be empty list)
    mp = data.MovementPurposes
    mp_el = _el(root, "MovementPurposes")
    if mp and mp.Purpose:
        _el(mp_el, "MovementPurpose", mp.Purpose.value if hasattr(mp.Purpose, "value") else str(mp.Purpose))
    if mp and mp.OtherReason:
        _el(mp_el, "OtherReason", mp.OtherReason)

    # Origin (required)
    origin = data.Origin
    origin_el = _el(root, "Origin")
    if origin and origin.PremId:
        _el(origin_el, "PremId", origin.PremId)
    if origin and origin.PremName:
        _el(origin_el, "PremName", origin.PremName)
    if origin and origin.Address:
        _build_us_address(origin_el, origin.Address)
    else:
        # Address is required in PremType - add minimal placeholder
        addr_el = _el(origin_el, "Address")
        _el(addr_el, "State", "IN")

    # Destination (required)
    dest = data.Destination
    dest_el = _el(root, "Destination")
    if dest and dest.PremId:
        _el(dest_el, "PremId", dest.PremId)
    if dest and dest.PremName:
        _el(dest_el, "PremName", dest.PremName)
    if dest and dest.Address:
        _build_us_address(dest_el, dest.Address)
    else:
        addr_el = _el(dest_el, "Address")
        _el(addr_el, "State", "IN")

    # Animals
    for animal in data.Animals:
        animal_el = _el(root, "Animal")

        # InspectionDate is required on Animal
        inspection_date = animal.InspectionDate or data.IssueDate or "1900-01-01"
        animal_el.set("InspectionDate", inspection_date)

        if animal.Age:
            animal_el.set("Age", animal.Age)
        if animal.Breed:
            animal_el.set("Breed", animal.Breed)
        if animal.Sex:
            sex_val = animal.Sex.value if hasattr(animal.Sex, "value") else str(animal.Sex)
            animal_el.set("Sex", sex_val)

        # Species (choice: SpeciesCode or SpeciesOther)
        if animal.SpeciesCode:
            sc_el = _el(animal_el, "SpeciesCode")
            sc_el.set("Code", animal.SpeciesCode)
        elif animal.SpeciesOther:
            _el(animal_el, "SpeciesOther", animal.SpeciesOther)
        else:
            _el(animal_el, "SpeciesOther", "Unknown")

        # AnimalTags (required, at least one)
        tags_el = _el(animal_el, "AnimalTags")
        if animal.Tags:
            for tag in animal.Tags:
                tag_type = tag.TagType.value if hasattr(tag.TagType, "value") else str(tag.TagType)
                if tag_type == "AIN":
                    _el(tags_el, "AIN", Number=tag.Number)
                elif tag_type == "NUES9":
                    _el(tags_el, "NUES9", Number=tag.Number)
                elif tag_type == "NUES8":
                    _el(tags_el, "NUES8", Number=tag.Number)
                elif tag_type == "MfrRFID":
                    _el(tags_el, "MfrRFID", Number=tag.Number)
                elif tag_type == "OtherOfficialID":
                    _el(tags_el, "OtherOfficialID", Number=tag.Number)
                elif tag_type == "ManagementID":
                    _el(tags_el, "ManagementID", Number=tag.Number)
                else:
                    _el(tags_el, "ManagementID", Number=tag.Number)
        else:
            _el(tags_el, "ManagementID", Number="NONE")

    # If no animals at all, we still need at least one (schema requires choice of Animal/GroupLot/Product)
    if not data.Animals:
        animal_el = _el(root, "Animal", InspectionDate=data.IssueDate or "1900-01-01")
        _el(animal_el, "SpeciesOther", "Unknown")
        tags_el = _el(animal_el, "AnimalTags")
        _el(tags_el, "ManagementID", Number="NONE")

    # Serialize
    xml_bytes = etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )
    return xml_bytes.decode("UTF-8")
