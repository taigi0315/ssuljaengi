# Agent Behavior Guidelines

## 1. Language Protocol (Strict)

- **Conversation**: Speak to me in **Korean (한국어)**.
- **Artifacts**: All code, comments, tickets, docs, and commits must be in **English**.

## 2. Project Management & Tickets

- **Ticket System**: All work must start from a ticket in `tickets/todo/`.
- **Ticket Lifecycle**:
  1.  Create ticket in `tickets/todo/`.
  2.  Implement & Test.
  3.  Review checklist (`- [x]`).
  4.  **MOVE** file to `tickets/done/` BEFORE merging to main.

## 3. Git & Version Control

- **No Main Commits**: NEVER push to `main` directly.
- **Branching**: Use feature branches (`feature/xyz`).
- **Secrets**: NEVER commit secrets or `.env` files. Update `.gitignore` if needed.
- **Commits**: Use **Conventional Commits** (e.g., `feat:`, `fix:`).

## 4. Coding Standards & Hygiene

- **Architecture**: Modular, OOP, Configurable (No hardcoding parameters).
- **Dependency Hygiene**: If you import a new library, **IMMEDIATELY** update `requirements.txt` (or equivalent).
- **Formatting**: Run code formatters (e.g., Black, Prettier) before submitting for review.
- **Debugging**: Apply "3-Strike Rule". Fail 3 times? STOP and ask user in Korean.

## 5. Documentation & Memory

- **Context**: Read `docs/ARCHITECTURE.md` before planning.
- **Visuals**: Use **Mermaid.js** for design changes.
- **ADR**: Record major architectural decisions in `docs/decisions/`.
- **Work Log**: Update `WORKLOG.md` with the narrative of changes.
