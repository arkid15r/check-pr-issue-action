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
        # Mock GraphQL response for linked issues
        mock_pr.base.repo.full_name = "testowner/testrepo"
        mock_github_client._Github__requester.requestJsonAndCheck.return_value = (
            {},
            {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "closingIssuesReferences": {
                                "edges": [
                                    {
                                        "node": {
                                            "number": 456,
                                            "title": "Test Issue",
                                            "url": "https://github.com/testowner/testrepo/issues/456",
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            },
        )
        mock_pr.base.repo.get_issue.return_value = mock_issue_with_assignee
        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_pr)

        assert result.is_valid is True
        assert result.reason == "All validations passed"
        assert result.issue == mock_issue_with_assignee

    def test_validate_pr_no_linked_issue(
        self, mock_github_client, mock_config, mock_pr
    ):
        """Test validation of PR with no linked issue."""
        # Mock GraphQL response with no linked issues
        mock_pr.base.repo.full_name = "testowner/testrepo"
        mock_github_client._Github__requester.requestJsonAndCheck.return_value = (
            {},
            {
                "data": {
                    "repository": {
                        "pullRequest": {"closingIssuesReferences": {"edges": []}}
                    }
                }
            },
        )
        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_pr)

        assert result.is_valid is False
        assert result.reason == "No linked issue"

    def test_validate_pr_no_linked_issue_with_description_reference_enabled_and_valid(
        self, mock_github_client, mock_config, mock_pr, mock_issue
    ):
        """When no linked issue and check_issue_reference is enabled, valid description reference should pass."""
        mock_config.check_issue_reference = True
        mock_config.require_assignee = False
        mock_pr.body = "This PR fixes #123"
        mock_pr.base.repo.full_name = "testowner/testrepo"

        def graphql_side_effect(*args, **kwargs):
            input_data = kwargs.get("input", {})
            query = input_data.get("query", "")
            variables = input_data.get("variables", {})

            if "GetLinkedIssues" in query:
                return (
                    {},
                    {
                        "data": {
                            "repository": {
                                "pullRequest": {
                                    "closingIssuesReferences": {"edges": []}
                                }
                            }
                        }
                    },
                )
            elif "GetIssue" in query and variables.get("issueNumber") == 123:
                return (
                    {},
                    {
                        "data": {
                            "repository": {
                                "issue": {
                                    "number": 123,
                                    "title": "Test Issue",
                                    "url": "https://github.com/testowner/testrepo/issues/123",
                                    "assignees": {"edges": []},
                                }
                            }
                        }
                    },
                )
            return ({}, {"data": {}})

        mock_github_client._Github__requester.requestJsonAndCheck.side_effect = (
            graphql_side_effect
        )
        mock_pr.base.repo.get_issue.return_value = mock_issue

        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_pr)

        assert result.is_valid is True
        assert result.reason == "All validations passed"

    def test_validate_pr_no_linked_issue_with_description_reference_enabled_and_invalid(
        self, mock_github_client, mock_config, mock_pr
    ):
        """When no linked issue and check_issue_reference is enabled, invalid description reference should fail."""
        mock_config.check_issue_reference = True
        mock_pr.body = "This PR references issue #123 but without closing keyword"
        mock_pr.base.repo.full_name = "testowner/testrepo"
        mock_github_client._Github__requester.requestJsonAndCheck.return_value = (
            {},
            {
                "data": {
                    "repository": {
                        "pullRequest": {"closingIssuesReferences": {"edges": []}}
                    }
                }
            },
        )

        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_pr)

        assert result.is_valid is False
        assert (
            result.reason
            == "No linked issue and no valid closing issue reference in PR description"
        )

    def test_validate_pr_no_linked_issue_with_invalid_reference_format(
        self, mock_github_client, mock_config, mock_pr
    ):
        """Invalid reference format in description should be rejected."""
        mock_config.check_issue_reference = True
        mock_config.require_assignee = False
        mock_pr.body = "Resolves some-org/some-repo#42"
        mock_pr.base.repo.full_name = "testowner/testrepo"
        mock_github_client._Github__requester.requestJsonAndCheck.return_value = (
            {},
            {
                "data": {
                    "repository": {
                        "pullRequest": {"closingIssuesReferences": {"edges": []}}
                    }
                }
            },
        )

        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_pr)

        assert result.is_valid is False
        assert (
            result.reason
            == "No linked issue and no valid closing issue reference in PR description"
        )

    def test_validate_pr_invalid_reference_format_with_require_assignee(
        self, mock_github_client, mock_config, mock_pr
    ):
        """Invalid reference format should fail regardless of require_assignee setting."""
        mock_config.check_issue_reference = True
        mock_config.require_assignee = True
        mock_pr.body = "Resolves some-org/some-repo#42"
        mock_pr.base.repo.full_name = "testowner/testrepo"
        mock_github_client._Github__requester.requestJsonAndCheck.return_value = (
            {},
            {
                "data": {
                    "repository": {
                        "pullRequest": {"closingIssuesReferences": {"edges": []}}
                    }
                }
            },
        )

        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_pr)

        assert result.is_valid is False
        assert (
            result.reason
            == "No linked issue and no valid closing issue reference in PR description"
        )

    def test_validate_pr_description_reference_with_assignee_check(
        self, mock_github_client, mock_config, mock_pr, mock_issue_with_assignee
    ):
        """When description reference exists and require_assignee is enabled, should fetch issue and validate assignee."""
        mock_config.check_issue_reference = True
        mock_config.require_assignee = True
        mock_pr.body = "This PR fixes #456"
        mock_pr.base.repo.full_name = "testowner/testrepo"

        def graphql_side_effect(*args, **kwargs):
            input_data = kwargs.get("input", {})
            query = input_data.get("query", "")
            variables = input_data.get("variables", {})

            if "GetLinkedIssues" in query:
                return (
                    {},
                    {
                        "data": {
                            "repository": {
                                "pullRequest": {
                                    "closingIssuesReferences": {"edges": []}
                                }
                            }
                        }
                    },
                )
            elif "GetIssue" in query and variables.get("issueNumber") == 456:
                return (
                    {},
                    {
                        "data": {
                            "repository": {
                                "issue": {
                                    "number": 456,
                                    "title": "Test Issue",
                                    "url": "https://github.com/testowner/testrepo/issues/456",
                                    "assignees": {
                                        "edges": [{"node": {"login": "testuser"}}]
                                    },
                                }
                            }
                        }
                    },
                )
            return ({}, {"data": {}})

        mock_github_client._Github__requester.requestJsonAndCheck.side_effect = (
            graphql_side_effect
        )
        mock_pr.base.repo.get_issue.return_value = mock_issue_with_assignee

        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_pr)

        assert result.is_valid is True
        assert result.reason == "All validations passed"

    def test_validate_pr_description_reference_with_assignee_mismatch(
        self,
        mock_github_client,
        mock_config,
        mock_pr,
        mock_issue_with_different_assignee,
    ):
        """When description reference exists and assignee doesn't match, should fail validation."""
        mock_config.check_issue_reference = True
        mock_config.require_assignee = True
        mock_pr.body = "This PR fixes #456"
        mock_pr.base.repo.full_name = "testowner/testrepo"

        def graphql_side_effect(*args, **kwargs):
            input_data = kwargs.get("input", {})
            query = input_data.get("query", "")
            variables = input_data.get("variables", {})

            if "GetLinkedIssues" in query:
                return (
                    {},
                    {
                        "data": {
                            "repository": {
                                "pullRequest": {
                                    "closingIssuesReferences": {"edges": []}
                                }
                            }
                        }
                    },
                )
            elif "GetIssue" in query and variables.get("issueNumber") == 456:
                return (
                    {},
                    {
                        "data": {
                            "repository": {
                                "issue": {
                                    "number": 456,
                                    "title": "Test Issue",
                                    "url": "https://github.com/testowner/testrepo/issues/456",
                                    "assignees": {
                                        "edges": [{"node": {"login": "differentuser"}}]
                                    },
                                }
                            }
                        }
                    },
                )
            return ({}, {"data": {}})

        mock_github_client._Github__requester.requestJsonAndCheck.side_effect = (
            graphql_side_effect
        )
        mock_pr.base.repo.get_issue.return_value = mock_issue_with_different_assignee

        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_pr)

        assert result.is_valid is False
        assert result.reason == "Assignee mismatch"

    def test_validate_pr_issue_linking_error(
        self, mock_github_client, mock_config, mock_pr
    ):
        """Test handling of error when checking issue linking."""
        # Mock GraphQL response with errors
        mock_pr.base.repo.full_name = "testowner/testrepo"
        mock_github_client._Github__requester.requestJsonAndCheck.return_value = (
            {},
            {"errors": [{"message": "GraphQL API Error"}]},
        )
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
        # Mock GraphQL response for linked issues
        mock_pr.base.repo.full_name = "testowner/testrepo"
        mock_github_client._Github__requester.requestJsonAndCheck.return_value = (
            {},
            {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "closingIssuesReferences": {
                                "edges": [
                                    {
                                        "node": {
                                            "number": 456,
                                            "title": "Test Issue",
                                            "url": "https://github.com/testowner/testrepo/issues/456",
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            },
        )
        mock_pr.base.repo.get_issue.return_value = mock_issue_with_different_assignee
        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_pr)

        assert result.is_valid is False
        assert result.reason == "Assignee mismatch"
        assert result.issue == mock_issue_with_different_assignee

    def test_validate_pr_no_assignee(
        self, mock_github_client, mock_config, mock_pr, mock_issue
    ):
        """Test validation when issue has no assignee."""
        # Mock GraphQL response for linked issues
        mock_pr.base.repo.full_name = "testowner/testrepo"
        mock_github_client._Github__requester.requestJsonAndCheck.return_value = (
            {},
            {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "closingIssuesReferences": {
                                "edges": [
                                    {
                                        "node": {
                                            "number": 456,
                                            "title": "Test Issue",
                                            "url": "https://github.com/testowner/testrepo/issues/456",
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            },
        )
        mock_pr.base.repo.get_issue.return_value = mock_issue
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
        mock_config.target_branches = []
        # Mock GraphQL response for linked issues
        mock_pr.base.repo.full_name = "testowner/testrepo"
        mock_github_client._Github__requester.requestJsonAndCheck.return_value = (
            {},
            {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "closingIssuesReferences": {
                                "edges": [
                                    {
                                        "node": {
                                            "number": 456,
                                            "title": "Test Issue",
                                            "url": "https://github.com/testowner/testrepo/issues/456",
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            },
        )
        mock_pr.base.repo.get_issue.return_value = mock_issue

        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_pr)

        assert result.is_valid is True
        assert result.reason == "All validations passed"
        assert result.issue == mock_issue

    def test_validate_pr_graphql_error_handling(
        self, mock_github_client, mock_config, mock_pr
    ):
        """Test GraphQL error handling."""
        mock_pr.base.repo.full_name = "testowner/testrepo"
        mock_github_client._Github__requester.requestJsonAndCheck.side_effect = (
            Exception("Network error")
        )

        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_pr)

        assert result.is_valid is False
        assert result.reason == "Error checking issue linking"

    def test_validate_target_branch_no_restrictions(
        self, mock_github_client, mock_config, mock_pr
    ):
        """Test branch validation when no target branches are configured."""
        mock_config.target_branches = []
        validator = PrValidator(mock_github_client, mock_config)
        result = validator._validate_target_branch(mock_pr)

        assert result.is_valid is True
        assert result.reason == "No branch restrictions"

    def test_validate_target_branch_allowed(
        self, mock_github_client, mock_config, mock_pr
    ):
        """Test branch validation when PR targets an allowed branch."""
        mock_config.target_branches = ["main", "develop", "feature-branch"]
        mock_pr.base.ref = "develop"
        validator = PrValidator(mock_github_client, mock_config)
        result = validator._validate_target_branch(mock_pr)

        assert result.is_valid is True
        assert result.reason == "Target branch allowed"

    def test_validate_target_branch_not_allowed(
        self, mock_github_client, mock_config, mock_pr
    ):
        """Test branch validation when PR targets a disallowed branch."""
        mock_config.target_branches = ["develop", "release"]
        mock_pr.base.ref = "feature-branch"
        # Set default branch to "main" (different from target_branches)
        mock_pr.base.repo.default_branch = "main"
        validator = PrValidator(mock_github_client, mock_config)
        result = validator._validate_target_branch(mock_pr)

        assert result.is_valid is False
        assert "PR must target one of the allowed branches" in result.reason
        # Should include both the configured branches and the default branch
        assert "develop" in result.reason
        assert "release" in result.reason
        assert "main" in result.reason

    def test_validate_target_branch_default_included(
        self, mock_github_client, mock_config, mock_pr
    ):
        """Test that default branch is automatically included in allowed branches."""
        mock_config.target_branches = ["develop", "release"]
        mock_pr.base.ref = "main"  # PR targets default branch
        mock_pr.base.repo.default_branch = "main"
        validator = PrValidator(mock_github_client, mock_config)
        result = validator._validate_target_branch(mock_pr)

        assert result.is_valid is True
        assert result.reason == "Target branch allowed"

    def test_validate_pr_with_branch_restriction_allowed(
        self, mock_github_client, mock_config, mock_pr, mock_issue_with_assignee
    ):
        """Test full PR validation with branch restriction when branch is allowed."""
        mock_config.target_branches = ["main", "develop"]
        mock_pr.base.ref = "main"

        # Mock GraphQL response for linked issue
        mock_pr.base.repo.full_name = "testowner/testrepo"
        mock_github_client._Github__requester.requestJsonAndCheck.return_value = (
            {},
            {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "closingIssuesReferences": {
                                "edges": [
                                    {
                                        "node": {
                                            "number": 456,
                                            "title": "Test Issue",
                                            "url": "https://github.com/testowner/testrepo/issues/456",
                                            "assignees": {
                                                "edges": [
                                                    {"node": {"login": "testuser"}}
                                                ]
                                            },
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            },
        )
        mock_pr.base.repo.get_issue.return_value = mock_issue_with_assignee

        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_pr)

        assert result.is_valid is True
        assert result.reason == "All validations passed"

    def test_validate_pr_with_branch_restriction_not_allowed(
        self, mock_github_client, mock_config, mock_pr
    ):
        """Test full PR validation with branch restriction when branch is not allowed."""
        mock_config.target_branches = ["main", "develop"]
        mock_pr.base.ref = "feature-branch"

        validator = PrValidator(mock_github_client, mock_config)
        result = validator.validate_pr(mock_pr)

        assert result.is_valid is False
        assert "PR must target one of the allowed branches" in result.reason


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
