"use client";

import { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

function MetadataRing({ radius, segments, speed, color, yOffset }: {
  radius: number;
  segments: number;
  speed: number;
  color: string;
  yOffset: number;
}) {
  const ref = useRef<THREE.LineLoop>(null);

  const geometry = useMemo(() => {
    const points: THREE.Vector3[] = [];
    for (let i = 0; i <= segments; i++) {
      const angle = (i / segments) * Math.PI * 2;
      const wobble = Math.sin(angle * 3) * 0.3 + Math.cos(angle * 5) * 0.15;
      points.push(
        new THREE.Vector3(
          Math.cos(angle) * (radius + wobble),
          yOffset + Math.sin(angle * 4) * 0.2,
          Math.sin(angle) * (radius + wobble)
        )
      );
    }
    return new THREE.BufferGeometry().setFromPoints(points);
  }, [radius, segments, yOffset]);

  useFrame(({ clock }) => {
    if (!ref.current) return;
    ref.current.rotation.y = clock.getElapsedTime() * speed;
    ref.current.rotation.x = Math.sin(clock.getElapsedTime() * 0.3) * 0.1;
  });

  return (
    <lineLoop ref={ref} geometry={geometry}>
      <lineBasicMaterial color={color} transparent opacity={0.6} />
    </lineLoop>
  );
}

function MetadataNode({ position, size }: { position: [number, number, number]; size: number }) {
  const ref = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (!ref.current) return;
    const t = clock.getElapsedTime();
    ref.current.scale.setScalar(size * (1 + Math.sin(t * 2 + position[0]) * 0.2));
  });

  return (
    <mesh ref={ref} position={position}>
      <dodecahedronGeometry args={[size, 0]} />
      <meshStandardMaterial
        color="#8844ff"
        emissive="#4488ff"
        emissiveIntensity={0.6}
        transparent
        opacity={0.7}
        wireframe
      />
    </mesh>
  );
}

export function MetadataCore() {
  const groupRef = useRef<THREE.Group>(null);

  const nodes = useMemo(() => {
    const result: { position: [number, number, number]; size: number }[] = [];
    for (let i = 0; i < 20; i++) {
      const phi = Math.acos(2 * Math.random() - 1);
      const theta = Math.random() * Math.PI * 2;
      const r = 3 + Math.random() * 3;
      result.push({
        position: [
          r * Math.sin(phi) * Math.cos(theta),
          r * Math.cos(phi),
          r * Math.sin(phi) * Math.sin(theta),
        ],
        size: 0.1 + Math.random() * 0.25,
      });
    }
    return result;
  }, []);

  // Connection lines between nodes
  const connections = useMemo(() => {
    const lines: THREE.Vector3[][] = [];
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dist = new THREE.Vector3(...nodes[i].position).distanceTo(
          new THREE.Vector3(...nodes[j].position)
        );
        if (dist < 4) {
          lines.push([
            new THREE.Vector3(...nodes[i].position),
            new THREE.Vector3(...nodes[j].position),
          ]);
        }
      }
    }
    return lines;
  }, [nodes]);

  useFrame(({ clock }) => {
    if (!groupRef.current) return;
    groupRef.current.rotation.y = clock.getElapsedTime() * 0.05;
  });

  return (
    <group ref={groupRef} position={[0, 10, -70]}>
      {/* Orbital rings */}
      <MetadataRing radius={5} segments={64} speed={0.1} color="#00f0ff" yOffset={0} />
      <MetadataRing radius={4} segments={48} speed={-0.15} color="#8844ff" yOffset={1} />
      <MetadataRing radius={6} segments={80} speed={0.08} color="#4488ff" yOffset={-0.5} />

      {/* Nodes */}
      {nodes.map((node, i) => (
        <MetadataNode key={i} {...node} />
      ))}

      {/* Connections */}
      {connections.map((line, i) => (
        <line key={i}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              args={[new Float32Array(line.flatMap((v) => [v.x, v.y, v.z])), 3]}
              count={2}
              itemSize={3}
            />
          </bufferGeometry>
          <lineBasicMaterial color="#00f0ff" transparent opacity={0.15} />
        </line>
      ))}

      {/* Central core */}
      <mesh>
        <sphereGeometry args={[0.5, 16, 16]} />
        <meshStandardMaterial
          color="#00f0ff"
          emissive="#00f0ff"
          emissiveIntensity={1}
          transparent
          opacity={0.8}
        />
      </mesh>
      <pointLight intensity={3} color="#00f0ff" distance={12} />
    </group>
  );
}
