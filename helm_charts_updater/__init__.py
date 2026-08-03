"""Helm Charts Updater - bump a chart in a separate Helm charts repository.

Clones a GitHub repository holding Helm charts, sets the target chart's
appVersion and bumps its chart version, then commits and pushes the change.
Optionally regenerates chart docs and the charts table in the repository README.
"""

import logging
import os

# Configure logging based on environment variable
_log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
)
