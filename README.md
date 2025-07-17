# 🎓 ScholarAI: Your Personal AI Research & Podcast Studio

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Framework-FastAPI-green" alt="FastAPI">
  <img src="https://img.shields.io/badge/Messaging-Kafka-black" alt="Kafka">
  <img src="https://img.shields.io/badge/Orchestration-LangGraph-orange" alt="LangGraph">
  <img src="https://img.shields.io/badge/License-MIT-lightgrey" alt="License">
</p>

![Image](https://github.com/user-attachments/assets/399df0d8-c49d-4f96-8de3-0dcdd3a13e87)

Effortlessly transform any research topic into a comprehensive, cited report and a studio-quality podcast. ScholarAI leverages a sophisticated, event-driven backend and multi-agent workflows powered by **LangGraph** and **Google Gemini 2.5 Pro** to automate the entire research-to-content pipeline.

This isn't just a script; it's a production-grade, asynchronous system designed for scalability, resilience, and real-time user feedback.

## ✨ Key Features

*   **⚡ Instantaneous API Response**: The API uses an event-driven architecture with Kafka to accept jobs instantly, providing a non-blocking user experience.
*   **🧠 Multi-Modal Intelligence**: Goes beyond text by analyzing **YouTube videos** to extract deep insights, enriching the final research report.
*   **🌐 Real-time Web Search**: Integrates Gemini's native **Google Search tool** to ground its research in up-to-the-minute, real-world data with citations.
*   **🎙️ Multi-Speaker Podcast Generation**: Creates engaging, conversational podcasts with distinct speaker voices using Gemini's advanced TTS capabilities.
*   **🔴 Live Job Tracking**: Users receive **real-time status updates** pushed from the server via WebSockets, from `PENDING` to `COMPLETED`.
*   **🔒 Secure, On-Demand Artifacts**: Generated reports and podcasts are stored securely in the cloud and accessed via temporary, pre-signed URLs, ensuring only the owner can download them.
*   **🏗️ Resilient & Scalable by Design**: Built with a decoupled, multi-worker architecture that can be scaled independently to handle heavy workloads.

## 🏛️ System Architecture

ScholarAI is built on a robust, event-driven architecture that separates the API from the long-running AI tasks. This ensures the system is responsive, scalable, and resilient.

<!-- <p align="center">
  <i>(A placeholder for a detailed architecture diagram)</i>
</p> -->

1.  **API Gateway (FastAPI)**: A single, secure entry point for all client requests. It handles user authentication (Firebase), request validation (Pydantic), and immediately offloads work to the message broker.
2.  **Message Broker (Apache Kafka)**: The central nervous system of the application. The API publishes job requests to Kafka topics (`research.requests`, `podcast.requests`), decoupling the frontend from the backend workers.
3.  **Source of Truth (PostgreSQL)**: A central database stores the state of every `ResearchJob`, including its status, user ownership, and links to generated artifacts. This prevents state loss and enables seamless context sharing between agents.
4.  **Async Workers (Python)**: Independent, scalable processes that consume tasks from Kafka.
    *   `Research Worker`: Handles the multi-modal research and report generation.
    *   `Podcast Worker`: Handles the scriptwriting and audio generation.
5.  **Object Storage (MinIO/S3)**: All generated artifacts (PDF reports, MP3 podcasts) are stored securely in a cloud object store.
6.  **Real-time Layer (WebSockets)**: The API server uses job-specific Kafka topics (`job.updates.{job_id}`) as a pub/sub bus to push live status updates from the workers directly to the correct client via a persistent WebSocket connection.

## 🧠 Agentic Workflow

The AI logic is orchestrated using LangGraph, allowing for complex, stateful, and observable agentic workflows.

```
START → Research Agent → [search_research → [analyze_video?] → create_report] → END
↓
(On user request)
↓
END ← [create_podcast ← generate_podcast_script] ← Podcast Agent
```


## 🛠️ Tech Stack

| Component             | Technology                                                              | Role & Justification                                                                            |
| --------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| **AI Orchestration**  | **LangGraph**                                                           | Manages the stateful, multi-step execution of agentic chains.                                   |
| **Language Model**    | **Google Gemini 2.5 Pro**                                               | Powers video understanding, search, synthesis, and multi-speaker TTS.                           |
| **Web Framework**     | **FastAPI**                                                             | High-performance, async-native framework for building the API and WebSocket endpoints.          |
| **Database ORM**      | **SQLAlchemy**                                                          | Provides a robust, programmatic interface to the PostgreSQL database.                           |
| **Database**          | **PostgreSQL**                                                          | The central "source of truth" for job state, user data, and artifact metadata.                  |
| **Data Validation**   | **Pydantic**                                                            | Enforces strict data schemas for API requests, responses, and application settings.             |
| **Messaging**         | **Apache Kafka**                                                        | A distributed event streaming platform for a highly scalable, decoupled, and resilient backend. |
| **Object Storage**    | **MinIO (or AWS S3)**                                                   | Secure, scalable storage for generated PDF reports and audio files.                             |
| **Authentication**    | **Firebase Auth**                                                       | Handles secure user authentication using industry-standard JWTs.                                  |
| **Containerization**  | **Docker & Docker Compose**                                             | Ensures a consistent, reproducible development and deployment environment.                      |

## 🚀 Getting Started

Follow these steps to get ScholarAI running locally.

### Prerequisites

*   [Git](https://git-scm.com/)
*   [Docker](https://www.docker.com/products/docker-desktop/) & Docker Compose
*   **Python 3.11+**
*   [uv](https://github.com/astral-sh/uv): An extremely fast Python package installer and resolver.
    ```bash
    # Install uv (if you don't have it already)
    pip install uv
    ```

### 1. Clone the Repository

```bash
git clone https://github.com/aryangautm/multi-modal-researcher.git
cd multi-modal-researcher
```

### 2. Configure Environment Variables

Create a `.env` file in the project root by copying the example file:

```bash
cp .env.example .env
```

Now, edit the `.env` file and fill in your credentials and settings:

- `DATABASE_URL`
- `FIREBASE_CREDENTIALS_PATH` (Point this to your Firebase Admin SDK JSON key file)
- `GOOGLE_API_KEY`
- MinIO/AWS credentials (the defaults in `docker-compose.yml` match the `.env.example`)

### 3. Install Dependencies

Install all Python dependencies for the backend using [`uv`](https://pypi.org/project/uv/).

```bash
# In project root
uv sync
```

### 4. Start Infrastructure Services

From the project root directory, start Kafka, MinIO, and PostgreSQL using Docker Compose.

```bash
docker-compose up --build -d
```

> Note: The `-d` flag runs the services in the background. You can check their status with `docker-compose ps`.

### 5. Apply Database Migrations

With the database container running, apply the initial schema using Alembic.

```bash
# In project root
alembic upgrade head
```

### 6. Run the Application

> Note: The full-stack application should be running in docker by now, You can access the application UI at [http://localhost:3000](http://localhost:3000) and the MinIO UI at [http://localhost:9000](http://localhost:9000). If you want to run it in your host machine locally, follow the instructions below.

You need to run three separate processes in three different terminals from the project root directory.

#### Terminal 1: Start the API Server

```bash
# In project root
cd backend && uvicorn app.main:app --reload --port 8000
```

The API will be available at [http://localhost:8000](http://localhost:8000).

#### Terminal 2: Start the Research Worker

```bash
# In project root
python -m backend.workers.research_worker
```

This worker will listen for jobs on the `research.requests` topic.

#### Terminal 3: Start the Podcast Worker

```bash
# In project root
python -m backend.workers.podcast_worker
```

This worker will listen for jobs on the `podcast.requests` topic.

---

## 🔐 API Endpoints

The API documentation is automatically generated by FastAPI and available at [http://localhost:8000/docs](http://localhost:8000/docs).

| Method  | Path                                        | Auth? | Description                                                  |
|---------|---------------------------------------------|-------|--------------------------------------------------------------|
| POST    | `/api/v1/research`                    | ✅    | Submits a new research topic. Returns `202 Accepted`.        |
| GET     | `/api/v1/research-jobs`   | ✅    | Get all research jobs by the user.     |
| POST    | `/api/v1/research-jobs/{job_id}/podcast`   | ✅    | Triggers podcast generation for a completed job.             |
| GET     | `/api/v1/research-jobs/{job_id}/report`    | ✅    | Gets a temporary, secure URL to download the PDF report.     |
| GET     | `/api/v1/research-jobs/{job_id}/podcast`   | ✅    | Gets a temporary, secure URL to download the audio file.     |
| WebSocket | `/api/v1/ws/jobs/{job_id}?token=<jwt>`          | ✅    | Establishes a real-time connection for job status updates.   |

---

## 💡 Future Roadmap

- **Agentic Chat**: Implement a follow-up chat interface for users to query the research report.
- **More Modalities**: Add support for analyzing images and other document types.
- **Guardrails**: Implement safety mechanisms to prevent misuse of the AI capabilities.

