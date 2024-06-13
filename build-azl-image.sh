#!/bin/sh
sudo bin/mkosi \
    --release=3.0 --distribution=azurelinux \
    --bootable=yes \
    --tools-tree=default --tools-tree-distribution=azurelinux --tools-tree-release=3.0 \
        --tools-tree-package=systemd-container \
        --tools-tree-package=systemd-udev \
        --tools-tree-package=systemd-ukify \
        --tools-tree-package=azurelinux-repos \
        --tools-tree-package=azurelinux-release \
        --tools-tree-package=qemu \
        --tools-tree-package=edk2-ovmf \
    --unified-kernel-images=yes \
    --qemu-kvm=yes \
    --qemu-vsock=no \
    --qemu-swtpm=no \
    --qemu-firmware=uefi \
    $@ \
    qemu
