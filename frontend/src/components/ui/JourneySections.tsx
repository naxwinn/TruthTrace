"use client";

import { motion } from "framer-motion";
import { useAppState } from "@/components/providers/AppStateProvider";

export function JourneySections() {
  const { phase, scrollProgress } = useAppState();

  if (phase !== "landing") return null;

  return (
    <div className="relative z-10 pointer-events-none">
      {/* Spacer for hero */}
      <div className="h-screen" />

      {/* Audio Abyss Section */}
      <motion.section
        className="min-h-screen flex items-center justify-center px-4"
        style={{ opacity: Math.min(1, Math.max(0, (scrollProgress - 0.15) * 4)) }}
      >
        <div className="max-w-2xl text-center">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 1 }}
            viewport={{ once: true }}
          >
            <span className="text-xs uppercase tracking-[0.3em] text-cyan-400/60 font-mono">
              Layer 01
            </span>
            <h2 className="mt-4 text-4xl sm:text-5xl font-bold text-white/90">
              The Audio Abyss
            </h2>
            <p className="mt-4 text-gray-400 leading-relaxed">
              Deep within the sonic canyon, our detectors identify splicing artifacts, 
              voice cloning signatures, and frequency anomalies invisible to the human ear. 
              Every waveform tells a story of authenticity or deception.
            </p>
            <div className="mt-6 flex justify-center gap-4">
              <span className="text-xs px-3 py-1.5 rounded-full border border-cyan-500/30 text-cyan-400/80 font-mono">
                Splicing Detection
              </span>
              <span className="text-xs px-3 py-1.5 rounded-full border border-cyan-500/30 text-cyan-400/80 font-mono">
                Voice Cloning
              </span>
            </div>
          </motion.div>
        </div>
      </motion.section>

      {/* Visual Rift Section */}
      <motion.section
        className="min-h-screen flex items-center justify-center px-4"
        style={{ opacity: Math.min(1, Math.max(0, (scrollProgress - 0.4) * 4)) }}
      >
        <div className="max-w-2xl text-center">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 1 }}
            viewport={{ once: true }}
          >
            <span className="text-xs uppercase tracking-[0.3em] text-amber-400/60 font-mono">
              Layer 02
            </span>
            <h2 className="mt-4 text-4xl sm:text-5xl font-bold text-white/90">
              The Visual Rift
            </h2>
            <p className="mt-4 text-gray-400 leading-relaxed">
              At the mountain peaks, fractures in visual continuity reveal frame-level 
              manipulation. Optical flow mapping, GOP structure analysis, and compression 
              artifact detection expose the deepest forgeries.
            </p>
            <div className="mt-6 flex justify-center gap-4">
              <span className="text-xs px-3 py-1.5 rounded-full border border-amber-500/30 text-amber-400/80 font-mono">
                Optical Flow
              </span>
              <span className="text-xs px-3 py-1.5 rounded-full border border-amber-500/30 text-amber-400/80 font-mono">
                GOP Analysis
              </span>
              <span className="text-xs px-3 py-1.5 rounded-full border border-amber-500/30 text-amber-400/80 font-mono">
                Compression
              </span>
            </div>
          </motion.div>
        </div>
      </motion.section>

      {/* Metadata Core Section */}
      <motion.section
        className="min-h-screen flex items-center justify-center px-4"
        style={{ opacity: Math.min(1, Math.max(0, (scrollProgress - 0.65) * 4)) }}
      >
        <div className="max-w-2xl text-center">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 1 }}
            viewport={{ once: true }}
          >
            <span className="text-xs uppercase tracking-[0.3em] text-purple-400/60 font-mono">
              Layer 03
            </span>
            <h2 className="mt-4 text-4xl sm:text-5xl font-bold text-white/90">
              The Metadata Core
            </h2>
            <p className="mt-4 text-gray-400 leading-relaxed">
              At the heart of every file lies its hidden history — timestamps, encoding 
              parameters, and device fingerprints form a constellation of truth. Our analysis 
              maps these invisible layers to uncover inconsistencies.
            </p>
            <div className="mt-6 flex justify-center gap-4">
              <span className="text-xs px-3 py-1.5 rounded-full border border-purple-500/30 text-purple-400/80 font-mono">
                Metadata Forensics
              </span>
              <span className="text-xs px-3 py-1.5 rounded-full border border-purple-500/30 text-purple-400/80 font-mono">
                Anomaly Detection
              </span>
            </div>
          </motion.div>
        </div>
      </motion.section>

      {/* Final CTA */}
      <motion.section
        className="min-h-[50vh] flex items-center justify-center px-4 pointer-events-auto"
        style={{ opacity: Math.min(1, Math.max(0, (scrollProgress - 0.85) * 6)) }}
      >
        <div className="text-center">
          <p className="text-gray-400 mb-6">Ready to uncover the truth?</p>
          <InitializeScanButton />
        </div>
      </motion.section>
    </div>
  );
}

function InitializeScanButton() {
  const { setPhase } = useAppState();

  return (
    <button
      onClick={() => setPhase("upload")}
      className="group relative inline-flex items-center gap-3 px-8 py-4 text-lg font-semibold rounded-xl overflow-hidden transition-all duration-500 hover:scale-105"
    >
      <div className="absolute inset-0 bg-gradient-to-r from-cyan-600 to-blue-600 opacity-80 group-hover:opacity-100 transition-opacity" />
      <span className="relative z-10 text-white">Begin Analysis</span>
      <svg
        className="relative z-10 w-5 h-5 text-white group-hover:translate-x-1 transition-transform"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
      </svg>
    </button>
  );
}
