1. Core User Flow & Application Behavior

    Authentication: The user first lands on a login page. They must authenticate using their Google account via Firebase Authentication.

    Dashboard: After logging in, they are redirected to the main dashboard. This page has a clean input form.

    Job Submission: The user enters a research topic and an optional YouTube URL. Upon submission, the UI immediately shows a "Job Queued" status and creates a new "card" or entry for this research job in a list of recent jobs. This must be an optimistic UI update.

    Real-time Tracking: A WebSocket connection is instantly established for that new job. The job card will reactively update its status in real-time (PENDING -> PROCESSING -> COMPLETED/FAILED) without any page reloads. A progress indicator (like a pulsing dot or a subtle progress bar) should be visible during the PROCESSING state.

    Accessing Results: Once the status is COMPLETED, "Download Report" and "Generate Podcast" buttons appear on the job card.

        Clicking "Download Report" fetches a secure, temporary URL from the backend and initiates a browser download of the PDF.

        Clicking "Generate Podcast" triggers the podcast generation flow. The button shows a loading state, and the job card's status updates via the WebSocket to PODCAST_PENDING, then PODCAST_COMPLETED.

    Podcast Access: Once the status is PODCAST_COMPLETED, a "Play Podcast" button appears, which opens an audio player, and a "Download Podcast" button becomes active.

    Error Handling: All API errors and connection issues are communicated to the user via non-intrusive toast notifications.

2. Recommended Tech Stack

    Framework: React with Vite for a fast development experience. Use TypeScript for type safety.

    Styling: Tailwind CSS for rapid, utility-first styling.

    State Management: Zustand. It's simple, powerful, and avoids boilerplate. We'll need a store for authentication state (user, token) and another for managing research jobs (jobs).

    Animations: Framer Motion for fluid, delightful animations on UI elements.

    Icons: Lucide React for a clean and consistent icon set.

    Authentication: Firebase Web SDK (v9+) for handling the authentication flow.

    Notifications: react-hot-toast for clean, simple toast notifications.

3. Detailed Backend API Specification

The base URL for the API is http://localhost:8000. All protected endpoints require an Authorization header with the Firebase JWT: Authorization: Bearer <ID_TOKEN>.
Authentication

    Handled entirely by the Firebase Web SDK. Your responsibility is to:

        Implement the "Sign in with Google" popup flow.

        On successful login, get the ID Token from the Firebase user object.

        Store this token in your state management solution (Zustand).

        Attach this token to all subsequent API requests.

        Implement a listener (onAuthStateChanged) to handle token refreshes and logouts.

HTTP Endpoints

A. Initiate Research Job

    Method: POST

    Path: /api/v1/research

    Auth: Required.

    Request Body:
    Generated json

          
    {
      "researchTopic": "string",
      "sourceVideoUrl": "string | null"
    }

        

    IGNORE_WHEN_COPYING_START

Use code with caution. Json
IGNORE_WHEN_COPYING_END

Success Response: 202 Accepted

    The body contains the jobId which is critical for tracking.

Generated json

      
{
  "jobId": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8"
}

    

IGNORE_WHEN_COPYING_START

    Use code with caution. Json
    IGNORE_WHEN_COPYING_END

    Frontend Action: Upon receiving 202, immediately use the jobId and the token to establish a WebSocket connection.

B. Get Report Download URL

    Method: GET

    Path: /api/v1/research-jobs/{job_id}/report

    Auth: Required.

    Success Response: 200 OK
    Generated json

          
    {
      "url": "https://temporary-secure-url-for-pdf..."
    }

        

    IGNORE_WHEN_COPYING_START

    Use code with caution. Json
    IGNORE_WHEN_COPYING_END

    Frontend Action: Take the url from the response and programmatically trigger a download (e.g., window.location.href = url or create a temporary <a> tag).

C. Initiate Podcast Generation

    Method: POST

    Path: /api/v1/research-jobs/{job_id}/podcast

    Auth: Required.

    Request Body: Empty.

    Success Response: 202 Accepted
    Generated json

          
    {
      "message": "Podcast generation has been queued."
    }

        

    IGNORE_WHEN_COPYING_START

    Use code with caution. Json
    IGNORE_WHEN_COPYING_END

    Frontend Action: The UI should show a loading state on the button. The actual status update (PODCAST_PENDING) will arrive via the existing WebSocket connection.

D. Get Podcast Download URL

    Method: GET

    Path: /api/v1/research-jobs/{job_id}/podcast

    Auth: Required.

    Success Response: 200 OK
    Generated json

          
    {
      "url": "https://temporary-secure-url-for-mp3..."
    }

        

    IGNORE_WHEN_COPYING_START

    Use code with caution. Json
    IGNORE_WHEN_COPYING_END

    Frontend Action: Use the URL to either trigger a download or as the src for an <audio> player.

WebSocket Endpoint

    Path: /api/v1/ws/jobs/{job_id}?token=<ID_TOKEN>

    Connection: This is the only way to authenticate a WebSocket connection. The Firebase ID Token must be passed as a query parameter named token.

    Behavior: This is a server-to-client channel. The frontend does not need to send any messages. It only listens.

    Message Format: The server will push JSON objects representing the job's state. The very first message after connection is the job's current state. Subsequent messages are live updates.
    Generated typescript

          
    // The structure of a WebSocket message payload
    interface JobStatusUpdate {
      jobId: string;
      status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'PODCAST_PENDING' | 'PODCAST_COMPLETED';
      summary?: string;
      reportUrl?: string;  // This is the S3 key, not a real URL
      podcastUrl?: string; // This is the S3 key, not a real URL
    }

        

    IGNORE_WHEN_COPYING_START

    Use code with caution. TypeScript
    IGNORE_WHEN_COPYING_END

4. Frontend Architecture & Logic
Component Structure

    App.tsx: Main router setup (e.g., using react-router-dom).

    pages/LoginPage.tsx: Handles Firebase authentication.

    pages/DashboardPage.tsx: The main page after login. Contains the research form and the list of job cards.

    components/JobCard.tsx: A reusable component to display a single research job, its status, and action buttons. This component will be highly reactive to the WebSocket data.

    components/ProtectedRoute.tsx: A wrapper component that redirects unauthenticated users to the login page.

    hooks/useWebSocket.ts: A custom hook to manage the WebSocket connection lifecycle for a given job.

State Management (Zustand)

    useAuthStore:

        user: The Firebase user object or null.

        token: The JWT string or null.

        setUser, setToken, logout.

    useJobStore:

        jobs: An object or Map where keys are jobIds and values are the JobStatusUpdate objects. Map<string, JobStatusUpdate>.

        addJob: Adds a new job stub after submission.

        updateJob: Updates a job's state based on a WebSocket message.

Production-Grade Resilience & Error Handling

    API Error Handling: All API calls made with fetch or axios must have .catch() blocks. On error, display a user-friendly message using react-hot-toast. For a 401 Unauthorized error, you should automatically attempt to refresh the token or log the user out.

    WebSocket Reconnection Logic: The useWebSocket hook must be robust.

        If the WebSocket connection drops unexpectedly, it must attempt to reconnect.

        Implement an exponential backoff strategy: try immediately, then after 2s, 4s, 8s, up to a maximum of 30s.

        While reconnecting, the UI should show a "Connection lost, attempting to reconnect..." indicator on the relevant job card.

        If reconnection fails after several attempts, show a persistent "Failed to connect" error.