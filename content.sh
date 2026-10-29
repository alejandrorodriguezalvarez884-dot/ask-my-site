#!/bin/bash
set -euo pipefail

# Syncs this deployment's content (config/site.yaml and context/) with its Cloud Storage
# bucket, which is where the Cloud Run service reads it from at startup.
#
# Usage:
#   ./content.sh pull   # bucket -> local files (do this first on a new computer)
#   ./content.sh push   # local files -> bucket, then restart the service so it reloads them
#
# Settings come from .env when there is one, else from the environment:
#   GCP_PROJECT_ID   (default: gcloud's current project)
#   CONTENT_BUCKET   (default: <GCP_PROJECT_ID>-ask-my-site)
#   GCP_REGION       (default: europe-west1)
#   SERVICE_NAME     (default: ask-my-site)
#
# The bucket has object versioning on, so an overwrite or delete by `push` can be undone
# from the console or `gcloud storage ls --all-versions`.

if [[ -f .env ]]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

GCP_PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
: "${GCP_PROJECT_ID:?No GCP project: set GCP_PROJECT_ID in .env or run gcloud config set project.}"
CONTENT_BUCKET="${CONTENT_BUCKET:-$GCP_PROJECT_ID-ask-my-site}"
GCP_REGION="${GCP_REGION:-europe-west1}"
SERVICE_NAME="${SERVICE_NAME:-ask-my-site}"
BUCKET_URL="gs://$CONTENT_BUCKET"

case "${1:-}" in
    pull)
        mkdir -p config context
        gcloud storage cp "$BUCKET_URL/config/site.yaml" config/site.yaml --project="$GCP_PROJECT_ID"
        # No deletes on pull: a local file that isn't in the bucket yet is kept.
        gcloud storage rsync "$BUCKET_URL/context" context --recursive \
            --exclude='\.gitkeep$' --project="$GCP_PROJECT_ID"
        echo "Pulled content from $BUCKET_URL."
        ;;
    push)
        if [[ ! -f config/site.yaml ]] || ! compgen -G "context/*.md" >/dev/null; then
            echo "Error: config/site.yaml or context/*.md missing locally - run ./content.sh pull"
            echo "first, or the push would wipe the bucket."
            exit 1
        fi
        gcloud storage cp config/site.yaml "$BUCKET_URL/config/site.yaml" --project="$GCP_PROJECT_ID"
        # Mirrors context/, deletes included, so removing a local file removes it there too.
        gcloud storage rsync context "$BUCKET_URL/context" --recursive \
            --delete-unmatched-destination-objects --exclude='\.gitkeep$' \
            --project="$GCP_PROJECT_ID"
        echo "Pushed content to $BUCKET_URL."

        # The service only reads the bucket at startup. Changing an env var rolls a new
        # revision of the same image (no rebuild), which loads the new content.
        if gcloud run services describe "$SERVICE_NAME" --project="$GCP_PROJECT_ID" \
            --region="$GCP_REGION" --format='value(metadata.name)' >/dev/null 2>&1; then
            echo "Restarting $SERVICE_NAME so it picks up the new content..."
            gcloud run services update "$SERVICE_NAME" --project="$GCP_PROJECT_ID" \
                --region="$GCP_REGION" --update-env-vars="CONTENT_VERSION=$(date +%Y%m%d%H%M%S)" \
                --quiet
        fi
        ;;
    *)
        echo "Usage: ./content.sh pull | push"
        exit 1
        ;;
esac
