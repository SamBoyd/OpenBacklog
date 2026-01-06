# OpenBacklog

**Product management for solo developers.** OpenBacklog is a strategic planning layer that helps you decide what to build next, not just track tasks. It structures vision, product thinking, initiatives, and priorities into actionable work, while letting you connect your own AI tools via MCP for planning and execution.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688.svg)](https://fastapi.tiangolo.com/)

<p align="center">
  <img src="static/screenshot.png" alt="OpenBacklog Screenshot" width="800" />
</p>

**[Documentation](https://docs.openbacklog.ai)** · **[Quickstart](https://docs.openbacklog.ai/quickstart)** · **[MCP Setup](https://docs.openbacklog.ai/mcp-integration/claude-code)**

---

## Overview

Most developer tools focus on task execution. OpenBacklog adds the product management layer solo developers are missing.

No built-in AI. OpenBacklog is an MCP server + UI so you can use your own model/tool (Claude Code, Cursor, etc.).”

| | Task Management Tools | OpenBacklog |
|---|---|---|
| **Focus** | Execute tasks from a list | Decide what to build and why |
| **Planning** | PRDs → Tasks | Vision → Strategy → Roadmap → Tasks |
| **AI Integration** | Built-in AI (subscription) | Bring your own AI via MCP |
| **Data** | Cloud-hosted | Self-hosted, you own it |
| **Cost** | Per-seat pricing | Free and open source |

## Features

- **Strategic Planning** — Define vision, pillars, outcomes, and themes. Think like a PM without being one.
- **Problem-First Planning** — Start with who you're building for and what problems they face.
- **MCP Integration** — Connect Claude Code, Cursor, or any MCP-compatible AI. No vendor lock-in.
- **Self-Hosted** — Your data stays on your machine. No tracking, no ads, no subscriptions.
- **Full API** — REST API for custom integrations and automation.


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
