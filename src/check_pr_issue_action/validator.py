"""Validation logic for PR-issue requirements."""

import logging

from github import Github, PullRequest
from github.Issue import Issue as GitHubIssue

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of PR validation."""

    def __init__(
        self,
        is_valid: bool,
        reason: str | None = None,
        issue: GitHubIssue | None = None,
    ):
        self.is_valid = is_valid
        self.reason = reason
        self.issue = issue


class PrValidator:
    """Validates PR requirements for issue linking and assignment."""

    def __init__(self, github_client: Github, config):
        self.github = github_client
        self.config = config

    def validate_pr(self, pr: PullRequest) -> ValidationResult:
        """
        Validate a PR against the configured requirements.

        Args:
            pr: The pull request to validate

        Returns:
            ValidationResult with validation status and details
        """
        logger.info(f"Validating PR #{pr.number} by {pr.user.login}")

        # Check if PR author is a bot (always skip)
        if pr.user.type == "Bot":
            logger.info(f"Skipping validation for bot user: {pr.user.login}")
            return ValidationResult(is_valid=True, reason="Bot user")

        # Check if PR author is in skip_users list
        if pr.user.login in self.config.skip_users:
            logger.info(f"Skipping validation for user in skip list: {pr.user.login}")
            return ValidationResult(is_valid=True, reason="User in skip list")

        # Validate issue linking
        issue_result = self._validate_issue_linking(pr)
        if not issue_result.is_valid:
            return issue_result

        # Validate assignee if required
        if self.config.require_assignee:
            assignee_result = self._validate_assignee(pr, issue_result.issue)
            if not assignee_result.is_valid:
                return assignee_result

        logger.info(f"PR #{pr.number} validation passed")
        return ValidationResult(
            is_valid=True, reason="All validations passed", issue=issue_result.issue
        )

    def _validate_issue_linking(self, pr: PullRequest) -> ValidationResult:
        """Validate that PR is linked to an issue."""
        try:
            # Get the issue associated with the PR
            issue = pr.issue()
            if issue:
                logger.info(f"PR #{pr.number} is linked to issue #{issue.number}")
                return ValidationResult(is_valid=True, issue=issue)
            else:
                logger.warning(f"PR #{pr.number} is not linked to any issue")
                return ValidationResult(is_valid=False, reason="No linked issue")
        except Exception as e:
            logger.error(f"Error checking issue linking for PR #{pr.number}: {e}")
            return ValidationResult(
                is_valid=False, reason="Error checking issue linking"
            )

    def _validate_assignee(
        self, pr: PullRequest, issue: GitHubIssue
    ) -> ValidationResult:
        """Validate that issue assignee matches PR author."""
        if not issue:
            return ValidationResult(is_valid=False, reason="No issue to check assignee")

        assignees = issue.assignees
        if not assignees:
            logger.warning(f"Issue #{issue.number} has no assignees")
            return ValidationResult(
                is_valid=False, reason="Issue has no assignee", issue=issue
            )

        pr_author = pr.user.login
        assignee_logins = [assignee.login for assignee in assignees]

        if pr_author in assignee_logins:
            logger.info(
                f"Issue #{issue.number} assignee matches PR author: {pr_author}"
            )
            return ValidationResult(is_valid=True, issue=issue)
        else:
            logger.warning(
                f"Issue #{issue.number} assignees {assignee_logins} do not include PR author {pr_author}"
            )
            return ValidationResult(
                is_valid=False, reason="Assignee mismatch", issue=issue
            )
