import React from "react";
import { TaxIntelligence } from "./TaxIntelligence";

interface TaxProps {
  demoMode?: boolean;
}

export default function Tax({ demoMode }: TaxProps) {
  return <TaxIntelligence />;
}
