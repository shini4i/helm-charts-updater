ARG PYTHON_VERSION=3.10.3-slim-buster

##################
# Backend build
##################
FROM python:${PYTHON_VERSION} as builder

WORKDIR /src

RUN apt update \
 && apt install gcc -y \
 && apt clean

RUN pip install cryptography==3.1.1 \
 && pip install "poetry==1.1.5"

COPY poetry.lock pyproject.toml /src/

RUN poetry export -f requirements.txt | pip install -r /dev/stdin

COPY . .

RUN poetry build

##################
# The resulting image build
##################
FROM python:${PYTHON_VERSION}

WORKDIR /app

COPY --from=builder /src/dist/*.tar.gz /app

RUN apt update && apt install -y git wget && apt clean

RUN wget https://github.com/norwoodj/helm-docs/releases/download/v1.11.0/helm-docs_1.11.0_Linux_x86_64.deb \
 && apt install ./helm-docs_1.11.0_Linux_x86_64.deb \
 && rm -f ./helm-docs_1.11.0_Linux_x86_64.deb

RUN pip install *.tar.gz && rm -f *.tar.gz

ENTRYPOINT ["python", "/usr/local/bin/helm-charts-updater"]
