#!/usr/bin/env python3
"""Main entry point for the check-pr-issue-action."""

import json
import logging
import os
import sys

from github import Github

from .config import Config
from .pr_manager import PrManager
from .validator import PrValidator

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main function to run the GitHub Action."""
    try:
        # Load configuration
        config = Config()
        logger.info("Configuration loaded successfully")

        # Initialize GitHub client
        github = Github(config.github_token)
        logger.info("GitHub client initialized")

        # Get GitHub event context
        event_path = os.getenv("GITHUB_EVENT_PATH")
        if not event_path:
            logger.error("GITHUB_EVENT_PATH environment variable not set")
            sys.exit(1)

        with open(event_path) as f:
            event_data = json.load(f)

        # Extract PR information
        pr_data = event_data.get("pull_request")
        if not pr_data:
            logger.error("No pull request data found in event")
            sys.exit(1)

        # Get repository and PR
        repo_name = event_data["repository"]["full_name"]
        pr_number = pr_data["number"]

        logger.info(f"Processing PR #{pr_number} in repository {repo_name}")

        repo = github.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        # Initialize validator and PR manager
        validator = PrValidator(github, config)
        pr_manager = PrManager(github, config)

        # Validate PR
        validation_result = validator.validate_pr(pr)

        if validation_result.is_valid:
            logger.info(
                f"PR #{pr_number} validation passed: {validation_result.reason}"
            )
            sys.exit(0)
        else:
            logger.warning(
                f"PR #{pr_number} validation failed: {validation_result.reason}"
            )

            # Handle validation failure
            success = pr_manager.handle_validation_failure(pr, validation_result)
            if success:
                logger.info(
                    f"Successfully handled validation failure for PR #{pr_number}"
                )
                sys.exit(1)  # Exit with error code to indicate failure
            else:
                logger.error(f"Failed to handle validation failure for PR #{pr_number}")
                sys.exit(1)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
