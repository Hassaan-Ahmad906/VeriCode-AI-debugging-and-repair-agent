#!/usr/bin/env bash
# Run as the dedicated service user from an existing checkout at /opt/vericode.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
if [[ "$(uname -s)" != "Linux" ]]; then
  echo 'Deployment requires a Linux host with Docker.' >&2
  exit 1
fi
python3 -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ required"'
docker info --format '{{.OSType}}' | python3 -c 'import sys; assert sys.stdin.read().strip() == "linux", "Linux Docker engine required"'
umask 077
python3 -m venv .venv
.venv/bin/python -m pip install --disable-pip-version-check -e '.[ui]'
docker build --tag vericode-runner:day2 sandbox
mkdir -p artifacts/private
echo 'Prepared. Install the reviewed systemd unit from deploy/README.md to start.'
