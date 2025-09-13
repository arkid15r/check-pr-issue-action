"""Tests for validator module."""

from unittest.mock import Mock

from check_pr_issue_action.validator import PrValidator, ValidationResult


class TestPrValidator:
    """Test cases for PrValidator class."""

    def test_validate_bot_pr(self, mock_github_client, mock_config, mock_bot_pr):
        """Test that bot PRs are always skipped."""
        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_bot_pr)

        assert result.is_valid is True
        assert result.reason == "Bot user"

    def test_validate_skip_user_pr(self, mock_github_client, mock_config, mock_pr):
        """Test that PRs from skip users are skipped."""
        mock_pr.user.login = "testuser1"  # This user is in skip_users
        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_pr)

        assert result.is_valid is True
        assert result.reason == "User in skip list"

    def test_validate_pr_with_linked_issue(
        self, mock_github_client, mock_config, mock_pr, mock_issue_with_assignee
    ):
        """Test validation of PR with properly linked issue and matching assignee."""
        mock_pr.issue.return_value = mock_issue_with_assignee
        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_pr)

        assert result.is_valid is True
        assert result.reason == "All validations passed"
        assert result.issue == mock_issue_with_assignee

    def test_validate_pr_no_linked_issue(
        self, mock_github_client, mock_config, mock_pr
    ):
        """Test validation of PR with no linked issue."""
        mock_pr.issue.return_value = None
        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_pr)

        assert result.is_valid is False
        assert result.reason == "No linked issue"

    def test_validate_pr_issue_linking_error(
        self, mock_github_client, mock_config, mock_pr
    ):
        """Test handling of error when checking issue linking."""
        mock_pr.issue.side_effect = Exception("API Error")
        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_pr)

        assert result.is_valid is False
        assert result.reason == "Error checking issue linking"

    def test_validate_pr_assignee_mismatch(
        self,
        mock_github_client,
        mock_config,
        mock_pr,
        mock_issue_with_different_assignee,
    ):
        """Test validation when assignee doesn't match PR author."""
        mock_pr.issue.return_value = mock_issue_with_different_assignee
        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_pr)

        assert result.is_valid is False
        assert result.reason == "Assignee mismatch"
        assert result.issue == mock_issue_with_different_assignee

    def test_validate_pr_no_assignee(
        self, mock_github_client, mock_config, mock_pr, mock_issue
    ):
        """Test validation when issue has no assignee."""
        mock_pr.issue.return_value = mock_issue
        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_pr)

        assert result.is_valid is False
        assert result.reason == "Issue has no assignee"
        assert result.issue == mock_issue

    def test_validate_pr_assignee_not_required(
        self, mock_github_client, mock_pr, mock_issue
    ):
        """Test validation when assignee requirement is disabled."""
        mock_config = Mock()
        mock_config.skip_users = []
        mock_config.require_assignee = False
        mock_pr.issue.return_value = mock_issue

        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_pr)

        assert result.is_valid is True
        assert result.reason == "All validations passed"
        assert result.issue == mock_issue


class TestValidationResult:
    """Test cases for ValidationResult class."""

    def test_validation_result_creation(self):
        """Test ValidationResult creation."""
        result = ValidationResult(is_valid=True, reason="Test reason", issue=Mock())

        assert result.is_valid is True
        assert result.reason == "Test reason"
        assert result.issue is not None

    def test_validation_result_minimal(self):
        """Test ValidationResult with minimal parameters."""
        result = ValidationResult(is_valid=False)

        assert result.is_valid is False
        assert result.reason is None
        assert result.issue is None
