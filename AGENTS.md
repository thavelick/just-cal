# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Developer Rules

### Linting and Code Quality

**NEVER ignore linting errors or warnings by adding them to the ignore list.**

If you encounter a linting issue:
1. **First choice:** Fix it immediately if it's straightforward
2. **Second choice:** Create a bd task to fix it later if it requires more work
3. **NEVER:** Add it to the ignore list in pyproject.toml or suppress it with comments

The only acceptable ignores are:
- Issues that are genuinely false positives across the entire codebase
- Style preferences that conflict with the formatter (e.g., E501 line length)

When in doubt, create a bd task and let the user decide.

## Managing Dependencies

**IMPORTANT:** When creating dependencies with `bd dep add`, the syntax is:
```bash
bd dep add <issue-that-depends> <issue-it-depends-on>
```

In other words: **the blocker comes SECOND**.

**Example:** If Phase 2 must be completed before Phase 3 can start:
```bash
bd dep add jc-phase3 jc-phase2
# This means: jc-phase3 depends on (is blocked by) jc-phase2
```

**Common mistake:**
```bash
bd dep add jc-phase2 jc-phase3  # WRONG! This makes phase2 depend on phase3
```

**Verify dependencies:**
```bash
bd dep tree <issue-id>  # Visualize dependency tree
bd show <issue-id>       # See what an issue depends on and what depends on it
```

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

