import { useJobStore } from '@/stores/useJobStore';
import { JobCard } from './JobCard';
import { AnimatePresence } from 'framer-motion';
import { FileSearch } from 'lucide-react';

export const JobList = () => {
  const { jobs } = useJobStore();

  if (jobs.size === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-700 p-12 text-center">
        <FileSearch className="mx-auto h-12 w-12 text-muted-foreground" />
        <h3 className="mt-4 text-xl font-semibold font-headline">No researches yet</h3>
        <p className="mt-2 text-sm text-muted-foreground">
          Create a new research job to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-headline font-semibold">Your Researches</h2>
      <div className="grid gap-4 md:grid-cols-1">
        <AnimatePresence>
            {Array.from(jobs.values())
            .filter(job => job.id) // Only render jobs with a valid id
            .reverse()
            .map((job) => (
          <JobCard key={job.id} job={job} />
            ))}
        </AnimatePresence>
      </div>
    </div>
  );
};