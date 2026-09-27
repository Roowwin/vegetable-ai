"use client";

import { useEffect, useState } from "react";

type HealthStatus = {
  status: string;
  service: string;
  version: string;
  timestamp: string;
  milestone: string;
};

export default function HomePage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/health")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: HealthStatus) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <main style={{ padding: "2rem", maxWidth: "800px", margin: "0 auto" }}>
      <h1 style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>
        🥬 VeggieOps AI
      </h1>
      <p style={{ color: "#666", fontSize: "1.1rem", marginBottom: "2rem" }}>
        AI-powered backend for vegetable resale businesses
      </p>

      <div
        style={{
          border: "1px solid #e5e5e5",
          borderRadius: "8px",
          padding: "1.5rem",
          marginBottom: "2rem",
          backgroundColor: "#fafafa",
        }}
      >
        <h2 style={{ marginTop: 0, fontSize: "1.25rem" }}>Backend Status</h2>

        {loading && <p>⏳ Checking backend...</p>}
        {error && <p style={{ color: "red" }}>❌ Backend unreachable: {error}</p>}

        {health && (
          <div>
            <p>
              <strong>Status:</strong>{" "}
              <span style={{ color: "green" }}>● {health.status}</span>
            </p>
            <p><strong>Service:</strong> {health.service}</p>
            <p><strong>Version:</strong> {health.version}</p>
            <p><strong>Milestone:</strong> {health.milestone}</p>
            <p style={{ fontSize: "0.85rem", color: "#888" }}>
              Last check: {new Date(health.timestamp).toLocaleString()}
            </p>
          </div>
        )}
      </div>

      <div
        style={{
          borderTop: "1px solid #e5e5e5",
          paddingTop: "1rem",
          color: "#666",
          fontSize: "0.9rem",
        }}
      >
        <p>Milestone 2 Part C — Next.js Frontend</p>
        <p>Coming soon: AI chat, analytics dashboard, forecasting (Milestones 10+)</p>
      </div>
    </main>
  );
}