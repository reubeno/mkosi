FROM ubuntu:jammy

COPY /scripts /scripts
WORKDIR /build

# Install prerequisites
RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install --assume-yes --no-install-recommends \
        gpg \
        gpg-agent \
        software-properties-common \
        sudo

# Install dependencies
RUN /scripts/install-dependencies.sh

# Update systemd
RUN /scripts/update-systemd.sh

# Cleanup
RUN rm -rf /scripts
