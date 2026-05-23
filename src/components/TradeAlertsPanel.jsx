// src/components/TradeAlertsPanel.jsx
import React, { useEffect, useState, useCallback } from "react";
import apiClient from '../api/apiClient';

/**
 * TradeAlertsPanel Component
 * Displays a list of real-time trade alerts (e.g., margin calls, price targets).
 * Uses Tailwind CSS for styling.
 */
export default function TradeAlertsPanel() {
  const [alerts, setAlerts] = useState([]); // State to hold trade alerts
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * Fetches trade alerts from the backend API.
   *
   * @async
   * @function fetchAlerts
   */
  const fetchAlerts = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Fetch trade alerts from the backend trading alerts endpoint
      const data = await apiClient.get('/api/v1/trading/alerts');

      // Support both array responses and object-wrapped payloads.
      const alertsList = Array.isArray(data)
        ? data
        : Array.isArray(data.alerts)
          ? data.alerts
          : [];
      if (alertsList.length === 0 && Array.isArray(data?.data)) {
        setAlerts(data.data);
      } else {
        setAlerts(alertsList);
    } catch (err) {
      console.error("Failed to fetch trade alerts:", err);
      setError("Failed to load trade alerts. Please try again later.");
      setAlerts([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
    // Potentially set up polling for real-time alerts if needed:
    // const interval = setInterval(fetchAlerts, 10000); // Poll every 10 seconds
    // return () => clearInterval(interval);
  }, [fetchAlerts]);

  return (
    <div className="max-w-3xl mx-auto p-6 bg-card-bg rounded-lg shadow-custom-medium space-y-4 font-body">
      <h2 className="text-2xl font-bold text-text-primary mb-4 font-display">🔔 Trade Alerts</h2>
      {isLoading ? (
        <p className="text-text-secondary">Loading alerts...</p>
      ) : error ? (
        <p className="text-accent-bad">{error}</p>
      ) : alerts.length === 0 ? (
        <p className="text-text-secondary">No recent trade alerts.</p>
      ) : (
        <ul className="list-none p-0 m-0 space-y-3">
          {alerts.map((alert, index) => (
            <li key={alert.id || index} className="p-3 rounded-md bg-gray-50 border border-border-color shadow-sm flex items-start space-x-3">
              {/* You can add an icon here based on alert.type (e.g., warning, info) */}
              <div className="flex-shrink-0 text-accent-primary mt-1">
                {/* Placeholder for Alert Icon */}
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
              </div>
              <div>
                <p className="text-text-primary font-medium">{alert.message}</p>
                <p className="text-text-secondary text-xs mt-1">{new Date(alert.timestamp).toLocaleString()}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}