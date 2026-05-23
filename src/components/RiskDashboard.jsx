// src/components/RiskDashboard.jsx
import React, { useEffect, useState, useCallback } from "react";
import apiClient from '../api/apiClient';

/**
 * RiskDashboard Component
 * Displays a table of risk analysis data for current trades,
 * fetched from the backend.
 * Uses Tailwind CSS for styling.
 */
export default function RiskDashboard() {
  const [riskData, setRiskData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * Fetches risk analysis data from the backend API.
   * Handles loading, success, and error states.
   *
   * @async
   * @function fetchRiskData
   */
  const fetchRiskData = useCallback(async () => {
    setIsLoading(true); // Indicate loading has started
    setError(null);     // Clear any previous errors
    try {
      const data = await apiClient.get('/api/v1/risk');

      // Ensure data.risk_analysis is an array, default to empty array if not
      if (Array.isArray(data.risk_analysis)) {
        setRiskData(data.risk_analysis);
      } else {
        console.warn("API returned non-array data for risk_analysis:", data);
        setRiskData([]); // Default to empty array if data format is unexpected
      }
    } catch (err) {
      console.error("Failed to fetch risk data:", err); // Log the detailed error
      setError("Failed to load risk data. Please try again."); // User-friendly error message
      setRiskData([]); // Clear any old data on error
    } finally {
      setIsLoading(false); // Indicate loading has finished
    }
  }, []); // useCallback with an empty dependency array ensures this function is stable

  // useEffect hook to trigger the data fetch when the component mounts
  useEffect(() => {
    fetchRiskData();
  }, [fetchRiskData]); // Dependency array includes fetchRiskData, which is stable due to useCallback

  return (
    <div className="max-w-5xl mx-auto p-6 bg-card-bg rounded-lg shadow-custom-medium space-y-4 font-body">
      <h2 className="text-2xl font-bold text-text-primary mb-4 font-display">📉 Risk Analyzer</h2>
      {isLoading ? (
        <p className="text-text-secondary">Loading risk data...</p>
      ) : error ? (
        <p className="text-accent-bad">{error}</p>
      ) : riskData.length === 0 ? (
        <p className="text-text-secondary">No trades to analyze.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border-color shadow-sm">
          <table className="min-w-full divide-y divide-border-color">
            <thead className="bg-gray-50">
              <tr>
                {["Symbol", "Risk ($)", "Risk %", "R:R", "Note"].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-card-bg divide-y divide-border-color">
              {riskData.map((row, idx) => (
                <tr
                  key={row.symbol || idx} // Use a unique identifier if available, fallback to index
                  className={`text-center ${row.note && row.note.includes("No stop") ? "bg-red-50" : "bg-card-bg"} hover:bg-main-bg transition-colors`}
                >
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-text-primary">{row.symbol}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-text-secondary">{row.risk_amount ?? "--"}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-text-secondary">{row.risk_pct != null ? `${row.risk_pct}%` : "--"}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-text-secondary">{row.rr_ratio ?? "--"}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-text-secondary">{row.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}