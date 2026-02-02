# Working with Claude Code - Solo Dev Guide

## Core Principle
**Move fast, stay oriented.** The AI handles velocity; you handle direction.

---

## File Organization

### Essential Files (Root Level)
- **README.md** - Your source of truth
  - Current Status section (what works now)
  - Next 3 Priorities (what you're building next)
  - Known Issues (what's broken/blocking)
  
### Documentation Structure
```
docs/
├── current/           # Active context (3-5 files max)
├── decisions/         # Key architectural choices (when you make them)
└── archive/
    └── YYYY-MM-DD-milestone-name/  # Old markdowns by checkpoint
```

**Rule:** When Claude Code generates markdown, it goes in `docs/current/`. When you hit a checkpoint, archive the whole folder.

---

## Working Rhythm

### Session Start
1. Read README.md status
2. Pick your next checkpoint/milestone (outcome-based, not time-based)
3. Tell Claude Code: "Current goal: [checkpoint]. Ignore old docs unless I reference them."

### During Work
- Let Claude Code generate whatever docs it needs in `docs/current/`
- Don't worry about cleanup mid-flow
- Stay focused on the checkpoint

### Hit Checkpoint (Outcome Achieved)
1. Update README.md status section
2. `git add . && git commit -m "Checkpoint: [brief outcome]"`
3. `mv docs/current docs/archive/$(date +%Y-%m-%d)-[milestone-name]`
4. `mkdir docs/current`
5. Move on to next checkpoint

### End of Session (Even If Incomplete)
- Update README.md with current state
- Commit: `git commit -am "WIP: [what you were doing]"`
- This gives you a rollback point

---

## Git Strategy (Lightweight)

**When to commit:**
- ✅ After each checkpoint/milestone
- ✅ Before risky refactors
- ✅ End of each session
- ❌ Not constantly during development

**Commit messages:**
- Keep them simple: "Checkpoint: auth working" or "WIP: debugging API"
- The code is the documentation
- Git is your undo button, not your diary

**Why bother?**
- `git diff` shows what changed between checkpoints
- `git reset --hard` is your escape hatch when confused
- Cheap insurance against "what did I break?"

---

## What Actually Matters

### Engineering Laws (Always Follow)
- **Working code over comprehensive docs** - If it runs, it's documented enough
- **One source of truth** - README.md status, not scattered markdowns
- **Commit before confusion** - Not after you're lost
- **Delete liberally** - Archive old docs, don't hoard them

### Best Practices (Adapt as Needed)
- Checkpoints instead of sprints
- Archive docs when stale
- Keep `docs/current/` under 5 files
- Review README.md weekly to keep it relevant

### Red Flags (Time to Reorganize)
- You can't explain current status in 2 minutes
- More than 10 unarchived markdown files
- Haven't committed in 2+ days
- Lost track of what you're building

---

## Context Management for Claude Code

**Each session, give Claude Code:**
```
Current goal: [your checkpoint]
Status: [paste README.md status section]
Working on: [specific task]

Ignore old docs unless I reference them.
Update docs/current/ only. Don't create new files unless needed.
```

**This keeps Claude Code focused on YOUR priorities, not its generated artifacts.**

---

## Recovery Tactics

**When you feel lost:**
1. Read README.md - does it match reality? Update it.
2. Check last commit - `git log -1`. What changed since then?
3. Archive everything in `docs/current/`
4. Write down your actual goal in README.md
5. Start fresh

**When docs are overwhelming:**
1. Archive all of `docs/current/`
2. Keep only README.md
3. Rebuild context as needed from code + commits

---

## Minimalist Version (If Above Feels Like Too Much)

**All you really need:**
1. README.md with "Status" and "Next 3 Priorities" sections
2. Commit whenever you'd be annoyed to lose your work
3. Archive old markdowns when they're obviously stale
4. That's it.

The AI moves fast. Your job is knowing where you're going, not maintaining perfect documentation.