# TICKET-016: EngagementWriter Agent

**Goal**: Create separate LangChain agent to generate viewer engagement hooks (text overlays).

## Background

User feedback: Videos need text overlays to:

- Help understanding
- Drive sympathy
- Provoke debate/comments
- Increase engagement

## Requirements

- **Separate from ScriptWriter** (maintainability, tuning)
- **2-3 hooks per video**
- **Position**: Top of screen
- **Styles**: Questions, comments, reaction polls
- **Timing**: LLM decides based on dramatic moments

## Tasks

### Phase A: Models & Agent

- [ ] Create `EngagementHook` and `EngagementProject` models <!-- id: 1 -->
- [ ] Implement `EngagementWriter` LangChain agent <!-- id: 2 -->
- [ ] Write system prompt with examples <!-- id: 3 -->
- [ ] Unit tests <!-- id: 4 -->

### Phase B: Pipeline Integration

- [ ] Add `_run_engagement_writer()` to orchestrator <!-- id: 5 -->
- [ ] Checkpoint integration <!-- id: 6 -->
- [ ] Update pipeline flow <!-- id: 7 -->

### Phase C: Testing

- [ ] Test with existing scripts <!-- id: 8 -->
- [ ] Verify hook quality and placement <!-- id: 9 -->
- [ ] End-to-end test <!-- id: 10 -->

## Acceptance Criteria

- [ ] Generates 2-3 hooks consistently
- [ ] Hooks < 50 characters
- [ ] Placed at strategic moments (hook, crisis, climax)
- [ ] Mix of styles (question, comment, poll)
- [ ] No pipeline errors
- [ ] Checkpoint save/load works
