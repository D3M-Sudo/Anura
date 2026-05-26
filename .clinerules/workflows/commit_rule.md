---
description: Automated commit message generation following Conventional Commits
---

# Commit Automation Rule

## Trigger Command
`prompt commit`

## Protocol Steps

When this command is triggered, follow this exact protocol:

### 1. Inspection
- Run `git status` to identify modified and untracked files
- List all files that need to be committed

### 2. Analysis
- Run `git diff` for modified files
- Analyze the content of new files
- Understand the logic and purpose of the changes

### 3. Commit Message Generation
Follow the Conventional Commits format:
- `feat:` for new features
- `fix:` for bug fixes
- `refactor:` for refactoring
- `docs:` for documentation
- `style:` for style changes
- `test:` for tests
- `chore:` for maintenance

### 4. Message Structure

```
<type>(<scope>): <clear and concise title>

- Logical change 1: brief description
- Logical change 2: brief description
- Logical change 3: brief description

Files changed:
- path/to/file1: change description
- path/to/file2: change description
- path/to/file3: change description
```

## Automatic Execution

This protocol must be executed autonomously when the `prompt commit` command is detected, without requiring further instructions from the user.

## Important Notes

- Always analyze the context of the changes before generating the message
- Be specific but concise in descriptions
- Always follow the Conventional Commits format
- Always include the "Files changed" section for traceability
