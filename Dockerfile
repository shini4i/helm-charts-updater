FROM python:3.10.7-slim-buster

WORKDIR /src

ENV POETRY_HOME=/usr/bin/poetry \
    PATH=/usr/bin/poetry/bin:$PATH \
    POETRY_VERSION=1.2.1

ENV HELM_DOCS_VERSION=1.11.0

RUN apt update && apt install curl git -y

RUN curl -sSL https://install.python-poetry.org > ./install-poetry.py \
 && python ./install-poetry.py \
 && rm -f ./install-poetry.py

COPY . .

RUN poetry install \
 && poetry build \
 && pip install dist/*.whl

RUN curl -L -o helm-docs.deb https://github.com/norwoodj/helm-docs/releases/download/v${HELM_DOCS_VERSION}/helm-docs_${HELM_DOCS_VERSION}_Linux_x86_64.deb \
 && apt install ./helm-docs.deb \
 && rm -f ./helm-docs.deb

ENTRYPOINT ["python", "/usr/local/bin/helm-charts-updater"]
