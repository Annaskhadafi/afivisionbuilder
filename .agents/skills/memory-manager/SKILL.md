---
name: memory-manager
description: Manages multiple memory files for AI sessions. Loads, compresses, and organizes context from CLAUDE.md, MEMORY.md, and other memory files to ensure AI understands project history and preferences when starting new sessions.
---

# Memory Manager

## Purpose

Ensure AI has optimal project context when starting new sessions by managing multiple memory files efficiently.

## Memory Files Hierarchy

Priority order (highest to lowest):
1. `CLAUDE.md` - Project-specific instructions and workflows
2. `MEMORY.md` - General project memory and preferences
3. `.memory/` - Directory for specialized memory files
4. `AGENTS.md` - Agent configuration (auto-loaded by system)

## Session Start Protocol

When starting a new session:

1. **Check existing memory files** in project root
2. **Load CLAUDE.md** first (mandatory)
3. **Load MEMORY.md** if exists
4. **Scan `.memory/` directory** for specialized files
5. **Prioritize recent context** over old information
6. **Compress if total tokens exceed 4000** (use compress skill)

## Memory Creation Rules

### When to create MEMORY.md:
- Project preferences not in CLAUDE.md
- Recurring patterns or decisions
- Team conventions and standards
- Historical context for features

### When to create `.memory/` files:
- `architecture.md` - System architecture decisions
- `decisions.md` - ADRs and technical choices
- `preferences.md` - Code style and tool preferences
- `history.md` - Feature development timeline

## Memory Compression

If combined memory files exceed 4000 tokens:
1. Use `compress` skill on oldest/least relevant files
2. Keep CLAUDE.md uncompressed (mandatory)
3. Archive old memories to `.memory/archive/`

## Memory Updates

After significant changes:
1. Update relevant memory file
2. Add timestamp to changes
3. Remove outdated information
4. Keep files under 2000 tokens each

## Quick Commands

```bash
# Check memory status
ls -la CLAUDE.md MEMORY.md .memory/

# Compress memory files
# Use compress skill on specific files

# Create new memory file
echo "# Project Memory" > MEMORY.md
```

## Memory Template

```markdown
# Project Memory

## Last Updated: [DATE]

## Key Decisions
- [Decision 1]
- [Decision 2]

## Preferences
- [Preference 1]
- [Preference 2]

## History
- [Date]: [Event]
```

## Integration with AGENTS.md

This skill works with the existing AGENTS.md system:
- AGENTS.md handles agent configuration
- MEMORY.md handles project context
- CLAUDE.md handles project-specific rules
- Together they provide complete AI context
