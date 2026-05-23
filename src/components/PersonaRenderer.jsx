import React, { useRef, useEffect, Suspense, useState, useCallback } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, useGLTF } from '@react-three/drei';
import { Physics } from '@react-three/cannon';
import * as THREE from 'three';
import { GroundPlane, SpawnedSphere, SpawnedBox } from './LooneyTunesPhysics';
import apiClient from '../api/apiClient';
import { useAppStore } from '../store/appStore';

// --- Persona Configuration for the PRIV Application ---
const PERSONA_CONFIG = {
  PRIV: {
    presenterId: 'rian-lZC66_E37I',
    gltfPath: '/priv_avatar.glb',
  },
  BRIDGETTE: {
    presenterId: 'jen-5s29d2Y2v5',
    gltfPath: '/priv_avatar.glb',
  },
};

// --- Advanced Application State Hook ---
const useAppState = () => {
  const { user, activePersona, setUser } = useAppStore();
  
  useEffect(() => {
    // Simulate fetching user data on component mount
    if (!user) {
      setUser({ age: 25, name: "John Doe" });
    }
  }, [user, setUser]);

  return { user, activePersona };
};

// --- REALISTIC VIDEO AVATAR COMPONENT ---
const RealisticAvatar = ({ persona, animationData }) => {
  const videoRef = useRef(null);
  const peerConnection = useRef(null);
  const sessionId = useRef(null);
  const [isConnected, setIsConnected] = useState(false);

  const connect = useCallback(async () => {
    if (peerConnection.current && peerConnection.current.connectionState === 'connected') {
      return;
    }
    try {
      const { data: streamDetails } = await apiClient.post('/video-streaming/create-stream', {
        presenter_id: PERSONA_CONFIG[persona]?.presenterId || PERSONA_CONFIG.PRIV.presenterId
      });
      const { offer, ice_servers, session_id } = streamDetails;
      sessionId.current = session_id;

      peerConnection.current = new RTCPeerConnection({ iceServers: ice_servers });

      peerConnection.current.ontrack = (event) => {
        if (videoRef.current && event.streams && event.streams[0]) {
          videoRef.current.srcObject = event.streams[0];
        }
      };

      await peerConnection.current.setRemoteDescription(offer);
      const answer = await peerConnection.current.createAnswer();
      await peerConnection.current.setLocalDescription(answer);

      await apiClient.post(`/video-streaming/streams/${session_id}/start`, { answer });
      setIsConnected(true);
    } catch (error) {
      console.error(`Failed to connect to video streaming service for persona ${persona}:`, error);
      setIsConnected(false);
    }
  }, [persona]);

  useEffect(() => {
    connect();
    return () => {
      if (peerConnection.current) peerConnection.current.close();
    };
  }, [connect]);

  // --- Emotional Feedback Loop ---
  useEffect(() => {
    const sendEmotionAndGetResponse = async () => {
        if (isConnected && sessionId.current && animationData.dominant_emotion && animationData.dominant_emotion !== 'neutral') {
            try {
                const textToSpeak = "I am sensing that you might be feeling " + animationData.dominant_emotion;
                await apiClient.post('/video-streaming/streams/talk', {
                    session_id: sessionId.current,
                    script: textToSpeak,
                    user_emotion: animationData.dominant_emotion
                });
            } catch (error) {
                console.error("Failed to send talk command:", error);
            }
        }
    };
    sendEmotionAndGetResponse();
  }, [animationData, isConnected]);

  return (
    <div className="w-full h-full flex items-center justify-center bg-green-500 rounded-lg">
      <video
        ref={videoRef}
        className="w-full h-full object-cover"
        style={{ mixBlendMode: 'screen' }}
        autoPlay
        playsInline
      />
       <div className="absolute bottom-4 left-4 bg-black bg-opacity-50 p-2 rounded text-white text-xs">
        <p>Displaying: {persona} (Live Video)</p>
        <p>Status: {isConnected ? 'Connected' : 'Connecting...'}</p>
      </div>
    </div>
  );
};

// --- 3D ANIMATED AVATAR COMPONENT ---
const AnimatedAvatar = ({ persona, animationData }) => {
  const group = useRef();
  const gltfPath = PERSONA_CONFIG[persona]?.gltfPath || PERSONA_CONFIG.PRIV.gltfPath;
  const { scene, nodes } = useGLTF(gltfPath);

  useFrame(() => {
    if (!group.current || !animationData) return;
    const head = group.current.getObjectByName('Head');
    if (head) {
      const targetRotationZ = (animationData.head_tilt_degrees || 0) * (Math.PI / 180);
      head.rotation.z = lerp(head.rotation.z, targetRotationZ, 0.1);
    }
    const mesh = nodes.Wolf3D_Avatar;
    if (mesh && mesh.morphTargetDictionary) {
      const blinkIndex = mesh.morphTargetDictionary['eyesBlink'];
      if (blinkIndex !== undefined) {
        mesh.morphTargetInfluences[blinkIndex] = lerp(
          mesh.morphTargetInfluences[blinkIndex],
          animationData.eye_blink || 0,
          0.3
        );
      }
    }
  });

  return (
    <primitive object={scene} ref={group} dispose={null} scale={1.5} position={[0, -1.7, 0]} />
  );
};

const lerp = (start, end, alpha) => start * (1 - alpha) + end * alpha;

// --- MAIN RENDERER COMPONENT ---
const PersonaRenderer = () => {
  const { user, activePersona } = useAppState();
  const [animationData, setAnimationData] = useState({});
  const [spawnedObjects, setSpawnedObjects] = useState([]);
  const ws = useRef(null);

  useEffect(() => {
    const wsUrl = import.meta.env.VITE_BACKEND_WS_URL || '/ws/v1/vision/stream';
    ws.current = new WebSocket(wsUrl);
    ws.current.onopen = () => console.log("Persona Renderer WebSocket connected");
    ws.current.onclose = () => console.log("Persona Renderer WebSocket disconnected");
    ws.current.onerror = (error) => console.error("WebSocket error:", error);
    ws.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'animation_parameters') {
          setAnimationData(message.payload);
        } else if (message.type === 'looney_tunes_action') {
          handleLooneyTunesAction(message.action);
        }
      } catch (error) {
        console.error("Failed to parse message:", error);
      }
    };
    return () => {
      if (ws.current) ws.current.close();
    };
  }, []);

  const handleLooneyTunesAction = (action) => {
    if (action.action_type === 'SPAWN_OBJECT') {
      const newObject = {
        id: `obj_${Date.now()}`,
        type: action.payload.object_type,
        position: action.payload.position || [Math.random() * 2 - 1, 2, Math.random() * 2 - 1],
      };
      setSpawnedObjects(prev => [...prev, newObject]);
    }
  };

  if (!user) {
    return <div>Loading User Profile...</div>;
  }

  const isYouthMode = user.age < 18;

  return (
    <div className="w-full h-full bg-gray-900 rounded-lg shadow-lg relative">
      {isYouthMode ? (
        <>
          <Canvas camera={{ position: [0, 0.5, 3], fov: 50 }} shadows>
            <ambientLight intensity={0.8} />
            <directionalLight position={[5, 5, 5]} intensity={1.5} castShadow />
            <Physics>
              <Suspense fallback={null}>
                <GroundPlane />
                <AnimatedAvatar persona={activePersona} animationData={animationData} />
                {spawnedObjects.map(obj => {
                  if (obj.type === 'sphere') return <SpawnedSphere key={obj.id} position={obj.position} />;
                  if (obj.type === 'box') return <SpawnedBox key={obj.id} position={obj.position} />;
                  return null;
                })}
              </Suspense>
            </Physics>
            <OrbitControls target={[0, 0, 0]} />
          </Canvas>
          <div className="absolute bottom-4 left-4 bg-black bg-opacity-50 p-2 rounded text-white text-xs">
            <p>Displaying: {activePersona} (Youth Mode)</p>
            <p>Emotion: {animationData.dominant_emotion || 'N/A'}</p>
          </div>
        </>
      ) : (
        <RealisticAvatar persona={activePersona} animationData={animationData} />
      )}
    </div>
  );
};

Object.values(PERSONA_CONFIG).forEach(persona => useGLTF.preload(persona.gltfPath));

export default PersonaRenderer;
