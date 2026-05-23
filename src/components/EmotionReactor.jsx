import React, { useState, useEffect, useRef } from 'react';
import Lottie from 'lottie-react';

// Assuming you have Lottie animation files in your public folder
// For now, these are placeholders.
import idleAnimation from '../../public/animations/priv_reactions/idle.json';
import speakingAnimation from '../../public/animations/priv_reactions/speaking.json';
import happyAnimation from '../../public/animations/priv_reactions/happy.json';
import concernedAnimation from '../../public/animations/priv_reactions/concerned.json';

const animationMap = {
  idle: idleAnimation,
  speaking: speakingAnimation,
  happy: happyAnimation,
  concerned: concernedAnimation,
};

const EmotionReactor = () => {
  const [currentEmotion, setCurrentEmotion] = useState('idle');
  const lottieRef = useRef();
  
  // NEW: WebSocket connection for real-time animation streaming
  const ws = useRef(null);

  useEffect(() => {
    // Establish WebSocket connection on component mount
    // The URL should point to your backend's WebSocket endpoint.
    // Use wss:// for secure connections in production.
    const wsUrl = import.meta.env.VITE_BACKEND_WS_URL || '/ws/v1/vision/stream';
    
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log("Vision WebSocket connected");
      // Conceptually, you would start sending video frames here
      // For now, we will just listen for messages.
    };

    ws.current.onmessage = (event) => {
      const animationParams = JSON.parse(event.data);
      console.log("Received animation parameters:", animationParams);
      
      // TODO: Implement logic to translate animation parameters into Lottie animations
      // or to drive a real-time rendering engine (e.g., Three.js).
      // For now, we can map a dominant emotion to a Lottie animation.
      if (animationParams.dominant_emotion && animationMap[animationParams.dominant_emotion]) {
        setCurrentEmotion(animationParams.dominant_emotion);
      }
    };

    ws.current.onclose = () => {
      console.log("Vision WebSocket disconnected");
    };

    ws.current.onerror = (error) => {
      console.error("Vision WebSocket error:", error);
    };

    // Cleanup function to close the WebSocket connection on component unmount
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);


  const handleInteraction = (emotion) => {
    setCurrentEmotion(emotion);
    // In a real scenario, you might also send an event back to the backend
    // to let the AI know about a user-initiated emotional change.
  };

  return (
    <div className="w-full h-full flex flex-col items-center justify-center p-4 bg-gray-900 rounded-lg shadow-lg">
      <div className="w-64 h-64">
        <Lottie
          lottieRef={lottieRef}
          animationData={animationMap[currentEmotion] || idleAnimation}
          loop={true}
          autoplay={true}
        />
      </div>
      <div className="mt-4 text-center">
        <p className="text-lg font-semibold text-gray-200">PRIV's Current State: <span className="font-bold text-cyan-400">{currentEmotion}</span></p>
        <p className="text-sm text-gray-400 mt-1">This component will render the real-time AI persona.</p>
      </div>
      {/* Example buttons to simulate changing emotion state */}
      <div className="flex space-x-2 mt-4">
          <button onClick={() => handleInteraction('idle')} className="px-3 py-1 bg-gray-700 text-white rounded hover:bg-gray-600 transition-colors">Idle</button>
          <button onClick={() => handleInteraction('speaking')} className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-500 transition-colors">Speak</button>
          <button onClick={() => handleInteraction('happy')} className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-500 transition-colors">Happy</button>
          <button onClick={() => handleInteraction('concerned')} className="px-3 py-1 bg-yellow-600 text-white rounded hover:bg-yellow-500 transition-colors">Concerned</button>
      </div>
    </div>
  );
};

export default EmotionReactor;
