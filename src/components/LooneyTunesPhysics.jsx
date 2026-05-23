import React from 'react';
import { useSphere, useBox, usePlane } from '@react-three/cannon';

// This component defines the physical objects that can be spawned in the scene.
// It uses the '@react-three/cannon' library for physics simulations.

export const GroundPlane = () => {
  const [ref] = usePlane(() => ({ rotation: [-Math.PI / 2, 0, 0], position: [0, -2, 0] }));
  return (
    <mesh ref={ref} receiveShadow>
      <planeGeometry args={[100, 100]} />
      <meshStandardMaterial color="#333" />
    </mesh>
  );
};

export const SpawnedSphere = ({ position }) => {
  const [ref] = useSphere(() => ({
    mass: 1,
    position,
    args: [0.2], // radius
  }));

  return (
    <mesh ref={ref} castShadow>
      <sphereGeometry args={[0.2, 32, 32]} />
      <meshStandardMaterial color="hotpink" />
    </mesh>
  );
};

export const SpawnedBox = ({ position }) => {
    const [ref] = useBox(() => ({
      mass: 1,
      position,
      args: [0.4, 0.4, 0.4], // width, height, depth
    }));
  
    return (
      <mesh ref={ref} castShadow>
        <boxGeometry args={[0.4, 0.4, 0.4]} />
        <meshStandardMaterial color="orange" />
      </mesh>
    );
  };
