import { create } from 'zustand';

// As defined in the backend spec
interface JobStatusUpdate {
  jobId: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'PODCAST_PENDING' | 'PODCAST_COMPLETED';
  summary?: string;
  reportUrl?: string;
  podcastUrl?: string;
}

interface JobStore {
  jobs: Map<string, JobStatusUpdate>;
  addJob: (job: JobStatusUpdate) => void;
  updateJob: (job: JobStatusUpdate) => void;
}

export const useJobStore = create<JobStore>((set) => ({
  jobs: new Map(),
  addJob: (job) => set((state) => ({
    jobs: new Map(state.jobs).set(job.jobId, job)
  })),
  updateJob: (job) => set((state) => ({
    jobs: new Map(state.jobs).set(job.jobId, job)
  }))
}));