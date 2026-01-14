# Contributing to Multi-Tenant SaaS Platform

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [GitHub Issues](https://github.com/your-repo/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Relevant logs or screenshots

### Suggesting Enhancements

1. Check existing issues and discussions
2. Create a new issue with the `enhancement` label
3. Clearly describe:
   - The problem you're solving
   - Your proposed solution
   - Alternative solutions considered
   - Potential impact

### Pull Requests

1. **Fork the repository**

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the code style guidelines
   - Add tests for new functionality
   - Update documentation as needed

4. **Commit your changes**
   ```bash
   git commit -m "feat: add amazing feature"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `style:` Code style changes (formatting, etc.)
   - `refactor:` Code refactoring
   - `test:` Adding or updating tests
   - `chore:` Maintenance tasks

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Provide a clear description
   - Reference related issues
   - Ensure CI passes

## Development Setup

See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for detailed setup instructions.

## Code Style

### Python (Backend)

- Follow [PEP 8](https://pep8.org/)
- Use type hints
- Maximum line length: 100 characters
- Use Black for formatting:
  ```bash
  black backend/app
  ```
- Use isort for imports:
  ```bash
  isort backend/app
  ```

### TypeScript (Frontend)

- Use ESLint and Prettier
- Follow React best practices
- Use functional components and hooks
- Format with Prettier:
  ```bash
  npm run format
  ```

## Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v --cov=app
```

Requirements:
- Minimum 80% code coverage
- All tests must pass
- Add tests for new features

These commands are meant to run on your host machine: create/activate a Python virtual environment if you haven’t already (for example `python -m venv venv && source venv/bin/activate` on Unix), install the backend dependencies (`pip install -r requirements.txt`, which already includes `pytest`), and execute `pytest` as shown. Running the suite inside Docker is optional and covered separately in the “Migration & Testing Workflow for Agents” section below if you prefer the containerized path.

#### Migration & Testing Workflow for Agents

1. **Start the stack via Docker** – bring up the services defined in `docker-compose.yml` (`docker compose up -d`). The backend image already installs `requirements.txt`, so you do not need to run `python -m venv`/`pip install` on the host.
2. **Run migrations inside the backend container** – if the schema might be stale, exec into `saas_backend` and run `cd /app && alembic upgrade head`. This keeps the database in sync with the latest models without touching a host `.venv`.
3. **Execute backend tests inside the container** – stay inside `saas_backend` and run `python -m pytest tests/ -v --cov=app`. Using `python -m pytest` (not a bare `pytest`) avoids import issues where `/app` is not on `sys.path`.
4. **Handle unexpected schema gaps** – if tests fail because columns or tables are missing (as happened before with `entity_type` and `client_group_entities` metadata), run appropriate `ALTER TABLE` statements via `docker exec saas_postgres psql -U saas_user -d saas_platform` to add the missing columns, then rerun `alembic upgrade head` and the pytest command.
5. **Repeat the containerized workflow whenever code or migrations change** – always re-run `python -m pytest ...` inside the container after schema/model updates so you never reinstall dependencies locally.


### Frontend Tests

```bash
cd frontend
npm test
```

Ensure you run `npm install` beforehand so the Vitest/React tooling is available before invoking `npm test`.

## Documentation

- Update README.md for user-facing changes
- Update DEVELOPER_GUIDE.md for technical changes
- Add docstrings to Python functions
- Add JSDoc comments to TypeScript functions
- Update API documentation

## Review Process

1. At least one maintainer must approve
2. All CI checks must pass
3. Code coverage must not decrease
4. Documentation must be updated

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to ask questions by:
- Opening a discussion on GitHub
- Commenting on relevant issues
- Reaching out to maintainers

Thank you for contributing! 🎉
