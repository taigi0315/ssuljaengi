I have a request for a new task/Epic. Follow this lifecycle strictly:

1.  **Phase 1: Planning & Ticket Creation**

    - Read `docs/ARCHITECTURE.md` to understand context.
    - Create a ticket in `tickets/todo/` with:
      - **Objective** & **Tasks** (Checklist).
      - **Design**: Mermaid diagram or tech specs.
    - Present the plan in Korean. STOP and wait for approval.

2.  **Phase 2: Implementation**

    - Create a branch.
    - Implement code (Modular/OOP).
    - **Add new dependencies** to package files immediately.
    - Check off ticket items as you go.

3.  **Phase 3: Verification & Polish**

    - Run **Linter/Formatter** to clean code.
    - Run tests (Create new ones if needed).
    - Update `WORKLOG.md`.

4.  **Phase 4: Closure (The Move Ritual)**
    - Confirm all checks in the ticket are `[x]`.
    - **MOVE** the ticket from `tickets/todo/` to `tickets/done/`.
    - Generate a PR description/Commit message in English.
