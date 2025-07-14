import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import useWebSocket from '@/hooks/useWebSocket';
import { motion } from 'framer-motion';
import { Badge } from './ui/badge';
import {
  CheckCircle2,
  Download,
  FileText,
  Headphones,
  Loader2,
  XCircle,
  Youtube,
} from "lucide-react";
import { Progress } from './ui/progress';
import { useJobStore } from '@/stores/useJobStore';
import { useAuthStore } from '@/stores/useAuthStore';
import axios from 'axios';
import toast from 'react-hot-toast';

// As defined in the backend spec
interface JobStatusUpdate {
  jobId: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'PODCAST_PENDING' | 'PODCAST_COMPLETED';
  summary?: string;
  reportUrl?: string;
  podcastUrl?: string;
  researchTopic?: string;
  sourceVideoUrl?: string;
}

interface JobCardProps {
  job: JobStatusUpdate;
}

const StatusBadge = ({ status }: { status: JobStatusUpdate["status"] }) => {
    const statusConfig = {
      PENDING: {
        color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
        icon: <Loader2 className="h-3 w-3 animate-spin" />,
        text: "Pending",
      },
      PROCESSING: {
        color: "bg-blue-500/20 text-blue-400 border-blue-500/30",
        icon: <Loader2 className="h-3 w-3 animate-spin" />,
        text: "Processing...",
      },
      COMPLETED: {
        color: "bg-green-500/20 text-green-400 border-green-500/30",
        icon: <CheckCircle2 className="h-3 w-3" />,
        text: "Completed",
      },
      FAILED: {
        color: "bg-red-500/20 text-red-400 border-red-500/30",
        icon: <XCircle className="h-3 w-3" />,
        text: "Failed",
      },
      PODCAST_PENDING: {
          color: "bg-purple-500/20 text-purple-400 border-purple-500/30",
          icon: <Loader2 className="h-3 w-3 animate-spin" />,
          text: "Generating Podcast...",
      },
      PODCAST_COMPLETED: {
          color: "bg-green-500/20 text-green-400 border-green-500/30",
          icon: <Headphones className="h-3 w-3" />,
          text: "Podcast Ready",
      }
    };
  
    const config = statusConfig[status] || statusConfig.PENDING;
  
    return (
      <Badge
        variant="outline"
        className={`text-xs capitalize ${config.color}`}>
        {config.icon}
        <span>{config.text}</span>
      </Badge>
    );
  };

export const JobCard = ({ job }: JobCardProps) => {
  useWebSocket(job.jobId);
  const { token } = useAuthStore();

  const handleDownload = async (url: string) => {
    window.open(url, '_blank');
  };

  const handleGeneratePodcast = async () => {
    try {
      await axios.post(`http://localhost:8000/api/v1/research-jobs/${job.jobId}/podcast`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success('Podcast generation started!');
    } catch (error) {
      toast.error('Failed to start podcast generation.');
    }
  };

  return (
    <motion.div layout initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -50 }}>
      <Card className="bg-slate-800/40 backdrop-blur-lg border border-slate-700/60 shadow-lg animate-in fade-in slide-in-from-bottom-4 duration-500">
        <CardHeader>
            <div className="flex justify-between items-start">
                <CardTitle className="font-headline text-lg mb-1 pr-4">{job.researchTopic}</CardTitle>
                <StatusBadge status={job.status} />
            </div>
            {job.sourceVideoUrl && (
            <CardDescription className="flex items-center gap-2 text-xs text-muted-foreground">
                <Youtube className="w-4 h-4 text-red-500" />
                <a href={job.sourceVideoUrl} target="_blank" rel="noopener noreferrer" className="hover:underline truncate">
                    {job.sourceVideoUrl}
                </a>
            </CardDescription>
            )}
        </CardHeader>
        <CardContent>
            {job.status === "COMPLETED" || job.status === "PODCAST_COMPLETED" || job.status === "PODCAST_PENDING" ? (
            <p className="text-sm text-muted-foreground">{job.summary}</p>
            ) : (
            <p className="text-sm text-muted-foreground italic">
                AI is working on your request...
            </p>
            )}
        </CardContent>
        <CardFooter className="flex-col items-start gap-4">
            {(job.status === 'COMPLETED' || job.status === 'PODCAST_COMPLETED' || job.status === 'PODCAST_PENDING') && (
                <div className="flex flex-col sm:flex-row gap-2 w-full">
                    <Button variant="outline" size="sm" onClick={() => handleDownload(job.reportUrl!)} disabled={!job.reportUrl}>
                        <FileText />
                        Download Report
                    </Button>
                    {job.status === 'COMPLETED' && (
                        <Button variant="outline" size="sm" onClick={handleGeneratePodcast}>
                            <Headphones />
                            Generate Podcast
                        </Button>
                    )}
                </div>
            )}
            {job.status === 'PODCAST_PENDING' && (
                <div className="w-full space-y-2">
                    <p className="text-xs text-muted-foreground">Generating podcast...</p>
                    <Progress value={50} className="w-full h-2"/>
                </div>
            )}
            {job.status === 'PODCAST_COMPLETED' && (
                <div className="w-full">
                    <audio controls className="w-full" src={job.podcastUrl!}>
                        Your browser does not support the audio element.
                    </audio>
                </div>
            )}
        </CardFooter>
      </Card>
    </motion.div>
  );
};