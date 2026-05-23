import React from "react";
import { SecurityGovernance } from "./SecurityGovernance";

interface SecurityProps {
  demoMode?: boolean;
}

export default function Security({ demoMode }: SecurityProps) {
  return <SecurityGovernance />;
}
