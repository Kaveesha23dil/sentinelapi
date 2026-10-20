
# SentinelAPI Development Instructions

You are developing SentinelAPI, an AI-powered API
security and monitoring platform using WSO2.

## Existing Technologies
- WSO2 API Manager 4.5.0
- Python 3.12 + FastAPI
- React + TypeScript
- PostgreSQL
- Docker Compose
- Pytest
- GitHub

## Development Rules

1. Inspect existing code before changing anything.
2. Preserve working functionality.
3. Develop one milestone at a time.
4. Write clean, modular, maintainable code.
5. Add automated tests for new functionality.
6. Run relevant tests before completing a milestone.
7. Never hardcode or commit credentials.
8. Never fabricate test results or screenshots.
9. Document architecture decisions and failures.
10. Never delete or recreate persistent Docker
    containers without explicit approval.

## Git Workflow

- Work only on the current milestone.
- Review git status before editing.
- Commit only after relevant tests pass.
- Use meaningful conventional commit messages.
- Do not push without user approval.

## Blog Evidence

Maintain:
docs/development-journal.md

Save screenshots under:
screenshots/<milestone>/

For each milestone:
- Record implementation details.
- Record test commands and actual results.
- Capture real screenshots where tooling permits.
- Document issues and solutions.
- Identify the Git commit associated with the work.

Never capture passwords, tokens, or private keys.
Never substitute generated images for real evidence.

## Current Milestone
Step 3.2: Integrate DemoCommerce FastAPI
with WSO2 API Manager 4.5.0.
