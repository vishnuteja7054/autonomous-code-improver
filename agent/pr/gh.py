"""
GitHub integration for creating and managing pull requests.
"""

import base64
import json
import os
from typing import Any, Dict, List, Optional

import requests
from loguru import logger

from agent.core.models import PRSummary


class GitHubClient:
    """
    Client for interacting with GitHub API.
    """
    
    def __init__(self, token: str):
        """
        Initialize the GitHub client.
        
        Args:
            token: GitHub personal access token
        """
        self.token = token
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
    def create_pull_request(
        self,
        repo_owner: str,
        repo_name: str,
        title: str,
        body: str,
        head: str,
        base: str
    ) -> Dict[str, Any]:
        """
        Create a pull request.
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            title: PR title
            body: PR body
            head: Head branch
            base: Base branch
            
        Returns:
            PR information
        """
        url = f"{self.api_base}/repos/{repo_owner}/{repo_name}/pulls"
        
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        return response.json()
        
    def update_pull_request(
        self,
        repo_owner: str,
        repo_name: str,
        pr_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a pull request.
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            pr_number: PR number
            title: New PR title
            body: New PR body
            state: New PR state ("open" or "closed")
            
        Returns:
            Updated PR information
        """
        url = f"{self.api_base}/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
        
        data = {}
        if title is not None:
            data["title"] = title
        if body is not None:
            data["body"] = body
        if state is not None:
            data["state"] = state
            
        response = requests.patch(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        return response.json()
        
    def get_pull_request(
        self,
        repo_owner: str,
        repo_name: str,
        pr_number: int
    ) -> Dict[str, Any]:
        """
        Get a pull request.
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            pr_number: PR number
            
        Returns:
            PR information
        """
        url = f"{self.api_base}/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
        
    def create_pull_request_comment(
        self,
        repo_owner: str,
        repo_name: str,
        pr_number: int,
        body: str
    ) -> Dict[str, Any]:
        """
        Create a comment on a pull request.
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            pr_number: PR number
            body: Comment body
            
        Returns:
            Comment information
        """
        url = f"{self.api_base}/repos/{repo_owner}/{repo_name}/issues/{pr_number}/comments"
        
        data = {
            "body": body
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        return response.json()
        
    def get_pull_request_comments(
        self,
        repo_owner: str,
        repo_name: str,
        pr_number: int
    ) -> List[Dict[str, Any]]:
        """
        Get comments on a pull request.
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            pr_number: PR number
            
        Returns:
            List of comments
        """
        url = f"{self.api_base}/repos/{repo_owner}/{repo_name}/issues/{pr_number}/comments"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
        
    def get_pull_request_reviews(
        self,
        repo_owner: str,
        repo_name: str,
        pr_number: int
    ) -> List[Dict[str, Any]]:
        """
        Get reviews on a pull request.
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            pr_number: PR number
            
        Returns:
            List of reviews
        """
        url = f"{self.api_base}/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/reviews"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
        
    def get_pull_request_files(
        self,
        repo_owner: str,
        repo_name: str,
        pr_number: int
    ) -> List[Dict[str, Any]]:
        """
        Get files in a pull request.
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            pr_number: PR number
            
        Returns:
            List of files
        """
        url = f"{self.api_base}/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/files"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
        
    def get_pull_request_status(
        self,
        repo_owner: str,
        repo_name: str,
        pr_number: int
    ) -> Dict[str, Any]:
        """
        Get the status of a pull request.
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            pr_number: PR number
            
        Returns:
            PR status information
        """
        # Get PR information
        pr = self.get_pull_request(repo_owner, repo_name, pr_number)
        
        # Get combined status
        url = f"{self.api_base}/repos/{repo_owner}/{repo_name}/commits/{pr['head']['sha']}/status"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        status = response.json()
        
        # Get reviews
        reviews = self.get_pull_request_reviews(repo_owner, repo_name, pr_number)
        
        return {
            "pr": pr,
            "status": status,
            "reviews": reviews
        }
        
    def merge_pull_request(
        self,
        repo_owner: str,
        repo_name: str,
        pr_number: int,
        commit_message: Optional[str] = None,
        merge_method: str = "merge"
    ) -> Dict[str, Any]:
        """
        Merge a pull request.
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            pr_number: PR number
            commit_message: Commit message for the merge
            merge_method: Merge method ("merge", "squash", or "rebase")
            
        Returns:
            Merge information
        """
        url = f"{self.api_base}/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/merge"
        
        data = {
            "merge_method": merge_method
        }
        
        if commit_message:
            data["commit_message"] = commit_message
            
        response = requests.put(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        return response.json()
        
    def close_pull_request(
        self,
        repo_owner: str,
        repo_name: str,
        pr_number: int
    ) -> Dict[str, Any]:
        """
        Close a pull request.
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            pr_number: PR number
            
        Returns:
            Updated PR information
        """
        return self.update_pull_request(
            repo_owner, repo_name, pr_number, state="closed"
        )


def create_pr(
    pr_summary: PRSummary,
    repo_owner: str,
    repo_name: str,
    head_branch: str,
    base_branch: str,
    github_token: str,
    attachments: Optional[List[Dict[str, Any]]] = None
) -> PRSummary:
    """
    Create a pull request on GitHub.
    
    Args:
        pr_summary: PR summary with title and description
        repo_owner: Repository owner
        repo_name: Repository name
        head_branch: Head branch
        base_branch: Base branch
        github_token: GitHub personal access token
        attachments: List of attachments to include in the PR body
        
    Returns:
        Updated PR summary with PR ID and URL
    """
    logger.info(f"Creating PR: {pr_summary.title}")
    
    try:
        # Initialize GitHub client
        client = GitHubClient(github_token)
        
        # Prepare PR body with attachments
        body = pr_summary.description
        
        if attachments:
            body += "\n\n## Attachments\n\n"
            
            for attachment in attachments:
                if attachment.get("type") == "coverage":
                    body += f"### Coverage Report\n\n"
                    body += f"- Overall coverage: {attachment.get('percentage', 0)}%\n"
                    body += f"- [View full report]({attachment.get('url', '#')})\n\n"
                elif attachment.get("type") == "benchmark":
                    body += f"### Benchmark Results\n\n"
                    for metric, value in attachment.get("metrics", {}).items():
                        body += f"- {metric}: {value}\n"
                    body += "\n"
                elif attachment.get("type") == "risk":
                    body += f"### Risk Assessment\n\n"
                    body += f"- Overall risk: {attachment.get('risk_level', 'unknown')}\n"
                    body += f"- Risk factors: {len(attachment.get('risk_factors', []))}\n"
                    body += "\n"
                    
        # Create PR
        pr_data = client.create_pull_request(
            repo_owner=repo_owner,
            repo_name=repo_name,
            title=pr_summary.title,
            body=body,
            head=head_branch,
            base=base_branch
        )
        
        # Update PR summary
        pr_summary.pr_id = pr_data["number"]
        pr_summary.pr_url = pr_data["html_url"]
        
        logger.info(f"Created PR: {pr_summary.pr_url}")
        return pr_summary
        
    except Exception as e:
        logger.error(f"Error creating PR: {e}")
        raise


def update_pr(
    pr_summary: PRSummary,
    repo_owner: str,
    repo_name: str,
    github_token: str,
    attachments: Optional[List[Dict[str, Any]]] = None
) -> PRSummary:
    """
    Update a pull request on GitHub.
    
    Args:
        pr_summary: PR summary with updated information
        repo_owner: Repository owner
        repo_name: Repository name
        github_token: GitHub personal access token
        attachments: List of attachments to include in the PR body
        
    Returns:
        Updated PR summary
    """
    logger.info(f"Updating PR #{pr_summary.pr_id}")
    
    try:
        # Initialize GitHub client
        client = GitHubClient(github_token)
        
        # Prepare PR body with attachments
        body = pr_summary.description
        
        if attachments:
            body += "\n\n## Attachments\n\n"
            
            for attachment in attachments:
                if attachment.get("type") == "coverage":
                    body += f"### Coverage Report\n\n"
                    body += f"- Overall coverage: {attachment.get('percentage', 0)}%\n"
                    body += f"- [View full report]({attachment.get('url', '#')})\n\n"
                elif attachment.get("type") == "benchmark":
                    body += f"### Benchmark Results\n\n"
                    for metric, value in attachment.get("metrics", {}).items():
                        body += f"- {metric}: {value}\n"
                    body += "\n"
                elif attachment.get("type") == "risk":
                    body += f"### Risk Assessment\n\n"
                    body += f"- Overall risk: {attachment.get('risk_level', 'unknown')}\n"
                    body += f"- Risk factors: {len(attachment.get('risk_factors', []))}\n"
                    body += "\n"
                    
        # Update PR
        pr_data = client.update_pull_request(
            repo_owner=repo_owner,
            repo_name=repo_name,
            pr_number=pr_summary.pr_id,
            title=pr_summary.title,
            body=body
        )
        
        logger.info(f"Updated PR #{pr_summary.pr_id}")
        return pr_summary
        
    except Exception as e:
        logger.error(f"Error updating PR: {e}")
        raise


def get_pr_status(
    pr_summary: PRSummary,
    repo_owner: str,
    repo_name: str,
    github_token: str
) -> Dict[str, Any]:
    """
    Get the status of a pull request.
    
    Args:
        pr_summary: PR summary
        repo_owner: Repository owner
        repo_name: Repository name
        github_token: GitHub personal access token
        
    Returns:
        PR status information
    """
    logger.info(f"Getting status for PR #{pr_summary.pr_id}")
    
    try:
        # Initialize GitHub client
        client = GitHubClient(github_token)
        
        # Get PR status
        status = client.get_pull_request_status(
            repo_owner=repo_owner,
            repo_name=repo_name,
            pr_number=pr_summary.pr_id
        )
        
        # Update PR summary
        pr_summary.merged = status["pr"]["merged"]
        pr_summary.closed = status["pr"]["state"] == "closed"
        
        if pr_summary.merged:
            pr_summary.merged_at = status["pr"]["merged_at"]
        elif pr_summary.closed:
            pr_summary.closed_at = status["pr"]["closed_at"]
            
        # Get CI status
        ci_status = status["status"]["state"]
        pr_summary.ci_status = ci_status
        
        # Get review comments
        reviews = status["reviews"]
        review_comments = []
        
        for review in reviews:
            if review.get("state") in ["APPROVED", "CHANGES_REQUESTED", "COMMENTED"]:
                review_comments.append({
                    "user": review["user"]["login"],
                    "state": review["state"],
                    "body": review.get("body", ""),
                    "submitted_at": review["submitted_at"]
                })
                
        pr_summary.review_comments = review_comments
        
        logger.info(f"Retrieved status for PR #{pr_summary.pr_id}: {ci_status}")
        return status
        
    except Exception as e:
        logger.error(f"Error getting PR status: {e}")
        raise
