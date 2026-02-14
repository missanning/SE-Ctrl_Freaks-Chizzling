# Git Workflow Rules

## Branching Strategy
We use a simple branching strategy:

- main → Production-ready code
- feature/* → New features

## Branch Naming Convention
feature/Ticket-ID-short-description

Example:
US-01-create-Digital-Transaction-Processing

## Commit Message Format
[Ticket-ID] Short description

Example:
US-01 Define Git workflow and branching strategy

## Merge Rules
- No direct push to main
- Feature branch must go through Pull Request
- At least one team member reviews
- Only approved pull requests can be merged
