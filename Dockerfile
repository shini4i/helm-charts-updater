FROM ghcr.io/shini4i/python-poetry:3.10-1.2.1

ENV HELM_DOCS_VERSION=1.11.0

RUN apt update && apt install curl git -y

COPY . .

RUN poetry install \
 && poetry build \
 && pip install dist/*.whl

RUN curl -L -o helm-docs.deb https://github.com/norwoodj/helm-docs/releases/download/v${HELM_DOCS_VERSION}/helm-docs_${HELM_DOCS_VERSION}_Linux_x86_64.deb \
 && apt install ./helm-docs.deb \
 && rm -f ./helm-docs.deb

ENTRYPOINT ["python", "/usr/local/bin/helm-charts-updater"]
