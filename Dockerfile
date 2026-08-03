FROM python:3.14-slim-trixie

ARG HELM_DOCS_VERSION=1.14.2

# uv ships as a single static binary; it is removed again once the venv is built
COPY --from=ghcr.io/astral-sh/uv:0.12.1 /uv /usr/local/bin/uv

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
WORKDIR /tmp
# --proto '=https' refuses a redirect that downgrades to plaintext
RUN curl -fsSL --proto '=https' --tlsv1.2 -o helm-docs.tar.gz \
        "https://github.com/norwoodj/helm-docs/releases/download/v${HELM_DOCS_VERSION}/helm-docs_${HELM_DOCS_VERSION}_Linux_x86_64.tar.gz" && \
    curl -fsSL --proto '=https' --tlsv1.2 -o checksums.txt \
        "https://github.com/norwoodj/helm-docs/releases/download/v${HELM_DOCS_VERSION}/checksums.txt" && \
    grep "_Linux_x86_64.tar.gz" checksums.txt | sed 's/helm-docs.*tar.gz/helm-docs.tar.gz/' | sha256sum -c && \
    tar -xzf helm-docs.tar.gz helm-docs && \
    mv helm-docs /usr/local/bin/ && \
    rm -f helm-docs.tar.gz checksums.txt

RUN groupadd --gid 1000 appuser && \
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
