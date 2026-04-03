"""Helm Charts Updater - A tool to update helm charts in a given repository.

This package provides functionality to automatically update Helm chart
versions and push changes to a GitHub repository.
"""

import logging
import os

from helm_charts_updater.config import Config

__all__ = ["config", "Config"]

# Initialize configuration singleton
config = Config()

# Configure logging based on environment variable
_log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
)
