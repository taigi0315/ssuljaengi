# GossipToon 🎬

AI-powered video generation system that transforms viral Reddit gossip into engaging YouTube Shorts (60-second vertical videos).

**Transform this:**
> "AITA for telling my sister her haircut looks bad?"

**Into this:**
> A fully-produced 60-second vertical video with cinematic visuals, emotional voice acting, dynamic captions, and Ken Burns effects.

---

## ✨ Features

- **🎭 Five-Act Narrative Structure**: Automatically converts stories into Hook → Build → Crisis → Climax → Resolution
- **🎙️ Emotional Voice Acting**: TTS with emotion mapping (dramatic, excited, shocked, neutral)
- **🎨 Cinematic AI Visuals**: 9:16 vertical images with character consistency across scenes
- **⏱️ Frame-Perfect Captions**: Word-level synchronization using Whisper timestamps
- **🎬 Professional Effects**: Ken Burns zoom/pan, dynamic caption highlighting
- **💾 Checkpoint Recovery**: Resume from any stage if pipeline fails
- **🔧 Highly Configurable**: Tune every aspect via YAML config

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **FFmpeg** (for video rendering)
- **API Keys:**
  - OpenAI (GPT-4o for script generation)
  - Google Gemini (Flash 2.5/3.0 for image generation)
  - ElevenLabs (for TTS)
  - Reddit API credentials (optional, for story finding)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ssuljaengi.git
cd ssuljaengi

# Install dependencies
pip install -e .

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Configure API Keys

Create a `.env` file in the project root:

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

### Validate Setup

```bash
gossiptoon validate
```

This checks:
- ✅ API keys are present
- ✅ FFmpeg is installed
- ✅ Output directories exist
- ✅ Whisper model (if installed)

### Generate Your First Video

```bash
gossiptoon run https://reddit.com/r/AmItheAsshole/comments/...
```

The pipeline will:
1. 🔍 Extract story from Reddit
2. ✍️ Generate five-act script
3. 🎙️ Create emotional TTS audio
4. 🎨 Generate cinematic images
5. 🎬 Assemble final video

**Output:** `outputs/videos/project_YYYYMMDD_HHMMSS.mp4`

---

## 📋 CLI Commands

### Run Pipeline

```bash
# Generate video from Reddit URL
gossiptoon run <reddit_url>

# With custom config
gossiptoon run <reddit_url> --config config/custom.yaml
```

### Resume from Checkpoint

If pipeline fails, resume from last successful stage:

```bash
gossiptoon resume project_20250131_123456
```

### List Checkpoints

```bash
gossiptoon list
```

Output:
```
┌──────────────────────────────┬────────────────────┬─────────────────────┐
│ Project ID                   │ Stage              │ Updated             │
├──────────────────────────────┼────────────────────┼─────────────────────┤
│ project_20250131_123456      │ audio_generated    │ 2025-01-31 12:45:00 │
│ project_20250131_234567      │ completed          │ 2025-01-31 23:50:00 │
└──────────────────────────────┴────────────────────┴─────────────────────┘
```

### Clean Old Checkpoints

```bash
# Delete checkpoints older than 7 days (default)
gossiptoon clean

# Custom retention period
gossiptoon clean --days 14
```

### Validate Setup

```bash
gossiptoon validate
```

---

## 🏗️ Architecture

GossipToon uses a **5-stage pipeline** with checkpoint recovery:

```
Story Finding → Script Writing → Audio Generation → Visual Generation → Video Assembly
     ↓               ↓                  ↓                   ↓                  ↓
  Reddit API      GPT-4o          ElevenLabs          Gemini Flash      FFmpeg Rendering
                                    Whisper                              Ken Burns + Captions
```

### Pipeline Stages

| Stage | Input | Output | Checkpoint |
|-------|-------|--------|------------|
| **1. Story Finding** | Reddit URL | Story object | `story_found` |
| **2. Script Writing** | Story | 5-act Script | `script_generated` |
| **3. Audio Generation** | Script | Audio + Timestamps | `audio_generated` |
| **4. Visual Generation** | Script | 9:16 Images | `visuals_generated` |
| **5. Video Assembly** | Audio + Visuals | Final MP4 | `video_assembled` |

### Key Design Decisions

**Audio as Master Clock**: Audio duration is fixed after TTS; visuals are extended to match. This ensures perfect A/V sync.

**Pydantic for LLM Output**: Strict validation prevents malformed outputs from breaking downstream stages.

**FFmpeg Subprocess Strategy**: More stable and 5x faster than Python libraries like MoviePy.

**Character Consistency via I2I**: First scene generates character normally; subsequent scenes use previous image as reference.

---

## ⚙️ Configuration

Configuration is managed via YAML files in `config/`:

```yaml
# config/default.yaml
video:
  resolution: "1080x1920"  # Vertical video
  fps: 30
  ken_burns_enabled: true
  captions_enabled: true

audio:
  voice_id: "default"      # ElevenLabs voice

visual:
  style: "cinematic"       # Image generation style
  aspect_ratio: "9:16"
```

**Override defaults:**

```bash
gossiptoon run <url> --config config/custom.yaml
```

See [Configuration Guide](docs/configuration.md) for all options.

---

## 🎨 Customization

### Effect Tuning

All effects are **highly tunable** via code:

```python
# Ken Burns effect
ken_burns_config = KenBurnsConfig(
    zoom_start=1.0,
    zoom_end=1.3,        # More dramatic zoom
    pan_direction="up",
    pan_intensity=0.2,
    ease_function="ease-in-out"
)
```

```python
# Caption styling
caption_config = CaptionConfig(
    font_family="Arial",
    font_size=48,
    font_color="white",
    box_enabled=True,
    box_color="black@0.6",
    highlight_enabled=True,
    highlight_color="yellow"
)
```

### Custom Effects

Create your own effects by implementing the `Effect` interface:

```python
from gossiptoon.video.effects.base import Effect, EffectConfig

class MyCustomEffect(Effect):
    def get_filter_string(self, input_label, output_label, **context):
        return f"{input_label}your_ffmpeg_filter{output_label}"

    def get_effect_name(self):
        return "MyCustomEffect"
```

See [Effect Development Guide](docs/effects.md) for details.

---

## 📊 Performance

Typical end-to-end times for 60-second video:

| Stage | Time | Notes |
|-------|------|-------|
| Story Finding | ~5s | Reddit API |
| Script Writing | ~15s | GPT-4o |
| Audio Generation | ~90s | ElevenLabs TTS + Whisper |
| Visual Generation | ~120s | Gemini Flash (10-15 images) |
| Video Assembly | ~45s | FFmpeg rendering |
| **Total** | **~5 min** | With parallel optimizations |

**Optimization tips:**
- Use `preset="faster"` for quicker (lower quality) renders
- Reduce image count by adjusting scene breakdown
- Use cheaper models (GPT-4o-mini, Gemini Flash 1.5)

---

## 🧪 Testing

Run the test suite:

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# With coverage report
pytest --cov=src/gossiptoon --cov-report=html
```

**Current coverage:** 38%

---

## 🐛 Troubleshooting

### FFmpeg Not Found

**Error:** `VideoAssemblyError: FFmpeg not found`

**Solution:**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### API Rate Limits

**Error:** `OpenAIAPIError: Rate limit exceeded`

**Solution:**
- Wait and retry (pipeline will auto-resume from checkpoint)
- Upgrade API tier for higher limits
- Use `gossiptoon resume <project_id>` to continue

### Out of Memory

**Error:** Process killed during video assembly

**Solution:**
- Reduce video resolution: `resolution: "720x1280"`
- Use faster preset: `preset: "ultrafast"`
- Close other applications

### Character Inconsistency

**Problem:** Characters look different across scenes

**Solution:**
- Ensure character descriptions are detailed in prompts
- Check I2I reference images are being saved correctly
- Try different `visual.style` settings

See [Troubleshooting Guide](docs/troubleshooting.md) for more.

---

## 📚 Documentation

- [Architecture Overview](docs/architecture.md)
- [Pipeline Flow](docs/pipeline.md)
- [Configuration Guide](docs/configuration.md)
- [API Reference](docs/api_reference.md)
- [Troubleshooting](docs/troubleshooting.md)

---

## 🛣️ Roadmap

- [ ] **Real-time voice cloning** for character dialogue
- [ ] **Background music** generation and sync
- [ ] **Multiple visual styles** (anime, realistic, comic)
- [ ] **Batch processing** for multiple stories
- [ ] **Web UI** for non-technical users
- [ ] **Cloud deployment** (AWS Lambda, GCP Functions)
- [ ] **Monetization tracking** (YouTube Analytics integration)

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Development setup:**

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run pre-commit hooks
pre-commit install

# Run tests before committing
pytest
```

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **OpenAI** for GPT-4o (script generation)
- **Google** for Gemini Flash (image generation)
- **ElevenLabs** for emotional TTS
- **OpenAI Whisper** for word-level timestamps
- **FFmpeg** for video rendering

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/ssuljaengi/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/ssuljaengi/discussions)

---

**Made with ❤️ by the GossipToon team**

Turn gossip into gold. 🎬✨
