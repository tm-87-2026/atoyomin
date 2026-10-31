FROM node:22-bookworm

ARG PNPM_VERSION=10.12.4

ENV PNPM_HOME=/pnpm
ENV PATH=${PNPM_HOME}:${PATH}

RUN mkdir -p ${PNPM_HOME} \
    && mkdir -p /home/node/.config/atoyomin \
    && chown -R node:node ${PNPM_HOME} \
    && chown -R node:node /home/node/.config \
    && corepack enable \
    && corepack prepare pnpm@${PNPM_VERSION} --activate

USER node
WORKDIR /workspaces/atoyomin
