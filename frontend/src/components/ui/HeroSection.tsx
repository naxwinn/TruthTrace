"use client";

import { motion } from "framer-motion";
import { useAppState } from "@/components/providers/AppStateProvider";

export function HeroSection() {
  const { phase, setPhase } = useAppState();

  if (phase !== "landing") return null;

  return (
    <motion.section
      className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 1.5 }}
    >
      {/* Mist overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-[#050508] via-transparent to-[#050508]/50 pointer-events-none" />

      <motion.div
        className="relative text-center"
        initial={{ y: 40, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 1.2, delay: 0.3 }}
      >
        {/* Subtitle */}
        <motion.p
          className="text-sm uppercase tracking-[0.4em] text-cyan-400/70 mb-4 font-mono"
          initial={{ opacity: 0, letterSpacing: "0.8em" }}
          animate={{ opacity: 1, letterSpacing: "0.4em" }}
          transition={{ duration: 2, delay: 0.5 }}
        >
          Media Forensics Analysis
        </motion.p>

        {/* Main Title */}
        <motion.h1
          className="text-7xl sm:text-9xl font-black tracking-tighter text-glow-cyan"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1.5, delay: 0.8 }}
        >
          <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-500 bg-clip-text text-transparent">
            TRUTH
          </span>
          <span className="text-white/90">TRACE</span>
        </motion.h1>

        {/* Description */}
        <motion.p
          className="mt-6 text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 1.5 }}
        >
          Detect audio splicing, voice cloning, frame manipulation, and metadata
          anomalies. Journey through the landscape of digital truth.
        </motion.p>

        {/* CTA */}
        <motion.div
          className="mt-12"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 2.0 }}
        >
          <button
            onClick={() => setPhase("upload")}
            className="group relative inline-flex items-center gap-3 px-8 py-4 text-lg font-semibold rounded-xl overflow-hidden transition-all duration-500 hover:scale-105"
          >
            {/* Button glow background */}
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-600 to-blue-600 opacity-80 group-hover:opacity-100 transition-opacity" />
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-400 to-blue-400 opacity-0 group-hover:opacity-30 blur-xl transition-opacity" />

            {/* Scan line animation */}
            <div className="absolute inset-0 overflow-hidden">
              <div className="absolute inset-x-0 h-px bg-white/30 animate-[scan-line_3s_linear_infinite]" />
            </div>

            <span className="relative z-10 text-white">Initialize Scan</span>
            <svg
              className="relative z-10 w-5 h-5 text-white group-hover:translate-x-1 transition-transform"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </button>
        </motion.div>

        {/* Scroll indicator */}
        <motion.div
          className="mt-20 flex flex-col items-center gap-2 text-gray-500"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 3 }}
        >
          <span className="text-xs uppercase tracking-widest">Explore the Landscape</span>
          <motion.div
            className="w-px h-8 bg-gradient-to-b from-cyan-400/50 to-transparent"
            animate={{ scaleY: [1, 1.5, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        </motion.div>
      </motion.div>
    </motion.section>
  );
}
