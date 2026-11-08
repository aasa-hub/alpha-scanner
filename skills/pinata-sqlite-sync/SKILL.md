---
name: pinata-sqlite-sync
description: Local SQLite database with Pinata backup, CID chain versioning, and rollback support. Optional encryption. Agent-agnostic memory and task management.
homepage: https://pinata.cloud
metadata: {"openclaw": {"emoji": "🔗", "requires": {"env": ["PINATA_JWT", "PINATA_GATEWAY_URL"]}, "optional": {"env": ["SYNC_ENCRYPTION_KEY", "SYNC_NETWORK"]}, "primaryEnv": "PINATA_JWT"}}
---

# Pinata SQLite Sync

Local-first SQLite database with Pinata backup. Version-controlled via CID chains. Optional encryption.

## Environment Variables

Set by the operator, not the agent.

| Variable | Required | Description |
|----------|----------|-------------|
| `PINATA_JWT` | Yes | Pinata API JWT token |
| `PINATA_GATEWAY_URL` | Yes | Pinata gateway domain |
| `SYNC_ENCRYPTION_KEY` | No | 256-bit AES-GCM key. If set, encryption is enabled. |
| `SYNC_NETWORK` | No | `private` (default) or `public` |

## Data Location

```
.sync/
├── db.sqlite      # SQLite database (local, unencrypted)
├── config.json    # Project config
└── state.json     # Current version state
```

**config.json:**
```json
{
  "project_id": "my-project",
  "group_id": "pinata-group-uuid",
  "created_at": 1709467200
}
```

**state.json:**
```json
{
  "current_cid": "bafybeig...",
  "version": 3,
  "last_backup": 1709467200,
  "last_restore": null
}
```

---

# Memory System

## Memory Architecture

Three-tier memory model:

```
┌─────────────────────────────────────────────────────────┐
│                    CORE MEMORY                          │
│  (Always in context - persona, user, current goals)     │
├─────────────────────────────────────────────────────────┤
│                  WORKING MEMORY                         │
│  (Recent interactions, active context, session state)   │
├─────────────────────────────────────────────────────────┤
│                  ARCHIVAL MEMORY                        │
│  (Long-term storage - facts, events, knowledge)         │
│  (Searchable, can be retrieved into working memory)     │
└─────────────────────────────────────────────────────────┘
         ↕ relationships ↕
┌─────────────────────────────────────────────────────────┐
│                  MEMORY GRAPH                           │
│  (Connections between memories - related, caused,       │
│   contradicts, supports, supersedes, etc.)              │
└─────────────────────────────────────────────────────────┘
```

## Memory Types

**Core Memory** (stored in `memory_blocks` table):

Standard blocks:
| Label | Description | Lifecycle |
|-------|-------------|-----------|
| `persona` | Agent identity and personality | Persistent, rarely changes |
| `user` | Information about the current user | Persistent, updated as learned |
| `goals` | Current objectives and priorities | Changes per project/session |
| `context` | Active project/session context | Changes frequently |

Config file blocks (synced with external files):
| Label | Source File | Description |
|-------|-------------|-------------|
| `identity` | `identity.md` | Agent name, role, voice |
| `instructions` | `agents.md` | Operating instructions, workflow |
| `tools` | `tools.md` | Tool notes and conventions |
| `heartbeat` | `heartbeat.md` | Execution config, scheduled tasks |

Note: `soul.md` maps to `persona` block. `user.md` maps to `user` block.

**Archival Memory** (stored in `memories` table):
| Type | Description | Lifecycle |
|------|-------------|-----------|
| `working` | Current session context, recent interactions | Session-scoped, may promote or archive |
| `episodic` | Events, conversations, things that happened | Long-term, searchable |
| `semantic` | Facts, knowledge, learned information | Long-term, searchable |
| `procedural` | How to do things, patterns, preferences | Long-term, searchable |

## Database Schema

```sql
-- Core memory blocks (always loaded into context)
-- Standard labels: persona, user, goals, context
-- Config file labels: identity, instructions, tools, heartbeat
CREATE TABLE IF NOT EXISTS memory_blocks (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL UNIQUE,         -- Extensible: persona, user, goals, context, identity, etc.
    description TEXT,                   -- What this block contains
    content TEXT NOT NULL,              -- The actual content
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

-- Archival/working memories
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK (type IN ('working', 'episodic', 'semantic', 'procedural')),
    content TEXT NOT NULL,
    summary TEXT,                       -- Condensed version for retrieval
    source TEXT,                        -- Where this came from (conversation, observation, inference, memory.md)
    importance REAL DEFAULT 0.5,        -- 0.0 to 1.0, affects retrieval priority
    access_count INTEGER DEFAULT 0,     -- How often retrieved
    last_accessed INTEGER,              -- Last retrieval timestamp
    session_id TEXT,                    -- For working memory scope (references sessions.id)
    metadata TEXT,                      -- JSON additional data
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    archived_at INTEGER                 -- NULL = active, timestamp = archived
);

-- Sessions (tracks agent interaction sessions)
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,                -- UUID
    started_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    ended_at INTEGER,                   -- NULL = active session
    summary TEXT,                       -- Session summary (populated on end)
    metadata TEXT,                      -- JSON additional data (user, project, etc.)
    status TEXT DEFAULT 'active'
        CHECK (status IN ('active', 'ended', 'abandoned'))
);

-- Memory relationships (graph edges)
-- ID convention: memory IDs use UUIDs, block IDs use 'block-{label}' prefix
CREATE TABLE IF NOT EXISTS memory_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,            -- Memory UUID or 'block-{label}'
    target_id TEXT NOT NULL,            -- Memory UUID or 'block-{label}'
    relation TEXT NOT NULL CHECK (relation IN (
        'related_to',      -- General association (bidirectional)
        'derived_from',    -- This memory came from that one
        'supports',        -- Evidence for
        'contradicts',     -- Conflicts with (bidirectional)
        'supersedes',      -- Replaces/updates
        'caused_by',       -- Causal relationship
        'part_of',         -- Hierarchical
        'references'       -- Mentions
    )),
    weight REAL DEFAULT 1.0,            -- Strength of relationship
    metadata TEXT,                      -- JSON additional data
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

-- Tasks
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'backlog'
        CHECK (status IN ('backlog', 'todo', 'in_progress', 'done', 'archived')),
    priority INTEGER NOT NULL DEFAULT 0,
    labels TEXT,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    due_date INTEGER
);

-- Toolcall audit
CREATE TABLE IF NOT EXISTS toolcalls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT NOT NULL,
    started_at INTEGER NOT NULL,
    ended_at INTEGER,
    inputs TEXT,
    outputs TEXT,
    status TEXT CHECK (status IN ('running', 'success', 'error'))
);

-- Sync log
CREATE TABLE IF NOT EXISTS sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cid TEXT NOT NULL,
    version INTEGER NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('backup', 'restore')),
    timestamp INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

-- Config file sync (bidirectional sync with external markdown files)
CREATE TABLE IF NOT EXISTS config_files (
    id TEXT PRIMARY KEY,              -- e.g., 'soul', 'identity', 'user'
    file_path TEXT NOT NULL,          -- relative path: 'soul.md', '.openclaw/identity.md'
    content_hash TEXT,                -- SHA256 of file content (detect changes)
    file_mtime INTEGER,               -- file modification time (unix timestamp)
    db_mtime INTEGER,                 -- last DB update time
    sync_status TEXT DEFAULT 'synced'
        CHECK (sync_status IN ('synced', 'file_ahead', 'db_ahead', 'conflict', 'file_deleted')),
    block_label TEXT,                 -- maps to memory_blocks.label (NULL for memory.md)
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

-- Available skills (agent capabilities)
CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,              -- e.g., 'pinata-sqlite-sync', 'commit-commands'
    name TEXT NOT NULL,               -- Display name
    description TEXT,                 -- What the skill does
    version TEXT,                     -- Semantic version (e.g., '1.0.0')
    source TEXT DEFAULT 'installed'   -- 'builtin', 'installed', 'workspace'
        CHECK (source IN ('builtin', 'installed', 'workspace')),
    enabled INTEGER DEFAULT 1,        -- 0 = disabled, 1 = enabled
    config TEXT,                      -- JSON skill-specific configuration
    file_path TEXT,                   -- Path to SKILL.md if file-based
    metadata TEXT,                    -- JSON additional data (author, homepage, etc.)
    installed_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC);
CREATE INDEX IF NOT EXISTS idx_memories_accessed ON memories(last_accessed DESC);
CREATE INDEX IF NOT EXISTS idx_memories_session ON memories(session_id);
CREATE INDEX IF NOT EXISTS idx_memories_archived ON memories(archived_at);
CREATE INDEX IF NOT EXISTS idx_memories_source ON memories(source);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_edges_source ON memory_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON memory_edges(target_id);
CREATE INDEX IF NOT EXISTS idx_edges_relation ON memory_edges(relation);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_toolcalls_started ON toolcalls(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_config_files_status ON config_files(sync_status);
CREATE INDEX IF NOT EXISTS idx_config_files_label ON config_files(block_label);
CREATE INDEX IF NOT EXISTS idx_skills_enabled ON skills(enabled);
CREATE INDEX IF NOT EXISTS idx_skills_source ON skills(source);
```

---

## Core Memory Operations

Core memory blocks are always loaded into the agent's context window.

### Initialize Default Blocks

On first run, create standard blocks:

```sql
INSERT OR IGNORE INTO memory_blocks (id, label, description, content) VALUES
    ('block-persona', 'persona', 'Agent identity and personality (from soul.md)', ''),
    ('block-identity', 'identity', 'Agent name, role, voice (from identity.md)', ''),
    ('block-user', 'user', 'User profile and preferences (from user.md)', ''),
    ('block-goals', 'goals', 'Current objectives and priorities', ''),
    ('block-context', 'context', 'Active project/session context', ''),
    ('block-instructions', 'instructions', 'Operating instructions (from agents.md)', ''),
    ('block-tools', 'tools', 'Tool notes and conventions (from tools.md)', ''),
    ('block-heartbeat', 'heartbeat', 'Execution config (from heartbeat.md)', '');
```

Initialize config file mappings:

```sql
INSERT OR IGNORE INTO config_files (id, file_path, block_label) VALUES
    ('soul', 'soul.md', 'persona'),
    ('identity', 'identity.md', 'identity'),
    ('user', 'user.md', 'user'),
    ('agents', 'agents.md', 'instructions'),
    ('tools', 'tools.md', 'tools'),
    ('heartbeat', 'heartbeat.md', 'heartbeat'),
    ('memory', 'memory.md', NULL);  -- maps to memories table, not a block
```

### Load Core Memory

At session start, load all blocks:

```sql
SELECT label, content FROM memory_blocks ORDER BY label;
```

Format into context:
```xml
<core_memory>
  <persona>{persona content from soul.md}</persona>
  <identity>{identity content from identity.md}</identity>
  <user>{user content from user.md}</user>
  <goals>{goals content}</goals>
  <context>{context content}</context>
  <instructions>{instructions content from agents.md}</instructions>
  <tools>{tools content from tools.md}</tools>
  <heartbeat>{heartbeat content from heartbeat.md}</heartbeat>
</core_memory>
```

Note: Empty blocks can be omitted from context to save tokens.

### Update Block

When agent learns persistent information:

```sql
UPDATE memory_blocks
SET content = ?, updated_at = strftime('%s', 'now')
WHERE label = ?;
```

**When to update core memory:**
- User states a preference → update `user` block
- Agent's role changes → update `persona` block
- New objective assigned → update `goals` block
- Project context changes → update `context` block
- Workflow/instructions change → update `instructions` block
- Tool usage notes change → update `tools` block

Note: When updating blocks linked to config files, run config sync to propagate changes.

---

## Archival Memory Operations

Long-term memories that can be searched and retrieved.

### Store Memory

**When to store:**
- Significant event occurred
- New fact learned
- User shared important information
- Decision was made and why
- Error occurred and how it was resolved

```sql
INSERT INTO memories (id, type, content, summary, source, importance, metadata)
VALUES (?, ?, ?, ?, ?, ?, ?);
```

**Importance scoring (0.0 - 1.0):**
- 0.9+ : Critical facts, user preferences, major decisions
- 0.7-0.9 : Important context, significant events
- 0.5-0.7 : Useful information, minor events
- 0.3-0.5 : Background details, routine interactions
- <0.3 : Trivial, may be pruned

### Retrieve Memories

**By recency:**
```sql
SELECT * FROM memories
WHERE archived_at IS NULL
ORDER BY created_at DESC
LIMIT ?;
```

**By importance:**
```sql
SELECT * FROM memories
WHERE archived_at IS NULL
ORDER BY importance DESC, last_accessed DESC
LIMIT ?;
```

**By type:**
```sql
SELECT * FROM memories
WHERE type = ? AND archived_at IS NULL
ORDER BY importance DESC
LIMIT ?;
```

**By text search (agent does semantic matching):**
```sql
SELECT * FROM memories
WHERE archived_at IS NULL
  AND (content LIKE ? OR summary LIKE ?)
ORDER BY importance DESC
LIMIT ?;
```

### Mark Retrieved

Update access patterns when memory is used:

```sql
UPDATE memories
SET access_count = access_count + 1,
    last_accessed = strftime('%s', 'now')
WHERE id = ?;
```

### Archive Memory

Move to cold storage (still searchable but deprioritized):

```sql
UPDATE memories
SET archived_at = strftime('%s', 'now')
WHERE id = ?;
```

**When to archive:**
- Session ended and working memory no longer needed
- Information superseded by newer memory
- Low importance + old + rarely accessed

### Delete Memory

Permanent removal:

```sql
DELETE FROM memory_edges WHERE source_id = ? OR target_id = ?;
DELETE FROM memories WHERE id = ?;
```

**When to delete:**
- User requests forgetting
- Information proven false
- Privacy requirement

---

## Working Memory Operations

Session-scoped context that may be promoted to archival.

### Start Session

Generate session ID and store session context:

```sql
INSERT INTO memories (id, type, content, source, session_id)
VALUES (?, 'working', ?, 'session_start', ?);
```

### End Session

Review and promote working memories:

```
1. Query working memories for this session
2. For each memory with importance >= 0.5:
   - Classify: Is this episodic (event), semantic (fact), or procedural (how-to)?
   - Update type accordingly
3. Archive low-importance memories
```

```sql
-- Step 1: Get working memories to review
SELECT * FROM memories
WHERE session_id = ? AND type = 'working'
ORDER BY importance DESC;

-- Step 2: Promote each classified memory (agent determines target_type)
UPDATE memories
SET type = ?, session_id = NULL
WHERE id = ? AND importance >= 0.5;

-- Step 3: Archive the rest
UPDATE memories
SET archived_at = strftime('%s', 'now')
WHERE session_id = ? AND type = 'working';
```

**Classification guidance:**
- **episodic**: "User asked about X", "Error occurred when doing Y", "Meeting happened"
- **semantic**: "User prefers dark mode", "API key is stored in .env", "Project uses React"
- **procedural**: "To deploy, run X then Y", "When errors occur, check logs first"

---

## Memory Graph Operations

Relationships between memories enable traversal and reasoning.

### Create Edge

```sql
INSERT INTO memory_edges (source_id, target_id, relation, weight, metadata)
VALUES (?, ?, ?, ?, ?);
```

**When to create edges:**
- New memory derived from existing one → `derived_from`
- Memories about same topic → `related_to`
- Memory updates previous knowledge → `supersedes`
- Conflicting information → `contradicts`
- Evidence for a belief → `supports`

### Query Related Memories

Find all memories connected to a given memory (bidirectional):

```sql
-- Outgoing edges (this memory → others)
SELECT m.*, e.relation, e.weight, 'outgoing' as direction
FROM memories m
JOIN memory_edges e ON m.id = e.target_id
WHERE e.source_id = ?

UNION ALL

-- Incoming edges (others → this memory)
SELECT m.*, e.relation, e.weight, 'incoming' as direction
FROM memories m
JOIN memory_edges e ON m.id = e.source_id
WHERE e.target_id = ?

ORDER BY weight DESC;
```

### Find Contradictions

```sql
SELECT m.*
FROM memories m
JOIN memory_edges e ON m.id = e.target_id
WHERE e.source_id = ? AND e.relation = 'contradicts';
```

### Traverse Graph

Find memories within N hops (bidirectional):

```sql
WITH RECURSIVE related AS (
    -- Start: direct connections (both directions)
    SELECT target_id as node_id, 1 as depth FROM memory_edges WHERE source_id = ?
    UNION
    SELECT source_id as node_id, 1 as depth FROM memory_edges WHERE target_id = ?

    UNION

    -- Recurse: follow edges in both directions
    SELECT e.target_id, r.depth + 1
    FROM memory_edges e
    JOIN related r ON e.source_id = r.node_id
    WHERE r.depth < ?

    UNION

    SELECT e.source_id, r.depth + 1
    FROM memory_edges e
    JOIN related r ON e.target_id = r.node_id
    WHERE r.depth < ?
)
SELECT DISTINCT m.* FROM memories m
JOIN related r ON m.id = r.node_id
WHERE m.id != ?;  -- Exclude starting node
```

---

## Memory Lifecycle Protocol

### On New Information

```
1. Classify: Is this core, episodic, semantic, or procedural?
2. Score importance: How critical is this information?
3. Check conflicts: Does this contradict existing memories?
   - If yes, create 'contradicts' edge, possibly 'supersedes'
4. Find related: What existing memories relate to this?
   - Create 'related_to' edges
5. Store: Insert into appropriate table
6. Update core: If this affects persona/user/goals/context, update block
```

### On Session End

```
1. Review working memories
2. Promote high-importance items to archival
3. Archive low-importance items
4. Consolidate: Summarize related memories if too many
5. Update core memory blocks if session changed them
```

### Periodic Maintenance

Run daily or weekly:

```sql
-- 1. Decay importance for stale memories (not accessed in 30+ days)
UPDATE memories
SET importance = MAX(0.3, importance * 0.95),
    updated_at = strftime('%s', 'now')
WHERE last_accessed < strftime('%s', 'now') - (30 * 86400)
  AND importance > 0.3
  AND archived_at IS NULL;

-- 2. Archive trivial memories older than 24 hours
UPDATE memories
SET archived_at = strftime('%s', 'now')
WHERE importance < 0.3
  AND created_at < strftime('%s', 'now') - 86400
  AND archived_at IS NULL;

-- 3. Prune archived memories older than 90 days
DELETE FROM memory_edges
WHERE source_id IN (
    SELECT id FROM memories
    WHERE archived_at < strftime('%s', 'now') - (90 * 86400)
) OR target_id IN (
    SELECT id FROM memories
    WHERE archived_at < strftime('%s', 'now') - (90 * 86400)
);
DELETE FROM memories
WHERE archived_at < strftime('%s', 'now') - (90 * 86400);

-- 4. Find unresolved contradictions
SELECT m1.id, m1.content, m2.id, m2.content
FROM memory_edges e
JOIN memories m1 ON e.source_id = m1.id
JOIN memories m2 ON e.target_id = m2.id
WHERE e.relation = 'contradicts'
  AND m1.archived_at IS NULL
  AND m2.archived_at IS NULL;
```

---

# Config File Sync

Bidirectional synchronization between external markdown config files and the database.

Compatible with [OpenClaw](https://docs.openclaw.ai/), [soul.md](https://github.com/aaronjmars/soul.md), and similar agentic frameworks.

## Supported Files

| File | Maps To | Purpose |
|------|---------|---------|
| `soul.md` | `memory_blocks.persona` | Behavioral philosophy, values, personality |
| `identity.md` | `memory_blocks.identity` | Agent name, role, goals, voice |
| `user.md` | `memory_blocks.user` | User profile, preferences, communication style |
| `agents.md` | `memory_blocks.instructions` | Operating instructions, workflow, priorities |
| `tools.md` | `memory_blocks.tools` | Tool notes and conventions |
| `heartbeat.md` | `memory_blocks.heartbeat` | Execution config, scheduled tasks |
| `memory.md` | `memories` table | Session memory log (special handling) |

## File Discovery

Files are searched in order (first found wins):

1. Project root: `./soul.md`
2. OpenClaw directory: `./.openclaw/soul.md`
3. Agent directory: `./.agent/soul.md`
4. Custom path in `config_files.file_path`

```sql
-- Check which file path is active for each config
SELECT id, file_path, sync_status FROM config_files;
```

## Sync Algorithm

Timestamp-based conflict resolution. Most recent modification wins.

```
FOR EACH config_file:
    1. Read file from disk (if exists)
    2. Compute file_hash = SHA256(file_content) if file exists
    3. Get file_mtime from filesystem if file exists
    4. Get db_mtime, content_hash from config_files table
    5. Get block_content from memory_blocks (via block_label)

    IF file doesn't exist AND db has content:
        → DB wins: write content to file, update file_mtime
        → Set sync_status = 'synced'

    ELSE IF file doesn't exist AND db is empty:
        → No action needed, skip

    ELSE IF file exists AND db is empty (first sync):
        → File wins: update memory_blocks.content
        → Set sync_status = 'synced'

    ELSE IF file_hash == content_hash:
        → No change, skip

    ELSE IF file_mtime > db_mtime:
        → File wins: update memory_blocks.content, update content_hash
        → Set sync_status = 'synced'

    ELSE IF db_mtime > file_mtime:
        → DB wins: write memory_blocks.content to file
        → Set sync_status = 'synced'

    ELSE (same mtime, different hash):
        → Mark sync_status = 'conflict'
        → Log warning, require manual resolution
```

## Handling File Deletion

When a previously synced file is deleted:

```
IF file doesn't exist AND content_hash is NOT NULL (was synced before):
    → Mark sync_status = 'file_deleted'
    → Preserve DB content (don't auto-delete)
    → Agent/operator decides: restore file or clear DB
```

**Resolution options:**

```sql
-- Option 1: Restore file from DB
UPDATE config_files SET sync_status = 'db_ahead', file_mtime = 0 WHERE id = ?;
-- Then run sync (will write DB content to file)

-- Option 2: Clear DB content (accept deletion)
UPDATE memory_blocks SET content = '', updated_at = strftime('%s', 'now')
WHERE label = (SELECT block_label FROM config_files WHERE id = ?);
UPDATE config_files SET content_hash = NULL, sync_status = 'synced' WHERE id = ?;
```

Add to schema CHECK constraint:
```sql
-- Update config_files sync_status to include 'file_deleted'
sync_status TEXT DEFAULT 'synced'
    CHECK (sync_status IN ('synced', 'file_ahead', 'db_ahead', 'conflict', 'file_deleted'))
```

## Sync Operations

### Run Sync

Called on session start, before backup, or manually:

```sql
-- Get all config files to sync
SELECT cf.id, cf.file_path, cf.content_hash, cf.file_mtime, cf.db_mtime, cf.block_label,
       mb.content as block_content, mb.updated_at as block_updated
FROM config_files cf
LEFT JOIN memory_blocks mb ON cf.block_label = mb.label;
```

After sync completes, update tracking:

```sql
UPDATE config_files
SET content_hash = ?,
    file_mtime = ?,
    db_mtime = ?,
    sync_status = 'synced',
    updated_at = strftime('%s', 'now')
WHERE id = ?;
```

### Check Sync Status

```sql
SELECT cf.id, cf.file_path, cf.sync_status, cf.file_mtime, cf.db_mtime,
       mb.label, LENGTH(mb.content) as content_length
FROM config_files cf
LEFT JOIN memory_blocks mb ON cf.block_label = mb.label
ORDER BY cf.id;
```

### Force Sync Direction

Override timestamp logic when needed:

```sql
-- Force file → DB (use file content regardless of timestamps)
UPDATE config_files SET db_mtime = 0 WHERE id = ?;
-- Then run sync

-- Force DB → file (write DB content regardless of timestamps)
UPDATE config_files SET file_mtime = 0 WHERE id = ?;
-- Then run sync
```

### Resolve Conflict

When `sync_status = 'conflict'`:

```sql
-- Option 1: Keep file version
UPDATE config_files SET db_mtime = 0 WHERE id = ? AND sync_status = 'conflict';

-- Option 2: Keep DB version
UPDATE config_files SET file_mtime = 0 WHERE id = ? AND sync_status = 'conflict';

-- Then run sync to apply resolution
```

### Register Custom Config File

Add additional config files beyond defaults:

```sql
INSERT INTO config_files (id, file_path, block_label)
VALUES ('custom', 'custom-config.md', 'custom');

-- Also create the memory block
INSERT INTO memory_blocks (id, label, description, content)
VALUES ('block-custom', 'custom', 'Custom config file', '');
```

## Special Handling: memory.md

`memory.md` doesn't map to a single block. It syncs with the `memories` table.

### memory.md Format

```markdown
# Memory Log

## Semantic (Facts)
<!-- type: semantic -->

- [id:abc123] User prefers dark mode | importance: 0.8
- [id:def456] Project uses TypeScript and React | importance: 0.7

## Episodic (Events)
<!-- type: episodic -->

- [id:ghi789] 2024-03-15: Deployed v2.0 to production | importance: 0.6
- [id:jkl012] 2024-03-14: Fixed auth bug in login flow | importance: 0.5

## Procedural (How-to)
<!-- type: procedural -->

- [id:mno345] To deploy: run `npm run build && npm run deploy` | importance: 0.7
```

**Format rules:**
- Sections denote memory type via HTML comment: `<!-- type: semantic -->`
- Each entry: `- [id:{uuid}] {content} | importance: {0.0-1.0}`
- ID is required for bidirectional sync (prevents duplicates)
- Entries without ID are assigned one on first sync

### Read (file → DB)

```sql
-- For each parsed entry:
INSERT INTO memories (id, type, content, source, importance)
VALUES (?, ?, ?, 'memory.md', ?)
ON CONFLICT(id) DO UPDATE SET
    content = excluded.content,
    importance = excluded.importance,
    updated_at = strftime('%s', 'now');
```

**Deletion handling:** Entries removed from file are archived (not deleted):
```sql
UPDATE memories
SET archived_at = strftime('%s', 'now')
WHERE source = 'memory.md'
  AND id NOT IN (/* ids found in file */);
```

### Write (DB → file)

```sql
-- Query memories to export
SELECT id, type, content, importance, created_at
FROM memories
WHERE source = 'memory.md'
  AND archived_at IS NULL
ORDER BY type, importance DESC, created_at DESC;
```

Group by type and format as markdown per the format above.

## Sync Timing

Config sync should run:
- **On session start** - Load latest file contents into DB
- **Before Pinata backup** - Ensure DB reflects current file state
- **After memory_blocks update** - Propagate changes to files
- **On demand** - Manual sync when files edited externally

---

# Skills

Track available agent capabilities for bootstrapping and change auditing.

## Skill Sources

| Source | Description |
|--------|-------------|
| `builtin` | Core skills bundled with the agent |
| `installed` | Skills added via package manager or manual install |
| `workspace` | Project-specific skills in `.skills/` or workspace config |

## Skill Discovery

Scan for skills on agent startup:

1. **Builtin skills** - Hardcoded list from agent implementation
2. **Installed skills** - From skill registry/package manager
3. **Workspace skills** - Scan `.skills/` directory for SKILL.md files

```sql
-- Register a discovered skill (preserves installed_at on update)
INSERT INTO skills (id, name, description, version, source, file_path, metadata)
VALUES (?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    name = excluded.name,
    description = excluded.description,
    version = excluded.version,
    source = excluded.source,
    file_path = excluded.file_path,
    metadata = excluded.metadata,
    updated_at = strftime('%s', 'now');
-- Note: installed_at is preserved, only updated_at changes
```

## Operations

### List Available Skills

```sql
-- All enabled skills
SELECT id, name, description, version, source
FROM skills
WHERE enabled = 1
ORDER BY source, name;

-- Skills with full details
SELECT * FROM skills ORDER BY source, name;
```

### Bootstrap Context

Load skills into agent context at session start:

```sql
SELECT id, name, description, version
FROM skills
WHERE enabled = 1
ORDER BY source, name;
```

Format for context:
```xml
<available_skills>
  <skill id="pinata-sqlite-sync" version="1.0.0">Local SQLite with Pinata backup</skill>
  <skill id="commit-commands" version="2.1.0">Git commit and PR workflows</skill>
  ...
</available_skills>
```

### Register Skill

```sql
INSERT INTO skills (id, name, description, version, source, file_path, metadata)
VALUES (
    'my-skill',
    'My Custom Skill',
    'Does something useful',
    '1.0.0',
    'workspace',
    '.skills/my-skill/SKILL.md',
    '{"author": "user", "homepage": "https://example.com"}'
);
```

### Update Skill

```sql
UPDATE skills
SET version = ?,
    description = ?,
    metadata = ?,
    updated_at = strftime('%s', 'now')
WHERE id = ?;
```

### Enable/Disable Skill

```sql
-- Disable
UPDATE skills SET enabled = 0, updated_at = strftime('%s', 'now') WHERE id = ?;

-- Enable
UPDATE skills SET enabled = 1, updated_at = strftime('%s', 'now') WHERE id = ?;
```

### Remove Skill

```sql
DELETE FROM skills WHERE id = ? AND source != 'builtin';
```

Note: Builtin skills cannot be removed, only disabled.

### Track Skill Changes

Query skill history via `installed_at` and `updated_at`:

```sql
-- Recently updated skills
SELECT id, name, version, updated_at
FROM skills
WHERE updated_at > ?
ORDER BY updated_at DESC;

-- Recently installed skills
SELECT id, name, version, source, installed_at
FROM skills
WHERE installed_at > ?
ORDER BY installed_at DESC;
```

## Skill Config

Store per-skill configuration in the `config` JSON field:

```sql
-- Set skill config
UPDATE skills
SET config = '{"api_key_env": "MY_API_KEY", "timeout": 30}',
    updated_at = strftime('%s', 'now')
WHERE id = ?;

-- Read skill config
SELECT id, config FROM skills WHERE id = ?;
```

---

# Task Operations

Kanban-style task management.

| Operation | SQL |
|-----------|-----|
| Add | `INSERT INTO tasks (id, title, description, status, priority, labels, ...) VALUES (...)` |
| Move | `UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?` |
| List | `SELECT * FROM tasks WHERE status != 'archived' ORDER BY priority DESC` |
| Get | `SELECT * FROM tasks WHERE id = ?` |
| Update | `UPDATE tasks SET ... WHERE id = ?` |
| Delete | `DELETE FROM tasks WHERE id = ?` |

**Statuses:** `backlog` → `todo` → `in_progress` → `done` → `archived`

---

# Toolcall Audit

Track agent tool invocations.

| Operation | SQL |
|-----------|-----|
| Start | `INSERT INTO toolcalls (tool_name, started_at, inputs, status) VALUES (?, ?, ?, 'running')` |
| Complete | `UPDATE toolcalls SET ended_at = ?, outputs = ?, status = ? WHERE id = ?` |
| List | `SELECT * FROM toolcalls ORDER BY started_at DESC LIMIT ?` |

---

# Sync Operations

## Security

### Encryption (Optional)

If `SYNC_ENCRYPTION_KEY` is set, backups are encrypted before upload.

**Algorithm:** AES-256-GCM with unique 12-byte nonce per backup.

### Network Choice

| Value | Default | Description |
|-------|---------|-------------|
| `private` | Yes | Pinata-hosted only |
| `public` | No | Published to public IPFS |

## Sync Timing

Sync should occur:
- **On session end** - Backup after significant work
- **Periodic cron** - e.g., `*/30 * * * *` for every 30 minutes
- **On demand** - Manual backup before risky operations

## Initialization

On first run, create a Pinata group to organize backups:

**Create Group:**
```
POST https://api.pinata.cloud/v3/groups
Authorization: Bearer $PINATA_JWT
Content-Type: application/json

{
  "name": "{project_id}-sync",
  "is_public": false
}
```

Response includes `id` - store this as `group_id` in config.json.

## Backup

1. Create atomic SQLite backup (`.backup` command or file copy)
2. Compress with gzip
3. If `SYNC_ENCRYPTION_KEY` set: encrypt with AES-256-GCM, save nonce
4. Calculate SHA256 checksum of final blob
5. Upload to Pinata with CID chain keyvalues
6. Update state.json with new CID and version

**Upload:**
```
POST https://uploads.pinata.cloud/v3/files
Authorization: Bearer $PINATA_JWT
Content-Type: multipart/form-data

file: <blob>
name: "db-v{version}.sqlite.gz"
group_id: "{group_id}"
network: "{$SYNC_NETWORK or 'private'}"
keyvalues: {
  "project_id": "{project_id}",
  "version": "{new_version}",
  "prev_cid": "{current_cid or ''}",
  "timestamp": "{unix_timestamp}",
  "checksum": "sha256:{hash}",
  "nonce": "{base64_nonce}"
}
```

Note: Omit `nonce` field entirely if not encrypting.

## Query Versions

List all backups for a project:

**Query by keyvalues:**
```
GET https://api.pinata.cloud/v3/files?group={group_id}&metadata[project_id]={project_id}
Authorization: Bearer $PINATA_JWT
```

Response includes array of files with their keyvalues. Sort by `version` to get history.

## Restore

1. Query Pinata for target version (or latest)
2. Download blob via gateway
3. Verify SHA256 checksum matches keyvalues
4. If `nonce` present in keyvalues: decrypt (error if no `SYNC_ENCRYPTION_KEY`)
5. Decompress gzip
6. Backup current db.sqlite to db.sqlite.bak
7. Replace db.sqlite with restored data
8. Update state.json

**Download via gateway:**
```
GET https://{PINATA_GATEWAY_URL}/files/{cid}
```

Or with signed URL for private files:
```
GET https://{PINATA_GATEWAY_URL}/files/{cid}?accessToken={token}
```

**Error conditions:**
- Checksum mismatch → abort, keep current db
- Encrypted but no `SYNC_ENCRYPTION_KEY` → abort with clear error
- Decryption fails → abort, likely wrong key
- Decompression fails → abort, corrupted backup

## CID Chain Traversal

Each backup's `prev_cid` points to the previous version, forming a linked list.

**Walk the chain:**
```
1. Start with latest CID from state.json (or query for highest version)
2. Fetch file metadata to get keyvalues
3. Read prev_cid from keyvalues
4. Repeat until prev_cid is empty (reached v1)
```

**Restore to specific version:**
```
1. Query all files with project_id
2. Find file where version = target
3. Download and restore that CID
```

---

# Implementation Notes

## General Notes

- IDs should be UUIDs (e.g., `uuid4()`) for memories, sessions, tasks, skills
- Graph edges are optional but enable richer reasoning
- Run maintenance periodically (daily, weekly) to prevent unbounded growth
- Memory consolidation: summarize 10+ related memories into one
- No foreign key constraints on `memory_edges` - allows referencing both tables

## Importance Scoring Reference

Importance scores determine retrieval priority and pruning eligibility.

| Score | Meaning | Examples | Retention |
|-------|---------|----------|-----------|
| 0.9 - 1.0 | **Critical** | User identity, core preferences, security decisions | Never prune |
| 0.7 - 0.9 | **High** | Project requirements, significant events, key decisions | Long-term |
| 0.5 - 0.7 | **Medium** | Useful context, minor events, learned patterns | Archive after 30 days inactive |
| 0.3 - 0.5 | **Low** | Background details, routine interactions | Archive after 7 days inactive |
| 0.0 - 0.3 | **Trivial** | Transient context, noise | Prune after 24 hours |

**Scoring rules:**
- User-stated preferences: 0.9
- Errors and their resolutions: 0.7
- Routine task completions: 0.4
- Transient observations: 0.2

**Decay formula:**
```
new_importance = importance * 0.95  -- Apply weekly for memories not accessed in 30+ days
```

Stop decay at 0.3 floor (preserve minimum context).

---

# Resources

- [Pinata API Docs](https://docs.pinata.cloud)
- [OpenClaw Agent Runtime](https://docs.openclaw.ai/concepts/agent)
- [soul.md Framework](https://github.com/aaronjmars/soul.md)
