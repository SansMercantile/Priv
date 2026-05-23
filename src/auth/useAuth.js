// src/auth/useAuth.js
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  hasLiveSession,
  isProfileComplete,
  getKycStatus,
  setLiveSession,
  setProfileComplete,
} from '../lib/environment';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || process.env.REACT_APP_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || process.env.REACT_APP_FIREBASE_PROJECT_ID,
};

const firebaseConfigured = Boolean(
  firebaseConfig.apiKey && firebaseConfig.authDomain && firebaseConfig.projectId
);

let firebaseAuth = null;

if (firebaseConfigured) {
  import('firebase/app').then(({ initializeApp }) => {
    try {
      initializeApp(firebaseConfig);
    } catch (e) {
      console.warn('Firebase may already be initialized.', e);
    }
  });
  import('firebase/auth').then(({ getAuth }) => {
    firebaseAuth = getAuth();
  });
}

function resolvePostLoginPath() {
  if (!isProfileComplete()) return '/create-profile';
  const kyc = getKycStatus();
  if (kyc === 'none' || kyc === 'pending') return '/verification';
  return '/dashboard';
}

export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [authError, setAuthError] = useState(null);
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let unsubscribe = () => {};

    const bootstrap = async () => {
      if (firebaseConfigured && firebaseAuth) {
        const { onAuthStateChanged } = await import('firebase/auth');
        unsubscribe = onAuthStateChanged(firebaseAuth, (currentUser) => {
          if (currentUser && !currentUser.isAnonymous) {
            setUser(currentUser);
            setLiveSession({
              uid: currentUser.uid,
              email: currentUser.email,
              displayName: currentUser.displayName,
            });
          } else if (hasLiveSession()) {
            try {
              setUser(JSON.parse(localStorage.getItem('privSession')));
            } catch {
              setUser(null);
            }
          } else {
            setUser(null);
          }
          setIsLoadingAuth(false);
        });
      } else if (hasLiveSession()) {
        try {
          setUser(JSON.parse(localStorage.getItem('privSession')));
        } catch {
          setUser(null);
        }
        setIsLoadingAuth(false);
      } else {
        setIsLoadingAuth(false);
      }
    };

    bootstrap();
    return () => unsubscribe();
  }, []);

  const handleAuthSuccess = useCallback(
    (result) => {
      const firebaseUser = result?.user;
      if (firebaseUser) {
        setUser(firebaseUser);
        setLiveSession({
          uid: firebaseUser.uid,
          email: firebaseUser.email,
          displayName: firebaseUser.displayName,
        });
      }
      const isNewUser =
        firebaseUser?.metadata?.creationTime === firebaseUser?.metadata?.lastSignInTime;
      if (isNewUser) {
        navigate('/create-profile');
      } else {
        navigate(resolvePostLoginPath());
      }
    },
    [navigate]
  );

  const handleLocalAuthSuccess = useCallback(
    (email, isNewUser) => {
      const session = { email, uid: `local-${email}`, displayName: email };
      setUser(session);
      setLiveSession(session);
      navigate(isNewUser ? '/create-profile' : resolvePostLoginPath());
    },
    [navigate]
  );

  const handleAuthError = (error) => {
    if (error.code === 'auth/weak-password') {
      setAuthError('Password must be at least 6 characters long.');
    } else if (error.code === 'auth/account-exists-with-different-credential') {
      setAuthError(
        'An account already exists with this email address using a different sign-in method.'
      );
    } else {
      setAuthError(error.message);
    }
  };

  const signUp = useCallback(
    async (email, password) => {
      setAuthError(null);
      if (firebaseConfigured && firebaseAuth) {
        try {
          const { createUserWithEmailAndPassword } = await import('firebase/auth');
          const result = await createUserWithEmailAndPassword(firebaseAuth, email, password);
          handleAuthSuccess(result);
        } catch (error) {
          handleAuthError(error);
        }
        return;
      }
      if (!email || password.length < 6) {
        setAuthError('Password must be at least 6 characters long.');
        return;
      }
      handleLocalAuthSuccess(email, true);
    },
    [handleAuthSuccess, handleLocalAuthSuccess]
  );

  const signIn = useCallback(
    async (email, password) => {
      setAuthError(null);
      if (firebaseConfigured && firebaseAuth) {
        try {
          const { signInWithEmailAndPassword } = await import('firebase/auth');
          const result = await signInWithEmailAndPassword(firebaseAuth, email, password);
          handleAuthSuccess(result);
        } catch (error) {
          handleAuthError(error);
        }
        return;
      }
      if (!email || !password) {
        setAuthError('Email and password are required.');
        return;
      }
      handleLocalAuthSuccess(email, false);
    },
    [handleAuthSuccess, handleLocalAuthSuccess]
  );

  const signInWithGoogle = useCallback(async () => {
    setAuthError(null);
    if (!firebaseConfigured || !firebaseAuth) {
      setAuthError('Google sign-in requires Firebase configuration in live mode.');
      return;
    }
    try {
      const { GoogleAuthProvider, signInWithPopup } = await import('firebase/auth');
      const result = await signInWithPopup(firebaseAuth, new GoogleAuthProvider());
      handleAuthSuccess(result);
    } catch (error) {
      handleAuthError(error);
    }
  }, [handleAuthSuccess]);

  const signInWithMicrosoft = useCallback(async () => {
    setAuthError(null);
    if (!firebaseConfigured || !firebaseAuth) {
      setAuthError('Microsoft sign-in requires Firebase configuration in live mode.');
      return;
    }
    try {
      const { OAuthProvider, signInWithPopup } = await import('firebase/auth');
      const result = await signInWithPopup(firebaseAuth, new OAuthProvider('microsoft.com'));
      handleAuthSuccess(result);
    } catch (error) {
      handleAuthError(error);
    }
  }, [handleAuthSuccess]);

  const signOutUser = useCallback(async () => {
    if (firebaseConfigured && firebaseAuth) {
      try {
        const { signOut } = await import('firebase/auth');
        await signOut(firebaseAuth);
      } catch (e) {
        console.warn('Firebase sign out failed', e);
      }
    }
    setLiveSession(null);
    setUser(null);
    navigate('/login');
  }, [navigate]);

  const markOnboardingComplete = useCallback(() => {
    setProfileComplete(true);
  }, []);

  return {
    user,
    isLoadingAuth,
    authError,
    signIn,
    signUp,
    signOutUser,
    signInWithGoogle,
    signInWithMicrosoft,
    markOnboardingComplete,
    firebaseConfigured,
  };
};
