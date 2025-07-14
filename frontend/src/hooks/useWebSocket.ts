import { useEffect, useRef, useState } from 'react';
import { useAuthStore } from '../stores/useAuthStore';
import { useJobStore } from '../stores/useJobStore';
import toast from 'react-hot-toast';

const useWebSocket = (jobId: string) => {
  const { token } = useAuthStore();
  const { updateJob } = useJobStore();
  const [isConnecting, setIsConnecting] = useState(true);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);

  useEffect(() => {
    if (!jobId || !token) return;

    const connect = () => {
      ws.current = new WebSocket(`ws://localhost:8000/api/v1/ws/jobs/${jobId}?token=${token}`);

      ws.current.onopen = () => {
        console.log(`WebSocket connected for job ${jobId}`);
        setIsConnecting(false);
        setIsReconnecting(false);
        reconnectAttempts.current = 0;
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateJob(data);
      };

      ws.current.onclose = () => {
        console.log(`WebSocket disconnected for job ${jobId}`);
        if (reconnectAttempts.current < 5) {
          setIsReconnecting(true);
          const delay = Math.pow(2, reconnectAttempts.current) * 1000;
          setTimeout(connect, delay);
          reconnectAttempts.current++;
        } else {
          toast.error('Failed to reconnect to the server.');
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        toast.error('An error occurred with the WebSocket connection.');
        ws.current?.close();
      };
    };

    connect();

    return () => {
      ws.current?.close();
    };
  }, [jobId, token, updateJob]);

  return { isConnecting, isReconnecting };
};

export default useWebSocket;