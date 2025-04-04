import json
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Generator
import requests
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin import Tool


class GitlabCommitsTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        branch = tool_parameters.get("branch", "")
        repository = tool_parameters.get("repository", "")
        employee = tool_parameters.get("employee", "")
        start_time = tool_parameters.get("start_time", "")
        end_time = tool_parameters.get("end_time", "")
        change_type = tool_parameters.get("change_type", "all")
        page = tool_parameters.get("page", "1")
        max_page = tool_parameters.get("max_page", "")
        page_size = tool_parameters.get("page_size", "100")
        if not repository:
            yield self.create_text_message("Either repository is required")
        if not start_time:
            start_time = (datetime.utcnow() - timedelta(days=1)).isoformat()
        if not end_time:
            end_time = datetime.utcnow().isoformat()
        access_token = self.runtime.credentials.get("access_tokens")
        site_url = self.runtime.credentials.get("site_url")
        if "access_tokens" not in self.runtime.credentials or not self.runtime.credentials.get("access_tokens"):
            yield self.create_text_message("Gitlab API Access Tokens is required.")
        if "site_url" not in self.runtime.credentials or not self.runtime.credentials.get("site_url"):
            site_url = "https://gitlab.com"
        result = self.fetch_commits(
            site_url, access_token, repository, branch, employee, start_time, end_time, change_type, is_repository=True,page=page,page_size=page_size,max_page=max_page
        )
        for item in result:
            yield self.create_json_message(item)

    def fetch_commits(
        self,
        site_url: str,
        access_token: str,
        repository: str,
        branch: str,
        employee: str,
        start_time: str,
        end_time: str,
        change_type: str,
        is_repository: bool,
        page: int,
        page_size:int,
        max_page:int
    ) -> list[dict[str, Any]]:
        domain = site_url
        headers = {"PRIVATE-TOKEN": access_token}
        results = []
        while True:
            try:
                if not max_page and page >= max_page:
                    break
                encoded_repository = urllib.parse.quote(repository, safe="")
                commits_url = f"{domain}/api/v4/projects/{encoded_repository}/repository/commits"
                params = {"page":page, "per_page": page_size}
                if branch:
                    params["ref_name"] = branch
                if employee:
                    params["author"] = employee
                commits_response = requests.get(commits_url, headers=headers, params=params)
                commits_response.raise_for_status()
                commits = commits_response.json()
                print(f"commits_url={commits_url} Page={page} commits_size: {len(commits)}")
                if not commits:
                    break
                page+=1
                for commit in commits:
                    results.append(commit)
            except requests.RequestException as e:
                print(f"Error fetching data from GitLab: {e}")
        return results
