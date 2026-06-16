"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import type { AnalysisReport, MediaFile, AnalysisJob } from "@/lib/api";

export type AppPhase =
  | "landing"
  | "upload"
  | "analyzing"
  | "timeline"
  | "report";

export interface AnalysisState {
  mediaFile: MediaFile | null;
  job: AnalysisJob | null;
  report: AnalysisReport | null;
  analysisMessages: string[];
  currentMessageIndex: number;
}

interface AppStateContextType {
  phase: AppPhase;
  setPhase: (phase: AppPhase) => void;
  analysisState: AnalysisState;
  setMediaFile: (file: MediaFile) => void;
  setJob: (job: AnalysisJob) => void;
  setReport: (report: AnalysisReport) => void;
  resetAnalysis: () => void;
  scrollProgress: number;
  setScrollProgress: (progress: number) => void;
}

const defaultAnalysisState: AnalysisState = {
  mediaFile: null,
  job: null,
  report: null,
  analysisMessages: [
    "Initializing forensic scan...",
    "Extracting audio channels...",
    "Analyzing GOP structures...",
    "Mapping optical flow vectors...",
    "Detecting voice cloning signatures...",
    "Scanning compression artifacts...",
    "Cross-referencing metadata layers...",
    "Computing authenticity score...",
    "Generating forensic report...",
  ],
  currentMessageIndex: 0,
};

const AppStateContext = createContext<AppStateContextType | null>(null);

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [phase, setPhase] = useState<AppPhase>("landing");
  const [analysisState, setAnalysisState] =
    useState<AnalysisState>(defaultAnalysisState);
  const [scrollProgress, setScrollProgress] = useState(0);

  const setMediaFile = useCallback((file: MediaFile) => {
    setAnalysisState((prev) => ({ ...prev, mediaFile: file }));
  }, []);

  const setJob = useCallback((job: AnalysisJob) => {
    setAnalysisState((prev) => ({ ...prev, job }));
  }, []);

  const setReport = useCallback((report: AnalysisReport) => {
    setAnalysisState((prev) => ({ ...prev, report }));
  }, []);

  const resetAnalysis = useCallback(() => {
    setAnalysisState(defaultAnalysisState);
    setPhase("landing");
  }, []);

  return (
    <AppStateContext.Provider
      value={{
        phase,
        setPhase,
        analysisState,
        setMediaFile,
        setJob,
        setReport,
        resetAnalysis,
        scrollProgress,
        setScrollProgress,
      }}
    >
      {children}
    </AppStateContext.Provider>
  );
}

export function useAppState() {
  const context = useContext(AppStateContext);
  if (!context) {
    throw new Error("useAppState must be used within AppStateProvider");
  }
  return context;
}
