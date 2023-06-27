#!/bin/bash
set -euo pipefail

echo "deb-src http://archive.ubuntu.com/ubuntu/ $(lsb_release -cs) main restricted universe multiverse" | sudo tee -a /etc/apt/sources.list
sudo DEBIAN_FRONTEND=noninteractive apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get build-dep --assume-yes --no-install-recommends systemd
sudo DEBIAN_FRONTEND=noninteractive apt-get install --assume-yes --no-install-recommends libfdisk-dev libssl-dev libtss2-dev

git clone https://github.com/systemd/systemd --depth=1
meson setup systemd/build systemd \
    -D repart=true \
    -D efi=true \
    -D bootloader=true \
    -D ukify=true \
    -D firstboot=true \
    -D blkid=true \
    -D openssl=true \
    -D tpm2=true

BINARIES=(
    bootctl
    systemctl
    systemd-analyze
    systemd-dissect
    systemd-firstboot
    systemd-measure
    systemd-nspawn
    systemd-repart
    ukify
)

ninja -C systemd/build ${BINARIES[@]}

for BINARY in "${BINARIES[@]}"; do
    sudo ln -svf $PWD/systemd/build/$BINARY /usr/bin/$BINARY
    $BINARY --version
done
