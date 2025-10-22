import re
import base64
import requests
from typing import Optional, Tuple
from agno.tools import Toolkit


class GitHubTools(Toolkit):
    def __init__(self, **kwargs):
        super().__init__(name="github_readme_tools",
                         tools=[self.get_readme_content, self.download_file_from_repo],
                         **kwargs)

    def _parse_github_url(self, repo_url: str) -> Tuple[str, str]:
        """
        Extract owner and repository name from a GitHub URL.
        """
        github_pattern = r"github\.com[/:]([^/]+)/([^/]+)"
        match = re.search(github_pattern, repo_url)
        
        if not match:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
        
        owner, repo = match.groups()
        return owner, repo.replace(".git", "")

    def get_readme_content(self, repo_url: str, pat: Optional[str] = None) -> str:
        """
        Fetch the content of the README file from a GitHub repository.
        """
        try:
            owner, repo = self._parse_github_url(repo_url)
            api_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
            headers = {"Accept": "application/vnd.github.v3.raw"}
            if pat:
                headers["Authorization"] = f"Bearer {pat}"

            response = requests.get(api_url, headers=headers, timeout=10)

            if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers:
                if int(response.headers['X-RateLimit-Remaining']) == 0:
                    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                    raise requests.HTTPError(
                        f"GitHub API rate limit exceeded. Reset at timestamp {reset_time}. "
                        f"Use a PAT to increase rate limits."
                    )

            response.raise_for_status()
            return response.text

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                raise requests.HTTPError(f"README not found for {owner}/{repo}. The repository may be private or doesn't exist.")
            elif e.response.status_code == 401:
                raise requests.HTTPError(f"Authentication failed. Check your Personal Access Token.")
            raise
        except Exception as e:
            raise ValueError(f"Failed to fetch README: {str(e)}")

    def download_file_from_repo(self,
                                repo_url: str,
                                file_path: str,
                                output_file: str = "downloaded_file.xlsx",
                                branch: str = "main",
                                pat: Optional[str] = None) -> str:
        """
        Download a file from a GitHub repository (public or private).

        Args:
            repo_url (str): GitHub repository URL
            file_path (str): Path to the file in the repository
            output_file (str): Local file name to save
            branch (str): Branch name (default: 'main')
            pat (Optional[str]): GitHub Personal Access Token (for private repos)

        Returns:
            str: Path to the saved file

        Raises:
            Exception: If the file could not be downloaded
        """
        owner, repo = self._parse_github_url(repo_url)

        if pat:
            # Use GitHub API (private/public with auth)
            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
            headers = {"Authorization": f"token {pat}"}
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                file_data = response.json()
                content = base64.b64decode(file_data["content"])
            else:
                raise Exception(f"GitHub API error: {response.status_code}, {response.text}")
        else:
            # Use raw.githubusercontent.com (public only)
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
            response = requests.get(raw_url)
            if response.status_code == 200:
                content = response.content
            else:
                raise Exception(f"Failed to download file: {response.status_code}, {response.text}")

        with open(output_file, "wb") as f:
            f.write(content)

        return output_file