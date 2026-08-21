#!/usr/bin/env python

"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# Builds and publishes the BELY python client packages (bely-api, bely-cli)
# to PyPI using uv.
#
# DEV NOTE: To publish a release
#   source setup.sh
#   ./sbin/bely_release_pip.py
# or, via make:
#   make release-python-client
#
# Regenerating belyApi requires a running portal (default http://localhost:8080/bely).
# Publishing requires a PyPI API token, e.g. via UV_PUBLISH_TOKEN or ~/.pypirc.

import argparse
import glob
import os
import shutil
import subprocess

DIST_ROOT_DIRECTORY_ENV_KEY = "LOGR_ROOT_DIR"
PYTHON_CLIENT_DIR = "tools/developer_tools/python-client"
CLI_DIR = "tools/developer_tools/bely-cli"
DEFAULT_PORTAL_URL = "http://localhost:8080/bely"

rootDir = os.getenv(DIST_ROOT_DIRECTORY_ENV_KEY)
if rootDir is None:
    raise EnvironmentError("Please run setup.sh from the root directory of the bely distribution.")

clientDir = os.path.join(rootDir, PYTHON_CLIENT_DIR)
cliDir = os.path.join(rootDir, CLI_DIR)

# Published first-to-last: bely-cli pins bely-api exactly, so bely-api must land on
# PyPI before bely-cli is published against it.
PACKAGES = {
    "api": {"cwd": clientDir, "build_args": ["--package", "bely-api"]},
    "cli": {"cwd": cliDir, "build_args": []},
}


def run(args, cwd):
    print("+ (%s) %s" % (cwd, " ".join(args)))
    subprocess.run(args, check=True, cwd=cwd)


def regenerate_client(portal_url):
    run(["./generatePyClient.sh", portal_url], clientDir)
    generated = os.path.join(clientDir, "packages", "api", "belyApi", "__init__.py")
    if not os.path.exists(generated):
        raise RuntimeError("generatePyClient.sh did not produce %s" % generated)


def build(name):
    spec = PACKAGES[name]
    dist_dir = os.path.join(spec["cwd"], "dist")
    if os.path.isdir(dist_dir):
        shutil.rmtree(dist_dir)
    run(["uv", "lock"], spec["cwd"])
    run(["uv", "build", "--out-dir", dist_dir] + spec["build_args"], spec["cwd"])
    artifacts = sorted(glob.glob(os.path.join(dist_dir, "*")))
    if not artifacts:
        raise RuntimeError("uv build produced no artifacts in %s" % dist_dir)
    return artifacts


def publish(artifacts, publish_url):
    args = ["uv", "publish"]
    if publish_url:
        args += ["--publish-url", publish_url]
    args += artifacts
    run(args, rootDir)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "packages",
        nargs="*",
        default=["api", "cli"],
        help="which package(s) to release: api, cli, or both (default: both)",
    )
    parser.add_argument(
        "--portal-url",
        default=DEFAULT_PORTAL_URL,
        help="running BELY portal used to regenerate belyApi (default: %(default)s)",
    )
    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="skip regenerating belyApi; use whatever is already in packages/api/belyApi",
    )
    parser.add_argument(
        "--publish-url",
        default=None,
        help="alternate index, e.g. https://test.pypi.org/legacy/ for a dry run upload",
    )
    parser.add_argument("--dry-run", action="store_true", help="build only; do not upload")
    args = parser.parse_args()

    unknown = sorted(set(args.packages) - set(PACKAGES))
    if unknown:
        raise ValueError("Unknown package(s): %s (choose from %s)" % (", ".join(unknown), ", ".join(PACKAGES)))

    # Always build/publish api before cli, regardless of the order given on the command line.
    selected = [name for name in ("api", "cli") if name in args.packages]

    if "api" in selected and not args.skip_generate:
        regenerate_client(args.portal_url)

    built = {}
    for name in selected:
        artifacts = build(name)
        built[name] = artifacts
        print("\nBuilt %d artifact(s) for %s:" % (len(artifacts), name))
        for artifact in artifacts:
            print("  %s" % os.path.relpath(artifact, rootDir))

    if args.dry_run:
        print("\n--dry-run given, not publishing.")
        return

    response = input("\nPublish these to %s? [y/N]: " % (args.publish_url or "PyPI")).strip().lower()
    if response not in ("y", "yes"):
        print("Aborted, nothing published.")
        return

    for name in selected:
        publish(built[name], args.publish_url)


if __name__ == "__main__":
    main()
