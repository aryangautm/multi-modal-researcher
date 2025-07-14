# **App Name**: ScholarAI

## Core Features:

- User Authentication: Google Authentication: Secure user login via Firebase, managing user sessions and tokens.
- Dashboard UI: Dashboard UI: A clean dashboard layout featuring a prominent research job submission form and a list of real-time updated job cards.
- Job Submission: Job Submission: Allows users to enter a research topic and an optional YouTube URL for job creation.
- Job Status Updates: Real-time job status updates via WebSocket, showing progress from 'PENDING' to 'COMPLETED' or 'FAILED'.
- Report Access: Enables secure access to generated research reports with a temporary URL for downloading PDFs.
- Podcast Generation: Initiates podcast creation with a loading state and provides access upon completion with an audio player.
- AI Research Summarization: Provides concise research summaries, leveraging a tool that decides if it is useful to reference given URL source, enhanced by multimodal data integration from video content.

## Style Guidelines:

- Primary color: Deep Indigo (#4F46E5) to convey intelligence and depth, contrasting well within a dark theme.
- Background color: Dark charcoal (#1E293B) provides a professional dark mode aesthetic, reducing eye strain.
- Accent color: Electric Purple (#A855F7), analogous to Indigo, but brighter and more saturated, used for interactive elements and highlights.
- Headline Font: 'Space Grotesk' sans-serif for headlines. It will provide a computerized, techy feel.
- Body Font: 'Inter' sans-serif for the body. To pair with 'Space Grotesk' for better readability, it will provide a neutral, modern look.
- Lucide React Icons: Use clean, consistent icons from Lucide, with a focus on clarity and representing AI/research concepts.
- Glassmorphism: Implement subtle glassmorphism/acrylic effects for cards and modals to create a sense of depth in the dark mode design.
- Framer Motion: Use fade-in/fade-out page transitions and subtle animations for job card entries and status updates.