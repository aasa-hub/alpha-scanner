---
name: pinata-platform
description: Self-service platform operations — manage skills, secrets, agents, tasks, channels, templates, config, and more. No setup required, all credentials are auto-injected.
homepage: https://pinata.cloud
metadata: {"openclaw": {"emoji": "🔧"}}
---

# pinata-platform

Platform self-service CLI for Pinata agents. Run commands to manage your skills, spin up agents, create secrets, schedule tasks, and more.

## Setup

No setup required. All credentials are automatically injected by the platform.

## Important Behaviors

When the user asks you to do any of the following, use the corresponding commands from this skill:

- **Open a port, expose a web app, make something publicly accessible, or set up routing** — use `open-port` to create a port forwarding rule. This maps an external path prefix to an internal container port so the app becomes reachable at `https://{agentId}.agents.pinata.cloud/{pathPrefix}`. Use `--protected=false` if the user wants the route publicly accessible without a gateway token.
- **Close or stop exposing a port** — use `close-port`.
- **List routes or check what ports are open** — use `list-routes`.
- **Give the app a friendly subdomain** (e.g. `swift-fox-347.agents.pinata.cloud`) — use `add-subdomain <port>` to register a mnemonic subdomain pointing at a container port. Pass `--subdomain=name-noun-NNN` to choose one, or omit to auto-generate. Use `--protected=false` for public access.
- **Connect a custom domain** (e.g. `app.example.com`) — this is a three-step flow:
  1. `domain-challenge <domain>` to get the `_pinata-verify.<domain>` TXT record value.
  2. The user adds that TXT record AND a `CNAME <domain> → apps.pinata.cloud` (use `apps.devpinata.cloud` on dev) to their DNS provider. **Do not point the CNAME at the agent subdomain.**
  3. `add-domain <domain> <port>` to register the domain. The endpoint validates the TXT record before accepting. The response includes `cnameTarget` — confirm it matches the value you told the user to use. `cfStatus` starts as `pending` and becomes `active` once Cloudflare provisions the SSL certificate.
- **Check SSL or verification status of a custom domain** — use `verify-domain <domainId>`. Run this periodically until `cfStatus` is `active` and `cfSslStatus` is `active`. Domains in `pending_ownership` need their TXT record added; `pending` domains are waiting on Cloudflare SSL.
- **List domains and subdomains for this agent** — use `list-domains`.
- **Update or change the target port of a domain** — use `update-domain <domainId> --targetPort=...`. Custom domains and subdomains themselves cannot be renamed — delete and recreate.
- **Remove a domain or subdomain** — use `remove-domain <domainId>`.
- **Install or add a skill** — browse ClawHub with `browse-hub`, then install with `install-hub <slug>`, attach with `attach <cid>`, and `restart` to activate it.
- **Create a skill** — write the skill files locally (a `skill.json` and a `SKILL.md` at minimum), then upload to the user's library. Skills can also be published to ClawHub via `submit-template`.
- **Create or submit a template** — use `submit-template <gitUrl>` to submit a public git repo as a template. Use `list-templates` to browse existing templates.
- **Create a secret or API key** — use `create-secret <path> <value>` to create an encrypted secret at a vault path. The path can be a single env-var name (`ANTHROPIC_API_KEY`) or a slash-separated path (`develop/ANTHROPIC_API_KEY`, `production/ANTHROPIC_API_KEY`) so the same env-var name can hold different values per environment or per agent. Add `--attach` to immediately attach it to this agent; combine with `--mount-as=ENV_VAR_NAME` if you want it mounted under a different env-var than the path's last segment. Use `--type=variable` for plaintext env vars. Always `restart` after attaching secrets so the container picks them up.
- **Attach an existing secret** — use `attach-secret <secretId>`. Pass `--mount-as=ENV_VAR_NAME` to override the env-var name the container will see (defaults to the source secret's last path segment). Then `restart`.
- **Per-instance secrets in a template (legacy workaround)** — partners sometimes have agents create per-instance secrets like `ANTHROPIC_API_KEY_<agentId>` from inside the bootstrap script. With vault paths this is no longer necessary: store the secret at `templates/{template-slug}/{agentId}/ANTHROPIC_API_KEY` (or any path that isolates it) and attach it with `--mount-as=ANTHROPIC_API_KEY`. The agent-id-suffix pattern still works but is no longer the recommended approach.
- **Change the model or update agent config** — use `get-config` to read the current `openclaw.json`, modify the model in `agents.defaults.model.primary` (e.g. `anthropic/claude-sonnet-4-6`), then `set-config` with the updated JSON. No restart needed — config changes apply immediately.
- **Pull in one of the user's GitHub repos** — when the user asks you to clone, import, or work on one of their repos, use `list-repos` to find it (matches what they connected under Integrations) and `clone-repo <owner>/<repo>` to clone it into the workspace. Requires the user to have connected GitHub first; if `list-repos` returns "GitHub is not connected", point them to Settings → Integrations → GitHub.
- **Create or list issue boards** — when the user asks you to organize issues into a new board ("make a board for the customer feedback work", "spin up an Upcoming board"), use `create-board <name>` and surface the returned `boardId` so subsequent `create-issue` calls can target it with `--boardId=...`. Use `list-boards` first to check whether a matching board already exists and to confirm the workspace hasn't hit its plan cap.
- **Delegate work to a sibling agent** — when the user asks you to hand off a task ("ask superbuilder-2 to write the docs", "have my research agent investigate X"), find the sibling with `list-agents`, then `create-issue` with `--agentId=<siblingId>`. The sibling's cron dispatcher picks it up automatically and runs it. Use this when the work belongs to a specialist agent, when you need parallel execution, or when the user explicitly names another agent. Confirm the assignment back to the user with the new issueId so they can track it.
- **Start a dev-server preview for an issue** — when you receive an issue whose prompt includes a PREVIEW MODE block (the user toggled "Generate preview" at create time), follow it step-by-step: run `list-ports` to see which ports are already forwarded, also check what's listening locally (e.g. `lsof -iTCP -sTCP:LISTEN -P` or `ss -tln`), pick a port that appears in neither, start the project's dev server bound to `0.0.0.0:<port>` **fully detached** (`setsid … > /tmp/preview.log 2>&1 &` — never a bare `&`, which leaves it holding this turn's stdio open and hangs the run), then call `open-preview --issue=<issueId> --port=<port>` so the platform reserves a routable path prefix. The Preview tab in the issue drawer goes live within seconds. Do not block — keep working. The platform closes the route automatically when the issue is marked done. You can also call `close-preview --issue=<issueId>` explicitly (e.g. if you want to restart the dev server on a different port mid-run).

## Usage

All commands output JSON. Replace `{baseDir}` with the skill's install directory.

```
node {baseDir}/cli.mjs <command> [args...]
node {baseDir}/cli.mjs help
```

## Commands

### Identity & Status

```bash
# Get your agent ID, name, status, user ID
node {baseDir}/cli.mjs whoami

# Check container health and status
node {baseDir}/cli.mjs status

# Update your name, description, emoji, or vibe
node {baseDir}/cli.mjs update-metadata --name="New Name" --emoji="🚀"

# Restart your container (e.g. after adding secrets/skills)
node {baseDir}/cli.mjs restart
```

### Skills

```bash
# List all skills in your user's library
node {baseDir}/cli.mjs list-library

# List skills currently attached to you
node {baseDir}/cli.mjs list-attached

# Browse ClawHub marketplace
node {baseDir}/cli.mjs browse-hub --q="web scraper"

# Get details for a specific skill
node {baseDir}/cli.mjs hub-detail <slug>

# Install a skill from ClawHub into your library
node {baseDir}/cli.mjs install-hub <slug>

# Attach skills to yourself (by CID from list-library)
node {baseDir}/cli.mjs attach <skillCid1> [skillCid2...]

# Detach a skill (by ID from list-attached)
node {baseDir}/cli.mjs detach <skillId>
```

### Secrets

Secrets are addressed by **vault path** (e.g. `ANTHROPIC_API_KEY`, `develop/ANTHROPIC_API_KEY`, `shared/openai/OPENAI_API_KEY`). Two secrets can share the same final segment as long as their full paths differ — useful for per-environment variants or per-template-instance credentials. When attaching to an agent, the env-var name the container sees defaults to the path's last segment; pass `--mount-as=...` to override.

```bash
# List available secrets (paths + names, values never exposed)
node {baseDir}/cli.mjs list-secrets

# Create an encrypted secret at a flat path (equivalent to old behavior)
node {baseDir}/cli.mjs create-secret MY_API_KEY sk-123abc

# Create per-environment variants — both mount as ANTHROPIC_API_KEY by default
node {baseDir}/cli.mjs create-secret develop/ANTHROPIC_API_KEY sk-ant-dev
node {baseDir}/cli.mjs create-secret production/ANTHROPIC_API_KEY sk-ant-prod

# Create a plaintext variable
node {baseDir}/cli.mjs create-secret DEBUG true --type=variable

# Create and immediately attach to yourself (mounts as the path's last segment)
node {baseDir}/cli.mjs create-secret OPENAI_API_KEY sk-xxx --attach

# Create + attach + override the env-var name the container sees
node {baseDir}/cli.mjs create-secret develop/ANTHROPIC_API_KEY sk-ant-dev --attach --mount-as=ANTHROPIC_API_KEY

# Attach an existing secret with the default mount alias
node {baseDir}/cli.mjs attach-secret <secretId>

# Attach an existing secret under a custom env-var name
node {baseDir}/cli.mjs attach-secret <secretId> --mount-as=ANTHROPIC_API_KEY

# Attach several secrets at once (each uses its default mount alias)
node {baseDir}/cli.mjs attach-secret <secretId1> <secretId2> <secretId3>

# Detach a secret from this agent
node {baseDir}/cli.mjs detach-secret <secretId>
```

### Tasks (Cron)

```bash
# List scheduled tasks
node {baseDir}/cli.mjs list-tasks

# Create a recurring task (runs every 6 hours)
node {baseDir}/cli.mjs create-task "Check news" --every="6h" --prompt="Search for AI news and summarize"

# Create a one-shot task (runs at a specific time)
node {baseDir}/cli.mjs create-task "Reminder" --at="2026-04-10T09:00:00Z" --prompt="Remind user about meeting"

# Create a cron-scheduled task
node {baseDir}/cli.mjs create-task "Daily digest" --cron="0 9 * * *" --prompt="Generate daily summary"

# Update an existing task
node {baseDir}/cli.mjs update-task <jobId> --prompt="New prompt" --every="12h"

# Run a task immediately
node {baseDir}/cli.mjs run-task <jobId>

# Enable/disable a task
node {baseDir}/cli.mjs toggle-task <jobId>

# Delete a task
node {baseDir}/cli.mjs delete-task <jobId>
```

Duration formats for `--every`: `30s`, `5m`, `6h`, `1d`, or raw milliseconds.

### Config

```bash
# Read current openclaw.json
node {baseDir}/cli.mjs get-config

# Write config (pass full JSON)
node {baseDir}/cli.mjs set-config '{"agents":{"defaults":{"model":{"primary":"anthropic/claude-sonnet-4-6"}}}}'
```

### Console

```bash
# Execute a shell command in your container
node {baseDir}/cli.mjs exec "ls -la /home/node/clawd"
node {baseDir}/cli.mjs exec "cat /home/node/.openclaw/openclaw.json"
```

### Routes (Port Forwarding)

```bash
# List current port forwarding rules
node {baseDir}/cli.mjs list-routes

# Open a port — maps a path prefix to a container port
node {baseDir}/cli.mjs open-port 3000 /app

# Open an unprotected port (no gateway token required)
node {baseDir}/cli.mjs open-port 8080 /public --protected=false

# Close a port by path prefix
node {baseDir}/cli.mjs close-port /app
```

Port rules map external path prefixes to internal container ports. Ports 0-1023 and 18789 (gateway) are reserved. Max 10 rules per agent.

### Custom Domains

Custom domains and mnemonic subdomains let you serve apps at clean URLs instead of path prefixes. Subdomains route immediately; custom domains require DNS verification before traffic flows.

```bash
# List subdomains and custom domains for this agent
node {baseDir}/cli.mjs list-domains

# Register a mnemonic subdomain for port 3000 (auto-generated name)
node {baseDir}/cli.mjs add-subdomain 3000
# → https://{adjective}-{noun}-{NNN}.agents.pinata.cloud

# Pick the subdomain explicitly (must match adjective-noun-NNN format)
node {baseDir}/cli.mjs add-subdomain 3000 --subdomain=swift-fox-347

# Public (no gateway token required)
node {baseDir}/cli.mjs add-subdomain 8080 --protected=false
```

For custom domains (bring-your-own), follow the three-step verification flow:

```bash
# 1. Get the TXT challenge for the domain
node {baseDir}/cli.mjs domain-challenge app.example.com
# → { txtName: "_pinata-verify.app.example.com", txtValue: "pinata-verify=..." }

# 2. User adds two DNS records at their provider:
#    - TXT   _pinata-verify.app.example.com   "pinata-verify=..."
#    - CNAME app.example.com                  apps.pinata.cloud
#    (use apps.devpinata.cloud on dev; the cnameTarget returned in step 3 will confirm it)

# 3. Register the domain (TXT must already be present in DNS or this fails)
node {baseDir}/cli.mjs add-domain app.example.com 3000
# → { domain: { id, cfStatus: "pending", cfSslStatus: "pending_validation", cnameTarget: "...", ... } }

# 4. Poll Cloudflare verification + SSL status until active
node {baseDir}/cli.mjs verify-domain <domainId>

# Update target port or protection
node {baseDir}/cli.mjs update-domain <domainId> --targetPort=8080

# Delete (releases the domain for reuse)
node {baseDir}/cli.mjs remove-domain <domainId>
```

Domain status fields:
- `cfStatus: null` — subdomain (always live, no verification needed)
- `cfStatus: "pending_ownership"` — TXT record not yet seen; ask the user to add it and call `verify-domain`
- `cfStatus: "pending"` — Cloudflare is provisioning the hostname / SSL cert
- `cfStatus: "active"` + `cfSslStatus: "active"` — fully live, traffic flows

Limits: max 5 domains per agent. Domains containing "pinata" or using reserved suffixes are banned. Port 18789 is reserved for the gateway.

### Channels

```bash
# List connected channels (Telegram, Discord, etc.)
node {baseDir}/cli.mjs list-channels

# Add a Telegram channel
node {baseDir}/cli.mjs add-channel telegram '{"botToken":"123456:ABC..."}'

# Add a Discord channel
node {baseDir}/cli.mjs add-channel discord '{"webhookUrl":"https://discord.com/api/webhooks/..."}'

# Remove a channel
node {baseDir}/cli.mjs remove-channel telegram
```

### Agents

```bash
# List all agents belonging to your user
node {baseDir}/cli.mjs list-agents

# Create a new agent
node {baseDir}/cli.mjs create-agent "My New Agent"

# Create with options
node {baseDir}/cli.mjs create-agent "Research Bot" --description="Researches topics" --emoji="🔬"

# Create from a template
node {baseDir}/cli.mjs create-agent "Web App" --templateId=<uuid>
```

### Templates

```bash
# Browse published templates
node {baseDir}/cli.mjs list-templates

# Filter by category
node {baseDir}/cli.mjs list-templates --category=productivity

# Submit a template from a public git repo
node {baseDir}/cli.mjs submit-template https://github.com/user/my-template

# Submit from a specific branch or subdirectory
node {baseDir}/cli.mjs submit-template https://github.com/user/repo --branch=dev --path=agents/my-template

# Get a published template by slug
node {baseDir}/cli.mjs get-template <slug>

# Validate a git repo without submitting it (checks manifest.json,
# README.md, workspace/). Use this to dry-run a submission.
node {baseDir}/cli.mjs validate-template https://github.com/user/my-template
node {baseDir}/cli.mjs validate-template https://github.com/user/repo --ref=dev --path=agents/my-template
```

### Boards

Boards group issues by topic (e.g. "Internals", "QA", "Upcoming"). Each workspace starts with one default board and can have up to 1/5/10 depending on plan (Free/Picnic/Fiesta). The management UI shows one board per page; pass `--boardId` to `create-issue` to route an issue at a specific board.

```bash
# List the workspace's boards
node {baseDir}/cli.mjs list-boards
# → { boards: [{ boardId, slug, name, description, isDefault, ... }], maxBoards }

# Create a new board
node {baseDir}/cli.mjs create-board "Upcoming"

# With a description
node {baseDir}/cli.mjs create-board "Customer Reports" --description="Bugs reported by support"

# Rename a board or update its description
node {baseDir}/cli.mjs update-board <boardId> --name="New Name"
node {baseDir}/cli.mjs update-board <boardId> --description="Updated context"
node {baseDir}/cli.mjs update-board <boardId> --description=""   # clears it

# Soft-delete a board. Issues on it get reassigned to the next active
# board; deleting the last board auto-creates a fresh default.
node {baseDir}/cli.mjs delete-board <boardId>
```

After creating a board, file issues onto it by passing the returned `boardId` to `create-issue --boardId=...`.

### Issues (Agent-to-Agent Delegation)

```bash
# List issues. Defaults to all; filter by assignee, board, or status.
node {baseDir}/cli.mjs list-issues
node {baseDir}/cli.mjs list-issues --agentId=<siblingId>
node {baseDir}/cli.mjs list-issues --status=running

# Delegate work to a sibling agent. The cron dispatcher picks the
# issue up automatically and runs it on the assigned agent's behalf.
node {baseDir}/cli.mjs create-issue "Title" "Prompt for the agent" --agentId=<siblingId>

# Same, with board + tags + a repo to clone before the run
node {baseDir}/cli.mjs create-issue "Fix login bug" "Please investigate and patch" \
  --agentId=<siblingId> --boardId=<boardId> --tags=urgent,security --repoUrl=https://github.com/...

# File an issue for yourself but skip auto-dispatch (e.g. so you can
# attach files via separate calls before the run starts)
node {baseDir}/cli.mjs create-issue "Later task" "Do this next" --skipAutoDispatch
```

`create-issue` defaults `agentId` to your own ID, so pass `--agentId=<siblingId>` explicitly when delegating. Use `list-agents` to discover sibling agents in the same workspace, then pick one whose name / vibe matches the task. The response includes the new `issueId` — surface it back to the user so they can find the work on their board.

```bash
# Get a single issue's full record
node {baseDir}/cli.mjs get-issue <issueId>

# Edit an issue. Most fields are backlog-only (prompt, agentId, repoUrl,
# previewUrlOverride); title / priority / dueAt / human assignee can be
# changed at any status. Hard-terminal statuses (archived, rejected,
# failed) only accept dueAt + priority.
node {baseDir}/cli.mjs update-issue <issueId> --title="New title"
node {baseDir}/cli.mjs update-issue <issueId> --prompt="Refined task description"
node {baseDir}/cli.mjs update-issue <issueId> --priority=high --dueAt=2026-06-01T17:00:00Z
node {baseDir}/cli.mjs update-issue <issueId> --agentId=<siblingId>          # reassign (backlog only)
node {baseDir}/cli.mjs update-issue <issueId> --repoUrl=""                   # clear repo
node {baseDir}/cli.mjs update-issue <issueId> --assigneeUserId="" --assigneeName=""  # unassign human

# Cancel an in-flight (assigned/running) issue. Frees the agent job and
# moves the issue back to backlog. Does NOT auto-dispatch.
node {baseDir}/cli.mjs cancel-issue <issueId>

# Archive an issue. For backlog/done this is a pure status flip; for
# in-flight issues this also cancels the agent job. Use /reject first
# if you need the workspace reverted (archive doesn't touch files).
node {baseDir}/cli.mjs archive-issue <issueId>

# Permanently delete an issue. Only allowed in backlog, done, rejected,
# failed, or archived. To delete an in-flight issue, cancel or archive
# it first.
node {baseDir}/cli.mjs delete-issue <issueId>

# Move a backlog issue (with an agent already assigned) into the dispatch
# queue. Starts immediately if the agent is idle.
node {baseDir}/cli.mjs assign-issue <issueId>

# Snapshot the workspace and move the issue into Review. Use this to
# signal that you're done with an issue assigned to you.
node {baseDir}/cli.mjs ready-issue <issueId>
```

#### Comments

```bash
# List threaded comments on an issue
node {baseDir}/cli.mjs list-comments <issueId>

# Post a comment (1–2000 chars). Notifies assignee, reviewer, creator,
# and any @-mentioned workspace members. Quote the body for multi-word.
node {baseDir}/cli.mjs add-comment <issueId> "Looks good — ready to merge"
```

### Issue Preview (dev-server proxying)

Used when an issue's prompt includes a `PREVIEW MODE` block. The user toggled "Generate preview" at create time and wants a live iframe of the project's dev server in the Preview tab.

```bash
# 1. See which ports are already forwarded on this agent (multiple
#    concurrent previews are allowed, but you must pick a port that
#    nobody else is using).
node {baseDir}/cli.mjs list-ports

# 2. Also check what's listening locally so you don't reuse a port
#    held by another process inside the container.
lsof -iTCP -sTCP:LISTEN -P     # or `ss -tln`

# 3. Start the project's dev server FULLY DETACHED, bound to 0.0.0.0 on a
#    port not in either list. You MUST redirect its stdout+stderr to a file
#    and start it in a new session (`setsid`) so it does NOT inherit this
#    turn's stdio. A plain `cmd &` leaves the server attached to the agent's
#    output pipes; the server keeps them open after the turn finishes, the
#    platform never sees the run end, and the issue hangs in "running" until
#    it times out. Always use this shape:
setsid sh -c 'PORT=5174 npm run dev' > /tmp/preview-5174.log 2>&1 &
# setsid sh -c 'python3 -m http.server 8081 --bind 0.0.0.0' > /tmp/preview-8081.log 2>&1 &
# (No `setsid`? fall back to: nohup PORT=5174 npm run dev > /tmp/preview-5174.log 2>&1 &)
# Then confirm it came up: sleep 1; tail -n 20 /tmp/preview-5174.log

# 4. Report the port. The platform reserves /preview-{shortIssueId}
#    on this agent's HTTPRoute and returns the prefix so you can
#    configure the dev server's base path if needed (Vite `base`,
#    Next `basePath`, CRA `homepage`).
node {baseDir}/cli.mjs open-preview --issue=<issueId> --port=5174
# → { pathPrefix: "/preview-ab12cd", port: 5174 }

# 5. (Optional) Close the preview explicitly. Otherwise the platform
#    tears it down automatically on done / reject / cancel / archive.
node {baseDir}/cli.mjs close-preview --issue=<issueId>
```

Pitfalls to avoid:
- **Detach the dev server from this turn's stdio** (`setsid … > /tmp/preview.log 2>&1 &`). A bare `npm run dev &` keeps the server attached to the agent's output pipes — it holds them open after you finish, so the platform never detects the turn ending and the issue stays stuck in "running". Redirect to a log file and `setsid` (or `nohup`) it.
- Don't pick a port that's already in `list-ports` — the open call returns a 400.
- Don't pick the gateway port (18789) or any port below 1024.
- Bind to `0.0.0.0`, not `127.0.0.1` — the HTTPRoute reaches the container by service IP.
- If the project uses a router with absolute asset paths, set its base / basePath to the prefix returned by `open-preview`, or assets will 404 under the iframe.

### GitHub

```bash
# List the workspace owner's connected GitHub repositories (100 most-recent)
node {baseDir}/cli.mjs list-repos

# Clone a repo into the agent workspace using the stored OAuth token
node {baseDir}/cli.mjs clone-repo pinata/agents-api

# Clone a specific branch shallowly into a custom directory
node {baseDir}/cli.mjs clone-repo pinata/agents-api --ref=main --depth=1 --dest=upstream

# Pull / fetch / push a cloned repo (operates on the clone's GitHub origin)
node {baseDir}/cli.mjs pull --dest=upstream
node {baseDir}/cli.mjs fetch --dest=upstream
node {baseDir}/cli.mjs push-branch --dest=upstream --branch=my-feature

# Open a pull request from a feature branch
node {baseDir}/cli.mjs open-pr --repo=pinata/agents-api --head=my-feature --title="Add widget" --body="Implements the widget."

# Inspect, comment on, merge, or close a PR
node {baseDir}/cli.mjs get-pr 42 --repo=pinata/agents-api
node {baseDir}/cli.mjs list-pr-comments 42 --repo=pinata/agents-api
node {baseDir}/cli.mjs comment-pr 42 "Rebased onto main, ready for another look." --repo=pinata/agents-api
node {baseDir}/cli.mjs merge-pr 42 --repo=pinata/agents-api --method=squash
node {baseDir}/cli.mjs close-pr 42 --repo=pinata/agents-api
```

Requires the workspace owner to have connected GitHub under Settings → Integrations. The OAuth token is injected server-side for every operation (clone URL, PR API calls, pull/fetch/push) and stripped from `.git/config` and command output — agents never see it. Clone destinations are workspace-relative and must not already exist; `pull`/`fetch`/`push-branch` operate on an already-cloned repo dir (`--dest`) whose origin points at github.com. Pushes are restricted to the current (or named) branch — no force-push.

### Platform Token

```bash
# Get a short-lived JWT (1h) for audit trails
node {baseDir}/cli.mjs get-token
```

## Workflows

### Install a skill and activate it

```bash
node {baseDir}/cli.mjs browse-hub --q="web scraper"
node {baseDir}/cli.mjs install-hub web-scraper
node {baseDir}/cli.mjs attach web-scraper
node {baseDir}/cli.mjs restart    # reload to pick up new skill
```

### Create a secret and use it

```bash
node {baseDir}/cli.mjs create-secret ANTHROPIC_API_KEY sk-ant-xxx --attach
node {baseDir}/cli.mjs restart    # reload to inject new env var
```

### Spin up another agent

```bash
node {baseDir}/cli.mjs list-templates
node {baseDir}/cli.mjs create-agent "Helper Bot" --emoji="🤖" --templateId=<uuid>
# returns agentId + gatewayToken for the new agent
```

### Schedule recurring work

```bash
node {baseDir}/cli.mjs create-task "Check news" --every="6h" --prompt="Search for AI news and summarize"
node {baseDir}/cli.mjs list-tasks
```

### Expose a web app

```bash
# Start your app on port 3000, then expose it
node {baseDir}/cli.mjs open-port 3000 /app
# Access at https://{agentId}.agents.pinata.cloud/app
```

### Give an app a friendly subdomain

```bash
# Auto-generated mnemonic subdomain
node {baseDir}/cli.mjs add-subdomain 3000
# → https://swift-fox-347.agents.pinata.cloud
```

### Connect a custom domain

```bash
# 1. Get the TXT verification token
node {baseDir}/cli.mjs domain-challenge app.example.com

# 2. User adds DNS records at their provider:
#    TXT   _pinata-verify.app.example.com   pinata-verify=...
#    CNAME app.example.com                  apps.pinata.cloud
#    (use apps.devpinata.cloud on dev)

# 3. Register (validates TXT, kicks off SSL provisioning)
node {baseDir}/cli.mjs add-domain app.example.com 3000

# 4. Poll until cfStatus + cfSslStatus are both "active"
node {baseDir}/cli.mjs verify-domain <domainId>
```

### Check everything

```bash
node {baseDir}/cli.mjs whoami           # who am I
node {baseDir}/cli.mjs status           # container health
node {baseDir}/cli.mjs list-attached    # my skills
node {baseDir}/cli.mjs list-secrets     # available credentials
node {baseDir}/cli.mjs list-tasks       # scheduled work
node {baseDir}/cli.mjs list-channels    # connected channels
node {baseDir}/cli.mjs list-agents      # all user's agents
node {baseDir}/cli.mjs list-routes      # port forwarding rules
node {baseDir}/cli.mjs list-domains     # subdomains and custom domains
```
