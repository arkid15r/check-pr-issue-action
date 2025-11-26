"""Tests for config module."""

import os
from unittest.mock import patch

import pytest

from check_pr_issue_action.config import Config


class TestConfig:
    """Test cases for Config class."""

    def test_required_input_missing(self):
        """Test that missing required input raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="Required input 'github_token' is not provided"
            ):
                Config()

    def test_required_input_present(self):
        """Test that required input is loaded correctly."""
        with patch.dict(os.environ, {"INPUT_GITHUB_TOKEN": "test_token"}):
            config = Config()
            assert config.github_token == "test_token"

    def test_optional_inputs_with_defaults(self):
        """Test that optional inputs use correct defaults."""
        with patch.dict(os.environ, {"INPUT_GITHUB_TOKEN": "test_token"}):
            config = Config()
            assert config.skip_users == []
            assert config.require_assignee is False
            assert config.close_pr_on_failure is True
            assert (
                config.no_issue_message
                == "This PR must be linked to an issue before it can be merged."
            )
            assert (
                config.no_assignee_message
                == "The linked issue must be assigned to the PR author before this PR can be merged."
            )

    def test_skip_users_parsing(self):
        """Test parsing of comma-separated skip users."""
        with patch.dict(
            os.environ,
            {
                "INPUT_GITHUB_TOKEN": "test_token",
                "INPUT_SKIP_USERS": "user1, user2, user3",
            },
        ):
            config = Config()
            assert config.skip_users == ["user1", "user2", "user3"]

    def test_skip_users_empty(self):
        """Test handling of empty skip users."""
        with patch.dict(
            os.environ, {"INPUT_GITHUB_TOKEN": "test_token", "INPUT_SKIP_USERS": ""}
        ):
            config = Config()
            assert config.skip_users == []

    def test_boolean_inputs(self):
        """Test parsing of boolean inputs."""
        with patch.dict(
            os.environ,
            {
                "INPUT_GITHUB_TOKEN": "test_token",
                "INPUT_REQUIRE_ASSIGNEE": "true",
                "INPUT_CLOSE_PR_ON_FAILURE": "false",
            },
        ):
            config = Config()
            assert config.require_assignee is True
            assert config.close_pr_on_failure is False

    def test_custom_messages(self):
        """Test custom error messages."""
        with patch.dict(
            os.environ,
            {
                "INPUT_GITHUB_TOKEN": "test_token",
                "INPUT_NO_ISSUE_MESSAGE": "Custom no issue message",
                "INPUT_NO_ASSIGNEE_MESSAGE": "Custom assignee message",
            },
        ):
            config = Config()
            assert config.no_issue_message == "Custom no issue message"
            assert config.no_assignee_message == "Custom assignee message"

    def test_skip_users_file_path_only(self, tmp_path):
        """Test parsing of skip users from file only."""
        skip_users_file = tmp_path / "skip_users.txt"
        skip_users_file.write_text("user1\nuser2\nuser3\n")

        with patch.dict(
            os.environ,
            {
                "INPUT_GITHUB_TOKEN": "test_token",
                "INPUT_SKIP_USERS_FILE_PATH": str(skip_users_file),
            },
        ):
            config = Config()
            assert config.skip_users == ["user1", "user2", "user3"]

    def test_skip_users_combined(self, tmp_path):
        """Test combining skip_users and skip_users_file_path."""
        skip_users_file = tmp_path / "skip_users.txt"
        skip_users_file.write_text("user2\nuser3\nuser4\n")

        with patch.dict(
            os.environ,
            {
                "INPUT_GITHUB_TOKEN": "test_token",
                "INPUT_SKIP_USERS": "user1, user2",
                "INPUT_SKIP_USERS_FILE_PATH": str(skip_users_file),
            },
        ):
            config = Config()
            assert sorted(config.skip_users) == ["user1", "user2", "user3", "user4"]

    def test_skip_users_file_not_found(self):
        """Test handling of a non-existent skip users file."""
        with patch.dict(
            os.environ,
            {
                "INPUT_GITHUB_TOKEN": "test_token",
                "INPUT_SKIP_USERS_FILE_PATH": "non_existent_file.txt",
            },
        ):
            config = Config()
            assert config.skip_users == []

    def test_skip_users_empty_file(self, tmp_path):
        """Test handling of an empty skip users file."""
        skip_users_file = tmp_path / "skip_users.txt"
        skip_users_file.write_text("")

        with patch.dict(
            os.environ,
            {
                "INPUT_GITHUB_TOKEN": "test_token",
                "INPUT_SKIP_USERS_FILE_PATH": str(skip_users_file),
            },
        ):
            config = Config()
            assert config.skip_users == []
