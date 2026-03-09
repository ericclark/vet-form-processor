import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listBatches } from "../services/api";

interface BatchInfo {
  id: string;
  name: string;
  status: string;
  total_documents: number;
  processed_documents: number;
  created_at: string;
}

export default function BatchListPage() {
  const [batches, setBatches] = useState<BatchInfo[]>([]);

  useEffect(() => {
    listBatches().then((res) => setBatches(res.data));
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <h1>Batches</h1>
        <Link to="/upload" className="btn-primary">Upload New Batch</Link>
      </div>

      {batches.length === 0 ? (
        <p>No batches yet. <Link to="/upload">Upload your first batch</Link>.</p>
      ) : (
        <table className="doc-table">
          <thead>
            <tr>
              <th>Batch Name</th>
              <th>Status</th>
              <th>Progress</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {batches.map((b) => (
              <tr key={b.id}>
                <td><Link to={`/batches/${b.id}`}>{b.name}</Link></td>
                <td><span className="status-badge">{b.status}</span></td>
                <td>{b.processed_documents}/{b.total_documents}</td>
                <td>{new Date(b.created_at).toLocaleString()}</td>
                <td><Link to={`/batches/${b.id}`} className="btn-sm">View</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
