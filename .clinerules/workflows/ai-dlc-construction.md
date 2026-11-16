---
description: "AI DLC Construction Phase — an adaptive workflow that guides you through functional design, NFR assessment, code generation, and testing for each unit of work. Inspired by the AI-Driven Development Life Cycle methodology."
author: "Cline Community"
version: "1.0"
category: "Software Development Lifecycle"
tags: ["ai-dlc", "construction", "code-generation", "testing", "design", "sdlc", "nfr"]
globs: ["*.*"]
---

<task name="AI-DLC Construction Phase">

<task_objective>
Guide the user through the Construction phase of the AI-Driven Development Life Cycle (AI-DLC). This phase determines HOW to build it by iterating through each unit of work with functional design, NFR assessment, code generation (plan then execute), and build/test verification. Each stage requires explicit user approval before proceeding. Artifacts are written to `aidlc-docs/construction/`.
</task_objective>

<detailed_sequence_steps>

# AI-DLC Construction Phase — Detailed Sequence of Steps

> **Core Principle**: Each unit of work is completed fully — from design through code — before moving to the next. Every stage has an approval gate. The AI proposes, the human approves.

---

## 0. Construction Phase Setup

**Purpose**: Load context from the Inception phase and prepare for construction.

**Always executes.**

1. Display a welcome message:

   ```
   🟢 AI-DLC CONSTRUCTION PHASE
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   I'll guide you through building each unit of work.
   This phase determines HOW to build it.

   Let me load your Inception artifacts...
   ```

2. Check for Inception phase artifacts:
   - Read `aidlc-docs/aidlc-state.md` for progress and context.
   - Read `aidlc-docs/inception/requirements/requirements.md` for requirements.
   - Read `aidlc-docs/inception/user-stories/user-stories.md` (if it exists).
   - Read `aidlc-docs/inception/application-design/` (if it exists).
   - Read `aidlc-docs/inception/units-of-work.md` (if it exists).

3. If no Inception artifacts are found:
   - Inform the user: "No Inception phase artifacts found. I'll gather minimal context before proceeding."
   - Ask the user to describe what they want to build.
   - Create a lightweight requirements summary.
   - Create a single unit of work covering the entire request.

4. Present the construction plan:

   ```
   📋 Construction Plan
   ━━━━━━━━━━━━━━━━━━━
   Units of Work: [list units in build order]

   For each unit, I'll guide you through:
   1. Functional Design (if needed)
   2. NFR Assessment (if needed)
   3. Code Generation (always — plan first, then build)

   After all units: Build & Test verification.

   Starting with Unit 1: [unit name]
   ```

5. Use `ask_followup_question` to confirm. Options: `["Start building", "Adjust the plan first", "Let me review the Inception artifacts"]`

---

## 1. Per-Unit Loop

**For each unit of work, execute the following stages in sequence. Complete one unit fully before starting the next.**

---

### Stage 1: Functional Design (Conditional)

**Purpose**: Design the data models, business logic, and component interfaces for this unit before writing code.

**Execute if**: The unit involves new data models, complex business logic, or component interfaces that need design. **Skip if**: Simple logic changes, bug fixes, or work within well-defined existing patterns.

#### Step 1a: Assess Need

1. Evaluate whether functional design is needed for this unit based on:
   - Does it introduce new data models or schemas?
   - Does it contain business rules that need specification?
   - Are there component interfaces to define?
   - Is the logic complex enough to warrant design before coding?

2. Present recommendation to the user with rationale.

3. Use `ask_followup_question` to confirm. Options: `["Proceed with Functional Design", "Skip — go straight to code", "Let me decide after I see the scope"]`

#### Step 1b: Create Functional Design (if proceeding)

4. Design the following elements for this unit:

   **Data Models:**
   - Entity definitions with fields and types
   - Relationships between entities
   - Validation rules and constraints
   - Database schema or storage approach

   **Business Logic:**
   - Business rules written as clear, testable statements
   - Decision tables or logic flows for complex rules
   - State machines for stateful processes
   - Edge cases and error conditions

   **Component Interfaces:**
   - Public API definitions (function signatures, parameters, return types)
   - Internal interfaces between sub-components
   - Event contracts (if event-driven)
   - Error handling contracts

5. Write to `aidlc-docs/construction/{unit-name}/functional-design/`:
   - `data-models.md` — Entity definitions and relationships
   - `business-logic.md` — Rules, flows, and edge cases
   - `interfaces.md` — API and component interface specs

6. **Approval Gate** — Use `ask_followup_question`:

   ```
   📐 Functional Design Complete — [Unit Name]

   Data Models: [N] entities defined
   Business Rules: [N] rules specified
   Interfaces: [N] APIs/contracts defined

   Please review aidlc-docs/construction/{unit-name}/functional-design/
   ```

   Options: `["Approve — continue to next stage", "I have changes to make"]`

7. If changes requested, iterate until approved.

---

### Stage 2: NFR Assessment (Conditional)

**Purpose**: Identify and address non-functional requirements — performance, security, scalability, reliability — for this unit.

**Execute if**: The unit has performance-sensitive code, security considerations, scalability concerns, or reliability requirements. **Skip if**: No significant NFR concerns, or NFRs are already well-defined from Inception.

#### Step 2a: Assess Need

1. Evaluate whether NFR assessment is needed:
   - Does this unit handle user authentication or sensitive data?
   - Are there performance targets (response time, throughput)?
   - Will this unit face variable or high load?
   - Are there reliability/availability requirements?
   - Does this unit interact with external systems that could fail?

2. Present recommendation and confirm with user.

#### Step 2b: NFR Assessment (if proceeding)

3. For each applicable NFR category, assess and document:

   **Performance:**
   - Response time targets
   - Throughput requirements
   - Resource utilization limits
   - Caching strategy
   - Database query optimization needs

   **Security:**
   - Authentication and authorization requirements
   - Data encryption (at rest and in transit)
   - Input validation and sanitization
   - Secrets management approach
   - OWASP Top 10 considerations

   **Scalability:**
   - Expected load patterns (steady, bursty, growing)
   - Horizontal vs. vertical scaling approach
   - Statelessness requirements
   - Database scaling strategy

   **Reliability:**
   - Error handling and retry strategies
   - Circuit breaker patterns
   - Graceful degradation approach
   - Data backup and recovery
   - Health check requirements

4. For each identified NFR, specify the **design pattern** or **implementation approach** to address it.

5. Write to `aidlc-docs/construction/{unit-name}/nfr-assessment/`:
   - `nfr-requirements.md` — Requirements and targets
   - `nfr-design.md` — Patterns and approaches to meet each requirement

6. **Approval Gate** — Use `ask_followup_question`:

   ```
   🛡️ NFR Assessment Complete — [Unit Name]

   Performance: [summary]
   Security: [summary]
   Scalability: [summary]
   Reliability: [summary]

   Please review aidlc-docs/construction/{unit-name}/nfr-assessment/
   ```

   Options: `["Approve — continue to next stage", "I have changes to make"]`

7. If changes requested, iterate until approved.

---

### Stage 3: Code Generation (Always Executes)

**Purpose**: Generate the actual code for this unit — always in two parts: plan first, then execute.

**Always executes for each unit.**

#### Part 1: Code Generation Plan

1. Create a detailed code generation plan based on:
   - Requirements (from Inception or gathered inline)
   - Functional design (if created in Stage 1)
   - NFR design patterns (if created in Stage 2)
   - Existing codebase patterns (if brownfield)

2. The plan should specify, as a checklist:
   - Files to create or modify (with paths)
   - Key functions/classes/modules to implement
   - External dependencies to install
   - Configuration changes needed
   - Test files to create

3. Present the plan:

   ```
   💻 Code Generation Plan — [Unit Name]
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Files to create/modify:
   - [ ] src/models/user.ts — User entity and validation
   - [ ] src/services/auth.ts — Authentication service
   - [ ] src/routes/auth.ts — Auth API endpoints
   - [ ] tests/services/auth.test.ts — Auth service tests
   - [ ] ...

   Dependencies to add:
   - bcrypt (password hashing)
   - jsonwebtoken (JWT generation)

   Shall I proceed with this plan?
   ```

4. **Approval Gate** — Use `ask_followup_question`:

   Options: `["Execute this plan", "I have changes to the plan", "Let's discuss before proceeding"]`

5. If changes requested, revise the plan and re-present.

#### Part 2: Code Execution

6. Execute the approved plan step by step:
   - Create/modify each file according to the plan.
   - Follow existing codebase patterns and conventions.
   - Apply functional design specs (if available).
   - Implement NFR patterns (if available).
   - Write tests alongside implementation code.
   - Install dependencies as needed.

7. After each file or logical group, mark the plan checkbox as complete.

8. Write a code summary to `aidlc-docs/construction/{unit-name}/code/code-summary.md`:
   - Files created/modified
   - Key implementation decisions
   - Deviations from the plan (if any) with rationale
   - Test coverage summary

9. **Approval Gate** — Use `ask_followup_question`:

   ```
   ✅ Code Generation Complete — [Unit Name]

   Files created: [N]
   Files modified: [M]
   Tests written: [T]

   Please review the generated code.
   ```

   Options: `["Approve — move to next unit", "I have changes to make"]`

10. If changes requested, iterate until approved.

---

### Stage 4: Repeat for Next Unit

1. If more units remain, display:

   ```
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ✅ Unit [N] complete: [unit name]
   ➡️ Next: Unit [N+1]: [next unit name]
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```

2. Return to Stage 1 for the next unit.

---

## 2. Build & Test Verification

**Purpose**: After all units are complete, verify that the entire system builds and passes tests.

**Always executes after all units are complete.**

1. Generate comprehensive build and test instructions:

   **Build Instructions:**
   - Step-by-step commands to build the entire project
   - Environment setup requirements
   - Configuration file setup
   - Dependency installation commands

   **Test Instructions:**
   - Unit test execution commands per module
   - Integration test instructions (how units interact)
   - End-to-end test instructions (if applicable)
   - Performance test instructions (if NFRs exist)
   - Manual verification steps

2. Write to `aidlc-docs/construction/build-and-test/`:
   - `build-instructions.md` — How to build
   - `test-instructions.md` — How to test (all levels)
   - `verification-checklist.md` — Manual verification steps

3. Attempt to run the build and test commands:
   - Execute build commands and report results.
   - Execute test commands and report results.
   - If failures occur, present them to the user with analysis.

4. **Approval Gate** — Use `ask_followup_question`:

   ```
   🧪 Build & Test Verification
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Build: [✅ Passed / ❌ Failed — details]
   Unit Tests: [✅ N passed / ❌ N failed — details]
   Integration Tests: [✅ Passed / ❌ Failed / ⏭️ Skipped]

   Instructions saved to aidlc-docs/construction/build-and-test/
   ```

   Options: `["All looks good — Construction complete", "There are issues to fix", "Run tests again"]`

---

## 3. Construction Phase Complete

1. Update `aidlc-docs/aidlc-state.md` with all Construction stages marked complete.

2. Present a final summary:

   ```
   🟢 CONSTRUCTION PHASE COMPLETE
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Units Completed: [N]

   Per Unit:
   ✅ [Unit 1]: [files created/modified] | [tests written]
   ✅ [Unit 2]: [files created/modified] | [tests written]
   ...

   Build: [status]
   Tests: [status]

   All documentation in aidlc-docs/construction/
   Code is in the workspace root.
   ```

3. Use `attempt_completion` to present the results.

</detailed_sequence_steps>

</task>
