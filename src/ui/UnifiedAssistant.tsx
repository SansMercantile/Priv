import React from "react";
import { PrivCopilot } from "../components/PrivCopilot";

interface UnifiedAssistantProps {
  isVisible?: boolean;
}

export default function UnifiedAssistant({ isVisible }: UnifiedAssistantProps) {
  return <PrivCopilot />;
}
