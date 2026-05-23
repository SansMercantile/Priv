import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useEnvironment } from '../context/EnvironmentContext';
import {
  canAccessLiveDashboard,
  getKycStatus,
  hasLiveSession,
  isProfileComplete,
} from '../lib/environment';

type GuardLevel = 'session' | 'profile' | 'kyc' | 'dashboard';

interface ProtectedRouteProps {
  children: React.ReactNode;
  level?: GuardLevel;
}

export default function ProtectedRoute({ children, level = 'dashboard' }: ProtectedRouteProps) {
  const { demoMode } = useEnvironment();
  const location = useLocation();

  if (demoMode) {
    return <>{children}</>;
  }

  if (level === 'session' || level === 'profile' || level === 'kyc' || level === 'dashboard') {
    if (!hasLiveSession()) {
      return <Navigate to="/login" state={{ from: location.pathname }} replace />;
    }
  }

  if (level === 'profile' || level === 'kyc' || level === 'dashboard') {
    if (!isProfileComplete()) {
      return <Navigate to="/create-profile" state={{ from: location.pathname }} replace />;
    }
  }

  if (level === 'kyc' || level === 'dashboard') {
    const kyc = getKycStatus();
    if (kyc === 'none' || kyc === 'pending') {
      return <Navigate to="/verification" state={{ from: location.pathname }} replace />;
    }
  }

  if (level === 'dashboard' && !canAccessLiveDashboard()) {
    return <Navigate to="/verification" replace />;
  }

  return <>{children}</>;
}
