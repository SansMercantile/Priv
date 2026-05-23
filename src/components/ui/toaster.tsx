import React from "react";

export function Toaster() {
  return (
    <div 
      id="toaster-portal" 
      className="fixed bottom-4 right-4 z-55 flex flex-col gap-2 pointer-events-none font-mono text-xs text-white" 
    />
  );
}
