# SPDX-License-Identifier: LGPL-2.1+

import os

from pathlib import Path

from mkosi.backend import MkosiState, add_packages
from mkosi.distributions import DistributionInstaller
from mkosi.distributions.fedora import Repo, install_packages_dnf, invoke_dnf, setup_dnf
from mkosi.install import write_resource
from mkosi.log import complete_step


class MarinerInstaller(DistributionInstaller):
    @classmethod
    def cache_path(cls) -> list[str]:
        return ["var/cache/dnf"]

    @classmethod
    def filesystem(cls) -> str:
        return "ext4"

    @classmethod
    def install(cls, state: "MkosiState") -> None:
        return install_mariner(state)

    @classmethod
    def remove_packages(cls, state: MkosiState, remove: list[str]) -> None:
        invoke_dnf(state, 'remove', remove)

    @staticmethod
    def kernel_image(name: str, architecture: str) -> Path:
        return Path(f"boot/vmlinuz-{name}")

    @staticmethod
    def initrd_path(kver: str) -> Path:
        return Path("boot") / f"initrd.img-{kver}"


@complete_step("Installing Mariner Linux…")
def install_mariner(state: MkosiState) -> None:
    release = state.config.release

    if state.config.local_mirror or state.config.mirror:
        die("Mirrors are not supported with Mariner Linux")

    base_url = "baseurl=https://packages.microsoft.com/cbl-mariner/$releasever/prod/base/$basearch"
    microsoft_url = "baseurl=https://packages.microsoft.com/cbl-mariner/$releasever/prod/Microsoft/$basearch"
    extras_url = "baseurl=https://packages.microsoft.com/cbl-mariner/$releasever/prod/extras/$basearch"

    gpgpath = Path("/etc/pki/rpm-gpg/MICROSOFT-RPM-GPG-KEY")
    repos = [Repo("mariner-official-base", base_url, gpgpath),
             Repo("mariner-official-microsoft", microsoft_url, gpgpath),
             Repo("mariner-official-extras", extras_url, gpgpath)]

    setup_dnf(state, repos)

    packages = {*state.config.packages}

    add_packages(state.config,
                 packages,
                 "mariner-release", # Brings os-release et al.
                 "filesystem",      # Brings base filesystem structures
                 "shadow-utils",    # Brings /etc/shadow
                 "dbus")            # Required for systemd

    if not state.do_run_build_script and state.config.bootable:
        add_packages(state.config, packages, "kernel", "dracut")

        # If using device mapper, we need dracut to be able to find udev dm rules and dm tools
        # TODO: Make conditional or require as config?
        add_packages(state.config, packages, "lvm2")

    if state.config.netdev:
        add_packages(state.config, packages, "systemd-networkd", conditional="systemd")

    if state.do_run_build_script:
        packages.update(state.config.build_packages)

    install_packages_dnf(state, packages)

    if state.config.base_image is None:
        kernel_d_dir = state.root / "etc/kernel/install.d"
        os.makedirs(kernel_d_dir, exist_ok=True)

        write_resource(kernel_d_dir / "50-mkosi-reconfigure-dracut.install",
                    "mkosi.resources", "mariner-reconfigure-dracut.install", executable=True)
