# Workflow Protocol (v2.0)

I have a request for a new task/Epic. Follow this lifecycle strictly:

1. **Phase 1: Context & Planning**

- **Context Gathering (Crucial Step)**:
- **IF New Feature**: Review all relevant documentation in `docs/` (including `ARCHITECTURE.md`) to understand the existing codebase and design patterns.
- **IF Debugging**: Review `WORKLOG.md` specifically to understand the detailed history of previous attempts and the current state of the task.

- **Ticket Creation**:
- Create a ticket in `tickets/todo/` with:
- **Objective** & **Tasks** (Checklist).
- **Design**: Mermaid diagram or tech specs.

- **Approval**: Present the plan in **Korean**. STOP and wait for approval.

2. **Phase 2: Implementation**

- **Branching**: Create a new branch (for features) or checkout the existing branch (for debugging).
- **Coding**: Implement code (Modular/OOP).
- **Dependencies**: **Add new dependencies** to package files immediately.
- **Tracking**: Check off ticket items as you go.

3. **Phase 3: Verification & Documentation**

- **Quality Control**: Run **Linter/Formatter** to clean code.
- **Testing**: Run tests (Create new ones if needed for features/bug reproduction).
- **Work Log (Mandatory)**:
- Update `WORKLOG.md` with a narrative of the changes.
- _Note: This applies to ALL tasks (Features & Debugging)._

4. **Phase 4: Closure (The Move Ritual)**

- Confirm all checks in the ticket are `[x]`.
- **MOVE** the ticket from `tickets/todo/` to `tickets/done/`.
- **Pull Request**: Push to origin and generate a PR description in English.
