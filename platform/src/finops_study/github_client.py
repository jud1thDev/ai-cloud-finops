"""GitHub Contents API wrapper for pulling/submitting problems."""

from __future__ import annotations

import base64
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Optional

from finops_study.config import GITHUB_TOKEN, REPO_NAME, REPO_OWNER


class GitHubClient:
    """Minimal GitHub API client using only stdlib."""

    def __init__(
        self,
        owner: str = "",
        repo: str = "",
        token: str = "",
    ) -> None:
        self.owner = owner or REPO_OWNER
        self.repo = repo or REPO_NAME
        self.token = token or GITHUB_TOKEN
        self.api_base = f"https://api.github.com/repos/{self.owner}/{self.repo}"

    def _headers(self) -> Dict[str, str]:
        h = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "finops-study-cli",
        }
        if self.token:
            h["Authorization"] = f"token {self.token}"
        return h

    def _request(self, path: str, method: str = "GET", data: bytes | None = None) -> Any:
        url = f"{self.api_base}{path}"
        req = urllib.request.Request(url, headers=self._headers(), method=method, data=data)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API error {e.code}: {body}") from e

    def list_contents(self, path: str) -> List[Dict[str, Any]]:
        """List contents of a directory in the repo."""
        return self._request(f"/contents/{path}")

    def get_file(self, path: str) -> str:
        """Get decoded file content."""
        data = self._request(f"/contents/{path}")
        content = data.get("content", "")
        return base64.b64decode(content).decode("utf-8")

    def download_directory(self, remote_path: str, local_dir: Path) -> List[Path]:
        """Download all files in a directory recursively."""
        downloaded: List[Path] = []
        items = self.list_contents(remote_path)

        for item in items:
            local_path = local_dir / item["name"]
            if item["type"] == "file":
                content = self.get_file(item["path"])
                local_path.parent.mkdir(parents=True, exist_ok=True)
                local_path.write_text(content, encoding="utf-8")
                downloaded.append(local_path)
            elif item["type"] == "dir":
                sub_dir = local_dir / item["name"]
                downloaded.extend(self.download_directory(item["path"], sub_dir))

        return downloaded

    def create_or_update_file(
        self,
        path: str,
        content: str,
        message: str,
        branch: str = "main",
    ) -> Dict[str, Any]:
        """Create or update a file in the repo."""
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")

        # Check if file exists to get sha
        sha: Optional[str] = None
        try:
            existing = self._request(f"/contents/{path}?ref={branch}")
            sha = existing.get("sha")
        except RuntimeError:
            pass

        payload: Dict[str, Any] = {
            "message": message,
            "content": encoded,
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.api_base}/contents/{path}",
            headers={**self._headers(), "Content-Type": "application/json"},
            method="PUT",
            data=data,
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
