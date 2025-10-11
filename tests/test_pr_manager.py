"""Tests for pr_manager module."""

from check_pr_issue_action.pr_manager import PrManager
from check_pr_issue_action.validator import ValidationResult


class TestPrManager:
    """Test cases for PrManager class."""

    def test_handle_validation_failure_with_close(
        self, mock_github_client, mock_config, mock_pr
    ):
        """Test handling validation failure with PR closure enabled."""
        mock_config.close_pr_on_failure = True
        validation_result = ValidationResult(is_valid=False, reason="No linked issue")

        pr_manager = PrManager(mock_github_client, mock_config)
        result = pr_manager.handle_validation_failure(mock_pr, validation_result)

        assert result is True
        mock_pr.create_issue_comment.assert_called_once()
        mock_pr.edit.assert_called_once_with(state="closed")

    def test_handle_validation_failure_without_close(
        self, mock_github_client, mock_config, mock_pr
    ):
        """Test handling validation failure with PR closure disabled."""
        mock_config.close_pr_on_failure = False
        validation_result = ValidationResult(is_valid=False, reason="No linked issue")

        pr_manager = PrManager(mock_github_client, mock_config)
        result = pr_manager.handle_validation_failure(mock_pr, validation_result)

        assert result is True
        mock_pr.create_issue_comment.assert_called_once()
        mock_pr.edit.assert_not_called()

    def test_get_error_message_no_issue(self, mock_github_client, mock_config):
        """Test getting error message for no linked issue."""
        validation_result = ValidationResult(is_valid=False, reason="No linked issue")
        pr_manager = PrManager(mock_github_client, mock_config)

        message = pr_manager._get_error_message(validation_result)
        assert message == mock_config.no_issue_message

    def test_get_error_message_assignee_mismatch(self, mock_github_client, mock_config):
        """Test getting error message for assignee mismatch."""
        validation_result = ValidationResult(is_valid=False, reason="Assignee mismatch")
        pr_manager = PrManager(mock_github_client, mock_config)

        message = pr_manager._get_error_message(validation_result)
        assert message == mock_config.no_assignee_message

    def test_get_error_message_no_assignee(self, mock_github_client, mock_config):
        """Test getting error message for no assignee."""
        validation_result = ValidationResult(
            is_valid=False, reason="Issue has no assignee"
        )
        pr_manager = PrManager(mock_github_client, mock_config)

        message = pr_manager._get_error_message(validation_result)
        assert message == mock_config.no_assignee_message

    def test_get_error_message_unknown_reason(self, mock_github_client, mock_config):
        """Test getting error message for unknown reason."""
        validation_result = ValidationResult(is_valid=False, reason="Unknown error")
        pr_manager = PrManager(mock_github_client, mock_config)

        message = pr_manager._get_error_message(validation_result)
        assert message == "PR validation failed: Unknown error"

    def test_get_error_message_invalid_branch(self, mock_github_client, mock_config):
        """Test getting error message for invalid branch."""
        validation_result = ValidationResult(
            is_valid=False,
            reason="PR must target one of the allowed branches: main, develop",
        )
        pr_manager = PrManager(mock_github_client, mock_config)

        message = pr_manager._get_error_message(validation_result)
        assert message == mock_config.invalid_branch_message

    def test_post_comment_success(self, mock_github_client, mock_config, mock_pr):
        """Test successful comment posting."""
        pr_manager = PrManager(mock_github_client, mock_config)
        result = pr_manager._post_comment(mock_pr, "Test message")

        assert result is True
        mock_pr.create_issue_comment.assert_called_once_with("Test message")

    def test_post_comment_failure(self, mock_github_client, mock_config, mock_pr):
        """Test comment posting failure."""
        mock_pr.create_issue_comment.side_effect = Exception("API Error")
        pr_manager = PrManager(mock_github_client, mock_config)
        result = pr_manager._post_comment(mock_pr, "Test message")

        assert result is False

    def test_close_pr_success(self, mock_github_client, mock_config, mock_pr):
        """Test successful PR closure."""
        pr_manager = PrManager(mock_github_client, mock_config)
        result = pr_manager._close_pr(mock_pr, "Test reason")

        assert result is True
        mock_pr.edit.assert_called_once_with(state="closed")

    def test_close_pr_failure(self, mock_github_client, mock_config, mock_pr):
        """Test PR closure failure."""
        mock_pr.edit.side_effect = Exception("API Error")
        pr_manager = PrManager(mock_github_client, mock_config)
        result = pr_manager._close_pr(mock_pr, "Test reason")

        assert result is False

    def test_handle_validation_failure_comment_error(
        self, mock_github_client, mock_config, mock_pr
    ):
        """Test handling validation failure when comment posting fails."""
        mock_pr.create_issue_comment.side_effect = Exception("Comment API Error")
        validation_result = ValidationResult(is_valid=False, reason="No linked issue")

        pr_manager = PrManager(mock_github_client, mock_config)
        result = pr_manager.handle_validation_failure(mock_pr, validation_result)

        assert result is False
