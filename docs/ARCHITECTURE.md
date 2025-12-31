# GossipToon Engine - Architecture & Modularity Guide

## Design Principles

The GossipToon Engine is built with **extreme modularity** and **scalability** as core principles:

1. **Easy LLM Swapping** - Change models without touching business logic
2. **Lightweight Components** - Each module has single responsibility
3. **Tunable Parameters** - All effects/settings exposed as Pydantic models
4. **Assembly Pattern** - Components compose together cleanly
5. **Future-Proof** - Adding new features doesn't require refactoring

---

## 1. LLM Abstraction Layer

### Current Design (Easy to Swap Models)

```python
# src/gossiptoon/agents/script_writer.py
class ScriptWriterAgent:
    def __init__(self, config: ConfigManager):
        # LangChain abstracts the model interface
        self.llm = ChatOpenAI(
            model="gpt-4o",  # <-- Change this line to swap models
            temperature=0.8,
            api_key=config.api.openai_api_key,
        )
```

### To Switch to Claude/Gemini (3 lines of code):

```python
# Option 1: Claude
from langchain_anthropic import ChatAnthropic
self.llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", api_key=config.api.anthropic_api_key)

# Option 2: Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", api_key=config.api.google_api_key)

# Option 3: Local Ollama
from langchain_ollama import ChatOllama
self.llm = ChatOllama(model="llama3.1:70b")
```

### Why This Works:
- **LangChain Interface** - All models implement same interface (`.ainvoke()`, `.stream()`, etc.)
- **Pydantic Output Parsing** - Works with any model that can output JSON
- **No Business Logic Changes** - ScriptWriter agent code stays identical

---

## 2. Modular Component Design

### Separation of Concerns

```
┌─────────────────────────────────────────────────────┐
│                   THIN LAYERS                       │
├─────────────────────────────────────────────────────┤
│  Agents (StoryFinder, ScriptWriter)                 │
│    - Orchestration logic only                       │
│    - Delegate to tools                              │
├─────────────────────────────────────────────────────┤
│  Tools (RedditSearch, TavilySearch, Whisper, etc.)  │
│    - Single responsibility                          │
│    - Independent, replaceable                       │
├─────────────────────────────────────────────────────┤
│  Models (Pydantic schemas)                          │
│    - Data validation                                │
│    - No logic                                       │
├─────────────────────────────────────────────────────┤
│  Config (ConfigManager)                             │
│    - Centralized settings                           │
│    - Environment-based                              │
└─────────────────────────────────────────────────────┘
```

### Example: Adding a New Story Source (Reddit → Twitter)

**Step 1:** Create new tool (independent module)
```python
# src/gossiptoon/agents/tools/twitter_search.py
class TwitterSearchTool:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search(self, query: str) -> list[Tweet]:
        # Twitter-specific logic
        pass
```

**Step 2:** Plug into agent (no refactoring)
```python
# src/gossiptoon/agents/story_finder.py
class StoryFinderAgent:
    def __init__(self, config: ConfigManager):
        # Just add new tool alongside existing
        self.reddit_tool = RedditSearchTool(...)
        self.twitter_tool = TwitterSearchTool(...)  # <-- New!

    async def find_story(self, source: str = "reddit"):
        if source == "reddit":
            return await self.reddit_tool.search(...)
        elif source == "twitter":  # <-- New!
            return await self.twitter_tool.search(...)
```

---

## 3. FFmpeg Effects - Strategy Pattern (Phase 5 Preview)

### Problem: FFmpeg Commands Can Get Messy

**Bad Approach** (monolithic):
```python
def render_video(images, audio):
    # 500 lines of FFmpeg filter chain building
    cmd = f"ffmpeg -i {img1} -i {img2} ... [complex filter] ..."
    # Impossible to tune, hard to read
```

### Good Approach: Modular Effect System

```python
# src/gossiptoon/video/effects/base.py
from abc import ABC, abstractmethod

class VideoEffect(ABC):
    """Base class for all video effects."""

    @abstractmethod
    def apply(self, input_label: str, duration: float, params: dict) -> str:
        """Apply effect and return output label.

        Args:
            input_label: FFmpeg input label (e.g., "v0")
            duration: Clip duration in seconds
            params: Effect-specific parameters

        Returns:
            Output label for next effect
        """
        pass

    @abstractmethod
    def get_filter_string(self) -> str:
        """Get FFmpeg filter string for this effect."""
        pass
```

```python
# src/gossiptoon/video/effects/ken_burns.py
class KenBurnsEffect(VideoEffect):
    """Ken Burns pan and zoom effect."""

    def __init__(
        self,
        zoom_start: float = 1.0,
        zoom_end: float = 1.2,
        direction: str = "in",  # "in" or "out"
        fps: int = 30,
    ):
        self.zoom_start = zoom_start
        self.zoom_end = zoom_end
        self.direction = direction
        self.fps = fps

    def apply(self, input_label: str, duration: float, params: dict) -> str:
        # Override defaults with params if provided
        zoom_start = params.get("zoom_start", self.zoom_start)
        zoom_end = params.get("zoom_end", self.zoom_end)

        # Build filter string
        zoom_expr = self._build_zoom_expression(zoom_start, zoom_end, duration)
        filter_str = (
            f"[{input_label}]"
            f"zoompan=z={zoom_expr}:d={int(duration*self.fps)}:"
            f"s=1080x1920:fps={self.fps}"
            f"[out]"
        )

        return filter_str

    def _build_zoom_expression(self, start: float, end: float, duration: float) -> str:
        if self.direction == "in":
            return f"'if(lte(zoom,{end}),{start}+({end}-{start})*t/{duration},{end})'"
        else:
            return f"'if(lte(zoom,{start}),{end}-({end}-{start})*t/{duration},{start})'"
```

```python
# src/gossiptoon/video/effects/captions.py
class CaptionsEffect(VideoEffect):
    """Dynamic word-level captions synced to audio."""

    def __init__(
        self,
        fontsize: int = 48,
        fontcolor: str = "white",
        font: str = "Arial-Bold",
        position: str = "bottom",
    ):
        self.fontsize = fontsize
        self.fontcolor = fontcolor
        self.font = font
        self.position = position

    def apply(self, input_label: str, caption: CaptionSegment, params: dict) -> str:
        # Easy to tune - all parameters exposed
        text = self._escape_text(caption.text)
        y_position = self._get_y_position(self.position)

        filter_str = (
            f"[{input_label}]"
            f"drawtext=text='{text}':"
            f"fontfile=/System/Library/Fonts/Supplemental/{self.font}.ttf:"
            f"fontsize={params.get('fontsize', self.fontsize)}:"
            f"fontcolor={params.get('fontcolor', self.fontcolor)}:"
            f"x=(w-text_w)/2:y={y_position}:"
            f"enable='between(t,{caption.start_time},{caption.end_time})'"
            f"[out]"
        )

        return filter_str
```

### Usage: Composing Effects (Clean Assembly)

```python
# src/gossiptoon/video/assembler.py
class VideoAssembler:
    def __init__(self, config: ConfigManager):
        # Effects are pluggable components
        self.ken_burns = KenBurnsEffect(
            zoom_start=config.video.ken_burns_zoom_start,
            zoom_end=config.video.ken_burns_zoom_end,
        )
        self.captions = CaptionsEffect(
            fontsize=config.video.caption_fontsize,
            fontcolor=config.video.caption_color,
        )

    def render(self, timeline: list[TimelineSegment]) -> Path:
        filters = []

        for segment in timeline:
            # Apply Ken Burns to image
            kb_filter = self.ken_burns.apply(
                f"img{segment.scene_id}",
                segment.duration,
                params={}  # Or override per-scene
            )
            filters.append(kb_filter)

            # Add captions
            for caption in segment.captions:
                cap_filter = self.captions.apply(
                    "outv",
                    caption,
                    params={"fontsize": 56}  # Tune per caption!
                )
                filters.append(cap_filter)

        # Combine filters
        ffmpeg_cmd = ["ffmpeg", "-filter_complex", ";".join(filters), ...]
        return self._execute_ffmpeg(ffmpeg_cmd)
```

### Benefits:
1. **Easy to Tune** - Change `fontsize=48` to `56` in one place
2. **Easy to Read** - Each effect is self-contained
3. **Easy to Test** - Unit test each effect independently
4. **Easy to Extend** - Add new effects without touching existing code

---

## 4. Pydantic Models as Configuration

### All Parameters Are Typed and Validated

```python
# src/gossiptoon/models/video.py
class RenderConfig(BaseModel):
    """Video rendering configuration - all settings in one place."""

    resolution: str = "1080x1920"
    fps: int = 30
    video_codec: str = "libx264"
    preset: str = "medium"

    # Effect settings (easy to expose to CLI/UI)
    ken_burns_zoom_start: float = 1.0
    ken_burns_zoom_end: float = 1.2
    caption_fontsize: int = 48
    caption_color: str = "white"
    caption_position: str = "bottom"

    @field_validator("preset")
    @classmethod
    def validate_preset(cls, v: str) -> str:
        valid = ["ultrafast", "fast", "medium", "slow"]
        if v not in valid:
            raise ValueError(f"Invalid preset: {v}")
        return v
```

### Tuning is Simple:

```python
# config/custom.yaml
video:
  ken_burns_zoom_end: 1.3  # More dramatic zoom
  caption_fontsize: 56      # Larger captions
  preset: fast              # Faster rendering

# Load and use
config = ConfigManager()
config.load_yaml("config/custom.yaml")
assembler = VideoAssembler(config)
```

---

## 5. Workflow State Management (LangGraph)

### Modular Nodes

```python
# src/gossiptoon/agents/state.py
class WorkflowBuilder:
    def build(self) -> StateGraph:
        # Each node is independent - easy to add/remove/reorder
        self.graph.add_node("find_story", self._find_story_node)
        self.graph.add_node("write_script", self._write_script_node)
        self.graph.add_node("generate_audio", self._generate_audio_node)
        self.graph.add_node("create_visuals", self._create_visuals_node)
        self.graph.add_node("assemble_video", self._assemble_video_node)

        # Easy to modify flow
        self.graph.set_entry_point("find_story")
        self.graph.add_edge("find_story", "write_script")
        # ... define flow

        return self.graph.compile(checkpointer=self.checkpointer)
```

### Adding a New Step (e.g., "optimize_audio"):

```python
# 1. Add node method
def _optimize_audio_node(self, state: GossipToonState) -> GossipToonState:
    # Audio optimization logic
    pass

# 2. Register node
self.graph.add_node("optimize_audio", self._optimize_audio_node)

# 3. Insert in flow
self.graph.add_edge("generate_audio", "optimize_audio")  # Before visuals
self.graph.add_edge("optimize_audio", "create_visuals")
```

---

## 6. Testing Strategy (Modularity Enables Easy Testing)

### Unit Tests: Each Component Isolated

```python
def test_ken_burns_effect():
    effect = KenBurnsEffect(zoom_start=1.0, zoom_end=1.5)
    filter_str = effect.apply("v0", duration=5.0, params={})

    assert "zoompan" in filter_str
    assert "1.0" in filter_str
    assert "1.5" in filter_str
```

### Integration Tests: Mock External Dependencies

```python
@pytest.mark.asyncio
async def test_script_writer_with_mocked_llm(sample_story):
    agent = ScriptWriterAgent(config)

    # Mock LLM - no real API call
    with patch.object(agent.llm, "ainvoke") as mock:
        mock.return_value = sample_script_json
        script = await agent.write_script(sample_story)

        assert len(script.acts) == 5
```

---

## 7. Future Extensibility Examples

### Adding New LLM Provider

```python
# src/gossiptoon/agents/llm_factory.py
def create_llm(provider: str, config: ConfigManager):
    if provider == "openai":
        return ChatOpenAI(...)
    elif provider == "anthropic":
        return ChatAnthropic(...)
    elif provider == "gemini":
        return ChatGoogleGenerativeAI(...)
    elif provider == "local":
        return ChatOllama(...)
```

### Adding New Video Effect

```python
# src/gossiptoon/video/effects/blur.py
class BlurEffect(VideoEffect):
    def __init__(self, strength: float = 5.0):
        self.strength = strength

    def apply(self, input_label: str, duration: float, params: dict) -> str:
        return f"[{input_label}]boxblur={self.strength}[out]"

# Usage: Just add to effect pipeline
assembler.effects.append(BlurEffect(strength=10.0))
```

### Adding New Audio Provider

```python
# src/gossiptoon/audio/tts_factory.py
def create_tts_client(provider: str, config: ConfigManager):
    if provider == "elevenlabs":
        return ElevenLabsClient(...)
    elif provider == "google":
        return GoogleTTSClient(...)
    elif provider == "azure":
        return AzureTTSClient(...)
```

---

## Summary: Modularity Checklist

- [x] **LLM Swappable** - LangChain interface + 3 lines to change model
- [x] **Tool-Based Architecture** - Each tool (Reddit, Tavily, Whisper) is independent
- [x] **Strategy Pattern for Effects** - Each FFmpeg effect is a class with tunable params
- [x] **Pydantic Everywhere** - All config/data structures validated and typed
- [x] **Thin Layers** - Agents orchestrate, tools execute (single responsibility)
- [x] **Easy Testing** - Mock at boundaries, test components in isolation
- [x] **LangGraph State** - Add/remove/reorder pipeline steps without refactoring
- [x] **No Monolithic Functions** - Everything is <100 lines, focused

**Result:** You can change LLM models, add new effects, swap TTS providers, or modify the pipeline flow without touching core business logic.
