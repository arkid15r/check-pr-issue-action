"""Configuration management for the check-pr-issue-action."""

import logging
import os

logger = logging.getLogger(__name__)


class Config:
    """Configuration class for the GitHub Action."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        self.github_token = self._get_required_input("github_token")
        self.skip_users = self._parse_skip_users()
        self.require_assignee = self._get_boolean_input("require_assignee", False)
        self.close_pr_on_failure = self._get_boolean_input("close_pr_on_failure", True)
        self.no_issue_message = self._get_input(
            "no_issue_message",
            "This PR must be linked to an issue before it can be merged.",
        )
        self.no_assignee_message = self._get_input(
            "no_assignee_message",
            "The linked issue must be assigned to the PR author before this PR can be merged.",
        )
        self.target_branches = self._parse_target_branches()
        self.invalid_branch_message = self._get_input(
            "invalid_branch_message",
            "This PR must target one of the allowed branches.",
        )

        logger.info(
            f"Configuration loaded: skip_users={self.skip_users}, "
            f"require_assignee={self.require_assignee}, "
            f"close_pr_on_failure={self.close_pr_on_failure}, "
            f"target_branches={self.target_branches}"
        )

    def _get_required_input(self, name: str) -> str:
        """Get a required input from environment variables."""
        value = os.getenv(f"INPUT_{name.upper()}")
        if not value:
            raise ValueError(f"Required input '{name}' is not provided")
        return value

    def _get_input(self, name: str, default: str = "") -> str:
        """Get an optional input from environment variables."""
        return os.getenv(f"INPUT_{name.upper()}", default)

    def _get_boolean_input(self, name: str, default: bool = False) -> bool:
        """Get a boolean input from environment variables."""
        value = self._get_input(name, str(default)).lower()
        return value in ("true", "1", "yes", "on")

    def _parse_skip_users(self) -> list[str]:
        """Parse comma-separated skip users list."""
        users_str = self._get_input("skip_users", "")
        if not users_str:
            return []

        users = [user.strip() for user in users_str.split(",") if user.strip()]
        logger.info(f"Skip users configured: {users}")
        return users

    def _parse_target_branches(self) -> list[str]:
        """Parse newline-separated target branches list."""
        branches_str = self._get_input("target_branches", "")
        if not branches_str:
            return []

        branches = [
            branch.strip() for branch in branches_str.split("\n") if branch.strip()
        ]
        logger.info(f"Target branches configured: {branches}")
        return branches
