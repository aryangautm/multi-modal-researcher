# ScholarAI: Multi-Modal Researcher

This project revolutionizes research workflows by combining LangGraph with Google Gemini 2.5's powerful capabilities. Enter a topic and optional YouTube URL to instantly receive comprehensive research with citations and an engaging podcast—all automatically generated. No more manual research or content creation bottlenecks.

Key Gemini 2.5 integrations:
- [Video understanding](https://developers.googleblog.com/en/gemini-2-5-video-understanding/): Extract deep insights from YouTube videos
- [Google search tool](https://developers.googleblog.com/en/gemini-2-5-thinking-model-updates/): Native Google Search tool integration with real-time web results
- [Multi-speaker text-to-speech](https://ai.google.dev/gemini-api/docs/speech-generation): Generate natural conversations with distinct speaker voices

## Tech Stack
- **LangGraph**: Framework for building multi-agent workflows
- **Google Gemini 2.5**: LLM for research, video analysis, and text-to-speech
- **FastAPI**: Web framework for building the API
- **SQLAlchemy**: ORM for database interactions
- **PostgreSQL**: Database for session management and storage
- **Pydantic**: Data validation and settings management

## Architecture

The system implements a multi-agent architecture using LangGraph, with the following components:

### Research Agent
1. **Search Research Node**: Performs web search using Gemini's Google Search integration
2. **Analyze Video Node**: Analyzes YouTube videos when provided (conditional)
3. **Create Report Node**: Synthesizes findings into a comprehensive markdown report

### Podcast Agent
1. **Generate Podcast Script Node**: Creates a natural dialogue script based on research
2. **Create Podcast Node**: Produces TTS audio with multiple speaker voices

### Workflow

```
START → Research Agent → [search_research → [analyze_video?] → create_report] → END
                                                                      ↓
                                                              (On user request)
                                                                      ↓
                          END ← [create_podcast ← generate_podcast_script] ← Podcast Agent
```

The workflow first completes the research process, providing the user with a comprehensive report. Afterward, the user has the option to generate a podcast based on the research results. Session management to maintain research context between agents is currently under development.

### Output

The system generates:

- **Research Report**: Comprehensive markdown report with executive summary and sources
- **Podcast Script**: Natural dialogue between Dr. Sarah (expert) and Mike (interviewer)  
- **Audio File**: Multi-speaker TTS audio file (`research_podcast_*.wav`)

## Configuration

The system supports runtime configuration through the `Configuration` class:

### Model Settings
- `search_model`: Model for web search (default: "gemini-2.5-flash")
- `synthesis_model`: Model for report synthesis (default: "gemini-2.5-flash")
- `video_model`: Model for video analysis (default: "gemini-2.5-flash")
- `tts_model`: Model for text-to-speech (default: "gemini-2.5-flash-preview-tts")

### Temperature Settings
- `search_temperature`: Factual search queries (default: 0.0)
- `synthesis_temperature`: Balanced synthesis (default: 0.3)
- `podcast_script_temperature`: Creative dialogue (default: 0.4)

### TTS Settings
- `mike_voice`: Voice for interviewer (default: "Kore")
- `sarah_voice`: Voice for expert (default: "Puck")
- Audio format settings for output quality

### Project structure
```
multi-modal-researcher/
├── README.md
├── .gitignore
├── pyproject.toml
├── .env.example
└── backend/
    └── app/
        ├── __init__.py
        ├── main.py
        ├── agent/
        │   ├── podcast/
        │   │   ├── __init__.py
        │   │   ├── graph.py
        │   │   ├── nodes.py
        │   │   └── tools.py
        │   └── research/
        │       ├── __init__.py
        │       ├── graph.py
        │       ├── nodes.py
        │       └── tools.py
        ├── core/
        │   ├── __init__.py
        │   ├── config.py
        │   ├── llm.py (contains the gemini genai sdk client setup)
        │   └── database.py
        ├── models/
        │   ├── __init__.py
        │   └── session.py
        ├── schemas/
        │   ├── __init__.py
        │   ├── podcast.py
        │   └── research.py
        ├── prompts/
        │   ├── __init__.py
        │   ├── podcast.py
        │   └── research.py
        └── utils/
            ├── __init__.py
            └── helpers.py (contains the output printer for console output)
```
