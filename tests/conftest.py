"""Pytest configuration and fixtures for check-pr-issue-action tests."""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from check_pr_issue_action.config import Config  # noqa: E402


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = Mock(spec=Config)
    config.skip_users = ["testuser1", "testuser2"]
    config.require_assignee = True
    config.close_pr_on_failure = True
    config.no_issue_message = "Test no issue message"
    config.assignee_mismatch_message = "Test assignee mismatch message"
    return config


@pytest.fixture
def mock_github_client():
    """Create a mock GitHub client for testing."""
    return Mock()


@pytest.fixture
def mock_pr():
    """Create a mock pull request for testing."""
    pr = Mock()
    pr.number = 123
    pr.user.login = "testuser"
    pr.user.type = "User"
    return pr


@pytest.fixture
def mock_bot_pr():
    """Create a mock bot pull request for testing."""
    pr = Mock()
    pr.number = 124
    pr.user.login = "dependabot[bot]"
    pr.user.type = "Bot"
    return pr


@pytest.fixture
def mock_issue():
    """Create a mock issue for testing."""
    issue = Mock()
    issue.number = 456
    issue.assignees = []
    return issue


@pytest.fixture
def mock_issue_with_assignee():
    """Create a mock issue with assignee for testing."""
    assignee = Mock()
    assignee.login = "testuser"

    issue = Mock()
    issue.number = 456
    issue.assignees = [assignee]
    return issue


@pytest.fixture
def mock_issue_with_different_assignee():
    """Create a mock issue with different assignee for testing."""
    assignee = Mock()
    assignee.login = "differentuser"

    issue = Mock()
    issue.number = 456
    issue.assignees = [assignee]
    return issue
