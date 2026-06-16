"use client";

import { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

interface CrystalProps {
  position: [number, number, number];
  scale?: number;
  color?: string;
  speed?: number;
}

function Crystal({ position, scale = 1, color = "#00f0ff", speed = 1 }: CrystalProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const initialY = position[1];

  useFrame(({ clock }) => {
    if (!meshRef.current) return;
    const t = clock.getElapsedTime() * speed;
    meshRef.current.position.y = initialY + Math.sin(t) * 0.5;
    meshRef.current.rotation.y = t * 0.3;
    meshRef.current.rotation.z = Math.sin(t * 0.5) * 0.1;
  });

  return (
    <mesh ref={meshRef} position={position} scale={scale}>
      <octahedronGeometry args={[1, 0]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={0.5}
        transparent
        opacity={0.7}
        roughness={0.1}
        metalness={0.8}
      />
    </mesh>
  );
}

function DataStream({ start, end, color }: { start: THREE.Vector3; end: THREE.Vector3; color: string }) {
  const ref = useRef<THREE.Points>(null);

  const { positions, velocities } = useMemo(() => {
    const count = 30;
    const pos = new Float32Array(count * 3);
    const vel = new Float32Array(count);

    for (let i = 0; i < count; i++) {
      const t = i / count;
      pos[i * 3] = THREE.MathUtils.lerp(start.x, end.x, t) + (Math.random() - 0.5) * 0.5;
      pos[i * 3 + 1] = THREE.MathUtils.lerp(start.y, end.y, t) + (Math.random() - 0.5) * 0.5;
      pos[i * 3 + 2] = THREE.MathUtils.lerp(start.z, end.z, t) + (Math.random() - 0.5) * 0.5;
      vel[i] = 0.5 + Math.random() * 1.5;
    }

    return { positions: pos, velocities: vel };
  }, [start, end]);

  useFrame(({ clock }) => {
    if (!ref.current) return;
    const posAttr = ref.current.geometry.attributes.position;
    const t = clock.getElapsedTime();

    for (let i = 0; i < velocities.length; i++) {
      const progress = ((t * velocities[i] * 0.1 + i / velocities.length) % 1);
      posAttr.setX(i, THREE.MathUtils.lerp(start.x, end.x, progress) + Math.sin(t + i) * 0.3);
      posAttr.setY(i, THREE.MathUtils.lerp(start.y, end.y, progress) + Math.cos(t * 0.7 + i) * 0.3);
      posAttr.setZ(i, THREE.MathUtils.lerp(start.z, end.z, progress));
    }
    posAttr.needsUpdate = true;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
          count={positions.length / 3}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.08}
        color={color}
        transparent
        opacity={0.8}
        sizeAttenuation
      />
    </points>
  );
}

export function FloatingElements() {
  const crystals: CrystalProps[] = useMemo(
    () => [
      { position: [-8, 6, -5], scale: 0.6, color: "#00f0ff", speed: 0.8 },
      { position: [10, 8, -10], scale: 0.4, color: "#00f0ff", speed: 1.2 },
      { position: [-5, 10, -18], scale: 0.8, color: "#4488ff", speed: 0.6 },
      { position: [7, 5, -25], scale: 0.5, color: "#00f0ff", speed: 1.0 },
      { position: [-12, 7, -30], scale: 0.7, color: "#8844ff", speed: 0.9 },
      { position: [3, 12, -15], scale: 0.3, color: "#00f0ff", speed: 1.4 },
      { position: [-3, 9, -40], scale: 0.9, color: "#ff6b2b", speed: 0.5 },
      { position: [12, 6, -35], scale: 0.4, color: "#00f0ff", speed: 1.1 },
    ],
    []
  );

  const streams = useMemo(
    () => [
      { start: new THREE.Vector3(-15, 5, 0), end: new THREE.Vector3(15, 8, -20), color: "#00f0ff" },
      { start: new THREE.Vector3(10, 3, -10), end: new THREE.Vector3(-10, 10, -35), color: "#4488ff" },
      { start: new THREE.Vector3(0, 12, -5), end: new THREE.Vector3(5, 4, -45), color: "#8844ff" },
    ],
    []
  );

  return (
    <group>
      {crystals.map((props, i) => (
        <Crystal key={i} {...props} />
      ))}
      {streams.map((props, i) => (
        <DataStream key={i} {...props} />
      ))}
    </group>
  );
}
