# OpenBacklog

**Free, open-source task management built for solo developers.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688.svg)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6+-blue.svg)](https://www.typescriptlang.org/)

## What is OpenBacklog?

OpenBacklog is a self-hosted project management tool designed for solo developers who want structure without the overhead of enterprise tools.

**Core Features:**
- **Task & Initiative Management** - Organize work into initiatives with tasks, checklists, and status tracking
- **Strategic Planning** - Define your Vision, Strategic Pillars, Outcomes, and Roadmap Themes
- **Narrative-Driven Development** - Frame your work as a story with Heroes (users), Villains (problems), and Conflicts to resolve
- **MCP Integration** - Bring your own AI via Claude Code, Cursor, or any MCP-compatible tool

**No built-in AI, no subscriptions** - OpenBacklog is a self-hosted tool that works with your existing AI subscriptions via the Model Context Protocol (MCP).

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/openbacklog/openbacklog.git
cd openbacklog

# Start the services
docker-compose up

# Access the app
open http://localhost:8000
```

### Connect Your AI

OpenBacklog uses the Model Context Protocol (MCP) to integrate with AI tools you already use. See [docs/MCP_SETUP.md](docs/MCP_SETUP.md) for setup instructions.

## Architecture

OpenBacklog is built with a minimal, self-hostable stack:

**Backend:**
- **FastAPI** - Python API server
- **PostgreSQL** - Primary database
- **PostgREST** - Additional REST API layer
- **SQLAlchemy** - ORM with Alembic migrations
- **Auth0** - Authentication (optional, can self-host)

**Frontend:**
- **React 18** - UI with TypeScript
- **Tailwind CSS** - Styling
- **Webpack** - Asset bundling

**Key Directories:**
- `/src/` - Python backend
- `/static/react-components/` - React frontend
- `/tests/` - Test suite
- `/alembic/` - Database migrations

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Before Submitting a PR

```bash
# Python formatting and tests
black --check --diff src/ tests/
ENVIRONMENT=test pytest --cov=src

# React tests and TypeScript compilation
cd static/react-components
npm run test
npm run compile
```

### Code Style References
- [`CLAUDE.md`](./CLAUDE.md) - Development guidelines
- [`CONVENTIONS.md`](./CONVENTIONS.md) - Python conventions
- [`static/react-components/CLAUDE.md`](./static/react-components/CLAUDE.md) - Frontend guidelines

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built for solo developers who ship.**
