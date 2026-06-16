"use client";

import { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

export function Landscape() {
  const meshRef = useRef<THREE.Mesh>(null);

  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(200, 200, 128, 128);
    const positions = geo.attributes.position;

    for (let i = 0; i < positions.count; i++) {
      const x = positions.getX(i);
      const z = positions.getY(i);

      // Multi-octave noise for stylized mountains
      let height = 0;
      height += Math.sin(x * 0.05) * Math.cos(z * 0.05) * 8;
      height += Math.sin(x * 0.1 + 1.5) * Math.cos(z * 0.08 + 0.5) * 4;
      height += Math.sin(x * 0.2 + 3.0) * Math.cos(z * 0.15 + 1.0) * 2;
      height += Math.sin(x * 0.4) * Math.cos(z * 0.3) * 1;

      // Create valleys and peaks
      const distFromCenter = Math.sqrt(x * x + z * z);
      const falloff = Math.max(0, 1 - distFromCenter / 100);
      height *= falloff;

      // Create a canyon in the middle for the "Audio Abyss"
      if (z < -20 && z > -50 && Math.abs(x) < 8) {
        height -= 6 * (1 - Math.abs(x) / 8);
      }

      // Create a peak for the "Visual Rift"
      if (z < -50 && z > -70 && Math.abs(x) < 15) {
        height += 5 * Math.exp(-((x * x) / 50));
      }

      positions.setZ(i, height);
    }

    geo.computeVertexNormals();
    return geo;
  }, []);

  const material = useMemo(() => {
    return new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uColorLow: { value: new THREE.Color("#0a0a1a") },
        uColorMid: { value: new THREE.Color("#1a0a2e") },
        uColorHigh: { value: new THREE.Color("#00f0ff") },
        uGlowColor: { value: new THREE.Color("#00f0ff") },
      },
      vertexShader: `
        varying vec3 vPosition;
        varying vec3 vNormal;
        varying float vElevation;
        
        void main() {
          vPosition = position;
          vNormal = normalize(normalMatrix * normal);
          vElevation = position.z;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform float uTime;
        uniform vec3 uColorLow;
        uniform vec3 uColorMid;
        uniform vec3 uColorHigh;
        uniform vec3 uGlowColor;
        
        varying vec3 vPosition;
        varying vec3 vNormal;
        varying float vElevation;
        
        void main() {
          float normalizedHeight = clamp((vElevation + 6.0) / 16.0, 0.0, 1.0);
          
          vec3 color = mix(uColorLow, uColorMid, smoothstep(0.0, 0.4, normalizedHeight));
          color = mix(color, uColorHigh, smoothstep(0.7, 1.0, normalizedHeight) * 0.3);
          
          // Edge glow effect on ridges
          float edge = 1.0 - abs(dot(vNormal, vec3(0.0, 0.0, 1.0)));
          edge = pow(edge, 3.0);
          color += uGlowColor * edge * 0.15;
          
          // Animated scan lines
          float scanLine = sin(vPosition.y * 2.0 + uTime * 0.5) * 0.5 + 0.5;
          scanLine = pow(scanLine, 8.0);
          color += uGlowColor * scanLine * 0.05;
          
          // Wireframe-like grid glow
          float gridX = abs(fract(vPosition.x * 0.5) - 0.5);
          float gridY = abs(fract(vPosition.y * 0.5) - 0.5);
          float grid = min(gridX, gridY);
          float gridLine = 1.0 - smoothstep(0.0, 0.02, grid);
          color += uGlowColor * gridLine * 0.08;
          
          gl_FragColor = vec4(color, 1.0);
        }
      `,
      wireframe: false,
      side: THREE.DoubleSide,
    });
  }, []);

  useFrame(({ clock }) => {
    if (material.uniforms) {
      material.uniforms.uTime.value = clock.getElapsedTime();
    }
  });

  return (
    <mesh
      ref={meshRef}
      geometry={geometry}
      material={material}
      rotation={[-Math.PI / 2, 0, 0]}
      position={[0, -2, -40]}
    />
  );
}
