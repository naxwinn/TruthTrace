"use client";

import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAppState } from "@/components/providers/AppStateProvider";
import { getJob, getReport } from "@/lib/api";

export function AnalysisView() {
  const { phase, setPhase, analysisState, setJob, setReport } = useAppState();
  const [messageIndex, setMessageIndex] = useState(0);
  const [progress, setProgress] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  const messages = analysisState.analysisMessages;

  // Cycle through analysis messages
  useEffect(() => {
    if (phase !== "analyzing") return;

    intervalRef.current = setInterval(() => {
      setMessageIndex((prev) => {
        if (prev < messages.length - 1) return prev + 1;
        return prev;
      });
      setProgress((prev) => Math.min(prev + 12, 95));
    }, 2200);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [phase, messages.length]);

  // Poll job status
  useEffect(() => {
    if (phase !== "analyzing" || !analysisState.job) return;

    const pollJob = async () => {
      try {
        const updatedJob = await getJob(analysisState.job!.id);
        setJob(updatedJob);

        if (updatedJob.status === "complete") {
          const report = await getReport(updatedJob.id);
          setReport(report);
          setProgress(100);

          // Transition to timeline after report is ready
          setTimeout(() => {
            setPhase("timeline");
          }, 1500);

          if (pollingRef.current) clearInterval(pollingRef.current);
        } else if (updatedJob.status === "failed") {
          if (pollingRef.current) clearInterval(pollingRef.current);
        }
      } catch {
        // silently retry
      }
    };

    pollingRef.current = setInterval(pollJob, 3000);
    pollJob();

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [phase, analysisState.job, setJob, setReport, setPhase]);

  if (phase !== "analyzing") return null;

  return (
    <motion.section
      className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 1 }}
    >
      <motion.div
        className="glass-strong rounded-2xl p-12 max-w-lg w-full text-center"
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        {/* Scanning animation */}
        <div className="relative w-24 h-24 mx-auto mb-8">
          <motion.div
            className="absolute inset-0 rounded-full border-2 border-cyan-400/30"
            animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <motion.div
            className="absolute inset-2 rounded-full border-2 border-cyan-400/50"
            animate={{ scale: [1, 1.3, 1], opacity: [0.7, 0.2, 0.7] }}
            transition={{ duration: 2, repeat: Infinity, delay: 0.3 }}
          />
          <motion.div
            className="absolute inset-4 rounded-full border-2 border-cyan-400"
            animate={{ rotate: 360 }}
            transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
          />
          <div className="absolute inset-6 rounded-full bg-cyan-400/10 flex items-center justify-center">
            <div className="w-3 h-3 rounded-full bg-cyan-400 animate-pulse-glow" />
          </div>
        </div>

        {/* Title */}
        <h2 className="text-2xl font-bold text-white mb-2">
          Multi-Layer Analysis
        </h2>
        <p className="text-gray-500 text-sm mb-8">
          Running forensic detectors on your media file
        </p>

        {/* Progress bar */}
        <div className="w-full bg-gray-800/50 rounded-full h-1.5 mb-6 overflow-hidden">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500"
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>

        {/* Rotating messages */}
        <div className="h-8 relative overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.p
              key={messageIndex}
              className="text-sm font-mono text-cyan-400/80 absolute inset-x-0"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.4 }}
            >
              {messages[messageIndex]}
            </motion.p>
          </AnimatePresence>
        </div>

        {/* Detector badges */}
        <div className="flex flex-wrap justify-center gap-2 mt-8">
          {["Audio", "Video", "GOP", "Flow", "Meta"].map((detector, i) => (
            <motion.span
              key={detector}
              className={clsx(
                "text-xs px-3 py-1 rounded-full border font-mono transition-all duration-500",
                messageIndex >= i * 2
                  ? "border-cyan-500/50 text-cyan-400 bg-cyan-500/10"
                  : "border-gray-700/50 text-gray-600 bg-gray-800/30"
              )}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
            >
              {detector}
            </motion.span>
          ))}
        </div>
      </motion.div>
    </motion.section>
  );
}

function clsx(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}
