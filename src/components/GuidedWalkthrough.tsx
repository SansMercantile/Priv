import React from "react";
import { GuidedTour } from "./GuidedTour";

interface GuidedWalkthroughProps {
  onEnd: () => void;
}

export default function GuidedWalkthrough({ onEnd }: GuidedWalkthroughProps) {
  return <GuidedTour onHighlightSection={() => {}} onClose={onEnd} />;
}
