# SPDX-License-Identifier: LGPL-2.1+

import os
import re
from collections.abc import Iterable, Sequence
from pathlib import Path

from mkosi.config import Architecture, Config
from mkosi.context import Context
from mkosi.distributions import (
    Distribution,
    DistributionInstaller,
    PackageType,
    join_mirror,
)
from mkosi.installer import PackageManager
from mkosi.installer.dnf import Dnf
from mkosi.installer.rpm import RpmRepository, find_rpm_gpgkey, setup_rpm
from mkosi.log import die
from mkosi.util import listify, startswith, tuplify


class Installer(DistributionInstaller):
    @classmethod
    def pretty_name(cls) -> str:
        return "Azure Linux"

    @classmethod
    def filesystem(cls) -> str:
        return "ext4"

    @classmethod
    def package_type(cls) -> PackageType:
        return PackageType.rpm

    @classmethod
    def default_release(cls) -> str:
        return "2.0"

    @classmethod
    def default_tools_tree_distribution(cls) -> Distribution:
        return Distribution.azurelinux

    @classmethod
    def grub_prefix(cls) -> str:
        return "grub2"

    @classmethod
    def package_manager(cls, config: Config) -> type[PackageManager]:
        return Dnf

    @classmethod
    def createrepo(cls, context: Context) -> None:
        Dnf.createrepo(context)

    @classmethod
    def setup(cls, context: Context) -> None:
        Dnf.setup(context, cls.repositories(context), filelists=False)
        setup_rpm(context, dbpath="/var/lib/rpm")

    @classmethod
    def install(cls, context: Context) -> None:
        cls.install_packages(context, ["filesystem"], apivfs=False)

    @classmethod
    def install_packages(cls, context: Context, packages: Sequence[str], apivfs: bool = True) -> None:
        Dnf.invoke(context, "install", packages, apivfs=apivfs)

        # Some images use an absolute symlink to point from /usr/lib/modules/<version>/vmlinuz to /boot;
        # that causes problems for mkosi to read from the kernel. We work around this by patching the
        # symlink with a relative target.
        if "kernel" in packages:
            for dirname in os.listdir(context.root / "usr/lib/modules"):
                link_path = context.root / "lib/modules" / dirname / "vmlinuz"
                if os.path.islink(link_path):
                    target_path = os.readlink(link_path)
                    target_name = os.path.basename(target_path)
                    os.unlink(link_path)
                    os.symlink(f"../../../../boot/{target_name}", link_path)

    @classmethod
    def remove_packages(cls, context: Context, packages: Sequence[str]) -> None:
        Dnf.invoke(context, "remove", packages, apivfs=True)

    @staticmethod
    def gpgurls(context: Context) -> tuple[str, ...]:
        keys = ("MICROSOFT-METADATA-GPG-KEY", "MICROSOFT-RPM-GPG-KEY")
        return tuple(f"file:///etc/pki/rpm-gpg/{key}" for key in keys)

    @classmethod
    @listify
    def repositories(cls, context: Context) -> Iterable[RpmRepository]:
        # TODO: support context.config.mirror being set?
        if context.config.local_mirror:
            yield RpmRepository("azurelinux", f"baseurl={context.config.local_mirror}", gpgurls)
            return

        if context.config.release == "2.0":
            distro_name = "cbl-mariner"
            release_type = "prod"
        else:
            distro_name = "azurelinux"
            release_type = "preview"

        gpgurls = cls.gpgurls(context)

        urlbase = f"baseurl=https://packages.microsoft.com/{distro_name}/$releasever/{release_type}"
        yield RpmRepository(f"{distro_name}-base", f"{urlbase}/base/$basearch", gpgurls)
        yield RpmRepository(f"{distro_name}-debuginfo", f"{urlbase}/base/debuginfo/$basearch", gpgurls, enabled=False)
        yield RpmRepository(f"{distro_name}-source", f"{urlbase}/base/srpms", gpgurls, enabled=False)
        yield RpmRepository(f"{distro_name}-extended", f"{urlbase}/extended/$basearch", gpgurls, enabled=False)

        if context.config.release == "2.0":
            yield RpmRepository(f"{distro_name}-microsoft", f"{urlbase}/Microsoft/$basearch", gpgurls)
            yield RpmRepository(f"{distro_name}-extras", f"{urlbase}/extras/$basearch", gpgurls)
        else:
            yield RpmRepository(f"{distro_name}-cloud-native", f"{urlbase}/cloud-native/$basearch", gpgurls)
            yield RpmRepository(f"{distro_name}-ms-non-oss", f"{urlbase}/ms-non-oss/$basearch", gpgurls)
            yield RpmRepository(f"{distro_name}-ms-oss", f"{urlbase}/ms-oss/$basearch", gpgurls)

    @classmethod
    def architecture(cls, arch: Architecture) -> str:
        a = {
            Architecture.arm64 : "aarch64",
            Architecture.x86_64: "x86_64",
        }.get(arch)

        if not a:
            die(f"Architecture {a} is not supported by Azure Linux")

        return a
