FROM python:3.13-slim-bookworm

ARG HELM_DOCS_VERSION=1.14.2
ARG POETRY_VERSION=2.2.1

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install helm-docs with checksum verification
RUN cd /tmp && \
    curl -fsSL -o helm-docs.tar.gz \
        "https://github.com/norwoodj/helm-docs/releases/download/v${HELM_DOCS_VERSION}/helm-docs_${HELM_DOCS_VERSION}_Linux_x86_64.tar.gz" && \
    curl -fsSL -o checksums.txt \
        "https://github.com/norwoodj/helm-docs/releases/download/v${HELM_DOCS_VERSION}/helm-docs_${HELM_DOCS_VERSION}_checksums.txt" && \
    grep "_Linux_x86_64.tar.gz" checksums.txt | sed 's/helm-docs.*tar.gz/helm-docs.tar.gz/' | sha256sum -c && \
    tar -xzf helm-docs.tar.gz helm-docs && \
    mv helm-docs /usr/local/bin/ && \
    rm -f helm-docs.tar.gz checksums.txt

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

COPY pyproject.toml poetry.lock ./
COPY helm_charts_updater/ ./helm_charts_updater/

RUN pip install --no-cache-dir poetry==${POETRY_VERSION} && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi && \
    pip uninstall -y poetry && \
    chmod -R a-w helm_charts_updater/ && \
    chown -R appuser:appuser .

USER appuser

ENTRYPOINT ["helm-charts-updater"]
