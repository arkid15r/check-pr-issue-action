"""Tests for main module."""

import json
import os
from pathlib import Path
import sys
from unittest.mock import Mock, mock_open, patch

import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from check_pr_issue_action.main import main  # noqa: E402


class TestMain:
    """Test cases for main function."""

    @patch("check_pr_issue_action.main.PrManager")
    @patch("check_pr_issue_action.main.PrValidator")
    @patch("check_pr_issue_action.main.Github")
    @patch("check_pr_issue_action.main.Config")
    @patch("builtins.open", new_callable=mock_open)
    @patch.dict(
        os.environ,
        {"GITHUB_EVENT_PATH": "/fake/event/path", "INPUT_GITHUB_TOKEN": "test_token"},
    )
    def test_main_success(
        self,
        mock_file,
        mock_config_class,
        mock_github_class,
        mock_validator_class,
        mock_pr_manager_class,
    ):
        """Test successful main execution."""
        # Mock event data
        event_data = {
            "pull_request": {"number": 123},
            "repository": {"full_name": "test/repo"},
        }
        mock_file.return_value.read.return_value = json.dumps(event_data)

        # Mock configuration
        mock_config = Mock()
        mock_config_class.return_value = mock_config

        # Mock GitHub client and repository
        mock_github = Mock()
        mock_repo = Mock()
        mock_pr = Mock()
        mock_repo.get_pull.return_value = mock_pr
        mock_github.get_repo.return_value = mock_repo
        mock_github_class.return_value = mock_github

        # Mock validator
        mock_validator = Mock()
        mock_validation_result = Mock()
        mock_validation_result.is_valid = True
        mock_validation_result.reason = "All validations passed"
        mock_validator.validate_pr.return_value = mock_validation_result
        mock_validator_class.return_value = mock_validator

        # Mock PR manager
        mock_pr_manager = Mock()
        mock_pr_manager_class.return_value = mock_pr_manager

        # Run main function
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        mock_validator.validate_pr.assert_called_once_with(mock_pr)
        mock_pr_manager.handle_validation_failure.assert_not_called()

    @patch("check_pr_issue_action.main.PrManager")
    @patch("check_pr_issue_action.main.PrValidator")
    @patch("check_pr_issue_action.main.Github")
    @patch("check_pr_issue_action.main.Config")
    @patch("builtins.open", new_callable=mock_open)
    @patch.dict(
        os.environ,
        {"GITHUB_EVENT_PATH": "/fake/event/path", "INPUT_GITHUB_TOKEN": "test_token"},
    )
    def test_main_validation_failure(
        self,
        mock_file,
        mock_config_class,
        mock_github_class,
        mock_validator_class,
        mock_pr_manager_class,
    ):
        """Test main execution with validation failure."""
        # Mock event data
        event_data = {
            "pull_request": {"number": 123},
            "repository": {"full_name": "test/repo"},
        }
        mock_file.return_value.read.return_value = json.dumps(event_data)

        # Mock configuration
        mock_config = Mock()
        mock_config_class.return_value = mock_config

        # Mock GitHub client and repository
        mock_github = Mock()
        mock_repo = Mock()
        mock_pr = Mock()
        mock_repo.get_pull.return_value = mock_pr
        mock_github.get_repo.return_value = mock_repo
        mock_github_class.return_value = mock_github

        # Mock validator with failure
        mock_validator = Mock()
        mock_validation_result = Mock()
        mock_validation_result.is_valid = False
        mock_validation_result.reason = "No linked issue"
        mock_validator.validate_pr.return_value = mock_validation_result
        mock_validator_class.return_value = mock_validator

        # Mock PR manager
        mock_pr_manager = Mock()
        mock_pr_manager.handle_validation_failure.return_value = True
        mock_pr_manager_class.return_value = mock_pr_manager

        # Run main function
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        mock_validator.validate_pr.assert_called_once_with(mock_pr)
        mock_pr_manager.handle_validation_failure.assert_called_once_with(
            mock_pr, mock_validation_result
        )

    @patch.dict(os.environ, {}, clear=True)
    def test_main_missing_event_path(self):
        """Test main execution with missing GITHUB_EVENT_PATH."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("builtins.open", side_effect=FileNotFoundError())
    @patch.dict(
        os.environ,
        {"GITHUB_EVENT_PATH": "/fake/event/path", "INPUT_GITHUB_TOKEN": "test_token"},
    )
    def test_main_event_file_not_found(self, mock_file):
        """Test main execution when event file is not found."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("builtins.open", new_callable=mock_open)
    @patch.dict(
        os.environ,
        {"GITHUB_EVENT_PATH": "/fake/event/path", "INPUT_GITHUB_TOKEN": "test_token"},
    )
    def test_main_no_pull_request_data(self, mock_file):
        """Test main execution with no pull request data in event."""
        event_data = {"repository": {"full_name": "test/repo"}}
        mock_file.return_value.read.return_value = json.dumps(event_data)

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("check_pr_issue_action.main.Config")
    @patch.dict(
        os.environ,
        {"GITHUB_EVENT_PATH": "/fake/event/path", "INPUT_GITHUB_TOKEN": "test_token"},
    )
    def test_main_config_error(self, mock_config_class):
        """Test main execution with configuration error."""
        mock_config_class.side_effect = ValueError("Config error")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
