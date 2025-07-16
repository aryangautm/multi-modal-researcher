import { useEffect, useRef, useState } from 'react';
import { useAuthStore } from '../stores/useAuthStore';
import { useJobStore } from '../stores/useJobStore';
import toast from 'react-hot-toast';
import { API_URL } from '../api/config';

const useWebSocket = (id: string) => {
  const { token } = useAuthStore();
  const { jobs, updateJob } = useJobStore();
  const [isConnecting, setIsConnecting] = useState(true);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);

  useEffect(() => {
    const currentJob = jobs.get(id);
    const currentStatus = currentJob?.status;
    const shouldConnect = currentStatus === 'PENDING' || currentStatus === 'PROCESSING' || currentStatus === 'PODCAST_PENDING';

    if (!id || !token || !shouldConnect) {
      ws.current?.close();
      return;
    }
    if (currentJob?.status === 'PODCAST_COMPLETED') {
      ws.current?.close();
      return;
    }

    const connect = () => {
      ws.current = new WebSocket(`ws://${API_URL}/api/v1/ws/jobs/${id}?token=${token}`);

      ws.current.onopen = () => {
        console.log(`WebSocket connected for job ${id}`);
        setIsConnecting(false);
        setIsReconnecting(false);
        reconnectAttempts.current = 0;
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("update received")
        updateJob(data);
      };

      ws.current.onclose = () => {
        console.log(`WebSocket disconnected for job ${id}`);
        if (reconnectAttempts.current < 5 || shouldConnect) {
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
  }, [id, token, updateJob]);

  return { isConnecting, isReconnecting };
};

export default useWebSocket;