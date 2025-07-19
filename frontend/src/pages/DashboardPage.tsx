import { useEffect } from 'react';
import axios from 'axios';
import DashboardHeader from '@/components/header';
import { JobSubmissionForm } from '@/components/job-submission-form';
import { JobList } from '@/components/job-list';
import { useAuthStore } from '@/stores/useAuthStore';
import { useJobStore } from '@/stores/useJobStore';
import toast from 'react-hot-toast';
import { API_URL } from '../api/config';

export default function DashboardPage() {
  const { token } = useAuthStore();
  const { addJob } = useJobStore();
  const logout = useAuthStore((state) => state.logout);

  useEffect(() => {
    const fetchJobs = async () => {
      if (!token) return; // Don't fetch if no token

      try {
        const response = await axios.get(`${API_URL}/api/v1/research-jobs`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        response.data.forEach((job: any) => {
          addJob(job);
        });
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 401) {
        toast.error('Session expired.');
        logout();
        }  else {
        console.error('Failed to fetch jobs:', error);
        toast.error('Failed to load your research jobs.');
      }
    }
    };

    fetchJobs();
  }, [token, addJob]);

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