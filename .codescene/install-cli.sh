#!/usr/bin/env bash
# Install the pinned CodeScene CLI (`cs`) into ~/.local/bin. Linux amd64 only,
# because orbs are the only place that uses this script; on other machines, use
# CodeScene's official installer. Does nothing when the pinned build is installed.
#
# To upgrade, look up the build of a new version with
#   curl -fsS "https://devtools.codescene.io/api/cli/cs?version=<version>"
# then download that build's zip and update all three values below.
set -euo pipefail

CS_VERSION="1.0.58"
CS_BUILD="b2580d71be8fbfd6a496d7a007062c0c81cd2b60"
CS_ZIP_SHA256="e358b332230f06ac81f9ca119c787860e25d86176d344fc06be1dffe2affb352"

bin="$HOME/.local/bin"
if "$bin/cs" version 2>/dev/null | grep -q "$CS_BUILD"; then
  exit 0
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
echo "Installing CodeScene CLI ${CS_VERSION} (${CS_BUILD})"
curl -fsSL -o "$tmp/cs.zip" \
  "https://downloads.codescene.io/enterprise/cli/cs-linux-amd64-${CS_BUILD}.zip"
echo "${CS_ZIP_SHA256}  $tmp/cs.zip" | sha256sum --check --quiet
unzip -q -o "$tmp/cs.zip" cs -d "$tmp"
install -D -m 0755 "$tmp/cs" "$bin/cs"
