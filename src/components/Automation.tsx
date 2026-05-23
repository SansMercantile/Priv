import React from "react";
import { AutomationAutonomy } from "./AutomationAutonomy";

interface AutomationProps {
  demoMode?: boolean;
}

export default function Automation({ demoMode }: AutomationProps) {
  return <AutomationAutonomy />;
}
