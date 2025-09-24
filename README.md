# OpenBacklog

**AI-powered task management built specifically for solo developers.**

You spend more time deciding what to work on than actually coding. Your brilliant feature ideas get lost in a maze of half-finished tasks and forgotten priorities. OpenBacklog empowers solo developers with intelligent project management that understands your workflow and keeps you in flow state.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Tests](https://github.com/samboyd/OpenBacklog/actions/workflows/python-tests.yml/badge.svg)](https://github.com/samboyd/OpenBacklog/actions/workflows/python-tests.yml)
[![TypeScript Tests](https://github.com/samboyd/OpenBacklog/actions/workflows/typescript-tests.yml/badge.svg)](https://github.com/samboyd/OpenBacklog/actions/workflows/typescript-tests.yml)
[![Security Scan](https://github.com/samboyd/OpenBacklog/actions/workflows/gitleaks.yml/badge.svg)](https://github.com/samboyd/OpenBacklog/actions/workflows/gitleaks.yml)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688.svg)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6+-blue.svg)](https://www.typescriptlang.org/)

## 🎬 See It In Action

**SCENE: A Solo Developer's Morning**

*Developer opens OpenBacklog, sees a cluttered backlog of 23 tasks*

**Developer:** "I have no idea what to work on next. This feature request is huge..."

*Types in chat:* "Help me break down 'Add user authentication system' into manageable tasks"

**AI Assistant:** *Immediately updates the task card with 6 specific subtasks: Set up Auth0, Create login component, Add middleware, etc.*

*Developer clicks "Start Coding" and OpenBacklog data flows seamlessly into Claude Code*

**Claude Code:** "I can see from OpenBacklog that you're working on authentication. I've pulled your task context - let's implement the Auth0 setup first."

*Cut to: Developer coding in flow state, with AI assistance grounded in their actual project goals*

---

**SCENE: Feature Planning Made Simple**

*Developer has a brilliant idea mid-coffee*

**Developer:** *Types quickly:* "Add real-time collaboration for task comments"

**AI Assistant:** *Instantly analyzes the existing codebase and creates a complete implementation plan with technical considerations, effort estimates, and prerequisite tasks*

*The new feature automatically slots into the backlog at the right priority level*

---

*This is the OpenBacklog experience: AI that actually understands your project, seamlessly integrated with your coding workflow.*

## 🎯 Why OpenBacklog?

**Built for Solo Developers, Not Teams**
- Simple, uncluttered interface focused on your backlog and your code
- No cluttered enterprise features you'll never use
- AI-assisted product management giving you the capacity of a much bigger team
- Claude code integration keeps you in your workflow
- Opinionated tools that nudge you toward best practices

**Key Features:**
- 🤖 **AI Product Management** - Get intelligent suggestions for task breakdown and project planning
- 🎯 **Solo-First Design** - Clean, focused interface without team management overhead
- 📚 **Best Practice Guidance** - AI mentorship helping you grow and build better
- 🔗 **Developer Workflow Integration** - Seamless connection with your existing development process

## 🌐 Open Source & Transparency

OpenBacklog is a **paid SaaS service** that I've open-sourced for complete transparency. I believe developers should be able to audit the code they rely on, understand how their data is handled, and contribute to the tools they use daily.

**This repository enables you to:**
- 🔍 Audit the codebase for security and privacy practices
- 🛠️ Run tests and contribute improvements via pull requests
- 📖 Understand the architecture and implementation details
- 🤝 Join a community of developers building better tools together

> **Note**: This codebase represents the full production application but is intended for transparency and contribution rather than self-hosting. I hope to simplify the infrastructure for self-hosting in the future. The live service is available at [openbacklog.com](https://openbacklog.com).

## 🚀 Quick Start

### For Users: Get Started in 3 Minutes

1. **Sign up** at [openbacklog.com](https://openbacklog.com)
2. **Create your first workspace** and project
3. **Set up Claude Code integration** with the mcp tools
4. **Start chatting with AI** to break down your first big feature
5. **Get Coding** by asking ClaudeCode to "pick up some work from OpenBacklog"

*That's it! Your AI-powered development workflow is ready.*

### For Contributors: Development Setup

Want to contribute or run tests? Here's how to get set up:

#### Prerequisites

- **Python 3.12** (recommended, 3.8+ supported) with pip
- **Node.js 18+** with npm
- **PostgreSQL 16+** (for running tests with database)
- **Git** for version control

> **Note**: The GitHub Actions workflows test against Python 3.12 and Node.js 22, so using these versions is recommended for the most consistent experience.

#### 1. Clone and Install Dependencies

```bash
git clone https://github.com/samboyd/OpenBacklog.git
cd OpenBacklog

# Install Python dependencies
pip install -r requirements.txt

# Install root npm dependencies
npm install

# Install React app dependencies
cd static/react-components
npm install
cd ../..
```

#### 2. Build Static Assets

```bash
# Build all static assets using the provided script
chmod +x scripts/build_static_files.sh
./scripts/build_static_files.sh
```

#### 3. Set Up Test Environment

```bash
# Install development dependencies (includes testing tools)
pip install -r requirements-dev.txt

# Set up test database (requires PostgreSQL)
./scripts/bootstrap_blank_test_database.sh
```

#### 4. Run Tests

```bash
# Run Python backend tests with coverage
ENVIRONMENT=test pytest --cov=src --cov-report=term-missing

# Run code formatting checks
black --check --diff src/ tests/
isort --check-only --diff src/ tests/

# Run React frontend tests
cd static/react-components
npm run test

# Run TypeScript compilation check
npm run compile
```

#### 5. Development Workflow

```bash
# Format Python code
black src/ tests/
isort src/ tests/

# Build and watch React components during development
cd static/react-components
npm run build:watch
```

## 🏗️ Architecture Overview

OpenBacklog is built with a modern, scalable architecture:

**Backend (Python)**
- **FastAPI** - High-performance API server
- **PostgreSQL** - Primary database with advanced querying
- **SQLAlchemy** - ORM with Alembic migrations
- **LangChain** - AI/LLM integration framework
- **Stripe** - Payment processing
- **Auth0** - Authentication and user management

**Frontend (React)**
- **React 18** - Modern UI with hooks and functional components
- **TypeScript** - Type safety throughout the frontend
- **Tailwind CSS** - Utility-first styling system
- **Webpack** - Asset bundling and optimization
- **Storybook** - Component development and testing

**Key Directories:**
- `/src/` - Python backend source code
- `/static/react-components/` - React frontend application
- `/tests/` - Python test suite
- `/scripts/` - Build and deployment scripts
- `/alembic/` - Database migrations

## 🤝 Contributing

Contributions are very welcome! Here's how to get involved:

#### Before You Submit a PR

1. **Run the full test suite** to ensure your changes don't break existing functionality:
   ```bash
   # Python tests with formatting checks
   ENVIRONMENT=test pytest --cov=src --cov-report=term-missing
   black --check --diff src/ tests/
   isort --check-only --diff src/ tests/

   # React tests with TypeScript compilation
   cd static/react-components
   npm run test
   npm run compile
   ```

2. **Follow code style** - Code must pass all formatting checks
3. **Update tests** when adding new features
4. **Keep commits focused** - One logical change per commit
5. **Test with PostgreSQL** - Ensure database tests pass locally

#### Development Guidelines

**Python Backend:**
- Follow PEP 8, use `black` for formatting with `isort` for imports
- Write tests for new endpoints and business logic
- Use type hints and maintain SQLAlchemy model consistency
- Follow existing patterns for FastAPI routes and dependency injection

**React Frontend:**
- Use TypeScript with strict mode enabled
- Functional components with hooks (no class components)
- Follow existing patterns in `static/react-components/`
- Maintain Tailwind CSS consistency
- Use existing import aliases (`#api/*`, `#hooks/*`, `#components/*`)

**Database Changes:**
- Create Alembic migrations for schema changes
- Test migrations both up and down
- Ensure test database setup scripts are updated if needed

#### Troubleshooting

**Test Database Issues:**
```bash
# Reset test database if needed
./scripts/bootstrap_blank_test_database.sh
```

**Asset Build Issues:**
```bash
# Clean rebuild of all assets
rm -rf static/react-components/dist
./scripts/build_static_files.sh
```

**Import/Module Issues:**
```bash
# Ensure Python path is set correctly
export PYTHONPATH=.
```

#### Code Style References

- [`CLAUDE.md`](./CLAUDE.md) - Comprehensive development guidelines and workflow
- [`CONVENTIONS.md`](./CONVENTIONS.md) - Python backend coding conventions
- [`static/react-components/CLAUDE.md`](./static/react-components/CLAUDE.md) - React frontend guidelines
- [`static/react-components/CONVENTIONS.md`](./static/react-components/CONVENTIONS.md) - Frontend-specific conventions
- [`.github/workflows/`](./.github/workflows/) - GitHub Actions CI/CD definitions

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Live Application**: [openbacklog.com](https://openbacklog.com)
- **Issues**: Report bugs and request features
- **Discussions**: Join the community conversation

---

**Built with ❤️ for the solo developer community**

*OpenBacklog empowers you to redefine what's possible, creating AI-driven solutions that reflect your personal passions and enrich lives.*