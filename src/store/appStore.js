import { create } from 'zustand';

// This file defines the global state management store for the PRIV application using Zustand.
// It will manage the user's profile and the currently active AI persona, allowing any
// component in the application to access and update this state in a reactive way.

export const useAppStore = create((set) => ({
  // --- State ---
  user: null, // User profile will be stored here after login
  activePersona: 'PRIV', // The default active persona for the application

  // --- Actions ---
  // Action to set the user profile, typically called after a successful login.
  setUser: (userProfile) => set({ user: userProfile }),

  // Action to change the active AI persona. This could be triggered by the user
  // from a settings panel or automatically based on the context of their query.
  setActivePersona: (personaName) => set({ activePersona: personaName }),

  // Action to log the user out and clear their data from the store.
  logout: () => set({ user: null, activePersona: 'PRIV' }),
}));

// --- Example Usage in another component ---
/*
import { useAppStore } from './store/appStore';

const MyComponent = () => {
  // Access state and actions from the store
  const { user, activePersona, setActivePersona } = useAppStore();

  return (
    <div>
      <p>Welcome, {user?.name || 'Guest'}</p>
      <p>Currently interacting with: {activePersona}</p>
      <button onClick={() => setActivePersona('BRIDGETTE')}>
        Switch to Bridgette
      </button>
    </div>
  );
};
*/
