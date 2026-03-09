import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getDocument, submitReview } from "../services/api";

interface Address {
  Line1?: string | null;
  Line2?: string | null;
  Town?: string | null;
  County?: string | null;
  State?: string | null;
  ZIP?: string | null;
}

interface VetInfo {
  FirstName?: string | null;
  LastName?: string | null;
  LicenseNumber?: string | null;
  NationalAccreditationNumber?: string | null;
  Address?: Address | null;
}

interface AnimalTag {
  TagType: string;
  Number: string;
}

interface AnimalInfo {
  SpeciesCode?: string | null;
  SpeciesOther?: string | null;
  Breed?: string | null;
  Age?: string | null;
  Sex?: string | null;
  InspectionDate?: string | null;
  Tags: AnimalTag[];
}

interface ECVIData {
  CviNumber?: string | null;
  IssueDate?: string | null;
  ExpirationDate?: string | null;
  ShipmentDate?: string | null;
  Veterinarian?: VetInfo | null;
  MovementPurposes?: { Purpose?: string | null; OtherReason?: string | null } | null;
  Origin?: { PremId?: string | null; PremName?: string | null; Address?: Address | null } | null;
  Destination?: { PremId?: string | null; PremName?: string | null; Address?: Address | null } | null;
  Animals: AnimalInfo[];
}

const MOVEMENT_PURPOSES = [
  "Racing", "Sale", "Grazing", "Training", "Slaughter", "Medical Treatment",
  "Exhibition/Show/Rodeo", "Breeding", "Competition", "Feeding to condition",
  "Feeding to slaughter", "Laying Hens", "Hunting for harvest", "Companion Animal",
  "Personal Travel/Transit", "Owner relocating", "Evacuation from Natural Disaster", "Other",
];

const SEX_OPTIONS = [
  "Female", "Male", "Spayed Female", "Neutered Male",
  "True Hermaphrodite", "Gender Unknown", "Other",
];

export default function ReviewPage() {
  const { docId } = useParams<{ docId: string }>();
  const navigate = useNavigate();
  const [doc, setDoc] = useState<any>(null);
  const [data, setData] = useState<ECVIData | null>(null);
  const [lowConfidence, setLowConfidence] = useState<Set<string>>(new Set());
  const [submitting, setSubmitting] = useState(false);
  const [xmlOutput, setXmlOutput] = useState<string | null>(null);

  useEffect(() => {
    if (!docId) return;
    getDocument(docId).then((res) => {
      const d = res.data;
      setDoc(d);
      // Use approved_json if available, otherwise pull from extracted_json
      const ecviSource = d.approved_json || d.extracted_json?.eCVI;
      if (ecviSource) {
        setData(ecviSource);
      }
      if (d.low_confidence_fields) {
        setLowConfidence(new Set(d.low_confidence_fields));
      }
      if (d.xml_output) {
        setXmlOutput(d.xml_output);
      }
    });
  }, [docId]);

  const isLowConf = (path: string) => {
    for (const lc of lowConfidence) {
      if (lc.includes(path)) return true;
    }
    return false;
  };

  const fieldClass = (path: string) =>
    isLowConf(path) ? "field-input field-input--low-confidence" : "field-input";

  const updateField = (path: string[], value: string) => {
    if (!data) return;
    const updated = JSON.parse(JSON.stringify(data));
    let obj: any = updated;
    for (let i = 0; i < path.length - 1; i++) {
      if (obj[path[i]] == null) obj[path[i]] = {};
      obj = obj[path[i]];
    }
    obj[path[path.length - 1]] = value || null;
    setData(updated);
  };

  const updateAnimalField = (idx: number, field: string, value: string) => {
    if (!data) return;
    const updated = JSON.parse(JSON.stringify(data));
    updated.Animals[idx][field] = value || null;
    setData(updated);
  };

  const updateTagField = (animalIdx: number, tagIdx: number, field: string, value: string) => {
    if (!data) return;
    const updated = JSON.parse(JSON.stringify(data));
    updated.Animals[animalIdx].Tags[tagIdx][field] = value;
    setData(updated);
  };

  const handleApprove = async () => {
    if (!docId || !data) return;
    setSubmitting(true);
    try {
      const res = await submitReview(docId, "approve", data);
      setXmlOutput(res.data.xml);
      setDoc({ ...doc, status: "approved" });
    } catch (err: any) {
      alert(err.response?.data?.detail || "Approval failed");
    } finally {
      setSubmitting(false);
    }
  };

  const handleUnreadable = async () => {
    if (!docId) return;
    setSubmitting(true);
    try {
      await submitReview(docId, "unreadable");
      navigate(-1);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed");
    } finally {
      setSubmitting(false);
    }
  };

  if (!doc || !data) return <p>Loading...</p>;

  const isReadonly = doc.status === "approved";

  return (
    <div className="page review-page">
      <div className="review-layout">
        {/* Left: Document Viewer */}
        <div className="review-viewer">
          <h2>Original Document</h2>
          {doc.gcs_raw_uri ? (
            doc.original_filename?.toLowerCase().endsWith(".pdf") ? (
              <iframe
                src={`${import.meta.env.VITE_API_URL || "http://localhost:8080"}/api/documents/${docId}/file`}
                className="doc-iframe"
                title="Scanned document"
              />
            ) : (
              <img
                src={`${import.meta.env.VITE_API_URL || "http://localhost:8080"}/api/documents/${docId}/file`}
                className="doc-image"
                alt="Scanned document"
              />
            )
          ) : (
            <div className="viewer-placeholder">
              <p>No document file available</p>
              <p className="filename">{doc.original_filename}</p>
            </div>
          )}
        </div>

        {/* Right: Editable Form */}
        <div className="review-form">
          <h2>Extracted Data</h2>
          {doc.overall_confidence != null && (
            <p className="confidence-badge">
              Confidence: {(doc.overall_confidence * 100).toFixed(0)}%
            </p>
          )}

          <fieldset>
            <legend>Certificate Info</legend>
            <label>
              CVI Number
              <input
                className={fieldClass("CviNumber")}
                value={data.CviNumber || ""}
                onChange={(e) => updateField(["CviNumber"], e.target.value)}
                readOnly={isReadonly}
              />
            </label>
            <label>
              Issue Date
              <input
                type="date"
                className={fieldClass("IssueDate")}
                value={data.IssueDate || ""}
                onChange={(e) => updateField(["IssueDate"], e.target.value)}
                readOnly={isReadonly}
              />
            </label>
            <label>
              Expiration Date
              <input
                type="date"
                className={fieldClass("ExpirationDate")}
                value={data.ExpirationDate || ""}
                onChange={(e) => updateField(["ExpirationDate"], e.target.value)}
                readOnly={isReadonly}
              />
            </label>
          </fieldset>

          <fieldset>
            <legend>Veterinarian</legend>
            <label>
              First Name
              <input
                className={fieldClass("Veterinarian.FirstName")}
                value={data.Veterinarian?.FirstName || ""}
                onChange={(e) => updateField(["Veterinarian", "FirstName"], e.target.value)}
                readOnly={isReadonly}
              />
            </label>
            <label>
              Last Name
              <input
                className={fieldClass("Veterinarian.LastName")}
                value={data.Veterinarian?.LastName || ""}
                onChange={(e) => updateField(["Veterinarian", "LastName"], e.target.value)}
                readOnly={isReadonly}
              />
            </label>
            <label>
              License #
              <input
                className={fieldClass("Veterinarian.LicenseNumber")}
                value={data.Veterinarian?.LicenseNumber || ""}
                onChange={(e) => updateField(["Veterinarian", "LicenseNumber"], e.target.value)}
                readOnly={isReadonly}
              />
            </label>
            <div className="address-group">
              <label>
                Address
                <input
                  className={fieldClass("Veterinarian.Address.Line1")}
                  value={data.Veterinarian?.Address?.Line1 || ""}
                  onChange={(e) => updateField(["Veterinarian", "Address", "Line1"], e.target.value)}
                  readOnly={isReadonly}
                />
              </label>
              <label>
                City
                <input
                  value={data.Veterinarian?.Address?.Town || ""}
                  onChange={(e) => updateField(["Veterinarian", "Address", "Town"], e.target.value)}
                  readOnly={isReadonly}
                />
              </label>
              <label>
                State
                <input
                  value={data.Veterinarian?.Address?.State || ""}
                  onChange={(e) => updateField(["Veterinarian", "Address", "State"], e.target.value)}
                  maxLength={2}
                  readOnly={isReadonly}
                />
              </label>
              <label>
                ZIP
                <input
                  value={data.Veterinarian?.Address?.ZIP || ""}
                  onChange={(e) => updateField(["Veterinarian", "Address", "ZIP"], e.target.value)}
                  maxLength={10}
                  readOnly={isReadonly}
                />
              </label>
            </div>
          </fieldset>

          <fieldset>
            <legend>Movement Purpose</legend>
            <select
              className={fieldClass("MovementPurposes.Purpose")}
              value={data.MovementPurposes?.Purpose || ""}
              onChange={(e) => updateField(["MovementPurposes", "Purpose"], e.target.value)}
              disabled={isReadonly}
            >
              <option value="">-- Select --</option>
              {MOVEMENT_PURPOSES.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
            {data.MovementPurposes?.Purpose === "Other" && (
              <label>
                Other Reason
                <input
                  value={data.MovementPurposes?.OtherReason || ""}
                  onChange={(e) => updateField(["MovementPurposes", "OtherReason"], e.target.value)}
                  readOnly={isReadonly}
                />
              </label>
            )}
          </fieldset>

          {/* Origin */}
          <fieldset>
            <legend>Origin</legend>
            <label>
              Premises Name
              <input
                value={data.Origin?.PremName || ""}
                onChange={(e) => updateField(["Origin", "PremName"], e.target.value)}
                readOnly={isReadonly}
              />
            </label>
            <div className="address-group">
              <label>Address<input className={fieldClass("Origin.Address.Line1")} value={data.Origin?.Address?.Line1 || ""} onChange={(e) => updateField(["Origin", "Address", "Line1"], e.target.value)} readOnly={isReadonly} /></label>
              <label>City<input value={data.Origin?.Address?.Town || ""} onChange={(e) => updateField(["Origin", "Address", "Town"], e.target.value)} readOnly={isReadonly} /></label>
              <label>State<input value={data.Origin?.Address?.State || ""} onChange={(e) => updateField(["Origin", "Address", "State"], e.target.value)} maxLength={2} readOnly={isReadonly} /></label>
              <label>ZIP<input value={data.Origin?.Address?.ZIP || ""} onChange={(e) => updateField(["Origin", "Address", "ZIP"], e.target.value)} maxLength={10} readOnly={isReadonly} /></label>
            </div>
          </fieldset>

          {/* Destination */}
          <fieldset>
            <legend>Destination</legend>
            <label>
              Premises Name
              <input
                value={data.Destination?.PremName || ""}
                onChange={(e) => updateField(["Destination", "PremName"], e.target.value)}
                readOnly={isReadonly}
              />
            </label>
            <div className="address-group">
              <label>Address<input className={fieldClass("Destination.Address.Line1")} value={data.Destination?.Address?.Line1 || ""} onChange={(e) => updateField(["Destination", "Address", "Line1"], e.target.value)} readOnly={isReadonly} /></label>
              <label>City<input value={data.Destination?.Address?.Town || ""} onChange={(e) => updateField(["Destination", "Address", "Town"], e.target.value)} readOnly={isReadonly} /></label>
              <label>State<input value={data.Destination?.Address?.State || ""} onChange={(e) => updateField(["Destination", "Address", "State"], e.target.value)} maxLength={2} readOnly={isReadonly} /></label>
              <label>ZIP<input value={data.Destination?.Address?.ZIP || ""} onChange={(e) => updateField(["Destination", "Address", "ZIP"], e.target.value)} maxLength={10} readOnly={isReadonly} /></label>
            </div>
          </fieldset>

          {/* Animals */}
          <fieldset>
            <legend>Animals ({data.Animals?.length || 0})</legend>
            {data.Animals?.map((animal, aIdx) => (
              <div key={aIdx} className="animal-card">
                <h4>Animal #{aIdx + 1}</h4>
                <div className="animal-fields">
                  <label>Species Code<input value={animal.SpeciesCode || ""} onChange={(e) => updateAnimalField(aIdx, "SpeciesCode", e.target.value)} readOnly={isReadonly} /></label>
                  <label>Species Other<input value={animal.SpeciesOther || ""} onChange={(e) => updateAnimalField(aIdx, "SpeciesOther", e.target.value)} readOnly={isReadonly} /></label>
                  <label>Breed<input value={animal.Breed || ""} onChange={(e) => updateAnimalField(aIdx, "Breed", e.target.value)} readOnly={isReadonly} /></label>
                  <label>Age<input value={animal.Age || ""} onChange={(e) => updateAnimalField(aIdx, "Age", e.target.value)} readOnly={isReadonly} /></label>
                  <label>Sex
                    <select value={animal.Sex || ""} onChange={(e) => updateAnimalField(aIdx, "Sex", e.target.value)} disabled={isReadonly}>
                      <option value="">--</option>
                      {SEX_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </label>
                  <label>Inspection Date<input type="date" value={animal.InspectionDate || ""} onChange={(e) => updateAnimalField(aIdx, "InspectionDate", e.target.value)} readOnly={isReadonly} /></label>
                </div>
                <div className="tags-section">
                  <strong>Tags:</strong>
                  {animal.Tags?.map((tag, tIdx) => (
                    <div key={tIdx} className="tag-row">
                      <select value={tag.TagType} onChange={(e) => updateTagField(aIdx, tIdx, "TagType", e.target.value)} disabled={isReadonly}>
                        <option value="AIN">AIN</option>
                        <option value="NUES9">NUES9</option>
                        <option value="NUES8">NUES8</option>
                        <option value="MfrRFID">MfrRFID</option>
                        <option value="OtherOfficialID">OtherOfficialID</option>
                        <option value="ManagementID">ManagementID</option>
                      </select>
                      <input value={tag.Number} onChange={(e) => updateTagField(aIdx, tIdx, "Number", e.target.value)} readOnly={isReadonly} />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </fieldset>

          {/* Actions */}
          {!isReadonly && (
            <div className="review-actions">
              <button className="btn-primary" onClick={handleApprove} disabled={submitting}>
                {submitting ? "Submitting..." : "Approve"}
              </button>
              <button className="btn-danger" onClick={handleUnreadable} disabled={submitting}>
                Mark Unreadable
              </button>
            </div>
          )}

          {/* XML Output */}
          {xmlOutput && (
            <fieldset>
              <legend>Generated XML</legend>
              <pre className="xml-output">{xmlOutput}</pre>
            </fieldset>
          )}
        </div>
      </div>
    </div>
  );
}
