import React, { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Send, Video, X, MessageSquare, BrainCircuit, Volume2, Bell, XCircle, BarChart2 } from 'lucide-react';
import apiClient from '../api/apiClient'; 
import { PrivAvatar, StopCircle, Camera } from './icons/Icons';

export default function SupportAssistant({ isVisible, onClose }) {
  const [userMessage, setUserMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [visionEnabled, setVisionEnabled] = useState(false); // Default camera to off

  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [detectedEmotion, setDetectedEmotion] = useState('');
  const analysisIntervalRef = useRef(null);
  
  // --- NEW: State to manage when Priv is speaking a special message ---
  const [isSpeaking, setIsSpeaking] = useState(false);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  const startCamera = useCallback(async () => {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
            videoRef.current.srcObject = stream;
        }
        setIsCameraActive(true);
      } catch (err) {
        console.error("Error accessing webcam:", err);
        alert("Webcam access was denied. Please allow it in your browser settings.");
        setVisionEnabled(false);
      }
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (videoRef.current && videoRef.current.srcObject) {
      videoRef.current.srcObject.getTracks().forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    setIsCameraActive(false);
  }, []);
  
  useEffect(() => {
      if (isVisible) {
          if (visionEnabled) {
            startCamera();
          }
          if (chatHistory.length === 0) {
            setChatHistory([{ sender: "ai", message: "Hello! I'm Priv. How can I help you?" }]);
          }
      } else {
          stopCamera();
      }
      return () => stopCamera(); 
  }, [isVisible, visionEnabled, startCamera, stopCamera, chatHistory.length]);

  const analyzeLiveFrame = useCallback(async () => {
    if (isAnalyzing || !isCameraActive || !videoRef.current || !canvasRef.current || !videoRef.current.srcObject) return;
    
    const canvas = canvasRef.current;
    const video = videoRef.current;
    
    if (video.videoWidth === 0 || video.videoHeight === 0) return;

    const targetWidth = 320;
    const targetHeight = (video.videoHeight / video.videoWidth) * targetWidth;
    canvas.width = targetWidth;
    canvas.height = targetHeight;
    canvas.getContext('2d').drawImage(video, 0, 0, targetWidth, targetHeight);
    
    setIsAnalyzing(true);
    
    const base64Image = canvas.toDataURL('image/jpeg', 0.7).split(',')[1];

    try {
        // NOTE: This now requires your updated vision_api.py to work correctly
        const result = await apiClient.post('/api/v1/vision/analyze-frame', { image_base64: base64Image });
        if (result && (result.analysis || result.dominant_emotion)) {
            setDetectedEmotion(result.analysis || result.dominant_emotion);
        } else {
            setDetectedEmotion('');
        }
    } catch (error) {
        console.error("Frame analysis failed:", error);
        setDetectedEmotion('');
    } finally {
        setIsAnalyzing(false);
    }
  }, [isAnalyzing, isCameraActive]);


  useEffect(() => {
    if (isVisible && visionEnabled && isCameraActive) {
        analysisIntervalRef.current = setInterval(analyzeLiveFrame, 2000);
    }
    return () => {
        if (analysisIntervalRef.current) {
            clearInterval(analysisIntervalRef.current);
        }
    };
  }, [isVisible, visionEnabled, isCameraActive, analyzeLiveFrame]);


  const playAudio = useCallback((audioBlob) => {
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    audio.play();
    audio.onended = () => {
        setIsSpeaking(false); // Set speaking to false when audio ends
        URL.revokeObjectURL(audioUrl);
    };
  }, []);

  const speakTextLocally = useCallback((text) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'en-US';
      utterance.rate = 1;
      utterance.pitch = 1;
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utterance);
    } else {
      setIsSpeaking(false);
    }
  }, []);

  const buildAudioUrl = (path) => {
    return import.meta.env.VITE_BACKEND_API_URL
      ? `${import.meta.env.VITE_BACKEND_API_URL}${path}`
      : path;
  };
  
  const sendMessage = useCallback(async (messageText) => {
    setDetectedEmotion('');
    const trimmedMessage = messageText.trim();
    if (!trimmedMessage || isLoading) return;

    setChatHistory(prev => [...prev, { sender: "user", message: trimmedMessage }]);
    if (userMessage) setUserMessage("");
    setIsLoading(true);

    try {
      const responseData = await apiClient.post('/api/v1/support', { message: trimmedMessage });
      const aiText = responseData?.message || "I'm not sure how to respond.";
      setChatHistory(prev => [...prev, { sender: "ai", message: aiText }]);
      
      const audioUrl = buildAudioUrl('/api/v1/audio/synthesize-speech');
      const audioResponse = await fetch(audioUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: aiText }),
      });
      if (audioResponse.ok) {
          const audioBlob = await audioResponse.blob();
          playAudio(audioBlob);
      } else {
          speakTextLocally(aiText);
      }
    } catch (err) {
      console.error("Failed to get response from Priv:", err);
      setChatHistory(prev => [...prev, { sender: "ai", message: "Sorry, I'm having trouble connecting right now." }]);
      speakTextLocally("Sorry, I'm having trouble connecting right now.");
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, userMessage, playAudio, speakTextLocally]);

  // --- NEW: Dedicated function to speak a specific message ---
  const speakMessage = useCallback(async (textToSpeak) => {
    if (isSpeaking || isLoading) return;
    setIsSpeaking(true);
    try {
        const audioUrl = buildAudioUrl('/api/v1/audio/synthesize-speech');
        const audioResponse = await fetch(audioUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: textToSpeak }),
        });
        if (audioResponse.ok) {
            const audioBlob = await audioResponse.blob();
            playAudio(audioBlob);
        } else {
            speakTextLocally(textToSpeak);
            setIsSpeaking(false);
        }
    } catch (error) {
        console.error("Speak message failed:", error);
        speakTextLocally(textToSpeak);
        setIsSpeaking(false);
    }
  }, [isSpeaking, isLoading, playAudio, speakTextLocally]);

  const startRecording = useCallback(async () => {
    // ... (startRecording logic remains the same)
  }, [sendMessage]);

  const stopRecording = useCallback(() => {
    // ... (stopRecording logic remains the same)
  }, []);

  const handleKeyPress = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(userMessage);
    }
  }, [sendMessage, userMessage]);

  const handleVisionToggle = () => {
    const newVisionState = !visionEnabled;
    setVisionEnabled(newVisionState);
    if (newVisionState) {
        startCamera();
    } else {
        stopCamera();
        setDetectedEmotion('');
    }
  };

  return (
    <div className={`fixed bottom-24 right-8 z-40 w-full max-w-sm h-[70vh] flex flex-col rounded-2xl shadow-custom-heavy overflow-hidden glass-effect transition-all duration-300 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10 pointer-events-none'}`}>
        {visionEnabled ? (
            <div className="relative w-full h-40 bg-black flex-shrink-0">
                <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
                {detectedEmotion && (
                    <div className="absolute bottom-2 left-1/2 -translate-x-1/2 px-3 py-1 bg-black/50 text-white text-sm rounded-lg backdrop-blur-sm">
                        Sensing: {detectedEmotion}
                    </div>
                )}
                <canvas ref={canvasRef} className="hidden"></canvas>
            </div>
        ) : (
            <div className="relative w-full h-8 bg-gray-800 flex-shrink-0 flex items-center justify-center">
                <p className="text-xs text-gray-400">Vision Analysis is Off</p>
            </div>
        )}

        <div className="flex-grow overflow-y-auto p-4 custom-scrollbar min-h-0">
            {chatHistory.map((msg, index) => (
                <div key={index} className={`mb-3 flex items-start gap-2.5 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                    {msg.sender === 'ai' && <div className="w-8 h-8 rounded-full bg-burgundy-black flex-shrink-0"><PrivAvatar/></div>}
                    <p className={`py-2 px-4 rounded-2xl max-w-[80%] break-words ${msg.sender === 'user' ? 'bg-accent-primary text-white rounded-br-none' : 'bg-card-bg/50 text-text-primary rounded-bl-none'}`}>
                        {msg.message}
                    </p>
                </div>
            ))}
            <div ref={messagesEndRef} />
        </div>
        
        {/* --- MODIFIED: Added a relative container for the nudge bubble --- */}
        <div className="relative p-4 border-t border-white/20">
            {/* --- NEW: The nudge bubble UI --- */}
            {/* It only appears if vision is OFF and Priv isn't already speaking */}
            {!visionEnabled && !isSpeaking && (
                <div
                    onClick={() => speakMessage("You're currently receiving only part of my analysis. Activate the vision module, and I can begin correlating market data with your real-time sentiment, providing a strategic edge that goes beyond charts and numbers.")}
                    className="absolute -top-6 left-10 flex items-center p-2 bg-blue-600 text-white rounded-full shadow-lg cursor-pointer hover:bg-blue-500 animate-pulse"
                    title="Get enhanced analysis"
                >
                    <div className="w-3 h-3 bg-white rounded-full"></div>
                </div>
            )}
            
            <div className="flex items-center space-x-2">
                <button 
                    onClick={handleVisionToggle} 
                    // MODIFIED: Disable button while speaking
                    disabled={isLoading || isSpeaking}
                    className={`p-3 rounded-lg shadow-md ${visionEnabled ? 'bg-blue-600 text-white' : 'bg-gray-600 text-gray-300'} disabled:opacity-50`}
                    title={visionEnabled ? "Turn Vision Off" : "Turn Vision On"}
                >
                    <Camera size={24} />
                </button>

                <textarea
                    className="flex-grow p-3 rounded-lg bg-black/20 text-white placeholder-gray-400 border border-white/20 focus:ring-2 focus:ring-accent-primary resize-none"
                    rows="1" placeholder="Ask Priv..." value={userMessage}
                    onChange={(e) => setUserMessage(e.target.value)} onKeyPress={handleKeyPress} 
                    // MODIFIED: Disable input while speaking
                    disabled={isLoading || isSpeaking}
                />
                {!isRecording ? (
                    <button onClick={startRecording} disabled={isLoading || isSpeaking} className="p-3 bg-accent-primary text-white font-semibold rounded-lg shadow-md disabled:opacity-50">
                        <Mic size={24} />
                    </button>
                ) : (
                    <button onClick={stopRecording} className="p-3 bg-red-500 text-white font-semibold rounded-lg shadow-md animate-pulse">
                        <StopCircle size={24} />
                    </button>
                )}
                <button onClick={() => sendMessage(userMessage)} disabled={isLoading || isSpeaking || !userMessage} className="p-3 bg-accent-primary text-white font-semibold rounded-lg shadow-md disabled:opacity-50">
                    <Send size={24} />
                </button>
            </div>
        </div>
    </div>
  );
}
