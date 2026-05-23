// src/components/UserProfileEditor.jsx
import React, { useEffect, useState, useCallback } from "react";
import { UserIcon } from "./icons/Icons.jsx"; // Assuming UserIcon is in Icons.jsx

const API_BASE = import.meta.env.VITE_BACKEND_API_URL || '';

// Define the initial default structure for the user profile
const DEFAULT_PROFILE = {
  preferred_assets: [],
  risk_tolerance: "",
  trading_style: "",
  emotional_tendencies: [],
  primary_goals: [],
  profile_picture_url: "", // Added field for profile picture URL
  ai_trading_bot_control: {
    enabled: false,
    kill_switch_triggered: false,
  },
  tone_preference: "neutral",
};

/**
 * UserProfileEditor Component
 * Allows users to view and edit their trading profile,
 * including preferences, risk tolerance, and AI auto-trading controls.
 * Uses Tailwind CSS for styling.
 */
export default function UserProfileEditor() {
  const [profile, setProfile] = useState(DEFAULT_PROFILE);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false); // New state for save operation
  const [error, setError] = useState(null);
  const [feedbackMessage, setFeedbackMessage] = useState(null); // For success/error feedback

  /**
   * Fetches the user profile from the backend API.
   * Handles loading and error states for the initial fetch.
   *
   * @async
   * @function fetchProfile
   */
  const fetchProfile = useCallback(async () => {
    setIsLoading(true); // Start loading
    setError(null);     // Clear any previous errors
    try {
      const response = await fetch(`${API_BASE}/api/v1/profile`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      // Merge fetched data with default to ensure all fields are present
      setProfile(prev => ({ ...DEFAULT_PROFILE, ...prev, ...data }));
    } catch (err) {
      console.error("Failed to fetch user profile:", err);
      setError("Failed to load profile. Please try again.");
    } finally {
      setIsLoading(false); // End loading
    }
  }, []);

  /**
   * Saves the updated user profile to the backend API.
   * Handles saving and error states, and provides user feedback.
   *
   * @async
   * @function saveProfile
   */
  const saveProfile = useCallback(async () => {
    setIsSaving(true); // Indicate saving has started
    setError(null);
    setFeedbackMessage(null);
    try {
      const response = await fetch(`${API_BASE}/api/v1/profile`, {
        method: "POST", // Or PUT, depending on your API
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(profile),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      setFeedbackMessage("Profile saved successfully! ✅");
      // Optionally re-fetch profile to ensure UI is in sync with backend after save
      // fetchProfile();
    } catch (err) {
      console.error("Failed to save user profile:", err);
      setError(`Failed to save profile: ${err.message}`);
      setFeedbackMessage(null);
    } finally {
      setIsSaving(false); // End saving
      setTimeout(() => setFeedbackMessage(null), 3000); // Clear feedback after 3 seconds
    }
  }, [profile]); // Depend on profile so the latest changes are sent

  // Handle changes for all form inputs
  const handleChange = useCallback((e) => {
    const { name, value, type, checked } = e.target;

    setProfile((prevProfile) => {
      // Handle nested properties (e.g., ai_trading_bot_control.enabled)
      if (name.includes(".")) {
        const [parent, child] = name.split(".");
        return {
          ...prevProfile,
          [parent]: {
            ...(prevProfile[parent] || {}), // Ensure nested object exists
            [child]: type === "checkbox" ? checked : value,
          },
        };
      }

      // Handle array fields (comma-separated strings)
      if (
        ["preferred_assets", "emotional_tendencies", "primary_goals"].includes(name)
      ) {
        return {
          ...prevProfile,
          [name]: value.split(",").map((v) => v.trim()).filter(v => v !== ''), // Filter out empty strings
        };
      }

      // Handle checkbox for top-level properties
      if (type === "checkbox") {
        return { ...prevProfile, [name]: checked };
      }

      // Handle all other simple text/select fields
      return { ...prevProfile, [name]: value };
    });
  }, []); // Empty dependency array ensures this function is stable

  const handleFileChange = useCallback((e) => {
    const file = e.target.files[0];
    if (file) {
      // Here you would typically upload the file to a storage service (Firebase Storage, S3)
      // and then get a URL back to save in the profile_picture_url field.
      // For now, we'll simulate a local URL for immediate preview.
      const reader = new FileReader();
      reader.onloadend = () => {
        setProfile(prev => ({ ...prev, profile_picture_url: reader.result }));
        // In a real app, you'd then upload `file` to your backend storage
        // and update the profile_picture_url with the *actual* hosted URL.
        console.log("File selected for upload. Implement actual upload to storage here.");
      };
      reader.readAsDataURL(file); // Reads the file as a Data URL for preview
    }
  }, []);

  // Fetch profile on component mount
  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]); // Dependency array to ensure it runs when fetchProfile is stable

  if (isLoading) {
    return (
      <div className="text-center p-8 font-body bg-card-bg rounded-lg shadow-custom-light max-w-3xl mx-auto mt-10">
        <h2 className="text-2xl font-bold text-text-primary mb-4 font-display">Edit Your Profile 🧬</h2>
        <p>Loading user profile...</p>
      </div>
    );
  }

  if (error && !profile.email) { // Only show full error if initial load failed significantly
    return (
      <div className="text-center p-8 text-red-500 font-body bg-card-bg rounded-lg shadow-custom-light max-w-3xl mx-auto mt-10">
        <h2 className="text-2xl font-bold text-text-primary mb-4 font-display">Edit Your Profile 🧬</h2>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto p-6 bg-card-bg rounded-lg shadow-custom-medium space-y-6 font-body">
      <h2 className="text-2xl font-bold text-text-primary mb-4 font-display">
        Personal Trading Profile
      </h2>

      {feedbackMessage && (
        <div className="bg-green-100 text-green-700 p-3 rounded-md text-center">
          {feedbackMessage}
        </div>
      )}
      {error && (
        <div className="bg-red-100 text-red-700 p-3 rounded-md text-center">
          {error}
        </div>
      )}

      <form onSubmit={(e) => { e.preventDefault(); saveProfile(); }} className="space-y-6">
        {/* Profile Picture Section */}
        <div className="flex flex-col items-center space-y-4">
          <div className="w-32 h-32 rounded-full overflow-hidden border-2 border-border-color shadow-sm flex items-center justify-center bg-gray-100">
            {profile.profile_picture_url ? (
              <img src={profile.profile_picture_url} alt="Profile" className="w-full h-full object-cover" />
            ) : (
              // Using UserIcon as a placeholder
              <UserIcon className="w-20 h-20 text-gray-400" />
            )}
          </div>
          <label htmlFor="profile-picture-upload" className="cursor-pointer bg-accent-primary hover:bg-opacity-80 text-white font-semibold py-2 px-4 rounded-lg shadow-md transition">
            Upload Profile Picture
            <input
              id="profile-picture-upload"
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="hidden" // Hides the default file input
            />
          </label>
        </div>


        {/* Preferred Assets */}
        <div>
          <label htmlFor="preferred_assets" className="block text-text-primary text-sm font-semibold mb-2">
            Preferred Assets:
          </label>
          <input
            type="text" // Changed to text input as multi-select HTML can be complex with Tailwind
            id="preferred_assets"
            name="preferred_assets" // Name attribute for generic handleChange
            value={profile.preferred_assets?.join(", ") || ""}
            onChange={handleChange}
            placeholder="e.g. Stocks, Crypto, Options"
            className="w-full p-3 rounded-lg bg-input-bg text-text-primary placeholder-text-secondary border border-border-color focus:ring-2 focus:ring-accent-primary focus:border-accent-primary transition"
          />
        </div>

        {/* Risk Tolerance */}
        <div>
          <label htmlFor="risk_tolerance" className="block text-text-primary text-sm font-semibold mb-2">
            Risk Tolerance:
          </label>
          <select
            id="risk_tolerance"
            name="risk_tolerance"
            value={profile.risk_tolerance || ""}
            onChange={handleChange}
            className="w-full p-3 rounded-lg bg-input-bg text-text-primary border border-border-color focus:ring-2 focus:ring-accent-primary focus:border-accent-primary transition"
          >
            <option value="">Select...</option>
            <option value="cautious">Cautious</option>
            <option value="moderate">Moderate</option>
            <option value="aggressive">Aggressive</option>
          </select>
        </div>

        {/* Trading Style */}
        <div>
          <label htmlFor="trading_style" className="block text-text-primary text-sm font-semibold mb-2">
            Trading Style:
          </label>
          <input
            type="text" // Changed to text input
            id="trading_style"
            name="trading_style"
            value={profile.trading_style || ""}
            onChange={handleChange}
            placeholder="e.g. Day Trading, Swing Trading"
            className="w-full p-3 rounded-lg bg-input-bg text-text-primary placeholder-text-secondary border border-border-color focus:ring-2 focus:ring-accent-primary focus:border-accent-primary transition"
          />
        </div>

        {/* Emotional Tendencies */}
        <div>
          <label htmlFor="emotional_tendencies" className="block text-text-primary text-sm font-semibold mb-2">
            Emotional Tendencies:
          </label>
          <input
            type="text" // Changed to text input
            id="emotional_tendencies"
            name="emotional_tendencies"
            value={profile.emotional_tendencies?.join(", ") || ""}
            onChange={handleChange}
            placeholder="e.g. Impulsive, Cautious"
            className="w-full p-3 rounded-lg bg-input-bg text-text-primary placeholder-text-secondary border border-border-color focus:ring-2 focus:ring-accent-primary focus:border-accent-primary transition"
          />
        </div>

        {/* Primary Goals */}
        <div>
          <label htmlFor="primary_goals" className="block text-text-primary text-sm font-semibold mb-2">
            Primary Goals:
          </label>
          <input
            type="text" // Changed to text input
            id="primary_goals"
            name="primary_goals"
            value={profile.primary_goals?.join(", ") || ""}
            onChange={handleChange}
            placeholder="e.g. Capital Growth, Income Generation"
            className="w-full p-3 rounded-lg bg-input-bg text-text-primary placeholder-text-secondary border border-border-color focus:ring-2 focus:ring-accent-primary focus:border-accent-primary transition"
          />
        </div>

        {/* Tone Preference */}
        <div>
          <label htmlFor="tone_preference" className="block text-text-primary text-sm font-semibold mb-2">
            AI Tone Preference:
          </label>
          <select
            id="tone_preference"
            name="tone_preference"
            value={profile.tone_preference || "neutral"}
            onChange={handleChange}
            className="w-full p-3 rounded-lg bg-input-bg text-text-primary border border-border-color focus:ring-2 focus:ring-accent-primary focus:border-accent-primary transition"
          >
            <option value="">Select...</option>
            <option value="neutral">Neutral</option>
            <option value="formal">Formal</option>
            <option value="friendly">Friendly</option>
            <option value="direct">Direct</option>
          </select>
        </div>

        {/* AI Trading Bot Control - RESTORED to its original place in UserProfileEditor */}
        <div className="p-4 bg-gray-50 rounded-lg border border-border-color">
          <label className="flex items-center text-text-primary font-semibold mb-2">
            <input
              type="checkbox"
              name="ai_trading_bot_control.enabled"
              checked={profile.ai_trading_bot_control?.enabled || false}
              onChange={handleChange}
              className="mr-2 h-4 w-4 text-accent-primary focus:ring-accent-primary border-gray-300 rounded"
              disabled={isSaving}
            />
            Enable Auto-Trading Assistant
          </label>
          <div>
            <button
              type="button" // Important: type="button" to prevent form submission
              disabled={!profile.ai_trading_bot_control?.enabled || isSaving || profile.ai_trading_bot_control?.kill_switch_triggered}
              onClick={() => setProfile(prev => ({
                ...prev,
                ai_trading_bot_control: {
                  ...(prev.ai_trading_bot_control || {}),
                  kill_switch_triggered: true
                }
              }))}
              className="mt-2 bg-dark-scarlet hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-lg shadow-md transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              🔒 Trigger Kill Switch
            </button>
            {profile.ai_trading_bot_control?.kill_switch_triggered && (
              <p className="text-orange-500 text-sm mt-2">
                Kill switch triggered. Remember to save changes.
              </p>
            )}
          </div>
        </div>

        <button
          type="submit"
          disabled={isSaving || isLoading}
          className="w-full bg-accent-primary hover:bg-opacity-80 text-white font-semibold py-3 rounded-lg shadow-md transition transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSaving ? "Saving..." : "Save Profile"}
        </button>
      </form>
    </div>
  );
}