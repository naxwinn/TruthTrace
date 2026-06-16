import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api",
});

export interface MediaFile {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  duration: number | null;
  created_at: string;
}

export interface AnalysisJob {
  id: string;
  media_file_id: string;
  status: string;
  progress: number;
  created_at: string;
  updated_at: string;
  error_message: string | null;
  authenticity_score: number | null;
}

export interface Finding {
  id: string;
  job_id: string;
  detector_type: string;
  finding_type: string;
  confidence: number;
  start_time: number | null;
  end_time: number | null;
  description: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface AnalysisReport {
  job: AnalysisJob;
  file: MediaFile;
  findings: Finding[];
  timeline: TimelineEntry[];
  summary: string;
}

export interface TimelineEntry {
  start: number;
  end: number;
  type: string;
  confidence: number;
  detector: string;
}

export async function uploadFile(file: File): Promise<MediaFile> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post<MediaFile>("/upload/", formData);
  return data;
}

export async function createJob(mediaFileId: string): Promise<AnalysisJob> {
  const { data } = await api.post<AnalysisJob>("/jobs/", {
    media_file_id: mediaFileId,
  });
  return data;
}

export async function getJob(jobId: string): Promise<AnalysisJob> {
  const { data } = await api.get<AnalysisJob>(`/jobs/${jobId}`);
  return data;
}

export async function getJobs(): Promise<AnalysisJob[]> {
  const { data } = await api.get<AnalysisJob[]>("/jobs/");
  return data;
}

export async function getReport(jobId: string): Promise<AnalysisReport> {
  const { data } = await api.get<AnalysisReport>(`/jobs/${jobId}/report`);
  return data;
}

export default api;
