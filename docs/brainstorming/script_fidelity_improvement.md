# Brainstorming: Script Fidelity & Flow Improvement

**Date**: 2026-01-03
**Objective**: Enhance the `ScriptWriter` to ensure < 5% information loss from original Reddit stories, improve narrative flow, and correctly balance narration vs. dialogue.

## 1. Problem Definition

The current script generation pipeline suffers from significant information loss (~30% or more of original context is missing).

- **Symptom 1: Information Gaps**: Key details from the Reddit post are dropped to fit into rigid time constraints or dialogue formats.
- **Symptom 2: Disjointed Flow**: The "Gossip Style" rewrite often fragments the narrative into reaction bites ("OMG", "No way") rather than telling the story.
- **Symptom 3: Over-Dramatization**: The instruction to "transform narration into dialogue" forces awkward conversations where exposition should be used.

## 2. Root Cause Analysis

### A. Over-Structuring in `SceneStructurer`

- **Rigid Durations**: Scenes are forced into 2-5 second buckets. Complex sentences take longer to read.
- **Act Limits**: The 5-act structure has tight duration targets (e.g., Hook 2-5s) which may cut off necessary context.

### B. "Gossip Style" Prompting in `ScriptWriter`

- **Focus on Reaction**: The system prompt prioritizes "reaction > exposition" and "imperfect speech". This encourages the LLM to generate filler words ("Like, um, literally") instead of story content.
- **Forced Dialogue**: The instruction "Transform narration into MEANINGFUL dialogue whenever possible" backfired, causing the LLM to convert efficient narration into inefficient, low-info conversational ping-pong.

## 3. Proposed Strategy: "Narration as Backbone, Dialogue as Spice"

We need to shift the paradigm fundamental:

- **Narration (85%)**: The protagonist (Narrator) carries the baton. They tell the story mostly as it was written in the post, preserving the original "voice" and details.
- **Dialogue (15%)**: Dialogue is used **exclusively** for high-impact moments—confrontations, immediate reactions, or specific quotes mentioned in the story. It is an _embellishment_, not the vehicle for plot progression.

### Core Principles

1.  **Fidelity First**: The script must convey 95-100% of the factual information present in the source text.
2.  **Flow over Format**: If a scene needs 10 seconds to tell a complex part of the story, let it take 10 seconds. Don't chop it up arbitrarily.
3.  **Respect the Source**: Reddit stories are written in first-person ("I"). Keep that perspective intact.

## 4. Implementation Plan

### Phase 1: Refining the Prompts

#### `ScriptWriter`

- **Remove** instructions to "rewrite in gossip style" or "add fillers".
- **Add** instructions to "Summarize lightly but PRESERVE all key details".
- **Enforce Ratio**: Explicitly state "85% Narration / 15% Dialogue".
- **Dialogue Rule**: "Only use dialogue when the original story explicitly captures a conversation, or for a single punchy reaction line."

#### `SceneStructurer`

- **Relax Constraints**: Allow scene durations to float based on content density (e.g., 4-8s instead of 2-4s).
- **Content-Driven Acts**: Instead of rigid time targets, guide acts by content milestones (e.g., "Crisis ends when the secret is revealed", regardless of time).

### Phase 2: Evaluation & Feedback Loop (New)

We need a way to measure "Information Retention".

#### `ScriptEvaluator` Update

- **New Check: Information Coverage**:
  - Input: Original Story Text + Generated Script
  - Prompt: "Compare the script to the original story. List any key facts, plot points, or details that were omitted in the script. Rate coverage from 0-100%."
  - **Threshold**: If coverage < 90%, fail validation and regenerate.
- **Flow Check**: "Does the narration transition smoothly between scenes? Are there abrupt jumps?"

## 5. Technical Changes Required

1.  **Modify `ScriptWriterAgent.SYSTEM_PROMPT`**:
    - Shift from "Gossip Writer" persona to "Compelling Storyteller" persona.
    - Emphasize "Retention of Details".
2.  **Modify `SceneStructurerAgent.SYSTEM_PROMPT`**:
    - Loosen duration constraints.
3.  **Update `ScriptEvaluator`**:
    - Add `_check_information_fidelity()` method.
    - Add `fidelity_score` to `ValidationResult`.

## 6. Expectation

- **Before**: "OMG, he cheated! Can you believe it?" (Details about _how_ or _when_ are lost).
- **After**: "I found the receipt in his car dated last Tuesday. When I confronted him, he tried to deny it, but..." (Narrator tells the facts, Dialogue adds the shout of "Liar!").

## 7. Timeline

1.  **Step 1**: Update Prompts (ScriptWriter, SceneStructurer) - [Immediate]
2.  **Step 2**: Implement Fidelity Check in Evaluator - [Follow-up]
3.  **Step 3**: Test with complex story - [Verification]
