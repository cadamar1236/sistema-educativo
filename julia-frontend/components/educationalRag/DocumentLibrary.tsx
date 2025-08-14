import React, { useState } from "react";
import { useEducationalRag } from "../../hooks/useEducationalRag";

export default function DocumentLibrary({ userId }: { userId: string }) {
  const { loading, result, upload, search, stats } = useEducationalRag();
  const [form, setForm] = useState({
    filename: "",
    content: "",
    category: "",
    subject: "",
    level: "",
  });
  const [searchQuery, setSearchQuery] = useState("");

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    upload({ user_id: userId, ...form });
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    search({ user_id: userId, query: searchQuery });
  }

  function handleStats() {
    stats(userId);
  }

  return (
    <div>
      <h2>Biblioteca Educativa RAG</h2>
      <form onSubmit={handleUpload}>
        <input name="filename" placeholder="Nombre del archivo" value={form.filename} onChange={handleChange} />
        <textarea name="content" placeholder="Contenido" value={form.content} onChange={handleChange} />
        <input name="category" placeholder="Categoría" value={form.category} onChange={handleChange} />
        <input name="subject" placeholder="Materia" value={form.subject} onChange={handleChange} />
        <input name="level" placeholder="Nivel" value={form.level} onChange={handleChange} />
        <button type="submit" disabled={loading}>Subir documento</button>
      </form>
      <form onSubmit={handleSearch}>
        <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)} placeholder="Buscar en documentos" />
        <button type="submit" disabled={loading}>Buscar</button>
      </form>
      <button onClick={handleStats} disabled={loading}>Ver estadísticas de biblioteca</button>
      {loading && <p>Cargando...</p>}
      {result && (
        <pre style={{ background: "#f4f4f4", padding: "1em" }}>{JSON.stringify(result, null, 2)}</pre>
      )}
    </div>
  );
}
