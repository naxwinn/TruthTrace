"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef } from "react";
import { AppStateProvider, useAppState } from "@/components/providers/AppStateProvider";
import { HeroSection } from "@/components/ui/HeroSection";
import { UploadInterface } from "@/components/ui/UploadInterface";
import { AnalysisView } from "@/components/ui/AnalysisView";
import { TimelineView } from "@/components/ui/TimelineView";
import { ReportView } from "@/components/ui/ReportView";
import { Navigation } from "@/components/ui/Navigation";
import { JourneySections } from "@/components/ui/JourneySections";
import { AnimatePresence } from "framer-motion";

const Scene = dynamic(
  () => import("@/components/three/Scene").then((mod) => ({ default: mod.Scene })),
  { ssr: false }
);

function AppContent() {
  const { phase, setScrollProgress } = useAppState();
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleScroll = () => {
      if (!containerRef.current) return;
      const scrollHeight = containerRef.current.scrollHeight - window.innerHeight;
      const progress = scrollHeight > 0 ? window.scrollY / scrollHeight : 0;
      setScrollProgress(Math.min(1, Math.max(0, progress)));
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [setScrollProgress]);

  return (
    <div ref={containerRef} className="relative">
      {/* 3D Background */}
      <Scene />

      {/* Navigation */}
      <Navigation />

      {/* Content Overlay */}
      <div className="relative z-10">
        <AnimatePresence mode="wait">
          {phase === "landing" && (
            <div key="landing">
              <HeroSection />
              <JourneySections />
            </div>
          )}
          {phase === "upload" && <UploadInterface key="upload" />}
          {phase === "analyzing" && <AnalysisView key="analyzing" />}
          {phase === "timeline" && <TimelineView key="timeline" />}
          {phase === "report" && <ReportView key="report" />}
        </AnimatePresence>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <AppStateProvider>
      <AppContent />
    </AppStateProvider>
  );
}
