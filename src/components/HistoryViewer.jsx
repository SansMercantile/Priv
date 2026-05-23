// src/components/HistoryViewer.jsx
import React, { useEffect, useState, useCallback } from "react";
import apiClient from '../api/apiClient'; 

export default function HistoryViewer() {
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchHistory = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient("/api/v1/history?limit=100");
      if (Array.isArray(data)) {
        setHistory([...data].reverse());
      } else {
        setHistory([]);
      }
    } catch (err) {
      console.error("Failed to fetch conversation history:", err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  return (
    <div className="max-w-3xl mx-auto p-6 bg-card-bg rounded-lg shadow-custom-medium space-y-4 font-body">
      <h2 className="text-2xl font-bold text-text-primary mb-4 font-display">🧾 Conversation History</h2>
      {isLoading ? <p className="text-text-secondary">Loading history...</p> : 
       error ? <p className="text-accent-bad">{error}</p> : 
       history.length === 0 ? <p className="text-text-secondary">No history found.</p> : (
        <ul className="list-none p-0 m-0 space-y-4">
          {history.map((entry, idx) => (
            <li key={entry.timestamp || idx} className="border-b border-border-color pb-3 last:border-b-0">
              <p className="text-text-primary mb-1"><strong>You:</strong> {entry.user}</p>
              <p className="text-text-primary mb-1"><strong>AI:</strong> {entry.ai}</p>
              <p className="text-text-secondary text-xs">{new Date(entry.timestamp).toLocaleString()}</p>
            </li>
          ))}
        </ul>
       )}
    </div>
  );
}
