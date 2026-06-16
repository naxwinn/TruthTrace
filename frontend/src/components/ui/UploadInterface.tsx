"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileVideo, FileAudio, Loader2, CheckCircle, AlertCircle } from "lucide-react";
import { uploadFile, createJob } from "@/lib/api";
import { useAppState } from "@/components/providers/AppStateProvider";
import clsx from "clsx";

type UploadState = "idle" | "uploading" | "creating_job" | "done" | "error";

export function UploadInterface() {
  const { phase, setPhase, setMediaFile, setJob } = useAppState();
  const [state, setState] = useState<UploadState>("idle");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      setFileName(file.name);

      try {
        setState("uploading");
        setError(null);
        setProgress(20);

        const mediaFile = await uploadFile(file);
        setMediaFile(mediaFile);
        setProgress(60);

        setState("creating_job");
        const job = await createJob(mediaFile.id);
        setJob(job);
        setProgress(100);

        setState("done");

        // Transition to analysis phase after brief pause
        setTimeout(() => {
          setPhase("analyzing");
        }, 1500);
      } catch (err) {
        setState("error");
        setError(err instanceof Error ? err.message : "Upload failed. Ensure the backend is running.");
      }
    },
    [setMediaFile, setJob, setPhase]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "video/*": [".mp4", ".avi", ".mov", ".mkv", ".webm"],
      "audio/*": [".mp3", ".wav", ".ogg", ".flac"],
    },
    maxFiles: 1,
    disabled: state === "uploading" || state === "creating_job",
  });

  if (phase !== "upload") return null;

  return (
    <motion.section
      className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -30 }}
      transition={{ duration: 0.8 }}
    >
      <motion.div
        className="w-full max-w-2xl"
        initial={{ scale: 0.95 }}
        animate={{ scale: 1 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        {/* Header */}
        <motion.div
          className="text-center mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <h2 className="text-3xl sm:text-4xl font-bold text-glow-cyan">
            <span className="bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
              Upload Media
            </span>
          </h2>
          <p className="mt-2 text-gray-400">
            Drop your file into the scan chamber to begin forensic analysis
          </p>
        </motion.div>

        {/* Drop Zone */}
        <div
          {...getRootProps()}
          className={clsx(
            "relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-16 transition-all duration-500 cursor-pointer overflow-hidden",
            isDragActive
              ? "border-cyan-400 bg-cyan-500/5 shadow-[0_0_60px_rgba(0,240,255,0.15)]"
              : "border-gray-700/50 hover:border-cyan-500/50 bg-gray-900/20 hover:bg-cyan-950/10",
            (state === "uploading" || state === "creating_job") &&
              "pointer-events-none"
          )}
        >
          <input {...getInputProps()} />

          {/* Animated corner accents */}
          <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-cyan-400/50 rounded-tl-lg" />
          <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-cyan-400/50 rounded-tr-lg" />
          <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-cyan-400/50 rounded-bl-lg" />
          <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-cyan-400/50 rounded-br-lg" />

          <AnimatePresence mode="wait">
            {state === "idle" && (
              <motion.div
                key="idle"
                className="flex flex-col items-center"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <motion.div
                  animate={{ y: isDragActive ? -5 : 0 }}
                  transition={{ type: "spring" }}
                >
                  <Upload className={clsx(
                    "h-16 w-16 mb-6 transition-colors duration-300",
                    isDragActive ? "text-cyan-400" : "text-gray-500"
                  )} />
                </motion.div>
                <p className="text-gray-200 font-semibold text-lg">
                  {isDragActive ? "Release to initialize scan" : "Drag & drop media file"}
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  or click to browse files
                </p>
                <div className="flex gap-4 mt-6">
                  <span className="flex items-center gap-2 text-xs text-gray-500 px-3 py-1.5 rounded-full bg-gray-800/50 border border-gray-700/50">
                    <FileVideo className="h-3.5 w-3.5" /> Video
                  </span>
                  <span className="flex items-center gap-2 text-xs text-gray-500 px-3 py-1.5 rounded-full bg-gray-800/50 border border-gray-700/50">
                    <FileAudio className="h-3.5 w-3.5" /> Audio
                  </span>
                </div>
              </motion.div>
            )}

            {(state === "uploading" || state === "creating_job") && (
              <motion.div
                key="loading"
                className="flex flex-col items-center"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
              >
                <Loader2 className="h-16 w-16 text-cyan-400 mb-6 animate-spin" />
                <p className="text-gray-200 font-semibold">
                  {state === "uploading" ? "Uploading to scan chamber..." : "Initializing forensic job..."}
                </p>
                {fileName && (
                  <p className="text-xs text-gray-500 mt-2 font-mono">{fileName}</p>
                )}
                <div className="w-full max-w-xs mt-6 bg-gray-800/50 rounded-full h-1.5 overflow-hidden">
                  <motion.div
                    className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-blue-500"
                    initial={{ width: "0%" }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              </motion.div>
            )}

            {state === "done" && (
              <motion.div
                key="done"
                className="flex flex-col items-center"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
              >
                <CheckCircle className="h-16 w-16 text-emerald-400 mb-6" />
                <p className="text-gray-200 font-semibold">Scan initialized</p>
                <p className="text-xs text-gray-500 mt-2">Entering analysis chamber...</p>
              </motion.div>
            )}

            {state === "error" && (
              <motion.div
                key="error"
                className="flex flex-col items-center"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
              >
                <AlertCircle className="h-16 w-16 text-red-400 mb-6" />
                <p className="text-red-300 font-semibold">Scan failed</p>
                <p className="text-xs text-gray-500 mt-2 max-w-sm text-center">{error}</p>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setState("idle");
                    setError(null);
                  }}
                  className="mt-4 px-4 py-2 text-sm rounded-lg border border-gray-700 text-gray-300 hover:bg-gray-800 transition-colors"
                >
                  Try Again
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Back button */}
        <motion.div
          className="flex justify-center mt-8"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <button
            onClick={() => {
              setState("idle");
              setError(null);
              setPhase("landing");
            }}
            className="text-sm text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 17l-5-5m0 0l5-5m-5 5h12" />
            </svg>
            Return to Threshold
          </button>
        </motion.div>
      </motion.div>
    </motion.section>
  );
}
