// Servicio para interactuar con el agente RAG educativo

const BASE_URL = "/api/agents/educational-rag";

export async function uploadDocument(data: {
  user_id: string;
  content: string;
  filename: string;
  category?: string;
  subject?: string;
  level?: string;
}) {
  const res = await fetch(`${BASE_URL}/upload-document`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function searchDocuments(data: {
  user_id: string;
  query: string;
  subject?: string;
  category?: string;
}) {
  const res = await fetch(`${BASE_URL}/search-documents`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function ragQuery(data: {
  user_id: string;
  message: string;
  subject?: string;
  category?: string;
  search_web?: boolean;
}) {
  const res = await fetch(`${BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function getLibraryStats(userId: string) {
  const res = await fetch(`${BASE_URL}/library-stats/${userId}`);
  return res.json();
}
