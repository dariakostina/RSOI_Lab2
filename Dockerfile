ARG PYTHON_VERSION=3.12.8
ARG BASE_PYTHON_IMAGE=python:${PYTHON_VERSION}-slim-bookworm

FROM ${BASE_PYTHON_IMAGE} AS base


FROM base AS environment
    RUN --mount=type=cache,target=/root/.cache,sharing=locked \
        pip install \
            pipx==1.7.1
    RUN --mount=type=cache,target=/root/.cache,sharing=locked \
        pipx install --global \
            poetry==1.8.5


FROM environment AS development
    RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' \
            > /etc/apt/apt.conf.d/keep-cache
    RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
        --mount=type=cache,target=/var/lib/apt,sharing=locked \
        set -eux; \
        apt-get update; \
        apt-get --no-install-recommends --yes install \
            git


FROM environment AS builder

    RUN --mount=type=cache,target=/root/.cache,sharing=locked \
        poetry self add \
            poetry-plugin-bundle==1.4.1
    WORKDIR /src
    COPY . .
    RUN poetry bundle venv --no-interaction --only=main /venv


FROM builder AS unit-tests
    RUN poetry bundle venv --no-interaction /venv
    ENTRYPOINT [ "/venv/bin/pytest" ]


FROM base AS production
    ARG SERVICE_NAME
    ENV SERVICE_NAME=$SERVICE_NAME

    ENV OPENAPI_URL=
    ENV UVICORN_HOST=0.0.0.0
    ENV UVICORN_PORT=8000

    COPY --from=builder /venv /venv
    COPY entrypoint.sh /usr/local/bin/entrypoint.sh

    EXPOSE $UVICORN_PORT

    ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
