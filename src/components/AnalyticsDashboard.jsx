// src/components/AnalyticsDashboard.jsx
import React, { useEffect, useState, useCallback } from "react";
import apiClient from '../api/apiClient'; 

export default function AnalyticsDashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAnalytics = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient("/api/v1/analytics");
      setAnalytics(data);
    } catch (err) {
      console.error("Failed to fetch analytics data:", err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  return (
    <div className="max-w-3xl mx-auto p-6 bg-card-bg rounded-lg shadow-custom-medium space-y-6 font-body">
      <h2 className="text-2xl font-bold text-text-primary mb-4 font-display">📊 AI Insight Dashboard</h2>
      {isLoading ? ( <p className="text-text-secondary">Loading analytics...</p> ) : 
       error ? ( <p className="text-accent-bad">{error}</p> ) : 
      (
        <>
          <div className="p-4 rounded-lg bg-gray-50 border border-border-color shadow-sm">
            <h4 className="text-lg font-semibold text-text-primary mb-2">Most Triggered Emotions</h4>
            {(analytics?.top_emotions?.length > 0) ? (
              <ul className="list-none p-0 m-0">
                {analytics.top_emotions.map(([emotion, count], idx) => (
                  <li key={idx} className="flex justify-between items-center py-1 border-b border-border-color last:border-b-0">
                    <span className="text-text-secondary">{emotion}</span>
                    <strong className="text-text-primary">{count}</strong>
                  </li>
                ))}
              </ul>
            ) : (<p className="text-text-secondary text-sm">No emotion data available.</p>)}
          </div>
          <div className="p-4 rounded-lg bg-gray-50 border border-border-color shadow-sm">
            <h4 className="text-lg font-semibold text-text-primary mb-2">Top User Phrases</h4>
            {(analytics?.top_user_terms?.length > 0) ? (
              <ul className="list-none p-0 m-0">
                {analytics.top_user_terms.map(([word, count], idx) => (
                  <li key={idx} className="flex justify-between items-center py-1 border-b border-border-color last:border-b-0">
                    <span className="text-text-secondary">“{word}”</span>
                    <strong className="text-text-primary">{count} mentions</strong>
                  </li>
                ))}
              </ul>
            ) : (<p className="text-text-secondary text-sm">No user phrase data available.</p>)}
          </div>
        </>
      )}
    </div>
  );
}
