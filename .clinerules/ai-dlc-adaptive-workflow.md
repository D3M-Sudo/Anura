# AI-DLC Adaptive Workflow Rule

> Inspired by the [AI-Driven Development Life Cycle (AI-DLC)](https://github.com/awslabs/aidlc-workflows) methodology. This rule embeds adaptive software development practices into every Cline session.

## Core Philosophy

**The workflow adapts to the work, not the other way around.**

Not every request needs a full development lifecycle. A one-line bug fix shouldn't go through requirements analysis. But a new multi-service application shouldn't start with code either. This rule ensures the right level of rigor is applied automatically.

---

## 🚨 Mandatory: Complexity Assessment

**Before starting ANY software development task**, you MUST perform a silent complexity assessment. This takes seconds and determines how much process to apply.

### Assessment Criteria

Evaluate the request against these dimensions:

| Dimension | Low (1) | Medium (2) | High (3) |
|-----------|---------|------------|----------|
| **Scope** | Single file/function | Multiple files/components | Multiple services/systems |
| **Risk** | No breaking changes | Could break existing features | Affects production data/users |
| **Ambiguity** | Crystal clear intent | Some questions needed | Significant unknowns |
| **Architecture** | Fits existing patterns | Minor new patterns | New architecture needed |
| **User Impact** | Internal/developer only | Indirect user impact | Direct user-facing changes |

### Complexity Tiers

**Sum the scores across all 5 dimensions:**

- **Score 5–7 → FAST TRACK**: Proceed directly to implementation. No ceremony needed.
- **Score 8–11 → STANDARD**: Lightweight planning, then implement with approval gates.
- **Score 12–15 → FULL LIFECYCLE**: Execute the complete Inception → Construction flow.

---

## Fast Track (Score 5–7)

For simple, clear, low-risk requests. Get in, build it, get out.

**Process:**
1. Confirm understanding of the request with a brief summary.
2. Implement the change.
3. Verify it works (run tests, lint, build).
4. Present the result.

**Examples:** Bug fixes, small features, config changes, dependency updates, documentation updates, refactoring within a single module.

---

## Standard Track (Score 8–11)

For moderate complexity work that benefits from a plan but doesn't need full lifecycle treatment.

**Process:**

### 1. Lightweight Planning (2–5 minutes)
- Summarize the requirements in 3–5 bullet points.
- Identify the components/files that will be affected.
- Note any risks or dependencies.
- Present the plan to the user for approval.

### 2. Implementation with Gates
- Create a code generation plan (checklist of files to create/modify).
- Get user approval on the plan.
- Implement the approved plan.
- Write tests alongside the implementation.

### 3. Verification
- Run build and tests.
- Present results with a summary of what was done.

**Examples:** New feature with 2–3 components, API integration, database schema changes, moderate refactoring across multiple files.

---

## Full Lifecycle (Score 12–15)

For complex, high-risk, or ambiguous work that needs the full AI-DLC treatment.

**Process:**

### 🔵 Inception Phase
Execute these stages, adapting depth to the specific project:

1. **Workspace Detection** — Scan the codebase, determine greenfield/brownfield, identify tech stack.

2. **Requirements Analysis** — Gather and document requirements:
   - Functional requirements (what should it do?)
   - Non-functional requirements (performance, security, scalability)
   - Constraints and assumptions
   - Write to `aidlc-docs/inception/requirements/requirements.md`

3. **User Stories** (if user-facing) — Generate stories with acceptance criteria:
   - Personas, stories in As-a/I-want/So-that format
   - Acceptance criteria in Given-When-Then format
   - Write to `aidlc-docs/inception/user-stories/user-stories.md`

4. **Application Design** (if new architecture needed) — Design the system:
   - Component architecture and relationships
   - Data models and API contracts
   - Technology decisions with rationale
   - Write to `aidlc-docs/inception/application-design/`

5. **Units of Work** (if multi-component) — Break down into buildable units:
   - Define scope, dependencies, and build order for each unit
   - Write to `aidlc-docs/inception/units-of-work.md`

**Each stage has an approval gate.** Present findings, get user approval, then proceed.

### 🟢 Construction Phase
For each unit of work:

1. **Functional Design** (if complex logic) — Design data models, business rules, interfaces before coding.

2. **NFR Assessment** (if performance/security/scale matters) — Identify requirements and design patterns.

3. **Code Generation** (always) — Two parts:
   - **Plan**: Checklist of files, functions, dependencies → get approval
   - **Execute**: Build the approved plan, writing tests alongside code

4. **Build & Test** — After all units: verify build, run tests, report results.

**Each stage has an approval gate.** Present work, get approval, then proceed.

---

## Approval Gates

At every significant decision point, you MUST pause and get explicit user approval before proceeding. This is non-negotiable at all complexity tiers.

**Approval gate format:**

```
[Stage] Complete — [Brief Summary]

Key outputs: [what was produced]
Key decisions: [what was decided]

How would you like to proceed?
```

Present clear options (approve / request changes / discuss further).

**Rules:**
- NEVER proceed to the next stage without approval.
- NEVER silently skip a stage — always explain why a stage is being skipped and confirm.
- If the user wants to override the recommended tier (e.g., "just build it"), respect their choice but note what's being skipped.

---

## Progress Tracking

For Standard and Full Lifecycle tracks, maintain an `aidlc-docs/aidlc-state.md` file that records:

```markdown
# AI-DLC State

## Project Context
- Request: [original user request]
- Complexity: [Fast Track / Standard / Full Lifecycle] (Score: N)
- Workspace: [Greenfield / Brownfield]
- Started: [timestamp]

## Stage Progress
- [x] Complexity Assessment
- [x/⏭️] Stage Name — [Completed / Skipped: reason]
- [ ] Next Stage
...
```

Update this file after each stage completion. This enables session continuity — if the conversation resets, read this file to resume where you left off.

---

## Audit Trail

For Full Lifecycle track, maintain an `aidlc-docs/audit.md` that logs every significant interaction:

```markdown
## [Stage Name]
**Timestamp**: [ISO 8601]
**User Input**: "[exact user input]"
**AI Action**: "[what was done]"
**Decision**: "[what was decided and why]"
---
```

This creates accountability and traceability for complex projects.

---

## Key Principles

1. **Adapt, don't impose.** Match the process to the work. Never apply heavy process to simple tasks.
2. **Plan before you code** — but only as much as the situation demands.
3. **The human is always in control.** Propose, don't dictate. Every gate needs approval.
4. **Document decisions, not just code.** Future-you (or future-Cline) needs to understand WHY, not just WHAT.
5. **Complete each unit fully** before starting the next. Don't scatter partial implementations across the codebase.
6. **Test alongside code.** Tests are not an afterthought — they're part of code generation.
7. **Fail fast, iterate.** If something isn't working at the design stage, catch it there — not after 500 lines of code.
