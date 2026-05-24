import React from "react";
import { DashboardOverview } from "../DashboardOverview";

interface DashboardProps {
  demoMode?: boolean;
}

export default function RealTimeDashboard({ demoMode }: DashboardProps) {
  // Pass matching function placeholders since DashboardOverview needs setActiveSection
  return <DashboardOverview demoMode={demoMode} setActiveSection={() => {}} />;
}
