export type JobStatus =
  | "PENDING"
  | "SUMMARIZING"
  | "COMPLETED"
  | "FAILED"
  | "GENERATING_PODCAST"
  | "PODCAST_READY";

export interface Job {
  id: string;
  researchTopic: string;
  youtubeUrl?: string;
  status: JobStatus;
  summary?: string | null;
  reportUrl?: string | null;
  podcastUrl?: string | null;
}
