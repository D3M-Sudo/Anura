---
description: "AI DLC Inception Phase — an adaptive workflow that guides you through planning, requirements, user stories, and application design before writing any code. Inspired by the AI-Driven Development Life Cycle methodology."
author: "Cline Community"
version: "1.0"
category: "Software Development Lifecycle"
tags: ["ai-dlc", "inception", "planning", "requirements", "user-stories", "design", "sdlc", "architecture"]
globs: ["*.*"]
---

<task name="AI-DLC Inception Phase">

<task_objective>
Guide the user through the Inception phase of the AI-Driven Development Life Cycle (AI-DLC). This phase determines WHAT to build and WHY by adaptively executing workspace detection, requirements analysis, user story creation, application design, and work decomposition — scaling depth to match the project's complexity. All artifacts are written to an `aidlc-docs/inception/` directory.
</task_objective>

<detailed_sequence_steps>

# AI-DLC Inception Phase — Detailed Sequence of Steps

> **Core Principle**: The workflow adapts to the work, not the other way around. Simple requests get lightweight treatment. Complex projects get comprehensive planning.

---

## 1. Welcome & Workspace Detection

**Purpose**: Understand what we're working with — greenfield or brownfield — and set the context for all subsequent stages.

**Always executes.**

1. Display a welcome message:

   ```
   🔵 AI-DLC INCEPTION PHASE
   ━━━━━━━━━━━━━━━━━━━━━━━━
   I'll guide you through planning before we write any code.
   This phase determines WHAT to build and WHY.

   Let's start by understanding your workspace.
   ```

2. Scan the current workspace:
   - Check for existing source code files, `package.json`, `Cargo.toml`, `pyproject.toml`, `go.mod`, `*.csproj`, `Makefile`, `Dockerfile`, or similar project markers.
   - Check for an existing `aidlc-docs/aidlc-state.md` file (indicates a prior AI-DLC session to resume).
   - Identify the primary language(s), framework(s), and tech stack.

3. Classify the workspace:
   - **Greenfield**: No existing application code detected. Starting fresh.
   - **Brownfield**: Existing codebase detected. We'll analyze it.
   - **Resuming**: Prior `aidlc-state.md` found. Offer to resume from last checkpoint.

4. If **Brownfield**, perform a lightweight reverse-engineering scan:
   - List top-level directory structure.
   - Identify key entry points, configuration files, and architecture patterns.
   - Summarize the tech stack, dependencies, and approximate codebase size.
   - Write findings to `aidlc-docs/inception/reverse-engineering/codebase-overview.md`.

5. Present findings to the user:

   ```
   📂 Workspace Analysis Complete
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Type: [Greenfield / Brownfield]
   Tech Stack: [detected technologies]
   Key Findings: [summary]

   Ready to proceed to Requirements Analysis.
   ```

6. Create or update `aidlc-docs/aidlc-state.md` with:
   ```markdown
   # AI-DLC State
   ## Workspace
   - Type: [Greenfield/Brownfield]
   - Tech Stack: [technologies]
   - Detection Date: [timestamp]

   ## Stage Progress
   - [x] Workspace Detection
   - [ ] Requirements Analysis
   - [ ] User Stories
   - [ ] Application Design
   - [ ] Units of Work
   ```

7. Automatically proceed to Stage 2.

---

## 2. Requirements Analysis

**Purpose**: Capture what the user wants to build, at the right level of detail for the project's complexity.

**Always executes — depth adapts to complexity.**

### Step 2a: Determine Depth

1. Ask the user to describe what they want to build:

   ```
   🎯 What would you like to build?

   Describe your intent — whether it's a quick feature, a full application,
   or a change to an existing system. Be as detailed or high-level as you like.
   ```

2. Analyze the user's response to assess complexity. Consider:
   - Number of distinct features or capabilities mentioned
   - Number of user types or personas implied
   - Integration requirements (APIs, databases, external services)
   - Whether the request involves new architecture or fits existing patterns

3. Classify the required depth:
   - **Minimal** (simple, clear request): Document intent and move on. Examples: bug fix, small feature, config change.
   - **Standard** (moderate complexity): Gather functional + non-functional requirements. Examples: new feature with multiple components, API integration.
   - **Comprehensive** (complex, high-risk): Detailed requirements with traceability. Examples: new application, major refactor, multi-service system.

4. Present the assessment to the user:

   ```
   📊 Complexity Assessment
   ━━━━━━━━━━━━━━━━━━━━━━━
   Assessed Depth: [Minimal / Standard / Comprehensive]
   Reasoning: [brief explanation]

   Would you like to proceed at this depth, or adjust?
   ```

5. Use `ask_followup_question` to confirm. Options: `["Proceed at this depth", "Go deeper (more thorough)", "Keep it lighter (faster)"]`

### Step 2b: Gather Requirements

6. Based on the confirmed depth:

   **Minimal Depth:**
   - Document the user's intent as a single requirements summary.
   - Identify any implicit assumptions.
   - Write to `aidlc-docs/inception/requirements/requirements.md`.

   **Standard Depth:**
   - Ask structured clarifying questions using multiple-choice format where possible:
     - Core functional requirements (what should the system do?)
     - Key non-functional requirements (performance, security, scalability expectations?)
     - Integration points (what external systems or APIs?)
     - User types (who will use this?)
     - Key constraints (timeline, technology restrictions, budget?)
   - Write to `aidlc-docs/inception/requirements/requirements.md` with sections for Functional Requirements, Non-Functional Requirements, Constraints, and Assumptions.

   **Comprehensive Depth:**
   - All of Standard, plus:
     - Detailed acceptance criteria per requirement
     - Priority ranking (MoSCoW: Must/Should/Could/Won't)
     - Traceability matrix (requirement → component mapping)
     - Risk assessment per requirement
   - Write to `aidlc-docs/inception/requirements/requirements.md` with full traceability.

7. Present the requirements document summary to the user.

8. **Approval Gate** — Use `ask_followup_question`:

   ```
   📋 Requirements Analysis Complete

   I've documented [N] requirements across [categories].
   Key highlights: [summary of top 3-5 requirements]

   Please review aidlc-docs/inception/requirements/requirements.md

   How would you like to proceed?
   ```

   Options: `["Approve and continue", "I have changes to make", "Let's discuss specific requirements"]`

9. If changes requested, iterate. If approved, update `aidlc-state.md` and proceed.

---

## 3. User Stories (Conditional)

**Purpose**: Translate requirements into user-centered stories with acceptance criteria — but only when it adds value.

**Executes conditionally based on intelligent assessment.**

### Step 3a: Assess Whether Stories Are Needed

1. Evaluate whether user stories add value based on these signals:

   **Generate stories if:**
   - New user-facing features or functionality
   - Multiple user types or personas involved
   - Complex business requirements needing acceptance criteria
   - Changes affecting user workflows or interactions

   **Skip stories if:**
   - Pure internal refactoring with no user impact
   - Simple bug fixes with clear, isolated scope
   - Infrastructure or tooling changes
   - Documentation-only updates

2. Present the assessment:

   ```
   📝 User Stories Assessment
   ━━━━━━━━━━━━━━━━━━━━━━━━
   Recommendation: [Generate Stories / Skip Stories]
   Reasoning: [explanation]
   ```

3. Use `ask_followup_question` to confirm. Options: `["Agree — generate stories", "Agree — skip stories", "Override — I want stories", "Override — skip stories"]`

### Step 3b: Generate Stories (if proceeding)

4. Identify user personas from the requirements. For each persona, document:
   - Name and role
   - Goals and motivations
   - Pain points

5. Generate user stories in standard format:
   ```
   As a [persona],
   I want to [action/capability],
   So that [benefit/value].

   Acceptance Criteria:
   - Given [context], When [action], Then [expected result]
   - Given [context], When [action], Then [expected result]
   ```

6. Organize stories by:
   - Epic / feature grouping
   - Priority (Must / Should / Could)
   - Estimated complexity (S / M / L / XL)

7. Write to `aidlc-docs/inception/user-stories/user-stories.md` with:
   - Personas section
   - Stories grouped by epic
   - Acceptance criteria for each story
   - Priority and complexity tags

8. **Approval Gate** — Use `ask_followup_question`:

   ```
   📝 User Stories Complete

   Generated [N] stories for [M] personas across [P] epics.

   Please review aidlc-docs/inception/user-stories/user-stories.md

   How would you like to proceed?
   ```

   Options: `["Approve and continue", "I have changes to make", "Add more stories"]`

9. If changes requested, iterate. If approved, update `aidlc-state.md` and proceed.

---

## 4. Application Design (Conditional)

**Purpose**: Define the system's architecture, components, and their relationships before writing code.

**Executes if: new components are needed, architecture decisions must be made, or the system is non-trivial.**

### Step 4a: Assess Whether Design Is Needed

1. Evaluate based on:
   - Is new architecture required, or does this fit within existing patterns?
   - Are there multiple components or services to coordinate?
   - Are there significant technology choices to make?

2. Present assessment and confirm with the user (same pattern as User Stories).

### Step 4b: Create Application Design (if proceeding)

3. Based on depth:

   **Minimal:**
   - Component list with responsibilities
   - Key technology choices
   - Simple interaction description

   **Standard:**
   - Component diagram (described in text or Mermaid)
   - API contracts between components
   - Data model overview
   - Technology stack decisions with rationale
   - Key design patterns to follow

   **Comprehensive:**
   - All of Standard, plus:
   - Detailed component specifications (methods, interfaces, dependencies)
   - Sequence diagrams for key workflows
   - Data flow diagrams
   - Error handling strategy
   - Security architecture
   - Scalability considerations

4. Write to `aidlc-docs/inception/application-design/` with:
   - `architecture-overview.md` — High-level architecture
   - `component-specs.md` — Component details (Standard/Comprehensive)
   - `data-model.md` — Data models and schemas (Standard/Comprehensive)
   - `api-contracts.md` — API definitions (Standard/Comprehensive)

5. **Approval Gate** — Use `ask_followup_question`:

   ```
   🏗️ Application Design Complete

   Designed [N] components with [M] key interactions.
   Architecture pattern: [pattern]
   Key decisions: [summary]

   Please review aidlc-docs/inception/application-design/

   How would you like to proceed?
   ```

   Options: `["Approve and continue", "I have changes to make", "Let's discuss the architecture"]`

6. If changes requested, iterate. If approved, update `aidlc-state.md` and proceed.

---

## 5. Units of Work Generation (Conditional)

**Purpose**: Break the project into independently implementable units of work that can be built and tested in sequence.

**Executes if: the project has multiple components, services, or logical modules to implement.**

1. Analyze the requirements, stories, and design to identify natural work boundaries:
   - Service boundaries
   - Feature boundaries
   - Data model boundaries
   - Dependency order (what must be built first?)

2. For each unit, define:
   - **Name**: Clear, descriptive identifier
   - **Scope**: What's included and excluded
   - **Dependencies**: Which other units must be complete first
   - **Inputs**: What artifacts or components this unit needs
   - **Outputs**: What this unit produces
   - **Estimated Complexity**: S / M / L / XL

3. Create a dependency graph showing the build order.

4. Write to `aidlc-docs/inception/units-of-work.md` with:
   - Unit list with details
   - Dependency graph (Mermaid or text)
   - Recommended execution order
   - Parallelization opportunities

5. **Approval Gate** — Use `ask_followup_question`:

   ```
   📦 Units of Work Complete

   Identified [N] units of work.
   Recommended build order: [sequence]
   Parallelizable: [which units can run in parallel]

   Please review aidlc-docs/inception/units-of-work.md

   Ready to proceed to the Construction Phase?
   ```

   Options: `["Approve — ready for Construction", "I have changes to make", "Let's adjust the breakdown"]`

6. If approved, update `aidlc-state.md` marking all Inception stages complete.

---

## 6. Inception Phase Complete

1. Present a summary:

   ```
   🔵 INCEPTION PHASE COMPLETE
   ━━━━━━━━━━━━━━━━━━━━━━━━━━
   ✅ Workspace Detection: [Greenfield/Brownfield]
   ✅ Requirements: [N] requirements documented
   [✅/⏭️] User Stories: [N stories / Skipped]
   [✅/⏭️] Application Design: [Completed / Skipped]
   [✅/⏭️] Units of Work: [N units / Skipped]

   All artifacts are in aidlc-docs/inception/

   You can now proceed to the Construction Phase workflow
   to start building.
   ```

2. Use `attempt_completion` to present the results.

</detailed_sequence_steps>

</task>
