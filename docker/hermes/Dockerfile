# Hermes Agent gateway container.
#
# Hermes is installed by its official installer *at first start*, into HERMES_HOME (/opt/data),
# which is a bind mount (./hermes/home). That keeps the install, config.yaml, .env, state.db,
# memories and skills together on a persistent volume and avoids baking an unknown layout into
# the image. The installer's launcher (hermes-agent/.hermes/bin/hermes) and its bundled Python
# (tools/) are on the volume, so PATH points there and a recreated container does not reinstall.
# The gateway runs as the container's main process (`hermes gateway run`), as the Hermes docs
# require inside containers.

FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    HERMES_HOME=/opt/data \
    HOME=/root \
    PATH="/opt/data/hermes-agent/.hermes/bin:/root/.local/bin:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates git bash ripgrep ffmpeg procps \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

VOLUME ["/opt/data"]
WORKDIR /opt/data

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["gateway"]
