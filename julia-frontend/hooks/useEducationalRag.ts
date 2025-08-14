import { useState } from "react";
import {
  uploadDocument,
  searchDocuments,
  ragQuery,
  getLibraryStats,
} from "../lib/educationalRagService";

export function useEducationalRag() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  async function upload(data: any) {
    setLoading(true);
    const res = await uploadDocument(data);
    setResult(res);
    setLoading(false);
  }

  async function search(data: any) {
    setLoading(true);
    const res = await searchDocuments(data);
    setResult(res);
    setLoading(false);
  }

  async function query(data: any) {
    setLoading(true);
    const res = await ragQuery(data);
    setResult(res);
    setLoading(false);
  }

  async function stats(userId: string) {
    setLoading(true);
    const res = await getLibraryStats(userId);
    setResult(res);
    setLoading(false);
  }

  return { loading, result, upload, search, query, stats };
}
