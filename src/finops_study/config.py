"""Configuration for the student CLI."""

from __future__ import annotations

import os

REPO_OWNER = os.environ.get("FINOPS_REPO_OWNER", "")
REPO_NAME = os.environ.get("FINOPS_REPO_NAME", "cloud-finops-ai")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
