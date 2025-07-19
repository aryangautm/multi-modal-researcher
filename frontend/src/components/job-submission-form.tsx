import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { useJobStore } from '@/stores/useJobStore';
import { useAuthStore } from '@/stores/useAuthStore';
import axios from 'axios';
import toast from 'react-hot-toast';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Loader2, Send } from 'lucide-react';
import { API_URL } from '../api/config';

const formSchema = z.object({
  researchTopic: z.string().min(10, 'Research topic must be at least 10 characters long.'),
  sourceVideoUrl: z.string().url().optional().or(z.literal('')),
});

export const JobSubmissionForm = () => {
  const { addJob } = useJobStore();
  const { token } = useAuthStore();
  const logout = useAuthStore((state) => state.logout);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      researchTopic: '',
      sourceVideoUrl: '',
    },
  });

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    try {
      const payload: { researchTopic: string; sourceVideoUrl?: string } = {
        researchTopic: values.researchTopic,
      };

      if (values.sourceVideoUrl) {
        payload.sourceVideoUrl = values.sourceVideoUrl;
      }

      const response = await axios.post(`${API_URL}/api/v1/research`, payload, {
      headers: { Authorization: `Bearer ${token}` },
      });
      addJob({ ...values, id: response.data.jobId, status: 'PENDING' });
      form.reset();
      toast.success('Job submitted successfully!');
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 400) {
          toast.error('Inappropriate topic or video URL.');
        } else if (error.response?.status === 401) {
          toast.error('Session expired.');
          logout();
      }
      } else {
      toast.error(error instanceof Error ? error.message : String(error));
    }
  }
  };

  return (
    <Card className="bg-slate-800/30 backdrop-blur-lg border border-slate-700/50">
      <CardHeader>
        <CardTitle className="font-headline text-2xl">
          Create New Research Job
        </CardTitle>
        <CardDescription>
          Enter a topic and optional YouTube URL to start your research.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="researchTopic"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Research Topic</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="e.g., 'The impact of AI on renewable energy'"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="sourceVideoUrl"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>YouTube URL (Optional)</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="e.g., 'https://www.youtube.com/watch?v=...'"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="flex justify-end">
                <Button type="submit" disabled={form.formState.isSubmitting} className="w-full sm:w-auto">
                    {form.formState.isSubmitting ? <Loader2 className="animate-spin" /> : <Send />}
                    <span>{form.formState.isSubmitting ? "Submitting..." : "Research"}</span>
                </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
};