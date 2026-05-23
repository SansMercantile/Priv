import React from "react";
import { DashboardOverview } from "../DashboardOverview";

interface DashboardProps {
  demoMode?: boolean;
}

export default function RealTimeDashboard({ demoMode }: DashboardProps) {
  return <DashboardOverview setActiveSection={() => {}} demoMode={demoMode} />;
}
