"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { useAppState } from "@/components/providers/AppStateProvider";
import * as THREE from "three";

const CAMERA_POSITIONS: Record<string, { pos: THREE.Vector3; lookAt: THREE.Vector3 }> = {
  landing: {
    pos: new THREE.Vector3(0, 8, 25),
    lookAt: new THREE.Vector3(0, 2, 0),
  },
  upload: {
    pos: new THREE.Vector3(0, 6, 15),
    lookAt: new THREE.Vector3(0, 3, 0),
  },
  analyzing: {
    pos: new THREE.Vector3(-5, 3, -5),
    lookAt: new THREE.Vector3(0, 0, -15),
  },
  timeline: {
    pos: new THREE.Vector3(5, 10, -20),
    lookAt: new THREE.Vector3(0, 5, -30),
  },
  report: {
    pos: new THREE.Vector3(0, 12, -35),
    lookAt: new THREE.Vector3(0, 8, -45),
  },
};

export function CameraController() {
  const { phase, scrollProgress } = useAppState();
  const currentPos = useRef(new THREE.Vector3(0, 8, 25));
  const currentLookAt = useRef(new THREE.Vector3(0, 2, 0));

  useFrame(({ camera }) => {
    const target = CAMERA_POSITIONS[phase] || CAMERA_POSITIONS.landing;

    // During landing phase, add scroll-based parallax
    let targetPos = target.pos.clone();
    let targetLookAt = target.lookAt.clone();

    if (phase === "landing") {
      const scrollOffset = scrollProgress * 30;
      targetPos = new THREE.Vector3(
        Math.sin(scrollProgress * Math.PI * 0.5) * 3,
        8 - scrollProgress * 4,
        25 - scrollOffset
      );
      targetLookAt = new THREE.Vector3(
        0,
        2 - scrollProgress * 2,
        -scrollOffset
      );
    }

    currentPos.current.lerp(targetPos, 0.02);
    currentLookAt.current.lerp(targetLookAt, 0.02);

    camera.position.copy(currentPos.current);
    camera.lookAt(currentLookAt.current);
  });

  return null;
}
