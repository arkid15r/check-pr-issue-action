# Check PR Issue Action

A GitHub Action that validates PR-issue relationships and optionally enforces assignment requirements.

## Features

- **Optional Issue Linking**: Ensures every PR is linked to an issue via GitHub API
- **Optional PR Description Check**: Fallback validation that checks PR description for closing issue references (e.g., "Closes #123")
- **Optional Assignee Validation**: Configurable check that issue assignee matches PR author
- **Bot Support**: Automatically skips validation for bot-authored PRs
- **User Whitelist**: Configurable list of users whose PRs can bypass all checks
- **Flexible Enforcement**: Option to close non-compliant PRs or just post warnings
- **Custom Messages**: Configurable error messages for different failure types

## Usage

### Basic Usage

```yaml
name: Test PR Issue
on:
  pull_request:
    types:
      - opened
      - synchronize

jobs:
  check-pr-issue:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: arkid15r/check-pr-issue-action@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

### Advanced Configuration

```yaml
- uses: arkid15r/check-pr-issue-action@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    skip_users: 'admin,maintainer'
    check_issue_reference: 'true'
    require_assignee: 'true'
    close_pr_on_failure: 'false'
    no_issue_message: 'Please link this PR to an issue before merging.'
    assignee_mismatch_message: 'The linked issue must be assigned to you before merging.'
```

## Configuration

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `github_token` | GitHub token for API access | Yes | - |
| `skip_users` | Comma-separated list of usernames to skip validation | No | `''` |
| `check_issue_reference` | Whether to allow PRs without a linked issue when the PR description contains a valid closing issue reference | No | `false` |
| `require_assignee` | Whether to require issue assignee to match PR author | No | `false` |
| `close_pr_on_failure` | Whether to close PR when validation fails | No | `true` |
| `no_issue_message` | Error message when PR has no linked issue | No | `'This PR must be linked to an issue before it can be merged.'` |
| `assignee_mismatch_message` | Error message when assignee doesn't match PR author | No | `'The linked issue must be assigned to the PR author before this PR can be merged.'` |

### PR Description Reference Check

When `check_issue_reference` is enabled, the action will check the PR description for valid closing issue references if no linked issue is found via the GitHub API. This is useful when PRs reference issues in their description but aren't formally linked.

**Supported Keywords** (case-insensitive):

- `close`, `closes`, `closed`
- `fix`, `fixes`, `fixed`
- `resolve`, `resolves`, `resolved`

**Valid Formats**:

- `Closes #123` - References an issue in the same repository
- `Resolves #10, resolves #123` - Multiple issues in one description
- `Closes: #10` - Optional colon after keyword
- `CLOSES #10` - Case-insensitive matching

**Example PR Description**:

```text
This PR implements the new feature requested in the issue.

Closes #123
```

## Required Permissions

This action requires the following GitHub permissions:

- **`pull-requests: write`** - To close PRs and post comments
- **`issues: read`** - To access linked issue information and assignees
- **`contents: read`** - To read repository contents (standard permission)

These permissions are automatically included in the action definition, but you may need to ensure your workflow has sufficient permissions if using a custom token.

## Development

### Setup

```bash
# Install pipx and Poetry (if not already installed)
python -m pip install --user pipx
python -m pipx ensurepath
pipx install poetry

# Install development dependencies (includes package in editable mode)
make install-dev

# Install pre-commit hooks
make pre-commit
```

### Poetry Commands

```bash
# Install all dependencies (production + development)
poetry install --with dev

# Install only production dependencies
poetry install --only main

# Run tests
poetry run pytest

# Run linting
poetry run ruff check .

# Format code
poetry run ruff format .

# Run all checks
make check
```

### Testing the Action

This repository includes a test workflow (`.github/workflows/test-action.yml`) that demonstrates how to use the action in a real environment:

- **PR Testing**: The workflow runs automatically when a PR is opened
- **Basic Configuration**: Tests the action with a simple configuration
- **Non-blocking**: Uses `close_pr_on_failure: 'false'` to avoid closing test PRs

### Running Tests

```bash
# Run tests
make test

# Run tests with coverage
make test-cov
```

### Code Quality

```bash
# Run linting
make lint

# Format code
make format

# Run all checks
make check
```

### Project Structure

```text
check-pr-issue-action/
├── src/check_pr_issue_action/     # Main package code
│   ├── __init__.py               # Package initialization
│   ├── main.py                   # Main entry point
│   ├── config.py                 # Configuration management
│   ├── validator.py              # Validation logic
│   └── pr_manager.py             # PR management
├── tests/                        # Test suite
├── .github/workflows/            # CI/CD workflows
│   ├── ci.yml                   # Main CI workflow
│   └── test-action.yml          # Action testing workflow
├── action.yml                    # GitHub Action metadata
├── Dockerfile                    # Container definition (Alpine Linux)
├── pyproject.toml               # Project configuration
└── README.md                    # Documentation
```

### Available Commands

- `make install` - Install production dependencies
- `make install-dev` - Install development dependencies
- `make test` - Run tests
- `make test-cov` - Run tests with coverage
- `make lint` - Run linting
- `make format` - Format code
- `make check` - Run linting and tests
- `make clean` - Clean up generated files
- `make pre-commit` - Run pre-commit on all files

## Docker Image

The action is built on **Alpine Linux** for a smaller, more secure container image:
- **Base Image**: `python:3.11-alpine`
- **Size**: ~410MB (significantly smaller than Debian-based images)
- **Security**: Minimal attack surface with Alpine's security-focused design
- **Multi-arch**: Supports both AMD64 and ARM64 architectures

## How It Works

1. **Bot Detection**: Automatically skips validation for any PR authored by a bot user
2. **Skip Users**: Bypasses validation for users in the `skip_users` list
3. **Issue Linking**: Uses GitHub API to check if PR is linked to an issue
4. **PR Description Fallback**: If `check_issue_reference` is enabled and no linked issue is found, checks the PR description for valid closing keywords (e.g., "Closes #123", "Fixes owner/repo#456"). Supports keywords: `close`, `closes`, `closed`, `fix`, `fixes`, `fixed`, `resolve`, `resolves`, `resolved`
5. **Assignee Validation**: If enabled, verifies that the issue assignee matches the PR author
6. **Enforcement**: Either closes the PR or posts a warning message based on configuration

## License

This project is licensed under the MIT License.
