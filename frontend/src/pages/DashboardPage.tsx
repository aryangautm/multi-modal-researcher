import DashboardHeader from '@/components/header';
import { JobSubmissionForm } from '@/components/job-submission-form';
import { JobList } from '@/components/job-list';

export default function DashboardPage() {
  return (
    <div className="flex min-h-screen w-full flex-col fade-in">
      <DashboardHeader />
      <main className="flex-1 p-4 md:p-8">
        <div className="mx-auto max-w-4xl space-y-8">
          <JobSubmissionForm />
          <JobList />
        </div>
      </main>
    </div>
  );
}