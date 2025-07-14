import { create } from 'zustand';

// As defined in the backend spec
interface JobStatusUpdate {
  id: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'PODCAST_PENDING' | 'PODCAST_COMPLETED';
  summary?: string;
  topic?: string;
  sourceVideoUrl?: string;
}
interface JobStore {
  jobs: Map<string, JobStatusUpdate>;
  addJob: (job: JobStatusUpdate) => void;
  updateJob: (job: JobStatusUpdate) => void;
}

const useJobStore = create<JobStore>((set) => ({
  jobs: new Map(),
  addJob: (job) => set((state) => {
    return { jobs: new Map(state.jobs).set(job.id, job) };
  }),
  updateJob: (updatedJob) => set((state) => {
    const currentJob = state.jobs.get(updatedJob.id);
    const newJob = { ...currentJob, ...updatedJob };
    return { jobs: new Map(state.jobs).set(updatedJob.id, newJob) };
  })
}));

export { useJobStore };
export type { JobStatusUpdate };