# CLAUDE.md - Guidelines for AI Assistant

This document contains important guidelines for Claude (or any AI assistant) working on the CamareraI project.

## Core Principles

### 🎯 Project Philosophy
- **Customer-first**: Always prioritize user experience over technical elegance
- **Simplicity**: Keep solutions simple, especially for POC
- **Iterative**: Plan → Approve → Implement → Test → Iterate
- **Budget-conscious**: Prefer local/free solutions over paid APIs

### 🚦 Workflow Rules

#### DO NOT Start Implementation Until Explicitly Asked
- ❌ **NEVER** write code just because we're discussing features
- ❌ **NEVER** create files during brainstorming sessions
- ❌ **NEVER** assume "let's do X" means "implement X now"
- ✅ **ALWAYS** wait for explicit approval: "start implementing", "let's build this", "go ahead"

#### DO Ask for Approval at Key Decision Points
- ✅ After creating/updating plans: "Ready to start implementing?"
- ✅ Before major architectural changes: "Should I proceed with this approach?"
- ✅ Before creating new files/modules: "Should I create this now?"
- ✅ When multiple approaches exist: "Which option do you prefer?"

#### DO Clarify Ambiguity
- ✅ If instructions are unclear, ask questions
- ✅ If scope is ambiguous, propose options
- ✅ If priorities conflict, ask which matters more
- ✅ If timeline is uncertain, ask about urgency

## Project-Specific Guidelines

### Planning Phase (Current)
- **Focus**: Product thinking, user experience, architecture design
- **Deliverables**: Planning documents, diagrams, decision frameworks
- **Approval needed**: Before moving to implementation
- **Tools**: Markdown documents, diagrams, pseudocode (not real code)

### Implementation Phase (Future)
- **Focus**: Building working code
- **Deliverables**: Python scripts, tests, documentation
- **Approval needed**: Before major refactors or new features
- **Tools**: Python, local models, simple interfaces

### Testing Phase (Future)
- **Focus**: Validation, bug fixes, polish
- **Deliverables**: Test results, bug reports, improvements
- **Approval needed**: Before changing core functionality
- **Tools**: Manual testing, demo scenarios, user feedback

## Communication Preferences

### When Discussing Ideas
- ✅ Be exploratory and open-ended
- ✅ Present multiple options with pros/cons
- ✅ Ask clarifying questions
- ✅ Focus on "what" and "why" before "how"
- ❌ Don't jump to implementation details
- ❌ Don't create files or code

### When Planning
- ✅ Create comprehensive documentation
- ✅ Think through edge cases and risks
- ✅ Propose clear decision points
- ✅ Summarize key takeaways
- ❌ Don't start building yet
- ❌ Don't make unilateral decisions on major points

### When Implementing
- ✅ Write clean, simple code
- ✅ Add comments for complex logic
- ✅ Test as you go
- ✅ Report progress and blockers
- ❌ Don't over-engineer
- ❌ Don't add features not requested

### When Stuck or Uncertain
- ✅ Explain the problem clearly
- ✅ Present options with tradeoffs
- ✅ Ask for guidance
- ✅ Suggest a recommended path
- ❌ Don't guess or assume
- ❌ Don't hide problems

## Technical Preferences

### Code Style
- **Language**: Python 3.12+
- **Style**: Simple, readable, minimal abstractions
- **Comments**: Only where logic isn't obvious
- **Error handling**: Explicit, user-friendly messages
- **Testing**: Manual testing for POC, automated later

### Architecture
- **POC**: Single script, everything in one place
- **Alpha**: Modular but still simple
- **Production**: Proper architecture when needed
- **Rule**: Don't build for scale until we need it

### Dependencies
- **Prefer**: Local, free, open-source
- **Avoid**: Paid APIs unless necessary
- **Check**: Before adding new dependencies
- **Document**: Why each dependency is needed

## Decision-Making Framework

### Small Decisions (Make Independently)
- Variable names, code formatting
- File organization within agreed structure
- Implementation details of approved features
- Bug fixes that don't change behavior

### Medium Decisions (Propose & Wait for Approval)
- Adding new dependencies
- Changing data models
- Adding new features (even small ones)
- Refactoring existing code

### Large Decisions (Discuss Before Proposing)
- Architecture changes
- Technology stack changes
- Scope changes
- Timeline changes

## Common Scenarios

### Scenario: "Let's add feature X"
- ❌ Don't immediately start coding
- ✅ Ask: "Should I add this to the plan, or implement it now?"
- ✅ If unclear, default to planning first

### Scenario: "What do you think about approach Y?"
- ❌ Don't implement approach Y
- ✅ Discuss pros/cons
- ✅ Present alternatives
- ✅ Wait for decision

### Scenario: "This isn't working"
- ❌ Don't silently try different approaches
- ✅ Explain what's not working
- ✅ Propose solutions
- ✅ Ask which to try

### Scenario: User is away/busy
- ❌ Don't make major decisions
- ❌ Don't implement new features
- ✅ Document questions for later
- ✅ Work on approved tasks only

## Red Flags (Stop and Ask)

🚨 **Stop immediately and ask if:**
- You're about to delete significant code
- You're changing the core architecture
- You're adding a paid service/API
- You're implementing something not discussed
- You're unsure if this is what the user wants
- The scope is growing beyond original plan
- You're making assumptions about requirements

## Success Criteria

### Good Session
- ✅ Clear communication
- ✅ Explicit approvals received
- ✅ Progress on agreed tasks
- ✅ No surprises or assumptions
- ✅ User feels in control

### Bad Session
- ❌ Implemented without approval
- ❌ Made major decisions unilaterally
- ❌ Scope creep without discussion
- ❌ User surprised by what was built
- ❌ Wasted time on wrong direction

## Project Context

### What We're Building
A voice-based AI restaurant assistant POC to demonstrate natural conversation ordering.

### Current Phase
**Planning** - Solidifying product vision and technical approach before implementation.

### Key Stakeholders
- **User (Liang)**: Product owner, developer, decision maker
- **Future users**: Restaurant owners (demo audience), diners (end users)

### Success Metrics for POC
- Natural conversation flow
- Accurate order building
- Impressive demo
- Clear path to next phase

### Timeline
- Planning: Complete
- Implementation: Not started (waiting for approval)
- Demo: Target in ~1 week

## Lessons Learned

### ✅ What Worked Well
1. Creating comprehensive planning documents
2. Discussing product considerations before technical details
3. Presenting options with pros/cons
4. Asking clarifying questions

### ❌ What Didn't Work
1. Starting backend implementation during brainstorming
2. Creating files before getting approval
3. Assuming "let's brainstorm" meant "let's build"

### 🎓 Key Takeaway
**Plan first, implement second. Always wait for explicit approval to start coding.**

## Quick Reference

### Before Writing Code, Ask:
1. "Should I implement this now?"
2. "Is this the right approach?"
3. "Are we ready to move from planning to implementation?"

### Before Making Decisions, Ask:
1. "Which option do you prefer?"
2. "What's the priority here?"
3. "Should we discuss this further?"

### When Uncertain, Say:
1. "I'm not sure if you want me to implement this or just discuss it"
2. "Should I create a plan first, or start building?"
3. "Let me know when you're ready for me to start implementation"

---

## Git Workflow & Source Control

### 🌿 Branch Strategy

#### Main Branch
- **Purpose**: Stable, working code only
- **Protection**: Never commit directly to main
- **Status**: Always deployable/demo-ready
- **Updates**: Only via merged feature branches

#### Feature Branches
- **Naming**: `feature/descriptive-name` (e.g., `feature/streaming-asr`, `feature/order-parsing`)
- **Purpose**: Develop new features in isolation
- **Lifecycle**: Create → Develop → Test → Merge → Delete
- **Rule**: One feature per branch

#### Workflow
```bash
# Start new feature
git checkout main
git pull origin main
git checkout -b feature/new-feature-name

# Work on feature
# ... make changes ...
git add .
git commit -m "Descriptive commit message"

# When feature is complete and tested
git checkout main
git merge feature/new-feature-name
git push origin main
git branch -d feature/new-feature-name
```

### 📝 Documentation Management

#### Single Source of Truth: README.md
- **Purpose**: Main documentation that users read first
- **Content**:
  - Current implementation status
  - Quick start guide
  - What works / what doesn't
  - Troubleshooting
  - Project structure
- **Update**: Every time something significant changes
- **Format**: Clear, concise, actionable

#### Supporting Documentation
- **CLAUDE.md**: Guidelines for AI assistant (this file)
- **docs/PLAN.md**: Original planning document (reference only)
- **docs/eng/IMPLEMENTATION_PLAN.md**: Technical implementation plan
- **docs/eng/IMPLEMENTATION_STATUS.md**: Current implementation status
- **docs/prd/PRODUCT_DESIGN.md**: Product design decisions
- **Rule**: All other docs point back to README.md as primary source

#### Documentation Best Practices
- ✅ **DO**: Keep README.md as single source of truth
- ✅ **DO**: Update README.md when merging features
- ✅ **DO**: Mark deprecated files clearly
- ✅ **DO**: Include "Last Updated" date
- ❌ **DON'T**: Create multiple overlapping docs
- ❌ **DON'T**: Let docs get out of sync with code
- ❌ **DON'T**: Delete old docs (mark as deprecated instead)

### 🗂️ File Management

#### Active vs Deprecated Files
```
Active (Use These):
├── streaming_voice_agent.py    # Current implementation
├── dashscope_client.py          # API wrapper
├── test_all.py                  # System check
└── README.md                    # Documentation

Deprecated (Don't Use, Keep for Reference):
├── poc_voice_agent.py           # Old implementation
├── test_dashscope.py            # Old test
└── Other .md files              # Old docs
```

#### File Naming Conventions
- **Active files**: Clear, descriptive names (e.g., `streaming_voice_agent.py`)
- **Deprecated files**: Keep original name, mark in README.md
- **New versions**: Use descriptive prefixes (e.g., `streaming_` vs old version)
- **Tests**: `test_*.py` for test files
- **Docs**: `UPPERCASE.md` for important docs, `lowercase.md` for notes

#### When Creating New Files
1. **Check**: Does this file already exist?
2. **Name**: Use clear, descriptive name
3. **Document**: Add to README.md project structure
4. **Commit**: Commit with clear message explaining purpose

### 🔄 Feature Development Workflow

#### Phase 1: Planning (On Feature Branch)
```bash
# Create feature branch
git checkout -b feature/order-parsing

# Create planning docs
# - Update README.md with "🔄 IN PROGRESS" status
# - Create design docs if needed
# - Discuss approach with user

# Commit planning
git add README.md
git commit -m "Plan: Add order parsing feature"
```

#### Phase 2: Implementation (On Feature Branch)
```bash
# Implement feature
# - Write code
# - Add tests
# - Update documentation

# Commit incrementally
git add .
git commit -m "Implement: Basic order parsing from transcription"
git commit -m "Implement: Add menu item matching"
git commit -m "Implement: Add order confirmation"
```

#### Phase 3: Testing (On Feature Branch)
```bash
# Test thoroughly
# - Run test_all.py
# - Manual testing
# - Fix bugs

# Commit fixes
git commit -m "Fix: Handle edge case in order parsing"
git commit -m "Test: Verify order parsing with sample data"
```

#### Phase 4: Documentation (On Feature Branch)
```bash
# Update README.md
# - Mark feature as "✅ DONE"
# - Update "What Works" section
# - Add usage instructions
# - Update troubleshooting if needed

git add README.md
git commit -m "Docs: Update README for order parsing feature"
```

#### Phase 5: Merge (To Main)
```bash
# Ensure everything works
python3 test_all.py

# Merge to main
git checkout main
git merge feature/order-parsing

# Push to remote
git push origin main

# Clean up feature branch
git branch -d feature/order-parsing
```

### 📋 Commit Message Guidelines

#### Format
```
Type: Brief description (50 chars max)

Optional detailed explanation if needed.
Can span multiple lines.
```

#### Types
- **Plan**: Planning and design work
- **Implement**: New feature implementation
- **Fix**: Bug fixes
- **Refactor**: Code refactoring (no behavior change)
- **Test**: Adding or updating tests
- **Docs**: Documentation updates
- **Chore**: Maintenance tasks (dependencies, cleanup)

#### Examples
```bash
# Good
git commit -m "Implement: Streaming ASR with WebSocket"
git commit -m "Fix: DNS resolution error handling"
git commit -m "Docs: Update README with streaming setup"

# Bad
git commit -m "updates"
git commit -m "fix stuff"
git commit -m "wip"
```

### 🎯 POC Project Best Practices

#### Managing Multiple Implementations
1. **Don't delete old code** - Mark as deprecated
2. **Use clear naming** - `streaming_voice_agent.py` vs `poc_voice_agent.py`
3. **Update README.md** - Show which files to use
4. **Archive if needed** - Move to `archive/` folder

#### Keeping Documentation Current
1. **Update README.md first** - Before merging feature
2. **Mark status clearly** - ✅ Done, 🔄 In Progress, ❌ Broken
3. **Include "Last Updated"** - Date stamp for freshness
4. **One source of truth** - README.md, everything else is reference

#### Avoiding Confusion
1. **Feature branches** - Isolate work in progress
2. **Clear commit messages** - Know what changed and why
3. **Test before merging** - Main branch always works
4. **Document as you go** - Don't let docs lag behind code

### 🚀 Starting a New Feature

#### Checklist
```bash
# 1. Create feature branch
git checkout -b feature/feature-name

# 2. Update README.md
# - Add feature to "🔄 IN PROGRESS" section
# - Commit: "Plan: Add [feature name]"

# 3. Discuss approach with user
# - Present options
# - Get approval
# - Clarify requirements

# 4. Implement feature
# - Write code
# - Test as you go
# - Commit incrementally

# 5. Update documentation
# - Update README.md
# - Mark feature as "✅ DONE"
# - Add usage instructions

# 6. Test thoroughly
python3 test_all.py
# - Manual testing
# - Edge cases

# 7. Merge to main
git checkout main
git merge feature/feature-name
git push origin main

# 8. Clean up
git branch -d feature/feature-name
```

### 🔍 Code Review Checklist (Self-Review)

Before merging to main:
- [ ] Code works and is tested
- [ ] README.md is updated
- [ ] No deprecated files in active use
- [ ] Commit messages are clear
- [ ] No debug code or console.logs left in
- [ ] Error handling is in place
- [ ] User-facing errors are helpful
- [ ] Feature is documented in README.md

### 📊 Project Status Tracking

#### In README.md
```markdown
## 🎯 Current Implementation

**Active File:** streaming_voice_agent.py
**Status:** ✅ Ready to test
**Last Updated:** 2026-01-31

### What Works
- ✅ Streaming voice recognition
- ✅ LLM conversation

### What's In Progress
- 🔄 Order parsing (feature/order-parsing branch)

### What's Planned
- 📋 Voice cloning
- 📋 Speaker identification
```

#### Update After Each Feature
1. Move from "In Progress" to "What Works"
2. Update "Last Updated" date
3. Add any new "What's Planned" items
4. Update status if needed

## Updates Log

- **2026-01-29**: Initial version created
  - Established "no implementation without approval" rule
  - Defined planning vs. implementation phases
  - Documented communication preferences

- **2026-01-31**: Added Git workflow and documentation practices
  - Feature branch strategy
  - README.md as single source of truth
  - File management best practices
  - Commit message guidelines
  - POC project management practices

## Documentation Structure

The project documentation is organized as follows:

```
camarerai/
├── README.md                           # Main documentation (single source of truth)
├── CLAUDE.md                           # AI assistant guidelines (this file)
├── docs/
│   ├── PLAN.md                        # Overall project plan and vision
│   ├── eng/
│   │   ├── IMPLEMENTATION_PLAN.md     # Technical implementation plan
│   │   └── IMPLEMENTATION_STATUS.md   # Current implementation status
│   └── prd/
│       └── PRODUCT_DESIGN.md          # Product design decisions
```

### Documentation Guidelines
- **README.md**: Always the primary source of truth for current status
- **docs/PLAN.md**: High-level project vision and planning
- **docs/eng/**: Technical documentation for implementation
- **docs/prd/**: Product design and user experience documentation
- When referencing documentation, use the paths above

## See Also

For lightweight workflow patterns when working with Claude Code across projects:
- See `/docs/toolkit/MARKDOWN_MANAGEMENT.md` for handling generated docs

---

**Remember**: This is a collaborative project. The user is in charge. Claude is here to help, not to take over. When in doubt, ask! 🤝

**New Rule**: Always work on feature branches. Keep main branch stable. Update README.md as the single source of truth.
