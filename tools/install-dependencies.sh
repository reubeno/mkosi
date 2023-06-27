#!/bin/bash
set -euo pipefail

# For archlinux-keyring and pacman
sudo add-apt-repository ppa:michel-slm/kernel-utils
sudo DEBIAN_FRONTEND=noninteractive apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install --assume-yes --no-install-recommends \
    archlinux-keyring \
    btrfs-progs \
    bubblewrap \
    cpio \
    debian-archive-keyring \
    dnf \
    dosfstools \
    e2fsprogs \
    erofs-utils \
    git \
    kmod \
    makepkg \
    mtools \
    ovmf \
    pacman-package-manager \
    pandoc \
    python3-pefile \
    python3-pip \
    python3-pyelftools \
    qemu-system-x86 \
    rpm \
    sbsigntool \
    squashfs-tools \
    swtpm \
    systemd-container \
    xfsprogs

sudo pacman-key --init
sudo pacman-key --populate archlinux
