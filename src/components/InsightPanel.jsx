// src/components/InsightPanel.jsx
import React, { useEffect, useState } from "react";
import apiClient from '../api/apiClient'; 

export default function InsightPanel() {
  const [summary, setSummary] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchInsight = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await apiClient.get('/api/v1/insights');
        setSummary((data && data.summary) || 'No insight available.');
      } catch (err) {
        console.error('Failed to fetch insight summary:', err);
        setError(err?.message || 'Insight service unavailable.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchInsight();
  }, []);

  // ... (rest of the component's return/JSX logic remains the same) ...
  return (
    <div className="max-w-3xl mx-auto p-6 bg-card-bg rounded-lg shadow-custom-medium space-y-4">
      <h2 className="text-2xl font-bold text-text-primary mb-4 font-display">🧠 Weekly Insight Summary</h2>
      {isLoading ? <p>Loading insight...</p> :
       error ? <p className="text-accent-bad">{error}</p> :
       <pre className="whitespace-pre-wrap leading-relaxed text-base bg-input-bg p-4 rounded-md text-text-primary">{summary || "No insight available."}</pre>
      }
    </div>
  );
}
