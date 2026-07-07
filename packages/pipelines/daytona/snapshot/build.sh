#!/usr/bin/env bash
# Build + register the adhdquest-pygame-base Daytona snapshot. Run once from
# packages/pipelines/daytona (so the COPY sources resolve). Re-run when the
# template library changes.
set -euo pipefail

SNAPSHOT_NAME="${DAYTONA_SNAPSHOT:-adhdquest-pygame-base}"

docker build -f snapshot/Dockerfile -t "${SNAPSHOT_NAME}:latest" .

# Register the built image as a Daytona snapshot.
daytona snapshot push "${SNAPSHOT_NAME}:latest" --name "${SNAPSHOT_NAME}"

echo "Registered Daytona snapshot: ${SNAPSHOT_NAME}"
