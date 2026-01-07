# OpenBacklog

OpenBacklog is where you plan your product before you code.

Figure out what you're building and why. Define who it's for and what problems you're solving. Break it into projects and tasks. It's the product thinking teams often rely on PMs for, simplified for solo developers.

Your AI assistant connects via MCP. Not just to pull context when coding, but to help you think through what to build, reason about priorities, and flesh out ideas before you commit to them.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Tests](https://github.com/SamBoyd/OpenBacklog/actions/workflows/python-tests.yml/badge.svg)](https://github.com/SamBoyd/OpenBacklog/actions/workflows/python-tests.yml)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://reactjs.org/)
![Status: Alpha](https://img.shields.io/badge/status-alpha-orange)

<p align="center">
  <img src="static/screenshot.png" alt="OpenBacklog Screenshot" width="800" />
</p>

**[Documentation](https://docs.openbacklog.ai)** · **[Quickstart](https://docs.openbacklog.ai/quickstart)** · **[MCP Setup](https://docs.openbacklog.ai/mcp-integration/claude-code)**

---

## What does using it look like?

1. **Define what you're building** — Write down your goal, who it's for, and what problems you're solving.

2. **Break it into projects** — Each project is a chunk of work that moves your goal forward. Prioritize them.

3. **Add tasks** — Each task belongs to a project, so you always know *why* you're doing the work.

4. **Connect your AI** — Via MCP, your AI can read your plan, help you decide what's worth building, and understand the full context when you're coding.

## Features

- **Strategic Planning** — Define vision, pillars, outcomes, and themes. Think like a PM without being one.
- **Problem-First Planning** — Start with who you're building for and what problems they face.
- **MCP Integration** — Connect Claude Code, Cursor, or any MCP-compatible AI. No vendor lock-in.
- **Self-Hosted** — Your data stays on your machine. No tracking, no ads, no subscriptions.


## How OpenBacklog is different (in practice)

Most project tools start with tasks. OpenBacklog starts with intent.

**In practice, this means:**

- **Work flows top-down, not as a flat list**

  You define a vision, break it into strategic bets then into initiatives. Tasks always belong to a higher-level goal, so you don’t end up with an unprioritized backlog of disconnected tickets.

- **Every task has context by default**

  Tasks carry the “why” (initiative, rationale, constraints) alongside the “what”. You don’t have to reconstruct intent weeks later or keep it in a separate doc.

- **Planning and execution stay close to code**

  OpenBacklog exposes a full API and MCP interface, so you can generate, refine, and update work items directly from your editor or AI tools (Claude, Cursor, etc.) instead of switching between apps.

- **Designed for solo developers, not teams**
  
  No sprints, story points, standups, or permission systems. The model assumes one person making decisions and writing code, and optimizes for focus rather than coordination.

- **Self-hosted and vendor-agnostic**
  
  Your data stays local. You choose which AI tools (if any) to connect. OpenBacklog works without requiring accounts, cloud services, or proprietary workflows.

## Quick Start

```bash
git clone https://github.com/samboyd/openbacklog.git
cd openbacklog
docker compose --env-file .env.cluster-dev up
```

Open http://localhost:8000 to get started.

See the [Quickstart Guide](https://docs.openbacklog.ai/quickstart) for detailed setup and [Claude Code Setup](https://docs.openbacklog.ai/mcp-integration/claude-code) to connect your AI.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## License

[MIT License](LICENSE)
