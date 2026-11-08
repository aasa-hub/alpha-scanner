---
name: paraspace
description: PARA-based workspace organization for AI agents. Keeps root clean with Projects, Areas, Resources, Archives structure.
metadata: {"openclaw": {"emoji": "📂"}}
---

# Paraspace: Agent Workspace Organization

PARA-based organization for AI agent workspaces. Prevents root clutter by giving everything a place: Projects, Areas, Resources, Archives.

---

## Quick Start

### Detect Workspace Type

```bash
[ -d ".paraspace" ] && echo "paraspace workspace" || echo "standard workspace"
```

**If `.paraspace/` exists:** Follow this system.
**If not:** Use standard conventions or initialize (see below).

### Initialize

```bash
mkdir -p .paraspace 00-inbox 01-projects 02-areas 03-resources 04-archive
echo "type: multi-project" > .paraspace/config.yaml
```

---

## PARA Structure

| Directory | Purpose | Examples |
|-----------|---------|----------|
| `00-inbox/` | Unsorted items, triage later | Quick notes, downloads, scratch files |
| `01-projects/` | Active work with end goals | `auth-system/`, `api-v2/`, `bugfix-123/` |
| `02-areas/` | Ongoing responsibilities | `security/`, `documentation/`, `infrastructure/` |
| `03-resources/` | Reference material | `style-guides/`, `api-specs/`, `templates/` |
| `04-archive/` | Completed/inactive items | Old projects, deprecated docs |

### Decision Tree

```
Does it have a deadline or end state?
  → Yes: 01-projects/
  → No: Continue...

Is it an ongoing responsibility?
  → Yes: 02-areas/
  → No: Continue...

Is it reference material you'll look up later?
  → Yes: 03-resources/
  → No: Continue...

Is it old/completed/inactive?
  → Yes: 04-archive/
  → No: 00-inbox/ (triage later)
```

---

## Workspace Types

### Single-Project

One repo, one project. Most common.

```
my-app/
├── .paraspace/
├── 00-inbox/
├── notes/              # Project notes (no 01-projects needed)
├── artifacts/          # Generated outputs
├── src/
├── tests/
└── docs/
```

### Multi-Project

Monorepo, knowledge base, or workspace with multiple efforts.

```
workspace/
├── .paraspace/
├── 00-inbox/
├── 01-projects/
│   ├── project-a/
│   └── project-b/
├── 02-areas/
├── 03-resources/
├── 04-archive/
```

### Which to Use

- **Cloning a repo?** → Single-project
- **Monorepo or knowledge base?** → Multi-project
- **Unsure?** → Single-project, migrate later if needed

---

## File Naming

### Loose Files (Notes, Artifacts)

Use timestamp + random suffix + slug:

```
YYYYMMDD-HHMMSS-XXX-description.ext
```

Example: `20260304-143022-a7f-meeting-notes.md`

**Generate:**
```bash
TS="$(date +%Y%m%d-%H%M%S)"
RND="$(LC_ALL=C tr -dc 'a-z0-9' < /dev/urandom | head -c3)"
echo "${TS}-${RND}-my-file.md"
```

### When to Use Timestamps

| Type | Timestamp? | Example |
|------|------------|---------|
| Notes, scratch | Yes | `20260304-143022-a7f-notes.md` |
| Artifacts, exports | Yes | `20260304-150000-b2k-diagram.png` |
| Source code | No | `auth.py`, `UserService.ts` |
| Config | No | `config.yaml`, `.gitignore` |
| Project directories | No | `auth-system/`, `api-v2/` |

### Directory Names

Lowercase kebab-case. No timestamps.

```
01-projects/auth-system/
02-areas/code-quality/
```

---

## Project Structure

Projects in `01-projects/` have their own internal structure:

```
01-projects/my-project/
├── src/                # Source code
├── tests/              # Tests
├── docs/               # Documentation
├── notes/              # Design decisions, meeting notes
├── artifacts/          # Generated outputs, diagrams
└── README.md           # Project overview
```

Keep it shallow. Don't over-organize inside projects.

---

## Inbox Workflow

`00-inbox/` is the escape valve. When unsure where something goes, put it there.

**Rules:**
1. Anything can go in inbox
2. Triage regularly (session end or daily)
3. Items should move out within 24-48 hours

**Triage:**
```bash
ls 00-inbox/

# Move to appropriate location
mv 00-inbox/meeting-notes.md 01-projects/auth-system/notes/
mv 00-inbox/api-spec.pdf 03-resources/

# Delete if no longer needed
rm 00-inbox/scratch.md
```

---

## Agent Behavior

### Session Start

1. Check for `.paraspace/` to detect workspace type
2. If paraspace workspace, note the structure
3. Check `00-inbox/` for pending items

### Creating Files

**Source code, config, standard project files:**
→ Use conventional names, put in appropriate project location

**Notes, scratch work:**
→ Timestamp ID, put in relevant `notes/` folder or `00-inbox/`

**Artifacts, exports, generated files:**
→ Timestamp ID, put in relevant `artifacts/` folder

**Unsure:**
→ `00-inbox/`

### Creating Projects

```bash
mkdir -p 01-projects/project-name/{src,tests,docs,notes,artifacts}
echo "# Project Name" > 01-projects/project-name/README.md
```

### Session End

1. Move root-level scratch files to `00-inbox/`
2. Don't stress about perfect organization

### Don't

- Create files at workspace root (except standard config like `.gitignore`)
- Use generic names: `notes.md`, `temp.txt`, `scratch.py`
- Nest deeper than 3-4 levels
- Reorganize existing files unless asked

---

## Special Cases

### Binary Files

Images, PDFs, etc. go in `artifacts/`:

```
01-projects/my-project/artifacts/20260304-143022-a7f-diagram.png
```

Large binaries: consider `.gitignore` or external storage.

### Existing Projects

When working in a repo that doesn't use paraspace:

1. Don't force-adopt
2. Add minimally (maybe just `notes/` folder)
3. Use timestamp IDs for any notes you create
4. Respect existing conventions

### Multi-Agent

If multiple agents work in the same workspace:

1. Timestamp IDs prevent file collisions
2. Use inbox when unsure
3. Don't delete other agents' files (archive instead)

---

## Configuration

### `.paraspace/config.yaml`

```yaml
type: single-project | multi-project
```

That's it. Keep it simple.

---

## Migration

### From Flat/Cluttered Root

```bash
# Initialize
mkdir -p .paraspace 00-inbox 01-projects 02-areas 03-resources 04-archive

# Move clutter to inbox
mv *.md 00-inbox/ 2>/dev/null
mv random-notes/ 00-inbox/

# Triage over time
```

### From Existing Project

Keep existing structure. Add paraspace alongside:

```
existing-project/
├── src/                   # Keep
├── tests/                 # Keep
├── .paraspace/            # Add
├── 00-inbox/              # Add
└── notes/                 # Add
```

---

## Anti-Patterns

| Don't | Instead |
|-------|---------|
| Files at root | Use PARA directories |
| `notes.md`, `temp.txt` | Timestamp + description |
| Deep nesting | Keep it shallow |
| Reorganizing unprompted | Only when asked |
| Over-organizing | Good enough is fine |
