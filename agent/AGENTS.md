# AGENTS.md

A guide for AI coding agents working on the GossipToon project.

## Project Overview

GossipToon is an AI-powered video generation system that transforms viral Reddit gossip into engaging YouTube Shorts (60-second vertical videos). The system:

- Extracts stories from Reddit posts and transforms them into five-act narratives
- Generates emotional voice acting using ElevenLabs TTS with Whisper timestamps
- Creates cinematic 9:16 AI-generated images with character consistency
- Produces frame-perfect word-level captions with dynamic highlighting
- Assembles professional videos with Ken Burns effects and rich overlays

**Tech Stack**: Python 3.12+, LangChain/LangGraph, OpenAI GPT-4o, Google Gemini Flash, ElevenLabs, Whisper, FFmpeg, Pydantic

## Setup Commands

```bash
# Clone and install
git clone https://github.com/yourusername/ssuljaengi.git
cd ssuljaengi
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"

# Set up environment variables
cp .env.example .env
# Edit .env with API keys (OPENAI_API_KEY, GEMINI_API_KEY, ELEVENLABS_API_KEY)

# Validate setup (checks API keys, FFmpeg, directories)
gossiptoon validate
```

## Build and Test Commands

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests

# Run with coverage
pytest --cov=src/gossiptoon --cov-report=html

# Linting and formatting
ruff check src/
black src/
mypy src/
```

## CLI Commands

```bash
# Generate video from Reddit URL
gossiptoon run <reddit_url>

# Generate with custom config
gossiptoon run <reddit_url> --config config/custom.yaml

# Resume from checkpoint (if pipeline fails)
gossiptoon resume <project_id>

# List all checkpoints
gossiptoon list

# Clean old checkpoints (default: 7 days)
gossiptoon clean --days 14
```

## Directory Structure

```
ssuljaengi/
├── src/gossiptoon/              # Main package
│   ├── main.py                  # CLI entry point (Click-based)
│   ├── agents/                  # AI agents
│   │   ├── script_writer.py     # GPT-4o script generation
│   │   ├── story_finder.py      # Reddit story extraction
│   │   ├── state.py             # LangGraph workflow state
│   │   └── tools/               # Agent tools (Reddit, Tavily, etc.)
│   ├── audio/                   # Audio generation
│   │   ├── generator.py         # Audio orchestration
│   │   ├── elevenlabs_client.py # TTS client
│   │   └── whisper.py           # Word-level timestamps
│   ├── visual/                  # Image generation
│   │   ├── director.py          # Visual direction
│   │   ├── gemini_client.py     # Gemini image generation
│   │   ├── dalle_client.py      # DALL-E fallback
│   │   └── character_bank.py    # Character consistency (I2I)
│   ├── video/                   # Video assembly
│   │   ├── assembler.py         # FFmpeg video assembly
│   │   ├── ffmpeg_builder.py    # FFmpeg command builder
│   │   └── effects/             # Video effects (Ken Burns, captions)
│   ├── pipeline/                # Pipeline orchestration
│   │   ├── orchestrator.py      # Main pipeline controller
│   │   └── checkpoint.py        # Checkpoint/recovery system
│   ├── models/                  # Pydantic data models
│   │   ├── script.py            # Script/act/scene models
│   │   ├── story.py             # Story models
│   │   ├── audio.py             # Audio models
│   │   ├── visual.py            # Visual models
│   │   └── video.py             # Video/render config models
│   ├── core/                    # Core utilities
│   │   └── config.py            # ConfigManager
│   └── utils/                   # Utilities
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   ├── fixtures/                # Test fixtures
│   └── conftest.py              # Pytest configuration
├── docs/                        # Documentation
│   └── ARCHITECTURE.md          # System architecture
├── config/                      # Configuration files (YAML)
├── outputs/                     # Generated outputs
└── pyproject.toml               # Project configuration
```

## Code Style

- **Type hints**: Required throughout for all function signatures
- **Pydantic models**: Use for all data validation (`models/` directory)
- **Docstrings**: Include for all public functions and classes
- **Logging**: Use `logging` module, not print statements
- **Line length**: 100 characters (enforced by Black and Ruff)
- **Naming**: No version prefixes (V1/V2/V3) in code

## Key Components

| Component             | Location                                    | Purpose                    |
| --------------------- | ------------------------------------------- | -------------------------- |
| CLI Entry Point       | `src/gossiptoon/main.py`                    | Click-based CLI commands   |
| Pipeline Orchestrator | `src/gossiptoon/pipeline/orchestrator.py`   | 5-stage pipeline execution |
| Checkpoint Manager    | `src/gossiptoon/pipeline/checkpoint.py`     | Save/resume from any stage |
| Story Finder Agent    | `src/gossiptoon/agents/story_finder.py`     | Reddit story extraction    |
| Script Writer Agent   | `src/gossiptoon/agents/script_writer.py`    | GPT-4o five-act narrative  |
| Workflow State        | `src/gossiptoon/agents/state.py`            | LangGraph state machine    |
| Audio Generator       | `src/gossiptoon/audio/generator.py`         | TTS orchestration          |
| ElevenLabs Client     | `src/gossiptoon/audio/elevenlabs_client.py` | Voice synthesis            |
| Whisper Client        | `src/gossiptoon/audio/whisper.py`           | Word-level timestamps      |
| Visual Director       | `src/gossiptoon/visual/director.py`         | Scene image generation     |
| Gemini Client         | `src/gossiptoon/visual/gemini_client.py`    | AI image generation        |
| Character Bank        | `src/gossiptoon/visual/character_bank.py`   | I2I character consistency  |
| Video Assembler       | `src/gossiptoon/video/assembler.py`         | FFmpeg final assembly      |
| FFmpeg Builder        | `src/gossiptoon/video/ffmpeg_builder.py`    | Filter chain construction  |
| Ken Burns Effect      | `src/gossiptoon/video/effects/ken_burns.py` | Zoom/pan effect            |
| Caption Effect        | `src/gossiptoon/video/effects/captions.py`  | Dynamic captions           |

## Pipeline Architecture

GossipToon uses a **5-stage pipeline** with checkpoint recovery:

```
Story Finding → Script Writing → Audio Generation → Visual Generation → Video Assembly
     ↓               ↓                  ↓                   ↓                  ↓
  Reddit API      GPT-4o          ElevenLabs          Gemini Flash      FFmpeg Rendering
                                    Whisper                              Ken Burns + Captions
```

| Stage                    | Input           | Output             | Checkpoint          |
| ------------------------ | --------------- | ------------------ | ------------------- |
| **1. Story Finding**     | Reddit URL      | Story object       | `story_found`       |
| **2. Script Writing**    | Story           | 5-act Script       | `script_generated`  |
| **3. Audio Generation**  | Script          | Audio + Timestamps | `audio_generated`   |
| **4. Visual Generation** | Script          | 9:16 Images        | `visuals_generated` |
| **5. Video Assembly**    | Audio + Visuals | Final MP4          | `video_assembled`   |

### Key Design Decisions

- **Audio as Master Clock**: Audio duration is fixed after TTS; visuals are extended to match
- **Pydantic for LLM Output**: Strict validation prevents malformed outputs
- **FFmpeg Subprocess Strategy**: More stable and 5x faster than Python libraries
- **Character Consistency via I2I**: First scene generates character; subsequent scenes use reference

## Testing Instructions

1. **Always run tests before committing**: `pytest`
2. **Add tests for new functionality** in appropriate `tests/` subdirectory
3. **Unit tests** should mock external APIs (OpenAI, Gemini, ElevenLabs)
4. **Integration tests** can use real APIs with proper fixtures
5. **Check coverage**: `pytest --cov=src/gossiptoon --cov-report=html`

## Configuration

Environment variables (`.env` file):

```env
# Required API Keys
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
ELEVENLABS_API_KEY=...

# Optional Reddit API
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=GossipToon/1.0
```

YAML configuration (`config/custom.yaml`):

```yaml
video:
  resolution: "1080x1920"
  fps: 30
  ken_burns_enabled: true
  captions_enabled: true

audio:
  voice_id: "default"

visual:
  style: "cinematic"
  aspect_ratio: "9:16"
```

## LLM Model Swapping

The project uses LangChain for LLM abstraction. To swap models:

```python
# Option 1: Claude
from langchain_anthropic import ChatAnthropic
self.llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", api_key=...)

# Option 2: Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", api_key=...)

# Option 3: Local Ollama
from langchain_ollama import ChatOllama
self.llm = ChatOllama(model="llama3.1:70b")
```

## Adding New Effects

Create effects by implementing the `VideoEffect` base class:

```python
from gossiptoon.video.effects.base import VideoEffect

class MyCustomEffect(VideoEffect):
    def apply(self, input_label: str, duration: float, params: dict) -> str:
        return f"[{input_label}]your_ffmpeg_filter[out]"

    def get_filter_string(self) -> str:
        return "filter_name=param1:param2"
```

## Related Documentation

- [README.md](README.md) - Project overview and quick start
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Detailed system architecture and modularity guide
