"""Validation logic for PR-issue requirements."""

import logging
import re

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

        if pr.user.type == "Bot":
            logger.info(f"Skipping validation for bot user: {pr.user.login}")
            return ValidationResult(is_valid=True, reason="Bot user")

        if pr.user.login in self.config.skip_users:
            logger.info(f"Skipping validation for user in skip list: {pr.user.login}")
            return ValidationResult(is_valid=True, reason="User in skip list")

        branch_result = self._validate_target_branch(pr)
        if not branch_result.is_valid:
            return branch_result

        issue_result = self._validate_issue_linking(pr)
        if not issue_result.is_valid:
            if (
                self.config.check_issue_reference
                and issue_result.reason == "No linked issue"
            ):
                reference_result = self._validate_issue_reference(pr)
                if not reference_result.is_valid:
                    return reference_result
            else:
                return issue_result

        if self.config.require_assignee and issue_result.issue:
            assignee_result = self._validate_assignee(pr, issue_result.issue)
            if not assignee_result.is_valid:
                return assignee_result

        logger.info(f"PR #{pr.number} validation passed")
        return ValidationResult(
            is_valid=True, reason="All validations passed", issue=issue_result.issue
        )

    def _validate_issue_reference(self, pr: PullRequest) -> ValidationResult:
        """Validate that PR description contains a valid closing issue reference."""
        description = pr.body or ""
        if not description.strip():
            logger.warning(
                f"PR #{pr.number} has no linked issue and empty description for reference check"
            )
            return ValidationResult(
                is_valid=False,
                reason="No linked issue and no valid closing issue reference in PR description",
            )

        pattern = re.compile(
            r"\b(close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)\b"
            r"(?:\s+|:\s*)"
            r"(?:#[0-9]+|[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[0-9]+)",
            re.IGNORECASE,
        )

        if pattern.search(description):
            logger.info(
                f"PR #{pr.number} has a valid closing issue reference in description"
            )
            return ValidationResult(
                is_valid=True,
                reason="Valid closing issue reference found in PR description",
            )

        logger.warning(
            f"PR #{pr.number} has no linked issue and no valid closing issue reference in description"
        )
        return ValidationResult(
            is_valid=False,
            reason="No linked issue and no valid closing issue reference in PR description",
        )

    def _validate_issue_linking(self, pr: PullRequest) -> ValidationResult:
        """Validate that PR is linked to an issue using GraphQL API."""
        try:
            linked_issues = self._get_linked_issues_via_graphql(pr)

            if linked_issues is None:
                return ValidationResult(
                    is_valid=False, reason="Error checking issue linking"
                )
            elif linked_issues:
                issue_number = linked_issues[0]["number"]
                repo = pr.base.repo
                issue = repo.get_issue(issue_number)
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

    def _get_linked_issues_via_graphql(self, pr: PullRequest) -> list[dict] | None:
        """Get linked issues using GitHub GraphQL API closingIssuesReferences edge."""
        try:
            query = """
            query GetLinkedIssues($owner: String!, $repo: String!, $pullRequestNumber: Int!) {
              repository(owner: $owner, name: $repo) {
                pullRequest(number: $pullRequestNumber) {
                  closingIssuesReferences(first: 10, userLinkedOnly: false) {
                    edges {
                      node {
                        number
                        title
                        url
                        assignees(first: 10) {
                          edges {
                            node {
                              login
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
            """

            repo = pr.base.repo
            owner, repo_name = repo.full_name.split("/")

            variables = {
                "owner": owner,
                "repo": repo_name,
                "pullRequestNumber": pr.number,
            }

            requester = self.github._Github__requester
            headers, response = requester.requestJsonAndCheck(
                "POST",
                "/graphql",
                input={"query": query, "variables": variables},
            )

            if "errors" in response:
                logger.error(f"GraphQL errors: {response['errors']}")
                return None

            data = response.get("data", {})
            repository = data.get("repository", {})
            pull_request = repository.get("pullRequest", {})
            closing_issues_refs = pull_request.get("closingIssuesReferences", {})
            edges = closing_issues_refs.get("edges", [])

            logger.info(
                f"Data structure: data={bool(data)}, repository={bool(repository)}, pullRequest={bool(pull_request)}"
            )
            logger.info(f"closingIssuesReferences: {closing_issues_refs}")
            logger.info(f"edges: {edges}")

            linked_issues = [edge.get("node", {}) for edge in edges]

            logger.info(
                f"Found {len(linked_issues)} closing issues for PR #{pr.number}"
            )
            if linked_issues:
                logger.info(f"Linked issues: {linked_issues}")
            return linked_issues

        except Exception as e:
            logger.error(f"Error fetching linked issues via GraphQL: {e}")
            return None

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
        assignee_logins = {assignee.login for assignee in assignees}

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

    def _validate_target_branch(self, pr: PullRequest) -> ValidationResult:
        """Validate that PR is targeting an allowed branch."""
        target_branch = pr.base.ref
        logger.info(f"PR #{pr.number} is targeting branch: {target_branch}")

        if not self.config.target_branches:
            logger.info("No target branches configured, allowing all branches")
            return ValidationResult(is_valid=True, reason="No branch restrictions")

        try:
            default_branch = pr.base.repo.default_branch
            allowed_branches = set(self.config.target_branches)
            if default_branch not in allowed_branches:
                allowed_branches.add(default_branch)
                logger.info(
                    f"Added default branch '{default_branch}' to allowed branches"
                )
        except Exception as e:
            logger.warning(f"Could not get default branch: {e}")
            allowed_branches = set(self.config.target_branches)

        if target_branch in allowed_branches:
            logger.info(f"Target branch '{target_branch}' is in allowed list")
            return ValidationResult(is_valid=True, reason="Target branch allowed")
        else:
            logger.warning(
                f"Target branch '{target_branch}' is not in allowed list: {sorted(allowed_branches)}"
            )
            return ValidationResult(
                is_valid=False,
                reason=f"PR must target one of the allowed branches: {', '.join(sorted(allowed_branches))}",
            )
