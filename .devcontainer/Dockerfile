FROM mcr.microsoft.com/devcontainers/python:3.11

# Install additional system packages if needed
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        postgresql-client \
        redis-tools \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /tmp/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp

# Set the default shell to bash rather than sh
ENV SHELL /bin/bash