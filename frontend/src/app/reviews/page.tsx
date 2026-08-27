"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

type Review = {
  thread_id: string;
  shipment_id: string;
  recommended_action: string;
  confidence: number;
  justification: string;
  matched_clauses: Record<string, unknown>[];
  options: string[];
};

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function fetchReviews() {
    try {
      const res = await fetch(`${API_BASE}/reviews`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as Review[];
      setReviews(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  async function submitDecision(threadId: string, decision: string) {
    const res = await fetch(`${API_BASE}/reviews/${threadId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision }),
    });
    if (!res.ok) {
      alert(`Failed: ${res.status}`);
      return;
    }
    await fetchReviews();
  }

  useEffect(() => {
    fetchReviews();
  }, []);

  if (loading) return <main style={{ padding: "2rem" }}>Loading…</main>;
  if (error) return <main style={{ padding: "2rem" }}>Error: {error}</main>;

  return (
    <main style={{ padding: "2rem" }}>
      <h1>Review Queue</h1>
      {reviews.length === 0 ? (
        <p>No pending reviews.</p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0 }}>
          {reviews.map((r) => (
            <li
              key={r.thread_id}
              style={{
                border: "1px solid #ddd",
                borderRadius: "8px",
                padding: "1rem",
                marginBottom: "1rem",
              }}
            >
              <strong>{r.shipment_id}</strong> — recommended action: {" "}
              <code>{r.recommended_action}</code> (confidence: {r.confidence})
              <p>{r.justification}</p>
              <details>
                <summary>Matched clauses</summary>
                <pre style={{ fontSize: "0.8rem" }}>
                  {JSON.stringify(r.matched_clauses, null, 2)}
                </pre>
              </details>
              <div style={{ marginTop: "0.5rem" }}>
                {r.options.map((opt) => (
                  <button
                    key={opt}
                    onClick={() => submitDecision(r.thread_id, opt)}
                    style={{ marginRight: "0.5rem", marginBottom: "0.5rem" }}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
