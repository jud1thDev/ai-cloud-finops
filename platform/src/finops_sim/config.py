"""Global configuration and path constants."""

from pathlib import Path

# Project root paths
PACKAGE_DIR = Path(__file__).parent
SCENARIOS_DIR = PACKAGE_DIR / "catalog" / "scenarios"
HCL_TEMPLATES_DIR = PACKAGE_DIR / "aws" / "hcl_templates"
COMPANY_TEMPLATES = PACKAGE_DIR / "company" / "templates.yaml"

# Default output
DEFAULT_OUTPUT_DIR = Path.cwd() / "output"

# Generation defaults
DEFAULT_SEED = 42
METRICS_DAYS = 30
METRICS_POINTS_PER_DAY = 24  # hourly resolution
COST_HISTORY_MONTHS = 6

# Scenario levels
LEVELS = ("L1", "L2", "L3")

# Scenario categories
CATEGORIES = (
    "unused",
    "overprovisioning",
    "rate",
    "anomaly",
    "tagging",
    "network",
    "architecture",
    "data",
)

# Business metrics
BUSINESS_METRICS_DAYS = 30

# Standard resource tags for compliance audit
STANDARD_TAGS = ("Service", "Team", "Env", "CostCenter", "Owner")
