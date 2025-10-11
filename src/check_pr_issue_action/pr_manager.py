"""PR management functionality for closing and messaging."""

import logging

from github import Github, PullRequest

logger = logging.getLogger(__name__)


class PrManager:
    """Manages PR operations like closing and posting messages."""

    def __init__(self, github_client: Github, config):
        self.github = github_client
        self.config = config

    def handle_validation_failure(self, pr: PullRequest, validation_result) -> bool:
        """
        Handle PR validation failure by posting message and optionally closing PR.

        Args:
            pr: The pull request that failed validation
            validation_result: The validation result with failure details

        Returns:
            True if operation succeeded, False otherwise
        """
        try:
            # Post appropriate error message
            message = self._get_error_message(validation_result)
            comment_success = self._post_comment(pr, message)

            # Close PR if configured to do so
            close_success = True
            if self.config.close_pr_on_failure:
                close_success = self._close_pr(pr, validation_result.reason)
                if close_success:
                    logger.info(
                        f"PR #{pr.number} closed due to validation failure: {validation_result.reason}"
                    )
                else:
                    logger.error(f"Failed to close PR #{pr.number}")
            else:
                logger.info(
                    f"PR #{pr.number} validation failed but not closed: {validation_result.reason}"
                )

            return comment_success and close_success

        except Exception as e:
            logger.error(f"Error handling validation failure for PR #{pr.number}: {e}")
            return False

    def _get_error_message(self, validation_result) -> str:
        """Get the appropriate error message based on validation failure."""
        if validation_result.reason == "No linked issue":
            return self.config.no_issue_message
        elif validation_result.reason == "Assignee mismatch":
            return self.config.no_assignee_message
        elif validation_result.reason == "Issue has no assignee":
            return self.config.no_assignee_message
        elif validation_result.reason and validation_result.reason.startswith(
            "PR must target one of the allowed branches"
        ):
            return self.config.invalid_branch_message
        else:
            return f"PR validation failed: {validation_result.reason}"

    def _post_comment(self, pr: PullRequest, message: str) -> bool:
        """Post a comment to the PR."""
        try:
            pr.create_issue_comment(message)
            logger.info(f"Posted comment to PR #{pr.number}")
            return True
        except Exception as e:
            logger.error(f"Failed to post comment to PR #{pr.number}: {e}")
            return False

    def _close_pr(self, pr: PullRequest, reason: str) -> bool:
        """Close the PR with a reason."""
        try:
            pr.edit(state="closed")
            logger.info(f"Closed PR #{pr.number} with reason: {reason}")
            return True
        except Exception as e:
            logger.error(f"Failed to close PR #{pr.number}: {e}")
            return False
