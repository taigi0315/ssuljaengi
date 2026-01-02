# TICKET-030: Enhance Narrative Dramatization (Hook & Ending)

**Priority**: High (P1)
**Status**: Todo
**Assignee**: AI Agent
**Created**: 2026-01-01
**Depends On**: None

## Problem

Current scriptwriter retells stories in chronological order, which doesn't maximize engagement. Need to restructure narratives for viral potential (likes, comments, shares).

## Goal

Update Scriptwriter to dramatically restructure stories using proven engagement techniques:
1. **The Hook** (0-3 seconds): Start with the most shocking/dramatic moment
2. **The Ending**: Close with controversial question or cliffhanger
3. **The Tone**: Emphasize conflict and polarization ("Two halves of people get involved")

## Requirements

### Narrative Structure

1. **Hook (First 0-3 seconds)**
   - Identify the most dramatic moment in the story
   - Move it to the opening
   - Use shocking/provocative framing
   - Examples:
     - "You won't believe what my MIL did next..."
     - "I caught my wife doing the unthinkable..."
     - "This is the day my life completely fell apart..."

2. **Story Body**
   - Build context after the hook
   - Maintain tension throughout
   - Emphasize conflict and emotions
   - Use polarizing language (but stay truthful)

3. **Ending (Last 5-10 seconds)**
   - Open-ended question to audience
   - Controversial statement
   - Request for judgment/opinions
   - Examples:
     - "Was I wrong? Let me know in the comments."
     - "Would you have done the same thing?"
     - "People are divided - what's YOUR take?"

### Tone & Style Guidelines

1. **Conflict Emphasis**
   - Highlight disagreements and drama
   - Use emotionally charged language
   - Present multiple perspectives
   - Create "us vs them" dynamics

2. **Avoid Flat Retelling**
   - Don't just summarize chronologically
   - Add dramatic framing
   - Use rhetorical questions
   - Build suspense

3. **Engagement Triggers**
   - Controversial opinions
   - Moral dilemmas
   - Relatable conflicts
   - Unexpected twists

## Implementation Plan

### Phase A: Scriptwriter Prompt Engineering

- [ ] Research viral storytelling patterns
- [ ] Analyze high-performing YouTube Shorts/TikToks
- [ ] Draft new scriptwriter system prompt
- [ ] Add hook extraction logic to prompts
- [ ] Add engagement ending templates

### Phase B: Story Analysis Module

- [ ] Implement "dramatic moment detection"
- [ ] Extract peak conflict/emotion from story
- [ ] Identify controversial elements
- [ ] Generate engagement questions

### Phase C: Script Structure Update

- [ ] Modify script generation to use hook-first structure
- [ ] Add engagement ending to all scripts
- [ ] Update timing to frontload drama
- [ ] Test with various story types

### Phase D: Validation & Testing

- [ ] Test hook effectiveness (manually review)
- [ ] Validate ending engagement potential
- [ ] Ensure factual accuracy maintained
- [ ] A/B test engagement metrics (manual)

## File Locations (Estimated)

- Scriptwriter: `src/gossiptoon/agents/scriptwriter.py`
- Prompts: `src/gossiptoon/prompts/scriptwriter_prompts.py`
- Story analyzer: `src/gossiptoon/agents/story_analyzer.py` (new)

## Prompt Engineering Examples

### System Prompt Addition

```
Your goal is to MAXIMIZE ENGAGEMENT (likes, comments, shares).

CRITICAL RULES:
1. THE HOOK (0-3 seconds): Start with the most shocking/dramatic moment
   - Don't start chronologically
   - Lead with conflict, surprise, or emotion
   - Make viewers NEED to keep watching

2. THE ENDING (last 5-10 seconds): Provoke comments
   - Ask controversial question
   - Request viewer judgment
   - Create debate opportunity

3. TONE: Emphasize conflict and polarization
   - Highlight disagreements
   - Use emotionally charged language
   - Create "us vs them" dynamics
   - Make people PICK A SIDE

AVOID:
- Flat chronological retelling
- Neutral/boring tone
- Conclusive endings that don't invite discussion
```

### Hook Examples by Story Type

```python
HOOK_TEMPLATES = {
    "relationship": [
        "I found out my {relationship} was {shocking_action}...",
        "My {relationship} did something I'll never forgive...",
        "This is the moment I knew my {relationship} was over...",
    ],
    "family": [
        "My {family_member} crossed a line I never thought possible...",
        "I can't believe what my {family_member} said at {event}...",
        "Everything changed when I discovered my {family_member}'s secret...",
    ],
    "revenge": [
        "They thought they could {wrong_action}. They were wrong...",
        "This is how I got revenge on {target}...",
        "You won't believe what I did to get back at {target}...",
    ],
}
```

### Ending Templates

```python
ENGAGEMENT_ENDINGS = [
    "Was I wrong? Let me know in the comments.",
    "What would YOU have done in my situation?",
    "People are divided on this. What's your take?",
    "Am I the villain here? You decide.",
    "Would you have reacted the same way?",
    "Let me know if I overreacted in the comments.",
    "I need to know - did I do the right thing?",
]
```

## Acceptance Criteria

- [ ] All generated scripts start with dramatic hook
- [ ] Hook occurs within first 3 seconds of video
- [ ] All scripts end with engagement question/statement
- [ ] Tone emphasizes conflict and polarization
- [ ] No chronological "Once upon a time..." openings
- [ ] Factual accuracy maintained (no fabrication)
- [ ] Scripts feel more dynamic and engaging

## Quality Metrics

- Manual review of 20+ generated scripts for:
  - Hook effectiveness (1-5 rating)
  - Ending engagement potential (1-5 rating)
  - Overall dramatic tension (1-5 rating)
  - Tone/conflict emphasis (1-5 rating)

## Related Tickets

- TICKET-026: Optimize Image Duration (both affect pacing)
- TICKET-031: High-Impact Text Overlay (visual emphasis complements narrative)

## Notes

- **Inspiration**: TikTok/YouTube Shorts best practices
- **Ethical Consideration**: Stay truthful, don't fabricate events
- **Target Metrics**: Likes, Comments, Shares (not just views)
- **User Feedback**: "Emphasize conflict - two halves of people get involved"
