FROM node:22-bookworm

ARG PNPM_VERSION=10.12.4

ENV PNPM_HOME=/pnpm
ENV PATH=${PNPM_HOME}:${PATH}

RUN apt-get update \
    && apt-get install -y --no-install-recommends openssh-client python3-yaml \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p ${PNPM_HOME} \
    && mkdir -p /home/node/.codex \
    && chown -R node:node ${PNPM_HOME} /home/node/.codex \
    && corepack enable \
    && corepack prepare pnpm@${PNPM_VERSION} --activate

USER node
WORKDIR /workspaces/atoyomin
