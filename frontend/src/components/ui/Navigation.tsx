"use client";

import { motion } from "framer-motion";
import { useAppState, type AppPhase } from "@/components/providers/AppStateProvider";
import { Shield } from "lucide-react";

const phases: { id: AppPhase; label: string }[] = [
  { id: "landing", label: "Threshold" },
  { id: "upload", label: "Upload" },
  { id: "analyzing", label: "Analysis" },
  { id: "timeline", label: "Timeline" },
  { id: "report", label: "Report" },
];

export function Navigation() {
  const { phase, setPhase, analysisState } = useAppState();

  const canNavigate = (targetPhase: AppPhase): boolean => {
    if (targetPhase === "landing" || targetPhase === "upload") return true;
    if (targetPhase === "analyzing" && analysisState.job) return true;
    if (targetPhase === "timeline" && analysisState.report) return true;
    if (targetPhase === "report" && analysisState.report) return true;
    return false;
  };

  return (
    <motion.nav
      className="fixed top-0 left-0 right-0 z-50 px-4 py-3"
      initial={{ y: -60, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.8, delay: 0.5 }}
    >
      <div className="mx-auto max-w-6xl flex items-center justify-between">
        {/* Logo */}
        <button
          onClick={() => setPhase("landing")}
          className="flex items-center gap-2 group"
        >
          <Shield className="h-6 w-6 text-cyan-400 group-hover:text-cyan-300 transition-colors" />
          <span className="text-lg font-bold tracking-tight text-white/90 group-hover:text-white transition-colors">
            TruthTrace
          </span>
        </button>

        {/* Phase indicators */}
        <div className="hidden sm:flex items-center gap-1">
          {phases.map(({ id, label }) => {
            const isActive = phase === id;
            const accessible = canNavigate(id);

            return (
              <button
                key={id}
                onClick={() => accessible && setPhase(id)}
                disabled={!accessible}
                className={`relative px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-300 ${
                  isActive
                    ? "text-cyan-400"
                    : accessible
                    ? "text-gray-500 hover:text-gray-300"
                    : "text-gray-700 cursor-not-allowed"
                }`}
              >
                {isActive && (
                  <motion.div
                    className="absolute inset-0 rounded-lg bg-cyan-400/10 border border-cyan-400/20"
                    layoutId="nav-indicator"
                    transition={{ type: "spring", bounce: 0.2, duration: 0.5 }}
                  />
                )}
                <span className="relative z-10">{label}</span>
              </button>
            );
          })}
        </div>

        {/* Phase dot indicator (mobile) */}
        <div className="flex sm:hidden items-center gap-1.5">
          {phases.map(({ id }) => (
            <div
              key={id}
              className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${
                phase === id ? "bg-cyan-400 scale-125" : "bg-gray-700"
              }`}
            />
          ))}
        </div>
      </div>
    </motion.nav>
  );
}
