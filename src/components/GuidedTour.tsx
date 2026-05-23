import React, { useState, useEffect } from "react";
import { 
  Award, 
  ChevronRight, 
  X, 
  HelpCircle,
  Brain,
  Users,
  ShieldCheck,
  LayoutDashboard
} from "lucide-react";

interface GuidedTourProps {
  onHighlightSection: (sec: string) => void;
  onClose: () => void;
}

export const GuidedTour: React.FC<GuidedTourProps> = ({ onHighlightSection, onClose }) => {
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    {
      title: "Welcome to PRIV Core",
      content: "This is a next-generation AI-driven execution engine built by Sans Mercantile. Let's take a quick tour of its key modules.",
      section: "dashboard",
      icon: LayoutDashboard,
      color: "text-white/70"
    },
    {
      title: "AGI Orchestration",
      content: "The AGI Core acts as the central nervous system, making high-level strategic decisions with a unique emotional intelligence tuning layer.",
      section: "agi-core",
      icon: Brain,
      color: "text-white/70"
    },
    {
      title: "Agent Arbitration",
      content: "PRIV is run by a fleet of specialized AI agents. The Arbitration Engine finds consensus among them, escalating critical issues to a simulated C-Suite.",
      section: "multi-agent",
      icon: Users,
      color: "text-white/70"
    },
    {
      title: "Security & Governance",
      content: "Zero-Knowledge Proofs and a Blockchain Logger ensure every action is transparent, ethically audited, and post-quantum secure.",
      section: "security",
      icon: ShieldCheck,
      color: "text-white/70"
    }
  ];

  // Auto-switch tabs in sidebar to mimic step highlighting
  useEffect(() => {
    onHighlightSection(steps[currentStep].section);
  }, [currentStep]);

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(prev => prev + 1);
    } else {
      localStorage.setItem("priv_tour_concluded", "true");
      onClose();
    }
  };

  const handleSkip = () => {
    localStorage.setItem("priv_tour_concluded", "true");
    onClose();
  };

  const StepIcon = steps[currentStep].icon;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-neutral-950 border border-white/10 rounded p-6 shadow-2xl relative transition-all duration-300 transform scale-100">
        
        {/* Header decoration */}
        <div className="flex items-center justify-between border-b border-white/5 pb-3 mb-4">
          <div className="flex items-center space-x-2">
            <StepIcon className={`w-4 h-4 ${steps[currentStep].color}`} />
            <span className="font-mono text-[9px] text-gray-500 uppercase tracking-widest">
              PRIV Walkthrough ({currentStep + 1} / {steps.length})
            </span>
          </div>
          <button 
            onClick={handleSkip}
            className="p-1 rounded-full hover:bg-white/5 text-gray-500 hover:text-white transition"
            title="Skip Tour"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Step Body */}
        <div className="space-y-3">
          <h2 className="text-xl font-serif italic text-white font-normal">
            {steps[currentStep].title}
          </h2>
          <p className="text-xs text-stone-400 leading-relaxed font-sans font-light">
            {steps[currentStep].content}
          </p>
        </div>

        {/* Action button row */}
        <div className="flex items-center justify-between pt-6 mt-6 border-t border-white/5">
          <button 
            onClick={handleSkip}
            className="text-gray-500 hover:text-white text-[11px] font-mono transition cursor-pointer"
          >
            Skip walkthrough
          </button>

          <button 
            onClick={handleNext}
            className="bg-white text-neutral-950 font-medium text-xs px-4 py-2.5 rounded hover:bg-stone-200 transition flex items-center space-x-1 cursor-pointer"
          >
            <span>{currentStep === steps.length - 1 ? "FINISH TOUR" : "NEXT MODULE"}</span>
            <ChevronRight className="w-4 h-4 text-neutral-950" />
          </button>
        </div>

      </div>
    </div>
  );
};
