# Contributing to OpenBacklog

Welcome to OpenBacklog! We're excited that you're interested in contributing to our open-source AI-powered task management platform for solo developers.

This guide will help you get started with contributing code, reporting issues, and submitting pull requests.

## 🚀 Quick Start for Contributors

### Prerequisites

- **Docker** and **Docker Compose** (for running the application)
- **Python 3.12** (recommended, 3.8+ supported) with pip (for running tests/linters locally)
- **Node.js 18+** with npm (for running frontend tests locally)
- **Git** for version control

> **Note**: The application runs in Docker containers. Python and Node.js are only needed locally for running tests and linters.

### 1. Clone the Repository

```bash
git clone https://github.com/samboyd/OpenBacklog.git OpenBacklogContrib
cd OpenBacklogContrib
```

### 2. Set Up Your Development Cluster

OpenBacklog uses Docker Compose for local development:

```bash
# One-time setup - creates .env.cluster-dev
./scripts/setup-cluster.sh create dev

# Build your cluster
docker compose --env-file .env.cluster-dev -p OpenBacklogContrib build

# Start your cluster
docker compose --env-file .env.cluster-dev -p OpenBacklogContrib up
```

### 3. Access the Application

Open http://localhost:8000 to access your development cluster.

### 4. Install Local Development Dependencies (for tests/linting)

While the application runs in Docker, you'll need local Python and Node.js for running tests and linters:

```bash
# Python dependencies (for running pytest, black, isort)
pip install -r requirements.txt
pip install -r requirements-dev.txt

# React app dependencies (for running vitest, typescript checks)
cd static/react-components
npm install
cd ../..
```

## 🛠️ Development Workflow

> **How it works**: The application runs in Docker containers, but tests and linters run locally on your machine. This gives you fast feedback while keeping the runtime environment consistent.

### Backend Development (Python/FastAPI)

**Architecture:**
- FastAPI with SQLAlchemy ORM and PostgreSQL
- Dependency injection via FastAPI's DI system
- Type annotations throughout, following PEP 8

**Key Files:**
- `/src/` - Python backend source code
- `/tests/` - Python test suite
- `/src/main.py` - FastAPI app entry point
- `/src/manage.py` - Background job processor

**Development Commands:**
```bash
# Format Python code
black src/ tests/
isort src/ tests/

# Run tests with coverage
ENVIRONMENT=test pytest --cov=src --cov-report=term-missing

# Check formatting
black --check --diff src/ tests/
isort --check-only --diff src/ tests/
```

### Frontend Development (React/TypeScript)

**Architecture:**
- React 18+ with TypeScript, functional components only
- Tailwind CSS for styling
- Import aliases: `#api/*`, `#hooks/*`, `#components/*`

**Key Files:**
- `/static/react-components/` - React frontend application
- `/static/react-components/CLAUDE.md` - Detailed frontend guidelines

**Development Commands:**
```bash
cd static/react-components

# Run tests
npm run test

# Run TypeScript compilation check
npm run compile

# Build and watch during development
npm run build:watch
```

## 📋 Code Standards and Conventions

### Python Backend

**Style Guidelines:**
- Follow **PEP 8** strictly, 88-character line limit
- Use **Black** for formatting with **isort** for imports
- **Type hints** required for all functions
- **Google-style docstrings**

**Testing:**
- Use **pytest** with `ENVIRONMENT=test pytest`
- **PyHamcrest** assertions preferred over built-in `assert`
- Unit tests should mock dependencies, use real DB session via `session` fixture
- Test coverage should be maintained above 80%

**Architecture Patterns:**
- Small, focused functions - split if you need comments to explain sections
- Explicit over implicit - clear function names over clever abstractions
- Use FastAPI dependency injection patterns

**Example:**
```python
def calculate_user_metrics(user_id: UUID, session: Session) -> UserMetrics:
    """
    Calculates comprehensive metrics for a user's task performance.

    Args:
        user_id: The unique identifier for the user
        session: Database session for queries

    Returns:
        UserMetrics object containing calculated performance data
    """
    # Implementation here
```

### React/TypeScript Frontend

**Style Guidelines:**
- **TypeScript** with React 18+, functional components with hooks only
- **camelCase** for variables/functions, **PascalCase** for components
- **JSDoc comments** for all functions and components
- Follow ESLint and Prettier configurations

**Testing:**
- **Vitest** for unit testing hooks and services
- **Storybook** for component validation (no unit tests for components)
- **Mock Service Worker (MSW)** for API mocking

**Architecture Patterns:**
- Components organized by feature, not by type
- Container/presentational pattern where appropriate
- Custom hooks for shared stateful logic

**Example:**
```tsx
/**
 * A reusable task card component with status management.
 * @param {object} props - The component props
 * @param {Task} props.task - The task object to display
 * @param {(id: string) => void} props.onStatusChange - Handler for status updates
 * @returns {React.ReactElement} The task card component
 */
const TaskCard: React.FC<TaskCardProps> = ({ task, onStatusChange }) => {
  // Component implementation
};
```

### Commit Message Format

We follow **Conventional Commits** specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(api): add user preference endpoints
fix(ui): resolve task card rendering issue
docs: update contributing guidelines
test(backend): add user metrics calculation tests
```

## 🔄 Pull Request Process

### Before You Submit

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Run the full test suite** to ensure your changes don't break existing functionality:
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

3. **Follow code style** - Code must pass all formatting checks
4. **Update tests** when adding new features
5. **Keep commits focused** - One logical change per commit
6. **Test with PostgreSQL** - Ensure database tests pass locally

### Pull Request Guidelines

**PR Title:** Use conventional commit format
```
feat: add GitHub filepath autocomplete feature
```

**PR Description Template:**
```markdown
## Summary
Brief description of the changes and why they were made.

## Changes Made
- List of specific changes
- Include any breaking changes
- Note any new dependencies

## Testing
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated (if needed)
- [ ] No sensitive information included
```

### Quality Gates

All pull requests must pass these automated checks:

- ✅ **Python Tests** (`python-tests.yml`) - All backend tests pass
- ✅ **TypeScript Tests** (`typescript-tests.yml`) - All frontend tests pass
- ✅ **Security Scan** (`gitleaks.yml`) - No secrets detected
- ✅ **Code Formatting** - Black, isort, ESLint, Prettier compliance

## 🐛 Reporting Issues

### Bug Reports

When reporting bugs, please include:

1. **Clear description** of the issue
2. **Steps to reproduce** the problem
3. **Expected behavior** vs **actual behavior**
4. **Environment details** (OS, Python/Node versions, browser)
5. **Error messages** or logs (if applicable)

### Feature Requests

For feature requests, please provide:

1. **Use case** - Why is this feature needed?
2. **Proposed solution** - How should it work?
3. **Alternatives considered** - Other approaches you've thought of
4. **Impact** - Who would benefit from this feature?

## 📚 Development Resources

### Project Documentation
- [`CLAUDE.md`](./CLAUDE.md) - Comprehensive development guidelines and workflow
- [`CONVENTIONS.md`](./CONVENTIONS.md) - Python backend coding conventions
- [`static/react-components/CLAUDE.md`](./static/react-components/CLAUDE.md) - React frontend guidelines
- [`static/react-components/CONVENTIONS.md`](./static/react-components/CONVENTIONS.md) - Frontend-specific conventions

### Architecture Overview
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL + LangChain
- **Frontend**: React 18 + TypeScript + Tailwind CSS + Webpack
- **Testing**: pytest (backend) + Vitest (frontend) + Storybook (component validation)
- **CI/CD**: GitHub Actions for automated testing and security scanning

## 🤝 Code Review Process

1. **Automated Checks**: All CI checks must pass before review
2. **Peer Review**: Maintainers will review code for:
   - Adherence to project conventions
   - Code quality and maintainability
   - Test coverage and quality
   - Security considerations
3. **Feedback**: Address any review comments promptly
4. **Approval**: At least one maintainer approval required for merge

## 🆘 Getting Help

- **Questions about contributing?** Open a discussion or issue
- **Stuck on implementation?** Reference the detailed guides in `CLAUDE.md`
- **Need architectural guidance?** Review existing patterns in the codebase

## 📄 License

By contributing to OpenBacklog, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

**Thank you for contributing to OpenBacklog!** 🎉

Your contributions help make AI-powered development tools accessible to the solo developer community.