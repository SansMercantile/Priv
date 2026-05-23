import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion } from 'framer-motion';
import { LayoutDashboard, Settings, User } from './icons/Icons.jsx';

// Tutorial steps for each function can be extended here
const tutorials = {
  onboarding: [
    {
      message: (user) => `Hello, ${user?.displayName || 'new trader'}! I'm Priv, your AI assistant. Let me give you a quick tour.`,
      animated: true,
    },
    {
      message: () => "This is the main sidebar. You can use it to navigate to all key sections of the application.",
      targetSelector: 'aside',
      icon: <LayoutDashboard className="w-10 h-10 text-accent-primary" />,
    },
    {
      message: () => "Your profile and settings are always accessible via your avatar at the top right of the screen.",
      targetSelector: '#profileDropdownBtn',
      icon: <User className="w-10 h-10 text-accent-primary" />,
    },
    {
      message: () => "Inside your Profile, you can control crucial features like the Kill Switch for automated trading.",
      targetSelector: '#profileDropdownBtn',
      icon: <Settings className="w-10 h-10 text-accent-primary" />,
    },
    {
      message: () => "And if you ever need my help, just click my avatar at the bottom-right to open our chat.",
      targetSelector: '#privFabContainer',
    },
    {
      message: () => "You're all set! You can now explore the dashboard. Happy trading!",
      finalStep: true,
    },
  ],
  // Example: add more tutorials for other functions
  dashboard: [
    {
      message: () => "Welcome to your dashboard! Here you can monitor your portfolio in real time.",
      animated: true,
    },
    {
      message: () => "Use the metric cards to track key performance indicators.",
      targetSelector: '.metric-card',
    },
    {
      message: () => "The live chart visualizes your portfolio's performance.",
      targetSelector: '.live-chart',
    },
    {
      message: () => "Activity feed keeps you updated on important events.",
      targetSelector: '.activity-feed',
      finalStep: true,
    },
  ],
};

export default function PrivOnboarding({ user, markOnboardingComplete, tutorialKey = 'onboarding', onFinish }) {
  const steps = useMemo(() => tutorials[tutorialKey] || [], [tutorialKey, user]);
  const [currentStep, setCurrentStep] = useState(0);
  const [displayedMessage, setDisplayedMessage] = useState('');
  const [typingEffectActive, setTypingEffectActive] = useState(false);

  const handleNextStep = useCallback(() => {
    if (typingEffectActive) return;
    if (currentStep < steps.length - 1) {
      setCurrentStep((prev) => prev + 1);
    } else {
      if (onFinish) onFinish();
      if (markOnboardingComplete) markOnboardingComplete();
    }
  }, [currentStep, steps.length, markOnboardingComplete, typingEffectActive, onFinish]);

  useEffect(() => {
    const step = steps[currentStep];
    let fullMessage = typeof step.message === 'function' ? step.message(user) : step.message;
    setTypingEffectActive(true);
    let i = 0;
    setDisplayedMessage('');
    if (step.animated) {
      // Use Framer Motion for animated welcome
      setDisplayedMessage(fullMessage);
      setTypingEffectActive(false);
      return;
    }
    const typingInterval = setInterval(() => {
      if (i < fullMessage.length) {
        setDisplayedMessage((prev) => prev + fullMessage.charAt(i));
        i++;
      } else {
        clearInterval(typingInterval);
        setTypingEffectActive(false);
      }
    }, 40);
    return () => clearInterval(typingInterval);
  }, [currentStep, steps, user]);

  if (!steps.length) return null;

  const step = steps[currentStep];

  return (
    <div className="fixed inset-0 z-[1000] tutorial-backdrop flex items-center justify-center p-4">
      <div className="relative text-center">
        <div className="speech-bubble bg-card-bg p-6 rounded-lg shadow-xl max-w-md mx-auto">
          {step.animated ? (
            <motion.p
              className="text-lg text-text-primary"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.5 }}
            >
              {displayedMessage}
            </motion.p>
          ) : (
            <p className="text-lg text-text-primary">{displayedMessage}</p>
          )}
          {step.icon && <div className="my-4 flex justify-center">{step.icon}</div>}
        </div>
        <button
          onClick={handleNextStep}
          disabled={typingEffectActive}
          className="mt-4 bg-accent-primary text-white font-semibold py-2 px-6 rounded-lg shadow-md disabled:opacity-50"
        >
          {step.finalStep ? 'Finish' : 'Next'}
        </button>
      </div>
    </div>
  );
}

// Usage:
// <PrivOnboarding user={user} markOnboardingComplete={fn} tutorialKey="dashboard" />
// Add more tutorials to the 'tutorials' object above for each app function.