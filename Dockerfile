FROM python:3.14-slim-trixie

ARG HELM_DOCS_VERSION=1.14.2
# Digest of the release above; update both together. Pinning it here is stronger
# than verifying against the upstream checksums.txt, which an attacker able to
# replace the archive could replace as well.
ARG HELM_DOCS_SHA256=a8cf72ada34fad93285ba2a452b38bdc5bd52cc9a571236244ec31022928d6cc

# uv ships as a single static binary; it is removed again once the venv is built
COPY --from=ghcr.io/astral-sh/uv:0.12.1 /uv /usr/local/bin/uv

ADD --checksum=sha256:${HELM_DOCS_SHA256} \
    "https://github.com/norwoodj/helm-docs/releases/download/v${HELM_DOCS_VERSION}/helm-docs_${HELM_DOCS_VERSION}_Linux_x86_64.tar.gz" \
    /tmp/helm-docs.tar.gz

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    tar -xzf /tmp/helm-docs.tar.gz -C /usr/local/bin helm-docs && \
    rm -f /tmp/helm-docs.tar.gz && \
    groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY helm_charts_updater/ ./helm_charts_updater/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

RUN uv sync --locked --no-dev --no-editable && \
    rm /usr/local/bin/uv

# /app stays root-owned — the app never writes to its own code — so standalone
# runs clone into a directory the runtime user owns. As a GitHub Action this
# WORKDIR is overridden: the runner mounts its workspace and runs from
# /github/workspace.
ENV PATH="/app/.venv/bin:$PATH"
RUN mkdir -p /workspace && chown appuser:appuser /workspace
WORKDIR /workspace

USER appuser

ENTRYPOINT ["helm-charts-updater"]
