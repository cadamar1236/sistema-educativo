import React from "react";
import RagChatInterface from "./educationalRag/RagChatInterface";
import DocumentLibrary from "./educationalRag/DocumentLibrary";

export default function MainDashboard({ userId }: { userId: string }) {
  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: 32 }}>
      <h1>Dashboard Principal del Sistema Educativo</h1>
      {/* Otros widgets y métricas del dashboard aquí... */}
      <section style={{ marginTop: 32 }}>
        <h2>Chat Educativo RAG</h2>
        <RagChatInterface userId={userId} />
      </section>
      <section style={{ marginTop: 32 }}>
        <h2>Biblioteca Educativa</h2>
        <DocumentLibrary userId={userId} />
      </section>
      {/* Puedes añadir más secciones aquí... */}
    </div>
  );
}
