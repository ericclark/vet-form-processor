import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8080",
});

// --- Batches ---
export const uploadBatch = (files: File[]) => {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  return api.post("/api/batches", form);
};

export const listBatches = () => api.get("/api/batches");

export const getBatch = (id: string) => api.get(`/api/batches/${id}`);

export const listBatchDocuments = (batchId: string) =>
  api.get(`/api/batches/${batchId}/documents`);

// --- Documents ---
export const getDocument = (id: string) => api.get(`/api/documents/${id}`);

export const triggerExtraction = (id: string) =>
  api.post(`/api/documents/${id}/extract`);

export const submitReview = (
  id: string,
  action: "approve" | "unreadable",
  editedData?: unknown
) => api.post(`/api/documents/${id}/review`, { action, edited_data: editedData });

// --- Search ---
export const searchDocuments = (params: Record<string, string>) =>
  api.get("/api/search", { params });

export default api;
