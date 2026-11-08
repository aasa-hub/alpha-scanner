#!/usr/bin/env node
// v1.8.0 — GitHub pull-request ops: open-pr / get-pr / list-pr-comments /
// comment-pr / merge-pr / close-pr, plus pull / fetch / push-branch for
// cloned repos (token injected server-side, never exposed to the agent).
// v1.7.0 — fills CRUD gaps: get-issue / update-issue / delete-issue /
// cancel-issue / archive-issue / assign-issue / ready-issue, plus
// list-comments / add-comment, update-board / delete-board,
// validate-template / get-template.

/**
 * CLI wrapper for @pinata/platform skill.
 *
 * Uses two authentication modes:
 *   1. Gateway token → agent subdomain (/v0/platform/*, /v0/tasks, /v0/config, etc.)
 *   2. Platform JWT  → management domain (/v0/agents, /v0/secrets, /v0/skills, etc.)
 *
 * The platform JWT is auto-obtained on the first management-domain call.
 *
 * Run `node cli.mjs help` for full command list.
 */

// Different engines inject the per-agent gateway token under different env
// var names — OpenClaw uses OPENCLAW_GATEWAY_TOKEN, Super Builder uses
// SUPERBUILDER_GATEWAY_TOKEN. The skill is engine-agnostic, so accept either.
const GATEWAY_TOKEN = process.env.OPENCLAW_GATEWAY_TOKEN || process.env.SUPERBUILDER_GATEWAY_TOKEN;
const AGENT_ID = process.env.AGENT_ID;
const AGENTS_API_URL = process.env.AGENTS_API_URL || "https://agents.pinata.cloud";

let _platformToken = null;

function headers(token) {
  return { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
}

/** Agent subdomain base: {AGENT_ID}.agents.pinata.cloud */
function agentOrigin() {
  if (!AGENT_ID) { console.error("Error: AGENT_ID is not set"); process.exit(1); }
  const url = new URL(AGENTS_API_URL);
  url.hostname = `${AGENT_ID}.${url.hostname}`;
  return url.origin;
}

/** Management domain base: agents.pinata.cloud */
function mgmtOrigin() {
  return new URL(AGENTS_API_URL).origin;
}

async function call(url, method, body, token) {
  const opts = { method, headers: headers(token) };
  if (body) opts.body = JSON.stringify(body);
  const response = await fetch(url, opts);
  const text = await response.text();
  if (!response.ok) { console.error(`Error ${response.status}: ${text}`); process.exit(1); }
  try { return JSON.parse(text); } catch { return text; }
}

/** Call per-agent API (gateway token auth, agent subdomain) */
async function agentApi(path, method = "GET", body) {
  if (!GATEWAY_TOKEN) { console.error("Error: OPENCLAW_GATEWAY_TOKEN / SUPERBUILDER_GATEWAY_TOKEN is not set"); process.exit(1); }
  return call(`${agentOrigin()}/v0${path}`, method, body, GATEWAY_TOKEN);
}

/** Call management API (platform JWT auth, management domain) */
async function mgmtApi(path, method = "GET", body) {
  if (!_platformToken) {
    const res = await agentApi("/platform/token", "POST");
    _platformToken = res.token;
  }
  return call(`${mgmtOrigin()}${path}`, method, body, _platformToken);
}

/** Parse a human duration string (e.g. "6h", "30m", "1d", "90s") to milliseconds. */
function parseDuration(str) {
  const m = str.match(/^(\d+(?:\.\d+)?)\s*(ms|s|m|h|d)$/i);
  if (!m) {
    // Try as raw milliseconds
    const n = Number(str);
    if (!isNaN(n)) return n;
    console.error(`Invalid duration: "${str}". Use e.g. "30m", "6h", "1d", "90s"`);
    process.exit(1);
  }
  const val = parseFloat(m[1]);
  const unit = m[2].toLowerCase();
  const multipliers = { ms: 1, s: 1000, m: 60000, h: 3600000, d: 86400000 };
  return Math.round(val * multipliers[unit]);
}

function parseFlags(args) {
  const flags = {};
  const positional = [];
  for (const arg of args) {
    const m = arg.match(/^--(\w[\w-]*)(?:=(.*))?$/);
    if (m) { flags[m[1]] = m[2] !== undefined ? m[2] : true; }
    else { positional.push(arg); }
  }
  return { flags, positional };
}

/** Resolve `--repo=owner/name` (or `--owner=` + `--repo=name`) into { owner, repo }.
 *  Exits with a usage error if either part is missing. */
function resolveRepo(flags, usage) {
  let owner = flags.owner;
  let repo = flags.repo;
  if (repo && repo.includes("/")) { [owner, repo] = repo.split("/", 2); }
  if (!owner || !repo) { console.error(usage); process.exit(1); }
  return { owner, repo };
}

const HELP = `
Pinata Platform CLI — self-service commands for agents.

Usage: node cli.mjs <command> [args...]

Identity & Status:
  whoami                                  Get agent identity
  status                                  Check agent health
  update-metadata [--name=...] [--description=...] [--emoji=...] [--vibe=...]
                                          Update this agent's metadata
  restart                                 Restart container (e.g. after adding skills/secrets)

Skills:
  list-library                            List user's skill library
  list-attached                           List skills attached to this agent
  browse-hub [--q=...] [--category=...]   Browse ClawHub marketplace
  hub-detail <slug>                       Get ClawHub skill details
  install-hub <slug>                      Install a ClawHub skill to library
  attach <cid1> [cid2...]                 Attach skills to this agent
  detach <skillId>                        Detach a skill from this agent

Secrets:
  list-secrets                            List available secrets (paths + names only)
  create-secret <path> <value> [--name=...] [--type=secret|variable] [--attach] [--mount-as=...]
                                          Create a new secret at the given vault path
                                          (e.g. ANTHROPIC_API_KEY or develop/ANTHROPIC_API_KEY).
                                          --mount-as only applies when --attach is set.
  attach-secret <secretId> [--mount-as=ENV_VAR_NAME]
                                          Attach an existing secret to this agent
                                          (use --mount-as to override the env-var name;
                                           defaults to the last path segment).
                                          Accepts multiple IDs; --mount-as applies only when one ID is given.
  detach-secret <secretId>                Detach a secret from this agent

Tasks (Cron):
  list-tasks                              List scheduled tasks
  create-task <name> [--every=...] [--at=...] [--cron=...] [--prompt=...]
                                          Create a scheduled task
  update-task <jobId> [--name=...] [--prompt=...] [--every=...] [--at=...] [--cron=...]
                                          Update a scheduled task
  delete-task <jobId>                     Delete a scheduled task
  run-task <jobId>                        Execute a task immediately
  toggle-task <jobId>                     Enable/disable a task

Routes (Port Forwarding):
  list-routes                             List port forwarding rules
  open-port <port> <pathPrefix> [--protected=true|false]
                                          Open a port (map path to container port)
  close-port <pathPrefix>                 Close a port (remove rule by path prefix)

Custom Domains:
  list-domains                            List subdomains and custom domains for this agent
  add-subdomain <port> [--subdomain=...] [--protected=true|false]
                                          Register an agents.pinata.cloud subdomain (auto-generated if --subdomain omitted)
  domain-challenge <domain>               Get the DNS TXT record required to verify a custom domain
  add-domain <domain> <port> [--protected=true|false]
                                          Register a custom domain. Requires the TXT record from domain-challenge
                                          to already exist in DNS, plus a CNAME pointing the domain at the
                                          cnameTarget returned in the response.
  verify-domain <domainId>                Re-check verification / SSL status for a custom domain
  update-domain <domainId> [--targetPort=...] [--protected=true|false]
                                          Update target port or protection on an existing domain
  remove-domain <domainId>                Delete a subdomain or custom domain

Config:
  get-config                              Read openclaw.json config
  set-config <json>                       Write openclaw.json config

Console:
  exec <command>                          Execute a shell command

Channels:
  list-channels                           List connected channels
  add-channel <type> '<configJson>'       Add a channel (type: telegram, discord, slack, whatsapp)
  remove-channel <type>                   Remove a channel

Agents:
  list-agents                             List user's agents
  create-agent <name> [--description=...] [--emoji=...] [--templateId=...]
                                          Create a new agent

Templates:
  list-templates [--category=...]         Browse published templates
  get-template <slug>                     Get a published template by its slug.
  submit-template <gitUrl> [--branch=...] [--path=...]
                                          Submit a template from a git repo
  validate-template <gitUrl> [--ref=...] [--path=...]
                                          Validate a git repo as a template (checks manifest.json,
                                          README.md, workspace/) without creating a submission.

Boards (issue grouping):
  list-boards                             List the workspace's issue boards (slug, id, name, description).
  create-board <name> [--description=...] Create a new issue board. Capped per plan (Free: 1, Picnic: 5,
                                          Fiesta: 10). Returns the new board's id + slug.
  update-board <boardId> [--name=...] [--description=...]
                                          Rename a board or update its description. Pass --description=
                                          with an empty value to clear it.
  delete-board <boardId>                  Soft-delete a board. Issues on the deleted board are reassigned
                                          to the next active board; a fresh default board is auto-created
                                          if you delete the last one.

Issues (agent-to-agent delegation):
  list-issues [--agentId=...] [--boardId=...] [--status=...]
                                          List issues. Filter by assignee, board, or status.
  get-issue <issueId>                     Get a single issue with its full record.
  create-issue <title> <prompt> [--agentId=...] [--boardId=...] [--tags=a,b]
               (--repoUrl=<url> | --no-repo)
                                          File an issue assigned to a sibling agent. The cron dispatcher
                                          picks it up on their behalf. Defaults agentId to SELF — pass
                                          --agentId=<siblingId> from list-agents to delegate work.
                                          You MUST pick either --repoUrl=<github-url> (issue will be
                                          worked on against that repo, branch + PR opened) or --no-repo
                                          (workspace-only issue, no clone). If the user's request is
                                          ambiguous about which repo to target, ask them first — running
                                          this without a repo choice exits 2 and lists connected repos.
                                          Add --skipAutoDispatch to leave it in backlog.
                                          Add --previewRequested to ask the assignee to start a dev
                                          server and report its port (see open-preview below).
  update-issue <issueId> [--title=...] [--prompt=...] [--agentId=...] [--repoUrl=...]
               [--priority=low|medium|high|urgent] [--dueAt=<iso8601>] [--previewUrlOverride=...]
               [--assigneeUserId=...] [--assigneeName=...]
                                          Edit an issue. Most fields (prompt, agentId, repoUrl,
                                          previewUrlOverride) are backlog-only; title, priority, dueAt,
                                          and human assignee can be changed at any status. Hard-terminal
                                          statuses (archived/rejected/failed) only accept dueAt + priority.
  delete-issue <issueId>                  Permanently delete an issue. Allowed in backlog, done, rejected,
                                          failed, or archived. To delete an in-flight issue, cancel or
                                          archive it first.
  cancel-issue <issueId>                  Cancel an in-flight (assigned or running) issue and move it back
                                          to backlog. Frees the agent job; does NOT auto-dispatch.
  archive-issue <issueId>                 Archive an issue. For backlog/done this is a pure status flip;
                                          for in-flight issues this also cancels the agent job. Review
                                          items should go through /reject first if you want the workspace
                                          reverted.
  assign-issue <issueId>                  Move a backlog issue with an agent assigned into the dispatch
                                          queue. Starts immediately if the agent is idle.
  ready-issue <issueId>                   Snapshot the agent workspace and move the issue into Review
                                          (the assignee uses this to signal "I'm done, please review").

Issue Comments:
  list-comments <issueId>                 List threaded comments on an issue.
  add-comment <issueId> <text>            Post a comment (1–2000 chars). Notifies assignee, reviewer,
                                          creator, and any @-mentioned workspace members.

Issue Preview (dev-server proxying):
  list-ports                              Alias of list-routes. Use to discover which ports are already
                                          forwarded before picking one for a preview dev server.
  open-preview --issue=<id> --port=<n>    When you started a dev server in preview mode, report its
                                          port to the platform. The Preview tab in the issue drawer
                                          will start iframing it at /preview-{shortIssueId} on your
                                          agent subdomain. The port MUST NOT collide with an existing
                                          rule from list-ports — check first and pick a free one.
  close-preview --issue=<id>              Tear down a preview port forward manually. The platform also
                                          closes it automatically when the issue is marked done.

GitHub:
  list-repos                              List the workspace owner's GitHub repos (requires connected GitHub)
  clone-repo <owner>/<repo> [--ref=...] [--dest=...] [--depth=...]
                                          Clone a GitHub repo into the agent workspace using the workspace owner's
                                          stored OAuth token. Token is stripped from the remote URL after clone.
  open-pr --repo=owner/repo --head=<branch> --title="..." [--base=<branch>] [--body="..."]
                                          Open a pull request (base defaults to the repo default branch).
  get-pr <number> --repo=owner/repo       Fetch a PR's current state (state, mergeable, url).
  list-pr-comments <number> --repo=owner/repo
                                          List a PR's conversation (issue + review comments).
  comment-pr <number> "text" --repo=owner/repo
                                          Post a comment on a PR.
  merge-pr <number> --repo=owner/repo [--method=squash|merge|rebase]
                                          Merge a PR (default merge method).
  close-pr <number> --repo=owner/repo     Close a PR without merging.
  pull --dest=<dir> [--branch=...]        Pull latest into a cloned repo (fast-forward only).
  fetch --dest=<dir> [--branch=...]       Fetch refs into a cloned repo.
  push-branch --dest=<dir> [--branch=...] Push the current (or named) branch of a cloned repo to GitHub.
                                          (GitHub token is injected server-side — never exposed to the agent.)

Other:
  get-token                               Get a short-lived platform JWT (1h)
  help                                    Show this help
`.trim();

const [command, ...rest] = process.argv.slice(2);
const { flags, positional } = parseFlags(rest);

async function main() {
  let result;

  switch (command) {
    // ── Identity & Status (agent subdomain) ────────────────────────────
    case "whoami":
      result = await agentApi("/platform/whoami");
      break;

    case "status":
      result = await agentApi("/status");
      break;

    case "update-metadata": {
      const body = {};
      if (flags.name) body.name = flags.name;
      if (flags.description) body.description = flags.description;
      if (flags.vibe) body.vibe = flags.vibe;
      if (flags.emoji) body.emoji = flags.emoji;
      if (Object.keys(body).length === 0) { console.error("Usage: update-metadata --name=... --description=... --emoji=... --vibe=..."); process.exit(1); }
      result = await agentApi("/platform/metadata", "PATCH", body);
      break;
    }

    case "restart":
      result = await agentApi("/restart", "POST");
      break;

    // ── Skills (mixed: agent subdomain + management domain) ────────────
    case "list-library":
      result = await mgmtApi("/v0/skills");
      break;

    case "list-attached":
      result = await agentApi("/platform/skills/attached");
      break;

    case "browse-hub": {
      const params = new URLSearchParams();
      if (flags.q) params.append("q", flags.q);
      if (flags.category) params.append("category", flags.category);
      if (flags.cursor) params.append("cursor", flags.cursor);
      const qs = params.toString();
      result = await mgmtApi(`/v0/clawhub${qs ? `?${qs}` : ""}`);
      break;
    }

    case "hub-detail": {
      const slug = positional[0] || flags.slug;
      if (!slug) { console.error("Usage: hub-detail <slug>"); process.exit(1); }
      result = await mgmtApi(`/v0/clawhub/${encodeURIComponent(slug)}`);
      break;
    }

    case "install-hub": {
      const slug = positional[0] || flags.slug;
      if (!slug) { console.error("Usage: install-hub <slug>"); process.exit(1); }
      // Hub install uses hubSkillId, but we have slug. Look up the skill first.
      const detail = await mgmtApi(`/v0/clawhub/${encodeURIComponent(slug)}`);
      const hubSkillId = detail?.skill?.hubSkillId || detail?.communitySkill?._id;
      if (!hubSkillId) { console.error(`Skill "${slug}" not found on ClawHub`); process.exit(1); }
      result = await mgmtApi(`/v0/clawhub/${encodeURIComponent(hubSkillId)}/install`, "POST");
      break;
    }

    case "attach": {
      const cids = positional.length > 0 ? positional : (flags.cids ? flags.cids.split(",") : []);
      if (cids.length === 0) { console.error("Usage: attach <cid1> [cid2...]"); process.exit(1); }
      result = await agentApi("/skills", "POST", { skillCids: cids });
      break;
    }

    case "detach": {
      const skillId = positional[0] || flags.skillId;
      if (!skillId) { console.error("Usage: detach <skillId>"); process.exit(1); }
      result = await agentApi(`/skills/${encodeURIComponent(skillId)}`, "DELETE");
      break;
    }

    // ── Secrets (mixed) ────────────────────────────────────────────────
    case "list-secrets":
      result = await mgmtApi("/v0/secrets");
      break;

    case "create-secret": {
      // First positional is the vault path. For flat secrets (no slash) this
      // is identical to the legacy "name". Server defaults `name` to the
      // last path segment when only `path` is provided.
      const path = positional[0];
      const value = positional[1];
      if (!path || !value) { console.error("Usage: create-secret <path> <value> [--name=...] [--type=secret|variable] [--attach] [--mount-as=ENV_VAR_NAME]"); process.exit(1); }
      const body = { path, value, type: flags.type || "secret" };
      if (flags.name) body.name = flags.name;
      const created = await mgmtApi("/v0/secrets", "POST", body);
      const secretId = created?.secret?.id;
      // If --attach, also attach the new secret to this agent
      if (flags.attach && secretId) {
        const mountAs = flags["mount-as"] || flags.mountAs;
        const attachBody = mountAs
          ? { attachments: [{ secretId, mountAs }] }
          : { secretIds: [secretId] };
        await agentApi("/secrets", "POST", attachBody);
        result = { ...created, attached: true, mountAs: mountAs || created?.secret?.name };
      } else {
        result = created;
      }
      break;
    }

    case "attach-secret": {
      const ids = positional.length > 0 ? positional : (flags.ids ? flags.ids.split(",") : []);
      if (ids.length === 0) { console.error("Usage: attach-secret <secretId> [--mount-as=ENV_VAR_NAME]"); process.exit(1); }
      const mountAs = flags["mount-as"] || flags.mountAs;
      if (mountAs && ids.length > 1) {
        console.error("--mount-as can only be used when attaching a single secret. Run the command once per secret.");
        process.exit(1);
      }
      const body = mountAs
        ? { attachments: [{ secretId: ids[0], mountAs }] }
        : { secretIds: ids };
      result = await agentApi("/secrets", "POST", body);
      break;
    }

    case "detach-secret": {
      const secretId = positional[0] || flags.secretId;
      if (!secretId) { console.error("Usage: detach-secret <secretId>"); process.exit(1); }
      result = await agentApi(`/secrets/${encodeURIComponent(secretId)}`, "DELETE");
      break;
    }

    // ── Tasks (management domain — tasks not mounted on per-agent subdomain) ─
    case "list-tasks":
      result = await mgmtApi(`/v0/agents/${AGENT_ID}/tasks`);
      break;

    case "create-task": {
      const name = positional[0] || flags.name;
      if (!name) { console.error("Usage: create-task <name> [--every=...] [--at=...] [--cron=...] [--prompt=...]"); process.exit(1); }
      // Build the schedule object from flags
      const schedule = {};
      if (flags.every) {
        schedule.kind = "every";
        schedule.everyMs = parseDuration(flags.every);
      } else if (flags.at) {
        schedule.kind = "at";
        schedule.at = flags.at;
      } else if (flags.cron) {
        schedule.kind = "cron";
        schedule.expr = flags.cron;
      }
      if (flags.tz) schedule.tz = flags.tz;
      // Build payload
      const payload = { kind: "agentTurn" };
      if (flags.prompt) payload.text = flags.prompt;
      const body = { name, payload };
      if (schedule.kind) body.schedule = schedule;
      if (flags.description) body.description = flags.description;
      result = await mgmtApi(`/v0/agents/${AGENT_ID}/tasks`, "POST", body);
      break;
    }

    case "update-task": {
      const jobId = positional[0] || flags.jobId;
      if (!jobId) { console.error("Usage: update-task <jobId> [--name=...] [--prompt=...] [--every=...] [--at=...] [--cron=...]"); process.exit(1); }
      const body = {};
      if (flags.name) body.name = flags.name;
      if (flags.description) body.description = flags.description;
      // Build schedule if any schedule flag is provided
      if (flags.every || flags.at || flags.cron) {
        const schedule = {};
        if (flags.every) { schedule.kind = "every"; schedule.everyMs = parseDuration(flags.every); }
        else if (flags.at) { schedule.kind = "at"; schedule.at = flags.at; }
        else if (flags.cron) { schedule.kind = "cron"; schedule.expr = flags.cron; }
        if (flags.tz) schedule.tz = flags.tz;
        body.schedule = schedule;
      }
      if (flags.prompt) body.payload = { kind: "agentTurn", text: flags.prompt };
      result = await mgmtApi(`/v0/agents/${AGENT_ID}/tasks/${encodeURIComponent(jobId)}`, "PUT", body);
      break;
    }

    case "delete-task": {
      const jobId = positional[0] || flags.jobId;
      if (!jobId) { console.error("Usage: delete-task <jobId>"); process.exit(1); }
      result = await mgmtApi(`/v0/agents/${AGENT_ID}/tasks/${encodeURIComponent(jobId)}`, "DELETE");
      break;
    }

    case "run-task": {
      const jobId = positional[0] || flags.jobId;
      if (!jobId) { console.error("Usage: run-task <jobId>"); process.exit(1); }
      result = await mgmtApi(`/v0/agents/${AGENT_ID}/tasks/${encodeURIComponent(jobId)}/run`, "POST");
      break;
    }

    case "toggle-task": {
      const jobId = positional[0] || flags.jobId;
      if (!jobId) { console.error("Usage: toggle-task <jobId>"); process.exit(1); }
      result = await mgmtApi(`/v0/agents/${AGENT_ID}/tasks/${encodeURIComponent(jobId)}/toggle`, "POST");
      break;
    }

    // ── Routes / Port Forwarding (agent subdomain) ────────────────────
    case "list-routes":
      result = await agentApi("/port-forwarding");
      break;

    case "open-port": {
      const port = parseInt(positional[0], 10);
      const pathPrefix = positional[1];
      if (!port || !pathPrefix) { console.error("Usage: open-port <port> <pathPrefix> [--protected=true|false]"); process.exit(1); }
      // GET current rules, upsert the new one, PUT back
      const current = await agentApi("/port-forwarding");
      const mappings = (current.mappings || []).filter(m => m.pathPrefix.toLowerCase() !== pathPrefix.toLowerCase());
      const entry = { port, pathPrefix };
      if (flags.protected !== undefined) entry.protected = flags.protected !== "false";
      mappings.push(entry);
      result = await agentApi("/port-forwarding", "PUT", { mappings });
      break;
    }

    case "close-port": {
      const pathPrefix = positional[0] || flags.pathPrefix;
      if (!pathPrefix) { console.error("Usage: close-port <pathPrefix>"); process.exit(1); }
      const current = await agentApi("/port-forwarding");
      const mappings = (current.mappings || []).filter(m => m.pathPrefix.toLowerCase() !== pathPrefix.toLowerCase());
      result = await agentApi("/port-forwarding", "PUT", { mappings });
      break;
    }

    // ── Custom Domains (agent subdomain) ───────────────────────────────
    case "list-domains":
      result = await agentApi("/domains");
      break;

    case "add-subdomain": {
      const port = parseInt(positional[0], 10);
      if (!port) { console.error("Usage: add-subdomain <port> [--subdomain=...] [--protected=true|false]"); process.exit(1); }
      const body = { targetPort: port };
      if (flags.subdomain) body.subdomain = String(flags.subdomain).toLowerCase();
      if (flags.protected !== undefined) body.protected = flags.protected !== "false";
      result = await agentApi("/domains", "POST", body);
      break;
    }

    case "domain-challenge": {
      const domain = positional[0] || flags.domain;
      if (!domain) { console.error("Usage: domain-challenge <domain>"); process.exit(1); }
      result = await agentApi("/domains/challenge", "POST", { customDomain: domain });
      break;
    }

    case "add-domain": {
      const domain = positional[0];
      const port = parseInt(positional[1], 10);
      if (!domain || !port) { console.error("Usage: add-domain <domain> <port> [--protected=true|false]"); process.exit(1); }
      const body = { customDomain: domain, targetPort: port };
      if (flags.protected !== undefined) body.protected = flags.protected !== "false";
      result = await agentApi("/domains", "POST", body);
      break;
    }

    case "verify-domain": {
      const domainId = positional[0] || flags.domainId;
      if (!domainId) { console.error("Usage: verify-domain <domainId>"); process.exit(1); }
      result = await agentApi(`/domains/${encodeURIComponent(domainId)}/verify`, "POST");
      break;
    }

    case "update-domain": {
      const domainId = positional[0] || flags.domainId;
      if (!domainId) { console.error("Usage: update-domain <domainId> [--targetPort=...] [--protected=true|false]"); process.exit(1); }
      const body = {};
      if (flags.targetPort !== undefined) body.targetPort = parseInt(flags.targetPort, 10);
      if (flags.protected !== undefined) body.protected = flags.protected !== "false";
      if (Object.keys(body).length === 0) { console.error("Nothing to update. Pass --targetPort=... or --protected=true|false"); process.exit(1); }
      result = await agentApi(`/domains/${encodeURIComponent(domainId)}`, "PUT", body);
      break;
    }

    case "remove-domain": {
      const domainId = positional[0] || flags.domainId;
      if (!domainId) { console.error("Usage: remove-domain <domainId>"); process.exit(1); }
      result = await agentApi(`/domains/${encodeURIComponent(domainId)}`, "DELETE");
      break;
    }

    // ── Config (agent subdomain) ───────────────────────────────────────
    case "get-config":
      result = await agentApi("/config");
      break;

    case "set-config": {
      const json = positional[0];
      if (!json) { console.error("Usage: set-config '<json>'"); process.exit(1); }
      // Validate it's valid JSON, then send as a string (route expects { config: string })
      try { JSON.parse(json); } catch { console.error("Invalid JSON"); process.exit(1); }
      result = await agentApi("/config", "PUT", { config: json });
      break;
    }

    // ── Console (agent subdomain) ──────────────────────────────────────
    case "exec": {
      const cmd = positional.join(" ");
      if (!cmd) { console.error("Usage: exec <command>"); process.exit(1); }
      result = await agentApi("/console/exec", "POST", { command: cmd });
      break;
    }

    // ── Channels (agent subdomain) ─────────────────────────────────────
    case "list-channels":
      result = await agentApi("/channels");
      break;

    case "add-channel": {
      const channel = positional[0];
      const json = positional[1] || flags.config;
      if (!channel) { console.error("Usage: add-channel <type> '<configJson>' (type: telegram, discord, slack, whatsapp)"); process.exit(1); }
      let config = {};
      if (json) {
        try { config = JSON.parse(json); } catch { console.error("Invalid JSON config"); process.exit(1); }
      }
      // Pass individual flags as config if no JSON provided
      if (!json) {
        if (flags.botToken) config.botToken = flags.botToken;
        if (flags.webhookUrl) config.webhookUrl = flags.webhookUrl;
        if (flags.token) config.token = flags.token;
      }
      result = await agentApi(`/channels/${encodeURIComponent(channel)}`, "POST", config);
      break;
    }

    case "remove-channel": {
      const channel = positional[0] || flags.channel;
      if (!channel) { console.error("Usage: remove-channel <type> (telegram, discord, slack, whatsapp)"); process.exit(1); }
      result = await agentApi(`/channels/${encodeURIComponent(channel)}`, "DELETE");
      break;
    }

    // ── Agents (management domain) ─────────────────────────────────────
    case "list-agents":
      result = await mgmtApi("/v0/agents");
      break;

    case "create-agent": {
      const name = positional[0];
      if (!name) { console.error("Usage: create-agent <name> [--description=...] [--emoji=...] [--templateId=...]"); process.exit(1); }
      const body = { name };
      if (flags.description) body.description = flags.description;
      if (flags.vibe) body.vibe = flags.vibe;
      if (flags.emoji) body.emoji = flags.emoji;
      if (flags.templateId) body.templateId = flags.templateId;
      result = await mgmtApi("/v0/agents", "POST", body);
      break;
    }

    // ── Templates (management domain) ──────────────────────────────────
    case "list-templates": {
      const params = new URLSearchParams();
      if (flags.category) params.append("category", flags.category);
      const qs = params.toString();
      result = await mgmtApi(`/v0/templates${qs ? `?${qs}` : ""}`);
      break;
    }

    case "submit-template": {
      const gitUrl = positional[0];
      if (!gitUrl) { console.error("Usage: submit-template <gitUrl> [--branch=...] [--path=...]"); process.exit(1); }
      const body = { gitUrl };
      if (flags.branch) body.branch = flags.branch;
      if (flags.path) body.path = flags.path;
      if (flags.name) body.nameOverride = flags.name;
      if (flags.slug) body.slugOverride = flags.slug;
      result = await mgmtApi("/v0/templates", "POST", body);
      break;
    }

    case "get-template": {
      const slug = positional[0] || flags.slug;
      if (!slug) { console.error("Usage: get-template <slug>"); process.exit(1); }
      result = await mgmtApi(`/v0/templates/${encodeURIComponent(slug)}`);
      break;
    }

    case "validate-template": {
      const gitUrl = positional[0] || flags.gitUrl;
      if (!gitUrl) { console.error("Usage: validate-template <gitUrl> [--ref=...] [--path=...]"); process.exit(1); }
      const body = { gitUrl };
      if (flags.ref) body.ref = flags.ref;
      if (flags.branch) body.ref = flags.branch; // alias
      if (flags.path) body.path = flags.path;
      result = await mgmtApi("/v0/templates/validate", "POST", body);
      break;
    }

    // ── Boards (management domain) — issue grouping ───────────────────
    case "list-boards":
      result = await mgmtApi("/v0/issues/boards");
      break;

    case "create-board": {
      const name = positional[0] || flags.name;
      if (!name) { console.error("Usage: create-board <name> [--description=...]"); process.exit(1); }
      const body = { name };
      if (flags.description !== undefined) body.description = flags.description;
      result = await mgmtApi("/v0/issues/boards", "POST", body);
      break;
    }

    case "update-board": {
      const boardId = positional[0] || flags.boardId;
      if (!boardId) { console.error("Usage: update-board <boardId> [--name=...] [--description=...]"); process.exit(1); }
      const body = {};
      if (flags.name !== undefined) body.name = flags.name;
      if (flags.description !== undefined) body.description = flags.description === "" ? null : flags.description;
      if (Object.keys(body).length === 0) { console.error("Nothing to update. Pass --name=... or --description=..."); process.exit(1); }
      result = await mgmtApi(`/v0/issues/boards/${encodeURIComponent(boardId)}`, "PATCH", body);
      break;
    }

    case "delete-board": {
      const boardId = positional[0] || flags.boardId;
      if (!boardId) { console.error("Usage: delete-board <boardId>"); process.exit(1); }
      result = await mgmtApi(`/v0/issues/boards/${encodeURIComponent(boardId)}`, "DELETE");
      break;
    }

    // ── Issues (management domain) — the agent-to-agent surface ────────
    case "list-issues": {
      const params = new URLSearchParams();
      if (flags.agentId) params.append("agentId", flags.agentId);
      if (flags.boardId) params.append("boardId", flags.boardId);
      if (flags.status) params.append("status", flags.status);
      const qs = params.toString();
      result = await mgmtApi(`/v0/issues${qs ? `?${qs}` : ""}`);
      break;
    }

    case "create-issue": {
      // Used for agent-to-agent delegation: agent A creates an issue
      // assigned to agent B, and the cron dispatcher picks it up on
      // behalf of B. Title + prompt are required; agentId defaults to
      // SELF (which would just re-run the caller, so callers will
      // almost always pass --agentId for a sibling).
      const title = flags.title || positional[0];
      const prompt = flags.prompt || positional[1];
      if (!title || !prompt) {
        console.error("Usage: create-issue <title> <prompt> [--agentId=...] [--boardId=...] [--tags=tag1,tag2] [--repoUrl=...] [--no-repo]");
        process.exit(1);
      }
      // Require an explicit repo decision. Without this, ambiguous prompts
      // ("fix the login bug") slipped through with repoUrl=null; the
      // assignee then ad-libbed into stale leftover clones in the workspace
      // and the outer snapshot captured nothing, producing silent "No
      // changes" reviews. Force the caller to either name a repo or opt
      // out explicitly with --no-repo.
      if (!flags.repoUrl && !flags["no-repo"]) {
        let repos = [];
        try {
          const r = await mgmtApi(`/v0/agents/${AGENT_ID}/github/repos`);
          repos = Array.isArray(r?.data?.repos) ? r.data.repos
                : Array.isArray(r?.repos) ? r.repos
                : Array.isArray(r?.data) ? r.data
                : [];
        } catch (_) { /* fall through with empty list */ }
        const lines = repos.slice(0, 20).map((r) => `  - ${r.full_name || r.fullName || `${r.owner?.login || r.owner}/${r.name}`}: ${r.html_url || r.htmlUrl || `https://github.com/${r.full_name || r.fullName}`}`);
        console.error([
          "create-issue requires an explicit repo choice. Pass one of:",
          "  --repoUrl=https://github.com/<owner>/<repo>   (issue will be worked on against that repo)",
          "  --no-repo                                      (workspace-only issue, no clone, no PR)",
          "",
          repos.length > 0
            ? `Connected GitHub repos for this workspace (${repos.length}):`
            : "No GitHub repos connected to this workspace — either connect one via the management UI or pass --no-repo.",
          ...lines,
          repos.length > 20 ? `  (+${repos.length - 20} more — run \`list-repos\` to see all)` : "",
          "",
          "If the user's request is ambiguous about which repo to target, ask them before re-invoking.",
        ].filter(Boolean).join("\n"));
        process.exit(2);
      }
      const body = { title, prompt };
      if (flags.agentId) body.agentId = flags.agentId;
      else body.agentId = AGENT_ID; // explicit so the response surfaces it
      if (flags.boardId) body.boardId = flags.boardId;
      if (flags.tags) body.tags = flags.tags.split(",").map((t) => t.trim()).filter(Boolean);
      if (flags.repoUrl) body.repoUrl = flags.repoUrl;
      if (flags.skipAutoDispatch) body.skipAutoDispatch = true;
      if (flags.previewRequested) body.previewRequested = true;
      result = await mgmtApi("/v0/issues", "POST", body);
      break;
    }

    case "get-issue": {
      const issueId = positional[0] || flags.issueId;
      if (!issueId) { console.error("Usage: get-issue <issueId>"); process.exit(1); }
      result = await mgmtApi(`/v0/issues/${encodeURIComponent(issueId)}`);
      break;
    }

    case "update-issue": {
      const issueId = positional[0] || flags.issueId;
      if (!issueId) {
        console.error("Usage: update-issue <issueId> [--title=...] [--prompt=...] [--agentId=...] [--repoUrl=...] [--priority=low|medium|high|urgent] [--dueAt=<iso8601>] [--previewUrlOverride=...] [--assigneeUserId=...] [--assigneeName=...]");
        process.exit(1);
      }
      const body = {};
      // Pass-through string fields. Empty-string flags map to `null` for the
      // nullable columns so callers can clear them (matches the route's
      // nullable schema for agentId / repoUrl / previewUrlOverride / dueAt /
      // assignee*). title and prompt aren't nullable on the server side.
      if (flags.title !== undefined) body.title = flags.title;
      if (flags.prompt !== undefined) body.prompt = flags.prompt;
      if (flags.agentId !== undefined) body.agentId = flags.agentId === "" ? null : flags.agentId;
      if (flags.repoUrl !== undefined) body.repoUrl = flags.repoUrl === "" ? null : flags.repoUrl;
      if (flags.previewUrlOverride !== undefined) body.previewUrlOverride = flags.previewUrlOverride === "" ? null : flags.previewUrlOverride;
      if (flags.dueAt !== undefined) body.dueAt = flags.dueAt === "" ? null : flags.dueAt;
      if (flags.priority !== undefined) body.priority = flags.priority;
      if (flags.assigneeUserId !== undefined) body.assigneeUserId = flags.assigneeUserId === "" ? null : flags.assigneeUserId;
      if (flags.assigneeName !== undefined) body.assigneeName = flags.assigneeName === "" ? null : flags.assigneeName;
      if (flags.assigneeImageUrl !== undefined) body.assigneeImageUrl = flags.assigneeImageUrl === "" ? null : flags.assigneeImageUrl;
      if (Object.keys(body).length === 0) {
        console.error("Nothing to update. Pass at least one flag (--title=, --prompt=, --priority=, --dueAt=, etc.)");
        process.exit(1);
      }
      result = await mgmtApi(`/v0/issues/${encodeURIComponent(issueId)}`, "PATCH", body);
      break;
    }

    case "delete-issue": {
      const issueId = positional[0] || flags.issueId;
      if (!issueId) { console.error("Usage: delete-issue <issueId>"); process.exit(1); }
      result = await mgmtApi(`/v0/issues/${encodeURIComponent(issueId)}`, "DELETE");
      break;
    }

    case "cancel-issue": {
      const issueId = positional[0] || flags.issueId;
      if (!issueId) { console.error("Usage: cancel-issue <issueId>"); process.exit(1); }
      result = await mgmtApi(`/v0/issues/${encodeURIComponent(issueId)}/cancel`, "POST");
      break;
    }

    case "archive-issue": {
      const issueId = positional[0] || flags.issueId;
      if (!issueId) { console.error("Usage: archive-issue <issueId>"); process.exit(1); }
      result = await mgmtApi(`/v0/issues/${encodeURIComponent(issueId)}/archive`, "POST");
      break;
    }

    case "assign-issue": {
      const issueId = positional[0] || flags.issueId;
      if (!issueId) { console.error("Usage: assign-issue <issueId>"); process.exit(1); }
      result = await mgmtApi(`/v0/issues/${encodeURIComponent(issueId)}/assign`, "POST");
      break;
    }

    case "ready-issue": {
      const issueId = positional[0] || flags.issueId;
      if (!issueId) { console.error("Usage: ready-issue <issueId>"); process.exit(1); }
      result = await mgmtApi(`/v0/issues/${encodeURIComponent(issueId)}/ready`, "POST");
      break;
    }

    // ── Issue Comments (management domain) ─────────────────────────────
    case "list-comments": {
      const issueId = positional[0] || flags.issueId;
      if (!issueId) { console.error("Usage: list-comments <issueId>"); process.exit(1); }
      result = await mgmtApi(`/v0/issues/${encodeURIComponent(issueId)}/comments`);
      break;
    }

    case "add-comment": {
      const issueId = positional[0] || flags.issueId;
      // Allow either `add-comment <issueId> <text...>` or `--text=...`.
      const text = flags.text !== undefined ? flags.text : positional.slice(1).join(" ");
      if (!issueId || !text) { console.error("Usage: add-comment <issueId> <text>  (or --text=\"...\")"); process.exit(1); }
      result = await mgmtApi(`/v0/issues/${encodeURIComponent(issueId)}/comments`, "POST", { text });
      break;
    }

    // ── Issue Preview (dev-server proxying) ────────────────────────────
    // Used when an issue was filed with "Generate preview" enabled. The
    // agent inspects what ports are already forwarded, starts its dev
    // server on a free port, and calls `open-preview` with that port so
    // the platform reserves an HTTPRoute prefix and the Preview tab in
    // the issue drawer starts working.
    case "list-ports": {
      // Convenience alias of list-routes — the agent prompt for preview
      // mode calls this name explicitly so it's discoverable.
      result = await agentApi("/port-forwarding");
      break;
    }

    case "open-preview": {
      const issueId = flags.issue || flags.issueId || positional[0];
      const portArg = flags.port || positional[1];
      const port = parseInt(portArg, 10);
      if (!issueId || !port) {
        console.error("Usage: open-preview --issue=<issueId> --port=<n>  (or positional: open-preview <issueId> <port>)");
        process.exit(1);
      }
      result = await mgmtApi(`/v0/issues/${issueId}/preview/open`, "POST", { port });
      break;
    }

    case "close-preview": {
      const issueId = flags.issue || flags.issueId || positional[0];
      if (!issueId) {
        console.error("Usage: close-preview --issue=<issueId>  (or positional: close-preview <issueId>)");
        process.exit(1);
      }
      result = await mgmtApi(`/v0/issues/${issueId}/preview/close`, "POST");
      break;
    }

    // ── GitHub (management domain) ─────────────────────────────────────
    case "list-repos": {
      result = await mgmtApi(`/v0/agents/${AGENT_ID}/github/repos`);
      break;
    }

    case "clone-repo": {
      // Accept either `clone-repo <owner>/<repo>` or `clone-repo <owner> <repo>`.
      let owner, repo;
      if (positional[0]?.includes("/")) {
        [owner, repo] = positional[0].split("/", 2);
      } else {
        owner = positional[0];
        repo = positional[1];
      }
      if (!owner || !repo) { console.error("Usage: clone-repo <owner>/<repo> [--ref=...] [--dest=...] [--depth=...]"); process.exit(1); }
      const body = { owner, repo };
      if (flags.ref) body.ref = flags.ref;
      if (flags.dest) body.dest = flags.dest;
      if (flags.depth) body.depth = Number(flags.depth);
      result = await mgmtApi(`/v0/agents/${AGENT_ID}/github/clone`, "POST", body);
      break;
    }

    // ── GitHub pull requests ───────────────────────────────────────────
    case "open-pr": {
      const { owner, repo } = resolveRepo(flags, 'Usage: open-pr --repo=owner/repo --head=<branch> --title="..." [--base=<branch>] [--body="..."]');
      const head = flags.head || positional[0];
      const title = flags.title;
      if (!head || !title) { console.error('Usage: open-pr --repo=owner/repo --head=<branch> --title="..." [--base=<branch>] [--body="..."]'); process.exit(1); }
      const body = { owner, repo, head, title };
      if (flags.base) body.base = flags.base;
      if (flags.body) body.body = flags.body;
      result = await mgmtApi(`/v0/agents/${AGENT_ID}/github/pr`, "POST", body);
      break;
    }

    case "get-pr": {
      const num = positional[0] || flags.number;
      if (!num) { console.error("Usage: get-pr <number> --repo=owner/repo"); process.exit(1); }
      const { owner, repo } = resolveRepo(flags, "Usage: get-pr <number> --repo=owner/repo");
      result = await mgmtApi(`/v0/agents/${AGENT_ID}/github/pr/${encodeURIComponent(num)}?owner=${encodeURIComponent(owner)}&repo=${encodeURIComponent(repo)}`);
      break;
    }

    case "list-pr-comments": {
      const num = positional[0] || flags.number;
      if (!num) { console.error("Usage: list-pr-comments <number> --repo=owner/repo"); process.exit(1); }
      const { owner, repo } = resolveRepo(flags, "Usage: list-pr-comments <number> --repo=owner/repo");
      result = await mgmtApi(`/v0/agents/${AGENT_ID}/github/pr/${encodeURIComponent(num)}/comments?owner=${encodeURIComponent(owner)}&repo=${encodeURIComponent(repo)}`);
      break;
    }

    case "comment-pr": {
      const num = positional[0] || flags.number;
      const text = positional[1] || flags.body;
      if (!num || !text) { console.error('Usage: comment-pr <number> "comment text" --repo=owner/repo'); process.exit(1); }
      const { owner, repo } = resolveRepo(flags, 'Usage: comment-pr <number> "comment text" --repo=owner/repo');
      result = await mgmtApi(`/v0/agents/${AGENT_ID}/github/pr/${encodeURIComponent(num)}/comment`, "POST", { owner, repo, body: text });
      break;
    }

    case "merge-pr": {
      const num = positional[0] || flags.number;
      if (!num) { console.error("Usage: merge-pr <number> --repo=owner/repo [--method=squash|merge|rebase]"); process.exit(1); }
      const { owner, repo } = resolveRepo(flags, "Usage: merge-pr <number> --repo=owner/repo [--method=squash|merge|rebase]");
      const body = { owner, repo };
      if (flags.method) body.method = flags.method;
      result = await mgmtApi(`/v0/agents/${AGENT_ID}/github/pr/${encodeURIComponent(num)}/merge`, "POST", body);
      break;
    }

    case "close-pr": {
      const num = positional[0] || flags.number;
      if (!num) { console.error("Usage: close-pr <number> --repo=owner/repo"); process.exit(1); }
      const { owner, repo } = resolveRepo(flags, "Usage: close-pr <number> --repo=owner/repo");
      result = await mgmtApi(`/v0/agents/${AGENT_ID}/github/pr/${encodeURIComponent(num)}/close`, "POST", { owner, repo });
      break;
    }

    case "pull":
    case "fetch":
    case "push-branch": {
      const dest = flags.dest || positional[0];
      if (!dest) { console.error(`Usage: ${command} --dest=<cloned-repo-dir> [--branch=<branch>]`); process.exit(1); }
      const action = command === "push-branch" ? "push" : command;
      const body = { action, dest };
      if (flags.branch) body.branch = flags.branch;
      result = await mgmtApi(`/v0/agents/${AGENT_ID}/github/git`, "POST", body);
      break;
    }

    // ── Other ──────────────────────────────────────────────────────────
    case "get-token": {
      result = await agentApi("/platform/token", "POST");
      break;
    }

    case "help":
    case "--help":
    case "-h":
      console.log(HELP);
      return;

    default:
      console.error(`Unknown command: ${command || "(none)"}\n`);
      console.log(HELP);
      process.exit(1);
  }

  console.log(JSON.stringify(result, null, 2));
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
