import React, { useState } from "react";
import { useEducationalRag } from "../../hooks/useEducationalRag";

export default function RagChatInterface({ userId }: { userId: string }) {
  const { loading, result, query } = useEducationalRag();
  const [message, setMessage] = useState("");
  const [subject, setSubject] = useState("");
  const [category, setCategory] = useState("");
  const [searchWeb, setSearchWeb] = useState(true);
  const [history, setHistory] = useState<any[]>([]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const data = {
      user_id: userId,
      message,
      subject,
      category,
      search_web: searchWeb,
    };
    await query(data);
    setHistory((h) => [...h, { role: "user", content: message }]);
    setMessage("");
  }

  React.useEffect(() => {
    if (result && result.response) {
      setHistory((h) => [...h, { role: "agent", content: result.response }]);
    }
  }, [result]);

  return (
    <div style={{ maxWidth: 600, margin: "0 auto" }}>
      <h2>Chat Educativo RAG</h2>
      <form onSubmit={handleSend} style={{ marginBottom: 16 }}>
        <input
          value={message}
          onChange={e => setMessage(e.target.value)}
          placeholder="Escribe tu consulta educativa..."
          style={{ width: "100%", marginBottom: 8 }}
        />
        <input
          value={subject}
          onChange={e => setSubject(e.target.value)}
          placeholder="Materia (opcional)"
          style={{ width: "100%", marginBottom: 8 }}
        />
        <input
          value={category}
          onChange={e => setCategory(e.target.value)}
          placeholder="Categoría (opcional)"
          style={{ width: "100%", marginBottom: 8 }}
        />
        <label style={{ display: "block", marginBottom: 8 }}>
          <input
            type="checkbox"
            checked={searchWeb}
            onChange={e => setSearchWeb(e.target.checked)}
          /> Buscar en web
        </label>
        <button type="submit" disabled={loading || !message}>
          {loading ? "Enviando..." : "Enviar"}
        </button>
      </form>
      <div style={{ background: "#f9f9f9", padding: 16, borderRadius: 8 }}>
        {history.map((msg, i) => (
          <div key={i} style={{ marginBottom: 12 }}>
            <strong>{msg.role === "user" ? "Tú" : "RAG"}:</strong>
            <div style={{ whiteSpace: "pre-wrap" }}>{msg.content}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
