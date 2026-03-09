import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getBatch, listBatchDocuments, triggerExtraction } from "../services/api";

interface BatchInfo {
  id: string;
  name: string;
  status: string;
  total_documents: number;
  processed_documents: number;
}

interface DocSummary {
  id: string;
  original_filename: string;
  status: string;
  overall_confidence: number | null;
  cvi_number: string | null;
  vet_name: string | null;
}

export default function BatchDetailPage() {
  const { batchId } = useParams<{ batchId: string }>();
  const [batch, setBatch] = useState<BatchInfo | null>(null);
  const [docs, setDocs] = useState<DocSummary[]>([]);
  const [extracting, setExtracting] = useState<Set<string>>(new Set());

  const load = async () => {
    if (!batchId) return;
    const [bRes, dRes] = await Promise.all([
      getBatch(batchId),
      listBatchDocuments(batchId),
    ]);
    setBatch(bRes.data);
    setDocs(dRes.data);
  };

  useEffect(() => {
    load();
  }, [batchId]);

  const handleExtract = async (docId: string) => {
    setExtracting((prev) => new Set(prev).add(docId));
    try {
      await triggerExtraction(docId);
      await load();
    } catch (err) {
      console.error("Extraction failed", err);
    } finally {
      setExtracting((prev) => {
        const next = new Set(prev);
        next.delete(docId);
        return next;
      });
    }
  };

  const handleExtractAll = async () => {
    const pending = docs.filter((d) => d.status === "uploaded");
    for (const doc of pending) {
      await handleExtract(doc.id);
    }
  };

  if (!batch) return <p>Loading...</p>;

  const statusColor = (s: string) => {
    switch (s) {
      case "approved": return "status--approved";
      case "review": return "status--review";
      case "failed": return "status--failed";
      case "unreadable": return "status--failed";
      case "extracting": return "status--extracting";
      default: return "";
    }
  };

  return (
    <div className="page">
      <Link to="/">&larr; All Batches</Link>
      <h1>{batch.name}</h1>
      <p>
        Status: <strong>{batch.status}</strong> | Documents:{" "}
        {batch.processed_documents}/{batch.total_documents}
      </p>

      {docs.some((d) => d.status === "uploaded") && (
        <button className="btn-primary" onClick={handleExtractAll}>
          Extract All Pending
        </button>
      )}

      <table className="doc-table">
        <thead>
          <tr>
            <th>Filename</th>
            <th>Status</th>
            <th>Confidence</th>
            <th>CVI #</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {docs.map((d) => (
            <tr key={d.id}>
              <td>{d.original_filename}</td>
              <td>
                <span className={`status-badge ${statusColor(d.status)}`}>
                  {d.status}
                </span>
              </td>
              <td>
                {d.overall_confidence != null
                  ? `${(d.overall_confidence * 100).toFixed(0)}%`
                  : "-"}
              </td>
              <td>{d.cvi_number || "-"}</td>
              <td>
                {d.status === "uploaded" && (
                  <button
                    className="btn-sm"
                    onClick={() => handleExtract(d.id)}
                    disabled={extracting.has(d.id)}
                  >
                    {extracting.has(d.id) ? "Extracting..." : "Extract"}
                  </button>
                )}
                {d.status === "review" && (
                  <Link to={`/review/${d.id}`} className="btn-sm btn-review">
                    Review
                  </Link>
                )}
                {d.status === "approved" && (
                  <Link to={`/review/${d.id}`} className="btn-sm">
                    View
                  </Link>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
