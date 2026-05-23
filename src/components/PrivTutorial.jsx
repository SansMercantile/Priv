// src/components/PrivTutorial.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { LayoutDashboard, Settings, User } from './icons/Icons.jsx'; // <-- CORRECTED IMPORTS

export default function PrivTutorial({ user, markOnboardingComplete }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [displayedMessage, setDisplayedMessage] = useState('');
  const [typingEffectActive, setTypingEffectActive] = useState(false);

  const tutorialSteps = useMemo(() => [
    {
      message: `Hello, ${user?.displayName || 'new trader'}! I'm Priv, your AI assistant. Let me give you a quick tour.`,
    },
    {
      message: "This is the main sidebar. You can use it to navigate to all key sections of the application.",
      targetSelector: 'aside', 
      icon: <LayoutDashboard className="w-10 h-10 text-accent-primary" />,
    },
    {
      message: "Your profile and settings are always accessible via your avatar at the top right of the screen.",
      targetSelector: '#profileDropdownBtn',
      icon: <User className="w-10 h-10 text-accent-primary" />,
    },
    {
      message: "Inside your Profile, you can control crucial features like the Kill Switch for automated trading.",
      targetSelector: '#profileDropdownBtn', 
      icon: <Settings className="w-10 h-10 text-accent-primary" />,
    },
    {
      message: "And if you ever need my help, just click my avatar at the bottom-right to open our chat.",
      targetSelector: '#privFabContainer',
    },
    {
      message: "You're all set! You can now explore the dashboard. Happy trading!",
      finalStep: true,
    },
  ], [user]);

  const handleNextStep = useCallback(() => {
    if (typingEffectActive) return;
    if (currentStep < tutorialSteps.length - 1) {
        setCurrentStep(prev => prev + 1);
    } else {
        markOnboardingComplete();
    }
  }, [currentStep, tutorialSteps.length, markOnboardingComplete, typingEffectActive]);

  useEffect(() => {
    const fullMessage = tutorialSteps[currentStep].message;
    setTypingEffectActive(true);
    let i = 0;
    setDisplayedMessage('');
    const typingInterval = setInterval(() => {
        if (i < fullMessage.length) {
            setDisplayedMessage(prev => prev + fullMessage.charAt(i));
            i++;
        } else {
            clearInterval(typingInterval);
            setTypingEffectActive(false);
        }
    }, 40);
    return () => clearInterval(typingInterval);
  }, [currentStep, tutorialSteps]);

  return (
    <div className="fixed inset-0 z-[1000] tutorial-backdrop flex items-center justify-center p-4">
        <div className="relative text-center">
            <div className="speech-bubble bg-card-bg p-6 rounded-lg shadow-xl max-w-md mx-auto">
                <p className="text-lg text-text-primary">{displayedMessage}</p>
            </div>
            <button onClick={handleNextStep} disabled={typingEffectActive} className="mt-4 bg-accent-primary text-white font-semibold py-2 px-6 rounded-lg shadow-md disabled:opacity-50">
                {tutorialSteps[currentStep].finalStep ? 'Finish' : 'Next'}
            </button>
        </div>
    </div>
  );
}