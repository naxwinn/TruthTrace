"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAppState } from "@/components/providers/AppStateProvider";
import { Clock, AlertTriangle, Shield, ChevronRight } from "lucide-react";
import type { Finding, TimelineEntry } from "@/lib/api";

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.7) return "bg-red-500";
  if (confidence >= 0.5) return "bg-amber-500";
  return "bg-yellow-500";
}

function getConfidenceTextColor(confidence: number): string {
  if (confidence >= 0.7) return "text-red-400";
  if (confidence >= 0.5) return "text-amber-400";
  return "text-yellow-400";
}

export function TimelineView() {
  const { phase, setPhase, analysisState } = useAppState();
  const [selectedEntry, setSelectedEntry] = useState<TimelineEntry | null>(null);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);

  if (phase !== "timeline") return null;

  const report = analysisState.report;
  if (!report) return null;

  const duration = report.file.duration || 60;
  const score = report.job.authenticity_score ?? 1;
  const verdict = score >= 0.7 ? "Likely Authentic" : score >= 0.4 ? "Suspicious" : "Likely Tampered";
  const verdictColor = score >= 0.7 ? "text-emerald-400" : score >= 0.4 ? "text-amber-400" : "text-red-400";

  return (
    <motion.section
      className="relative z-10 flex flex-col items-center justify-start min-h-screen px-4 py-12 overflow-y-auto"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.8 }}
    >
      <motion.div
        className="w-full max-w-5xl"
        initial={{ y: 30 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.6 }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-3xl font-bold">
              <span className="bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                Analysis Timeline
              </span>
            </h2>
            <p className="text-gray-500 text-sm mt-1 font-mono">
              {report.file.original_filename}
            </p>
          </div>
          <div className={`flex items-center gap-2 px-4 py-2 rounded-xl glass ${verdictColor}`}>
            <Shield className="h-5 w-5" />
            <div className="text-right">
              <div className="text-sm font-bold">{(score * 100).toFixed(0)}%</div>
              <div className="text-xs opacity-80">{verdict}</div>
            </div>
          </div>
        </div>

        {/* Timeline Bar */}
        <motion.div
          className="glass rounded-2xl p-6 mb-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="flex items-center gap-2 mb-4">
            <Clock className="h-4 w-4 text-cyan-400" />
            <span className="text-sm text-gray-400">
              Duration: {formatTime(duration)}
            </span>
            <span className="text-xs text-gray-600 ml-auto">
              {report.timeline.length} suspicious region{report.timeline.length !== 1 ? "s" : ""}
            </span>
          </div>

          <div className="relative h-16 bg-gray-800/50 rounded-xl overflow-hidden border border-gray-700/30">
            {/* Grid lines */}
            {Array.from({ length: 9 }).map((_, i) => (
              <div
                key={i}
                className="absolute top-0 bottom-0 border-l border-gray-700/30"
                style={{ left: `${(i + 1) * 10}%` }}
              />
            ))}

            {/* Time markers */}
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={`marker-${i}`}
                className="absolute bottom-0"
                style={{ left: `${(i + 1) * 20}%` }}
              >
                <span className="absolute -bottom-6 -translate-x-1/2 text-[10px] text-gray-500 font-mono">
                  {formatTime((duration * (i + 1)) / 5)}
                </span>
              </div>
            ))}

            {/* Suspicious segments */}
            {report.timeline.map((entry, i) => {
              const left = (entry.start / duration) * 100;
              const width = Math.max(((entry.end - entry.start) / duration) * 100, 1.5);
              const isSelected = selectedEntry === entry;

              return (
                <motion.div
                  key={i}
                  className={`absolute top-2 bottom-2 rounded-md cursor-pointer transition-all ${getConfidenceColor(entry.confidence)} ${
                    isSelected ? "ring-2 ring-white/50 z-10" : "opacity-70 hover:opacity-100"
                  }`}
                  style={{ left: `${left}%`, width: `${width}%`, minWidth: "6px" }}
                  onClick={() => {
                    setSelectedEntry(isSelected ? null : entry);
                    setSelectedFinding(null);
                  }}
                  whileHover={{ scaleY: 1.1 }}
                  layoutId={`segment-${i}`}
                />
              );
            })}
          </div>

          <div className="h-6" />

          {/* Legend */}
          <div className="flex gap-4 text-xs text-gray-400">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-red-500 inline-block" /> High ≥70%
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-amber-500 inline-block" /> Medium 50-70%
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-yellow-500 inline-block" /> Low &lt;50%
            </span>
          </div>
        </motion.div>

        {/* Selected segment detail */}
        <AnimatePresence>
          {selectedEntry && (
            <motion.div
              className="glass rounded-2xl p-6 mb-6 border border-cyan-500/20"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
            >
              <h3 className="text-sm font-semibold text-cyan-400 mb-3 uppercase tracking-wider">
                Segment Detail
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500 block text-xs">Type</span>
                  <span className="capitalize font-medium">{selectedEntry.type.replace(/_/g, " ")}</span>
                </div>
                <div>
                  <span className="text-gray-500 block text-xs">Confidence</span>
                  <span className={`font-bold ${getConfidenceTextColor(selectedEntry.confidence)}`}>
                    {(selectedEntry.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-500 block text-xs">Start</span>
                  <span className="font-mono">{formatTime(selectedEntry.start)}</span>
                </div>
                <div>
                  <span className="text-gray-500 block text-xs">End</span>
                  <span className="font-mono">{formatTime(selectedEntry.end)}</span>
                </div>
              </div>
              <div className="mt-3 text-xs text-gray-500">
                Detector: <span className="text-gray-300 font-mono">{selectedEntry.detector}</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Findings List */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-400" />
            Findings ({report.findings.length})
          </h3>

          <div className="space-y-3">
            {report.findings.map((finding) => {
              const isSelected = selectedFinding?.id === finding.id;
              return (
                <motion.div
                  key={finding.id}
                  className={`glass rounded-xl p-4 cursor-pointer transition-all ${
                    isSelected ? "border-cyan-500/50 shadow-[0_0_20px_rgba(0,240,255,0.1)]" : ""
                  }`}
                  onClick={() => setSelectedFinding(isSelected ? null : finding)}
                  whileHover={{ x: 4 }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${getConfidenceColor(finding.confidence)}`} />
                      <span className="text-sm font-medium capitalize">
                        {finding.finding_type.replace(/_/g, " ")}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-gray-800/80 text-gray-400 font-mono">
                        {finding.detector_type}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-sm font-mono ${getConfidenceTextColor(finding.confidence)}`}>
                        {(finding.confidence * 100).toFixed(0)}%
                      </span>
                      <ChevronRight className={`h-4 w-4 text-gray-600 transition-transform ${isSelected ? "rotate-90" : ""}`} />
                    </div>
                  </div>

                  <AnimatePresence>
                    {isSelected && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mt-3 pt-3 border-t border-gray-800"
                      >
                        {finding.description && (
                          <p className="text-sm text-gray-400">{finding.description}</p>
                        )}
                        {finding.start_time !== null && (
                          <p className="text-xs text-gray-500 mt-2 font-mono">
                            ⏱ {formatTime(finding.start_time)}
                            {finding.end_time !== null && ` — ${formatTime(finding.end_time)}`}
                          </p>
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        {/* Actions */}
        <motion.div
          className="flex flex-wrap gap-4 mt-10 justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
        >
          <button
            onClick={() => setPhase("report")}
            className="group relative inline-flex items-center gap-2 px-6 py-3 text-sm font-semibold rounded-xl overflow-hidden transition-all hover:scale-105"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-600 to-blue-600 opacity-80 group-hover:opacity-100 transition-opacity" />
            <span className="relative z-10 text-white">View Full Report</span>
          </button>

          <button
            onClick={() => setPhase("upload")}
            className="px-6 py-3 text-sm font-medium rounded-xl border border-gray-700/50 text-gray-300 hover:bg-gray-800/50 transition-all"
          >
            Analyze Another File
          </button>

          <button
            onClick={() => setPhase("landing")}
            className="px-6 py-3 text-sm text-gray-500 hover:text-gray-300 transition-colors"
          >
            ← Back to Threshold
          </button>
        </motion.div>
      </motion.div>
    </motion.section>
  );
}
