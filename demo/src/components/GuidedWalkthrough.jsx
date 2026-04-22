import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Lightbulb, Zap, Users, Shield } from 'lucide-react';
import { Button } from './ui/button';

const steps = [
  {
    title: "Welcome to PRIV Core",
    content: "This is a next-generation AI-driven execution engine. Let's take a quick tour of its key modules.",
    icon: Lightbulb,
    target: null
  },
  {
    title: "AGI Orchestration",
    content: "The AGI Core acts as the central nervous system, making high-level strategic decisions with a unique emotional intelligence layer.",
    icon: Zap,
    target: "sidebar-agi-core"
  },
  {
    title: "Agent Arbitration",
    content: "PRIV is a fleet of specialized AI agents. The Arbitration Engine finds consensus among them, escalating critical issues to a simulated C-Suite.",
    icon: Users,
    target: "sidebar-multi-agent"
  },
  {
    title: "Security & Governance",
    content: "Zero-Knowledge Proofs and a Blockchain Logger ensure every action is transparent, ethical, and secure.",
    icon: Shield,
    target: "sidebar-security"
  },
];

const GuidedWalkthrough = ({ onEnd }) => {
  const [currentStep, setCurrentStep] = useState(0);

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onEnd();
    }
  };

  const step = steps[currentStep];

  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center">
      <AnimatePresence mode="wait">
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, y: 50, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -50, scale: 0.9 }}
          transition={{ duration: 0.3 }}
          className="glass-morphism rounded-2xl w-full max-w-md p-8 text-center border border-green-500/30"
        >
          <div className="flex justify-end">
              <Button variant="ghost" size="icon" onClick={onEnd} className="absolute top-4 right-4">
                  <X className="w-5 h-5" />
              </Button>
          </div>
          <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6 border border-green-500/50">
            <step.icon className="w-8 h-8 text-green-400" />
          </div>
          <h2 className="text-2xl font-bold gradient-text mb-4">{step.title}</h2>
          <p className="text-gray-300 mb-8">{step.content}</p>
          <div className="flex items-center justify-between">
            <div className="flex space-x-2">
                {steps.map((_, index) => (
                    <div key={index} className={`w-2 h-2 rounded-full transition-colors ${index === currentStep ? 'bg-green-400' : 'bg-gray-600'}`}></div>
                ))}
            </div>
            <Button onClick={nextStep} className="bg-green-500 hover:bg-green-600">
              {currentStep === steps.length - 1 ? "Finish Tour" : "Next"}
            </Button>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

export default GuidedWalkthrough;
