import { useState } from "react";
import { Link } from "react-router-dom";
import { searchDocuments } from "../services/api";

interface DocResult {
  id: string;
  original_filename: string;
  status: string;
  overall_confidence: number | null;
  cvi_number: string | null;
  vet_name: string | null;
  issue_date: string | null;
}

export default function SearchPage() {
  const [cviNumber, setCviNumber] = useState("");
  const [vetName, setVetName] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [tagNumber, setTagNumber] = useState("");
  const [results, setResults] = useState<DocResult[]>([]);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    const params: Record<string, string> = {};
    if (cviNumber) params.cvi_number = cviNumber;
    if (vetName) params.vet_name = vetName;
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    if (tagNumber) params.tag_number = tagNumber;

    const res = await searchDocuments(params);
    setResults(res.data);
    setSearched(true);
  };

  return (
    <div className="page">
      <h1>Search Records</h1>
      <div className="search-form">
        <label>CVI Number<input value={cviNumber} onChange={(e) => setCviNumber(e.target.value)} placeholder="e.g. IN-2025-001234" /></label>
        <label>Veterinarian<input value={vetName} onChange={(e) => setVetName(e.target.value)} placeholder="Name" /></label>
        <label>Date From<input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} /></label>
        <label>Date To<input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} /></label>
        <label>Tag Number<input value={tagNumber} onChange={(e) => setTagNumber(e.target.value)} placeholder="e.g. 840003123456789" /></label>
        <button className="btn-primary" onClick={handleSearch}>Search</button>
      </div>

      {searched && (
        <div className="search-results">
          <h3>{results.length} result{results.length !== 1 ? "s" : ""}</h3>
          {results.length > 0 && (
            <table className="doc-table">
              <thead>
                <tr>
                  <th>CVI #</th>
                  <th>Filename</th>
                  <th>Veterinarian</th>
                  <th>Issue Date</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r) => (
                  <tr key={r.id}>
                    <td>{r.cvi_number || "-"}</td>
                    <td>{r.original_filename}</td>
                    <td>{r.vet_name || "-"}</td>
                    <td>{r.issue_date ? new Date(r.issue_date).toLocaleDateString() : "-"}</td>
                    <td><span className="status-badge">{r.status}</span></td>
                    <td><Link to={`/review/${r.id}`} className="btn-sm">View</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
