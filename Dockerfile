FROM python:3.13-slim-bookworm

ARG HELM_DOCS_VERSION=1.14.2

# Install system dependencies and clean up in single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        git \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install helm-docs with checksum verification
RUN curl -L -o /tmp/helm-docs.tar.gz \
        "https://github.com/norwoodj/helm-docs/releases/download/v${HELM_DOCS_VERSION}/helm-docs_${HELM_DOCS_VERSION}_Linux_x86_64.tar.gz" && \
    curl -L -o /tmp/helm-docs_checksums.txt \
        "https://github.com/norwoodj/helm-docs/releases/download/v${HELM_DOCS_VERSION}/helm-docs_${HELM_DOCS_VERSION}_checksums.txt" && \
    cd /tmp && grep "helm-docs_${HELM_DOCS_VERSION}_Linux_x86_64.tar.gz" helm-docs_checksums.txt | sha256sum -c - && \
    tar -xzf helm-docs.tar.gz helm-docs && \
    mv helm-docs /usr/local/bin/helm-docs && \
    rm -f /tmp/helm-docs.tar.gz /tmp/helm-docs_checksums.txt

WORKDIR /app

# Copy and install dependencies first for better caching
COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi --no-root

# Create non-root user for security
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Copy application code
COPY --chown=appuser:appuser helm_charts_updater/ ./helm_charts_updater/

# Install the package to create the console script entry point
RUN poetry install --only main --no-interaction --no-ansi && \
    pip uninstall -y poetry

# Switch to non-root user
USER appuser

ENTRYPOINT ["helm-charts-updater"]
