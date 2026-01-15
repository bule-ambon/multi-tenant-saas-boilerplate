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

### Backend Tests (always run inside the provided virtualenv)


```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
export DATABASE_URL="your-database-url"
python -m pytest tests/ -v --cov=app

```

Requirements:
- Minimum 80% code coverage
- All tests must pass
- Add tests for new features

These commands are meant to run on your host machine. If you already have a virtual environment, just activate it and skip the `python3 -m venv venv` step. The backend settings require a `DATABASE_URL`, so export it from your shell environment (as shown) or copy `.env.example` to `.env` and update the value to match your local database. Running the suite inside Docker is optional and covered separately in the “Migration & Testing Workflow for Agents” section below if you prefer the containerized path.





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
