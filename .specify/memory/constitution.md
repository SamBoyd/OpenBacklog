<!--
SYNC IMPACT REPORT
==================
Version Change: 0.0.0 → 1.0.0
Ratification Date: 2025-10-17
Last Amendment: 2025-10-17

INITIAL CONSTITUTION CREATION
This is the first version of the OpenBacklog Project Constitution, codifying existing
practices from CLAUDE.md, CONVENTIONS.md, and static/react-components/CLAUDE.md into
a formal governance document.

PRINCIPLES ESTABLISHED:
1. Code Quality & Maintainability - Enforces simplicity, explicit code, modularity
2. Testing Standards & Reliability - Mandates TDD, isolation, comprehensive coverage
3. User Experience Consistency - Ensures design system adherence, accessibility
4. Performance & Efficiency - Requires measurement-driven optimization

TEMPLATES STATUS:
✅ plan-template.md - Created with constitution checks
✅ spec-template.md - Created with requirements alignment
✅ tasks-template.md - Created with principle-driven categorization

FOLLOW-UP ACTIONS:
- None - all placeholders resolved
-->

# OpenBacklog Project Constitution

**Version:** 1.0.0
**Ratification Date:** 2025-10-17
**Last Amended:** 2025-10-17
**Project:** OpenBacklog - AI-Powered Task Management for Solo Developers

---

## Preamble

This constitution establishes the foundational principles governing all development activities within the OpenBacklog project. These principles are non-negotiable guardrails that ensure consistent quality, maintainability, and user value across the entire codebase.

OpenBacklog is built as a production SaaS application with a commitment to transparency through open source. Every feature, every line of code, and every architectural decision must serve the solo developer with simplicity, reliability, and performance.

---

## Core Principles

### Principle 1: Code Quality & Maintainability

**Name:** Simplicity and Explicit Design

**Rules:**

- **KISS (Keep It Simple, Stupid):** MUST choose the simplest solution that solves the stated problem. Complexity requires explicit justification and approval.
- **YAGNI (You Aren't Gonna Need It):** MUST implement only planned features. Speculative features, abstractions, or "future-proofing" are prohibited.
- **Explicit Over Implicit:** MUST use clear, verbose naming and obvious data flow. Clever abstractions, magic behavior, and hidden dependencies are forbidden.
- **Small, Focused Functions:** MUST keep functions small and single-purpose. If comments are needed to explain code sections, split into separate functions.
- **Modular File Structure:** MUST keep files small and highly modular. Group related functionality into clear packages. Prefer many small files over few large ones.
- **No Deprecated Code:** MUST delete old code completely when replacing. No versioned names (e.g., `processV2`, `handleNew`, `ClientOld`), no migration code unless explicitly requested, no "removed code" comments.
- **Type Safety:** MUST use type annotations in Python (FastAPI/Pydantic) and strict TypeScript for all frontend code.
- **No Magic Numbers:** MUST define all constants explicitly in uppercase with descriptive names.

**Rationale:**

OpenBacklog is maintained primarily by AI-assisted development. Small, explicit, modular code minimizes context windows, reduces token usage, and allows focused reasoning about isolated units. This principle ensures code remains understandable and maintainable as the project scales.

**Code Quality Standards:**

**Python Backend:**
- MUST follow PEP 8 with 88-character line length (Black formatter)
- MUST use snake_case for variables/functions, PascalCase for classes
- MUST use FastAPI with dependency injection for all endpoints
- MUST use SQLAlchemy ORM with declarative syntax exclusively
- MUST use Pydantic models for all API schemas
- MUST write Google-style docstrings for all public functions

**React Frontend:**
- MUST use TypeScript with strict mode enabled
- MUST use functional components with hooks (no class components)
- MUST use camelCase for variables/functions, PascalCase for components/interfaces
- MUST use import aliases (`#api/*`, `#hooks/*`, `#components/*`, etc.)
- MUST write JSDoc comments for all components and exported functions
- MUST use Tailwind CSS exclusively for styling (no custom CSS files)
- MUST follow container/presentational pattern for complex components

**Enforcement:**
- Black formatter MUST pass on all Python code
- ESLint and Prettier MUST pass on all TypeScript/React code
- Type checking MUST pass (mypy for Python, tsc for TypeScript)
- Pre-commit hooks enforce formatting and linting

---

### Principle 2: Testing Standards & Reliability

**Name:** Test-Driven Development and Isolation

**Rules:**

- **Test-Driven Development:** MUST write tests for complex business logic. Match testing approach to code complexity:
  - Complex business logic → Write tests first (TDD)
  - Simple CRUD operations → Write code first, then tests
  - Hot paths → Add benchmarks after implementation
- **Unit Test Isolation:** CRITICAL - Unit tests MUST test functions in isolation by mocking ALL dependencies. Never allow unit tests to call real implementations (that creates integration tests, not unit tests).
- **Comprehensive Coverage:** MUST maintain test coverage for all business logic, API endpoints, and complex UI interactions.
- **Test Environment:** MUST set `ENVIRONMENT=test` when running pytest to use test database.
- **Fixture Usage:** MUST use fixtures from `tests/conftest.py` for common test setup (user, workspace, session).
- **No DB Mocking in Controllers:** Controller tests MUST use the real `session` fixture, not mock the database.
- **Frontend Testing:**
  - MUST use vitest for testing React hooks, contexts, and services
  - MUST use Storybook for visual validation of React components (no unit tests for components)
  - MUST mock all hooks and contexts in Storybook stories
  - Unit tests MUST use `vi.spyOn()` to mock dependencies within the same module

**Rationale:**

Reliable, well-tested code is essential for a production SaaS application. Testing in isolation ensures changes don't cascade failures and enables confident refactoring. TDD for complex logic ensures edge cases are considered upfront. Visual testing with Storybook provides faster feedback cycles for UI work than traditional unit tests.

**Testing Workflow:**

1. **Before Implementation:**
   - For complex logic: Write failing test cases first
   - For simple features: Plan test cases, implement after
2. **During Implementation:**
   - Run tests continuously during development
   - Verify mocks are properly isolating dependencies
3. **After Implementation:**
   - MUST run full test suite: `ENVIRONMENT=test pytest --cov=src --cov-report=term-missing`
   - MUST run formatters: `black --check src/ tests/`
   - MUST run TypeScript tests: `npm run test` (in static/react-components/)
   - MUST validate UI in Storybook at `http://localhost:6006/`

**Assertion Standards:**
- Python: MUST use PyHamcrest assertions (e.g., `assert_that(value, equal_to(expected))`)
- TypeScript: MUST use vitest expect assertions with descriptive messages

**Security Testing:**
- MUST validate all user inputs in tests
- MUST test authentication and authorization paths
- MUST use `crypto/rand` for randomness in tests
- MUST verify SQL injection protection with parameterized queries

---

### Principle 3: User Experience Consistency

**Name:** Design System Adherence and Accessibility

**Rules:**

- **Tailwind Theme Exclusivity:** MUST use ONLY the Tailwind theme defined in `static/react-components/tailwind.config.js` for all colors, spacing, typography, and layout.
- **Design Token Compliance:** MUST use CSS variables from the design system (e.g., `hsl(var(--primary))`, `var(--radius-lg)`).
- **Content Design System:** MUST follow guidelines in `content-design-system/guidelines.md` for voice, tone, structure, and copy.
- **Accessibility Standards:** MUST ensure all UI components meet WCAG 2.1 AA standards:
  - Keyboard navigation support
  - ARIA labels where appropriate
  - Sufficient color contrast ratios
  - Screen reader compatibility
- **Component Consistency:** MUST reuse existing components from `static/react-components/components/` before creating new ones.
- **Responsive Design:** MUST support mobile, tablet, and desktop breakpoints using Tailwind responsive utilities.
- **Error States:** MUST implement consistent error boundaries and error states across all components.
- **Loading States:** MUST provide loading indicators for all asynchronous operations visible to users.

**Rationale:**

OpenBacklog serves solo developers who expect professional, polished experiences. A consistent design system reduces cognitive load, builds trust, and ensures the application feels cohesive. Accessibility is non-negotiable for an inclusive product.

**UI Validation Process:**

1. **Development:** Use Storybook to develop and validate components in isolation
2. **Visual Testing:** View changes in Storybook at `http://localhost:6006/`
3. **Integration Testing:** Test in development environment at `http://dev.openbacklog.ai/`
4. **Accessibility Check:** Verify keyboard navigation, screen reader compatibility, color contrast

**Copy Standards:**
- Follow voice and tone guidelines from content-design-system
- Create new copy documents in `content-design-system/` for major features
- Suggest creating missing copy documents when working on new pages

---

### Principle 4: Performance & Efficiency

**Name:** Measurement-Driven Optimization

**Rules:**

- **Measure Before Optimize:** MUST measure performance before implementing optimizations. No guessing allowed.
- **Hot Path Identification:** MUST identify and document hot paths (frequently executed code) and validate performance with benchmarks.
- **Database Query Optimization:** MUST use proper indexes, avoid N+1 queries, and profile slow queries before optimization.
- **Frontend Performance:**
  - MUST use React.memo() for expensive components only after measuring
  - MUST lazy load routes and heavy components
  - MUST optimize bundle size (monitor with webpack bundle analyzer)
  - MUST use Tailwind's purge/JIT mode to minimize CSS
- **API Response Times:** MUST keep API endpoints under 200ms for standard requests (measure with logging/monitoring).
- **Asset Optimization:** MUST optimize images, compress assets, use appropriate formats (WebP, SVG).
- **Caching Strategy:** MUST implement appropriate caching (browser cache, CDN, Redis where needed).
- **Background Jobs:** MUST offload heavy processing to background jobs (`src/manage.py` job processor).
- **Efficient Workflows:** MUST maximize efficiency in development:
  - Run parallel operations (multiple searches, reads, greps) in single messages
  - Use multiple agents for complex tasks (one for tests, one for implementation)
  - Batch similar work (group related file edits together)

**Rationale:**

Solo developers demand fast, responsive tools. Performance optimization must be data-driven to avoid premature optimization that adds complexity without benefit. Efficient development workflows respect both the developer's time and AI token budgets.

**Performance Monitoring:**

- Backend: Use Python logging with structured format
- Frontend: Use browser performance tools and React DevTools Profiler
- Database: Use PostgreSQL query logs and EXPLAIN ANALYZE
- Establish baseline metrics before optimization attempts
- Document performance improvements with before/after measurements

**Optimization Workflow:**

1. **Identify:** Profile and measure to find actual bottlenecks
2. **Document:** Record baseline metrics
3. **Optimize:** Implement targeted improvements
4. **Verify:** Measure again to confirm improvement
5. **Monitor:** Add monitoring to catch regressions

---

## Governance

### Amendment Process

This constitution may be amended only through the following process:

1. **Proposal:** Amendments must be proposed with clear rationale and impact analysis
2. **Review:** Proposals must be reviewed for consistency with existing principles
3. **Approval:** Amendments require explicit approval before adoption
4. **Documentation:** All amendments must update the Sync Impact Report
5. **Propagation:** All dependent templates and documentation must be updated to reflect changes

### Versioning Policy

The constitution version follows semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR:** Backward-incompatible changes (principle removals, redefinitions)
- **MINOR:** New principles added or existing principles materially expanded
- **PATCH:** Clarifications, wording improvements, typo fixes, non-semantic refinements

### Compliance Review

All code contributions must comply with this constitution:

- **Pre-commit:** Automated checks enforce code quality and testing standards
- **Code Review:** Human or AI review verifies adherence to principles
- **CI/CD:** GitHub Actions enforce testing, formatting, and build requirements
- **Documentation:** All feature work must reference applicable constitutional principles

### Principle Conflict Resolution

If principles appear to conflict in specific scenarios:

1. **Simplicity First:** Principle 1 (Code Quality) takes precedence when in doubt
2. **Measure, Don't Assume:** Principle 4 (Performance) requires data before action
3. **User Value:** User experience (Principle 3) and reliability (Principle 2) outweigh developer convenience
4. **Escalate Ambiguity:** When unclear, stop and ask for guidance rather than making assumptions

---

## Development Partnership

### Core Workflow: Research → Plan → Implement → Validate

All feature work MUST follow this workflow:

1. **Research:** Understand existing patterns and architecture before coding
2. **Plan:** Propose approach and verify before implementing
3. **Implement:** Build with tests and error handling
4. **Validate:** ALWAYS run formatters, linters, unit tests, and visual tests after implementation

### AI-Specific Guidance

- Assume code was written by another AI, not a human
- Break tasks into small, incremental steps
- Use TodoWrite tool for task tracking
- Stop when stuck - the simple solution is usually correct
- When uncertain about architecture, ask for guidance
- When choosing between approaches, present options and ask for preference

---

## Appendix: Tool & Framework Mandates

### Backend Stack
- **Framework:** FastAPI with type annotations
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Migrations:** Alembic
- **Testing:** pytest with PyHamcrest
- **Formatting:** Black (88 char line length)
- **Validation:** Pydantic models
- **Auth:** Auth0
- **Payments:** Stripe
- **AI/LLM:** LangChain

### Frontend Stack
- **Framework:** React 18+ (functional components, hooks only)
- **Language:** TypeScript (strict mode)
- **Styling:** Tailwind CSS (theme-only, no custom CSS)
- **Testing:** vitest for hooks/services, Storybook for components
- **API Mocking:** MSW (Mock Service Worker)
- **Bundler:** Webpack
- **Linting:** ESLint + Prettier

### Development Tools
- **Version Control:** Git with conventional commits
- **CI/CD:** GitHub Actions
- **Code Quality:** Pre-commit hooks
- **Documentation:** MCP tools (Context7, Playwright for visual validation)

---

**End of Constitution**
