"use client";

import { useRef } from "react";
import { motion } from "framer-motion";
import { useAppState } from "@/components/providers/AppStateProvider";
import {
  FileText,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  Download,
  ArrowLeft,
} from "lucide-react";
import type { Finding } from "@/lib/api";

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function ReportView() {
  const { phase, setPhase, analysisState } = useAppState();
  const reportRef = useRef<HTMLDivElement>(null);

  if (phase !== "report") return null;

  const report = analysisState.report;
  if (!report) return null;

  const score = report.job.authenticity_score ?? 1;
  const tamperScore = 1 - score;
  const verdict =
    score >= 0.7 ? "Authentic" : score >= 0.4 ? "Suspicious" : "Tampered";
  const verdictColor =
    score >= 0.7
      ? "text-emerald-400"
      : score >= 0.4
      ? "text-amber-400"
      : "text-red-400";
  const verdictBorderColor =
    score >= 0.7
      ? "border-emerald-500/30"
      : score >= 0.4
      ? "border-amber-500/30"
      : "border-red-500/30";

  const highFindings = report.findings.filter((f) => f.confidence >= 0.7);
  const medFindings = report.findings.filter(
    (f) => f.confidence >= 0.5 && f.confidence < 0.7
  );
  const lowFindings = report.findings.filter((f) => f.confidence < 0.5);

  const handleGeneratePDF = () => {
    if (!reportRef.current) return;

    // Create a clean print layout
    const printWindow = window.open("", "_blank");
    if (!printWindow) return;

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>TruthTrace Forensic Report - ${report.file.original_filename}</title>
        <style>
          * { margin: 0; padding: 0; box-sizing: border-box; }
          body { font-family: system-ui, sans-serif; padding: 40px; color: #1a1a2e; line-height: 1.6; }
          h1 { font-size: 24px; margin-bottom: 8px; }
          h2 { font-size: 18px; margin-top: 24px; margin-bottom: 12px; color: #333; border-bottom: 2px solid #00f0ff; padding-bottom: 4px; }
          .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #050508; padding-bottom: 16px; margin-bottom: 24px; }
          .verdict { font-size: 28px; font-weight: bold; }
          .verdict.good { color: #059669; }
          .verdict.warn { color: #d97706; }
          .verdict.bad { color: #dc2626; }
          .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 12px 0; }
          .grid dt { color: #666; }
          .finding { padding: 8px 0; border-bottom: 1px solid #eee; }
          .finding-type { font-weight: 600; text-transform: capitalize; }
          .confidence { font-family: monospace; }
          .meta { color: #666; font-size: 12px; margin-top: 4px; }
          @media print { body { padding: 20px; } }
        </style>
      </head>
      <body>
        <div class="header">
          <div>
            <h1>TruthTrace Forensic Report</h1>
            <p style="color: #666;">Generated: ${new Date().toLocaleString()}</p>
          </div>
          <div class="verdict ${score >= 0.7 ? "good" : score >= 0.4 ? "warn" : "bad"}">
            ${verdict} (${(tamperScore * 100).toFixed(0)}% tampering probability)
          </div>
        </div>

        <h2>File Information</h2>
        <div class="grid">
          <dt>Filename</dt><dd>${report.file.original_filename}</dd>
          <dt>Size</dt><dd>${(report.file.file_size / 1024 / 1024).toFixed(2)} MB</dd>
          <dt>Type</dt><dd>${report.file.mime_type}</dd>
          <dt>Duration</dt><dd>${report.file.duration ? formatTime(report.file.duration) : "N/A"}</dd>
        </div>

        <h2>Summary</h2>
        <p>${report.summary}</p>

        <h2>Findings (${report.findings.length})</h2>
        ${report.findings
          .map(
            (f) => `
          <div class="finding">
            <span class="finding-type">${f.finding_type.replace(/_/g, " ")}</span>
            <span class="confidence"> — ${(f.confidence * 100).toFixed(0)}%</span>
            <span style="color: #888;"> [${f.detector_type}]</span>
            ${f.description ? `<p class="meta">${f.description}</p>` : ""}
            ${f.start_time !== null ? `<p class="meta">⏱ ${formatTime(f.start_time)}${f.end_time !== null ? ` — ${formatTime(f.end_time)}` : ""}</p>` : ""}
          </div>
        `
          )
          .join("")}

        <h2>Timeline Segments (${report.timeline.length})</h2>
        ${report.timeline
          .map(
            (t) => `
          <div class="finding">
            <span class="finding-type">${t.type.replace(/_/g, " ")}</span>
            <span class="confidence"> — ${(t.confidence * 100).toFixed(0)}%</span>
            <p class="meta">${formatTime(t.start)} — ${formatTime(t.end)} [${t.detector}]</p>
          </div>
        `
          )
          .join("")}
      </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };

  return (
    <motion.section
      className="relative z-10 flex flex-col items-center justify-start min-h-screen px-4 py-12 overflow-y-auto"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.8 }}
    >
      <motion.div
        ref={reportRef}
        className="w-full max-w-4xl"
        initial={{ y: 30 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.6 }}
      >
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <FileText className="h-6 w-6 text-cyan-400" />
          <h2 className="text-3xl font-bold">
            <span className="bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
              Forensic Report
            </span>
          </h2>
        </div>

        {/* Executive Summary */}
        <motion.div
          className={`glass rounded-2xl p-6 mb-6 border ${verdictBorderColor}`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <h3 className="text-lg font-semibold mb-4 text-gray-200">
            Executive Summary
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="text-center p-4 rounded-xl bg-gray-800/30 border border-gray-700/30">
              <Shield className={`h-8 w-8 mx-auto mb-2 ${verdictColor}`} />
              <div className={`text-xl font-bold ${verdictColor}`}>
                {verdict}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Tampering: {(tamperScore * 100).toFixed(0)}%
              </div>
            </div>
            <div className="text-center p-4 rounded-xl bg-gray-800/30 border border-gray-700/30">
              <AlertTriangle className="h-8 w-8 mx-auto mb-2 text-amber-400" />
              <div className="text-xl font-bold text-amber-400">
                {report.findings.length}
              </div>
              <div className="text-xs text-gray-500 mt-1">Findings</div>
            </div>
            <div className="text-center p-4 rounded-xl bg-gray-800/30 border border-gray-700/30">
              <Clock className="h-8 w-8 mx-auto mb-2 text-blue-400" />
              <div className="text-xl font-bold text-blue-400">
                {report.timeline.length}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Suspicious Segments
              </div>
            </div>
          </div>
          <p className="mt-4 text-sm text-gray-300">{report.summary}</p>
        </motion.div>

        {/* File Info */}
        <motion.div
          className="glass rounded-2xl p-6 mb-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h3 className="text-lg font-semibold mb-3 text-gray-200">
            File Information
          </h3>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <dt className="text-gray-500">Filename</dt>
            <dd className="font-mono text-gray-300">
              {report.file.original_filename}
            </dd>
            <dt className="text-gray-500">Size</dt>
            <dd className="font-mono text-gray-300">
              {(report.file.file_size / 1024 / 1024).toFixed(2)} MB
            </dd>
            <dt className="text-gray-500">Type</dt>
            <dd className="font-mono text-gray-300">{report.file.mime_type}</dd>
            <dt className="text-gray-500">Duration</dt>
            <dd className="font-mono text-gray-300">
              {report.file.duration ? formatTime(report.file.duration) : "N/A"}
            </dd>
          </dl>
        </motion.div>

        {/* Findings by severity */}
        {highFindings.length > 0 && (
          <FindingsSection
            title="High Confidence Findings"
            findings={highFindings}
            color="red"
            delay={0.3}
          />
        )}
        {medFindings.length > 0 && (
          <FindingsSection
            title="Medium Confidence Findings"
            findings={medFindings}
            color="amber"
            delay={0.4}
          />
        )}
        {lowFindings.length > 0 && (
          <FindingsSection
            title="Low Confidence Findings"
            findings={lowFindings}
            color="yellow"
            delay={0.5}
          />
        )}

        {/* Recommendations */}
        <motion.div
          className="glass rounded-2xl p-6 mt-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <h3 className="text-lg font-semibold mb-3 text-gray-200">
            Recommendations
          </h3>
          <ul className="space-y-3 text-sm text-gray-300">
            {score < 0.4 && (
              <li className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-red-400 mt-0.5 shrink-0" />
                <span>
                  High probability of tampering detected. Manual expert review
                  strongly recommended.
                </span>
              </li>
            )}
            {highFindings.length > 0 && (
              <li className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-400 mt-0.5 shrink-0" />
                <span>
                  Multiple high-confidence anomalies found. Cross-reference with
                  original source material.
                </span>
              </li>
            )}
            {report.findings.length === 0 && (
              <li className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-emerald-400 mt-0.5 shrink-0" />
                <span>
                  No tampering indicators detected. File appears authentic.
                </span>
              </li>
            )}
            <li className="flex items-start gap-2">
              <Clock className="h-4 w-4 text-blue-400 mt-0.5 shrink-0" />
              <span>
                Review the timeline visualization for temporal context of
                anomalies.
              </span>
            </li>
          </ul>
        </motion.div>

        {/* Actions */}
        <motion.div
          className="flex flex-wrap gap-4 mt-10 justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
        >
          <button
            onClick={handleGeneratePDF}
            className="group relative inline-flex items-center gap-2 px-6 py-3 text-sm font-semibold rounded-xl overflow-hidden transition-all hover:scale-105"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-600 to-blue-600 opacity-80 group-hover:opacity-100 transition-opacity" />
            <Download className="relative z-10 h-4 w-4 text-white" />
            <span className="relative z-10 text-white">Generate PDF Report</span>
          </button>

          <button
            onClick={() => setPhase("timeline")}
            className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium rounded-xl border border-gray-700/50 text-gray-300 hover:bg-gray-800/50 transition-all"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Timeline
          </button>

          <button
            onClick={() => setPhase("landing")}
            className="px-6 py-3 text-sm text-gray-500 hover:text-gray-300 transition-colors"
          >
            ← Return to Threshold
          </button>
        </motion.div>
      </motion.div>
    </motion.section>
  );
}

function FindingsSection({
  title,
  findings,
  color,
  delay,
}: {
  title: string;
  findings: Finding[];
  color: "red" | "amber" | "yellow";
  delay: number;
}) {
  const borderColor =
    color === "red"
      ? "border-red-500/30"
      : color === "amber"
      ? "border-amber-500/30"
      : "border-yellow-500/30";
  const dotColor =
    color === "red"
      ? "bg-red-500"
      : color === "amber"
      ? "bg-amber-500"
      : "bg-yellow-500";

  return (
    <motion.div
      className={`glass rounded-2xl p-6 mb-4 border ${borderColor}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
    >
      <h3 className="text-lg font-semibold mb-3 text-gray-200">{title}</h3>
      <div className="space-y-3">
        {findings.map((f, i) => (
          <div key={i} className="flex items-start gap-3 text-sm">
            <span className={`shrink-0 mt-1.5 w-2 h-2 rounded-full ${dotColor}`} />
            <div>
              <span className="font-medium capitalize text-gray-200">
                {f.finding_type.replace(/_/g, " ")}
              </span>
              <span className="text-gray-500 ml-2 font-mono">
                ({(f.confidence * 100).toFixed(0)}%)
              </span>
              <span className="text-gray-600 ml-2 text-xs">
                [{f.detector_type}]
              </span>
              {f.description && (
                <p className="text-gray-400 text-xs mt-0.5">{f.description}</p>
              )}
              {f.start_time !== null && (
                <p className="text-gray-500 text-xs font-mono mt-0.5">
                  ⏱ {formatTime(f.start_time)}
                  {f.end_time !== null && ` — ${formatTime(f.end_time)}`}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
