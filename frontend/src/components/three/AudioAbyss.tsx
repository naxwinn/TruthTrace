"use client";

import { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

export function AudioAbyss() {
  const meshRef = useRef<THREE.Mesh>(null);
  const waveformRef = useRef<THREE.LineSegments>(null);

  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(16, 30, 64, 64);
    return geo;
  }, []);

  const material = useMemo(() => {
    return new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uColor1: { value: new THREE.Color("#00f0ff") },
        uColor2: { value: new THREE.Color("#ff6b2b") },
      },
      vertexShader: `
        uniform float uTime;
        varying vec2 vUv;
        varying float vElevation;
        
        void main() {
          vUv = uv;
          vec3 pos = position;
          
          // Sound wave morphing terrain
          float wave1 = sin(pos.x * 2.0 + uTime * 1.5) * 0.5;
          float wave2 = sin(pos.x * 4.0 - uTime * 2.0) * 0.25;
          float wave3 = cos(pos.y * 0.5 + uTime * 0.8) * 0.3;
          float wave4 = sin((pos.x + pos.y) * 3.0 + uTime * 1.2) * 0.15;
          
          pos.z = wave1 + wave2 + wave3 + wave4;
          vElevation = pos.z;
          
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        uniform float uTime;
        uniform vec3 uColor1;
        uniform vec3 uColor2;
        varying vec2 vUv;
        varying float vElevation;
        
        void main() {
          float t = (vElevation + 1.0) / 2.0;
          vec3 color = mix(uColor1, uColor2, t);
          
          // Pulsing glow
          float pulse = sin(uTime * 2.0 + vUv.x * 10.0) * 0.5 + 0.5;
          color += color * pulse * 0.2;
          
          // Fade at edges
          float edgeFade = smoothstep(0.0, 0.1, vUv.x) * smoothstep(1.0, 0.9, vUv.x);
          edgeFade *= smoothstep(0.0, 0.1, vUv.y) * smoothstep(1.0, 0.9, vUv.y);
          
          gl_FragColor = vec4(color, edgeFade * 0.6);
        }
      `,
      transparent: true,
      side: THREE.DoubleSide,
    });
  }, []);

  // Floating fractured waveform lines
  const waveformGeo = useMemo(() => {
    const points: number[] = [];
    const segments = 100;

    for (let line = 0; line < 5; line++) {
      const yOffset = (line - 2) * 2;
      for (let i = 0; i < segments; i++) {
        const x = (i / segments) * 16 - 8;
        const y = yOffset + Math.sin(x * 2 + line) * 0.5;
        const z = Math.sin(x * 3 + line * 2) * 0.3;
        points.push(x, y, z);

        if (i < segments - 1) {
          const nx = ((i + 1) / segments) * 16 - 8;
          const ny = yOffset + Math.sin(nx * 2 + line) * 0.5;
          const nz = Math.sin(nx * 3 + line * 2) * 0.3;
          points.push(nx, ny, nz);
        }
      }
    }

    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(points, 3));
    return geo;
  }, []);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    material.uniforms.uTime.value = t;

    if (waveformRef.current) {
      const positions = waveformRef.current.geometry.attributes.position;
      for (let i = 0; i < positions.count; i++) {
        const x = positions.getX(i);
        const baseY = positions.getY(i);
        positions.setY(i, baseY + Math.sin(t * 2 + x * 0.5 + i * 0.01) * 0.01);
      }
      positions.needsUpdate = true;
    }
  });

  return (
    <group position={[0, -4, -35]}>
      <mesh
        ref={meshRef}
        geometry={geometry}
        material={material}
        rotation={[-Math.PI / 2.5, 0, 0]}
      />
      <lineSegments ref={waveformRef} geometry={waveformGeo} position={[0, 2, 0]}>
        <lineBasicMaterial color="#00f0ff" transparent opacity={0.4} />
      </lineSegments>
    </group>
  );
}
