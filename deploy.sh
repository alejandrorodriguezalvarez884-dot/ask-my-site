#!/bin/bash
set -euo pipefail

# Deploys ask-my-site to Google Cloud Run.
#
# Usage: ./deploy.sh
#
# GCP_PROJECT_ID and ALLOWED_ORIGINS are read from .env - required, no fallback default,
# so a deploy never silently goes out under the wrong project or the wrong CORS origin.
# The rest have sensible defaults, overridable via environment variables:
#   GCP_REGION       (default: europe-west1)
#   SERVICE_NAME     (default: ask-my-site)
#   SECRET_NAME      (default: ask-my-site-anthropic-api-key)
#   CONTENT_BUCKET   (default: <GCP_PROJECT_ID>-ask-my-site)
#
# SAVE_CONVERSATIONS and CHAT_STORE_COLLECTION are also read from .env (defaulting to
# false/conversations if unset there) and passed through - see README "Persisting
# conversations" before setting SAVE_CONVERSATIONS=true.
#
# One-time setup before the first run (see README "Deploying to Cloud Run"):
#   - gcloud auth login
#   - gcloud config set project "$GCP_PROJECT_ID"
#   - Required APIs enabled: run, cloudbuild, artifactregistry, secretmanager
#     (add firestore if SAVE_CONVERSATIONS=true - see README)
#   - The ANTHROPIC_API_KEY secret created in Secret Manager
#   - The content bucket created, readable by the service's account, and filled with
#     config/site.yaml and context/ via `make content-push` (see README "Content"). The
#     service downloads them at startup; they are not baked into the image.

if [[ ! -f .env ]]; then
    echo "Error: .env not found. Copy .env.example to .env and fill in GCP_PROJECT_ID and"
    echo "ALLOWED_ORIGINS (and ANTHROPIC_API_KEY, for local runs) first."
    exit 1
fi
set -a
# shellcheck disable=SC1091
source .env
set +a

: "${GCP_PROJECT_ID:?GCP_PROJECT_ID is not set in .env - deploy refuses to guess a project.}"
: "${ALLOWED_ORIGINS:?ALLOWED_ORIGINS is not set in .env - deploy refuses to guess the site origin.}"

GCP_REGION="${GCP_REGION:-europe-west1}"
SERVICE_NAME="${SERVICE_NAME:-ask-my-site}"
SECRET_NAME="${SECRET_NAME:-ask-my-site-anthropic-api-key}"
SAVE_CONVERSATIONS="${SAVE_CONVERSATIONS:-false}"
CHAT_STORE_COLLECTION="${CHAT_STORE_COLLECTION:-conversations}"
CONTENT_BUCKET="${CONTENT_BUCKET:-$GCP_PROJECT_ID-ask-my-site}"

if ! gcloud storage objects describe "gs://$CONTENT_BUCKET/config/site.yaml" \
    --project="$GCP_PROJECT_ID" --format='value(name)' >/dev/null 2>&1; then
    echo "Error: gs://$CONTENT_BUCKET/config/site.yaml not found. The service reads its persona"
    echo "and context/ from that bucket at startup - set it up first (README \"Content\")."
    exit 1
fi

echo "Deploying $SERVICE_NAME to Cloud Run"
echo "  Project:          $GCP_PROJECT_ID"
echo "  Region:           $GCP_REGION"
echo "  Allowed origins:  $ALLOWED_ORIGINS"
echo "  Content bucket:   gs://$CONTENT_BUCKET"
echo ""

gcloud run deploy "$SERVICE_NAME" \
    --source=. \
    --project="$GCP_PROJECT_ID" \
    --region="$GCP_REGION" \
    --allow-unauthenticated \
    --set-env-vars="ALLOWED_ORIGINS=$ALLOWED_ORIGINS,SAVE_CONVERSATIONS=$SAVE_CONVERSATIONS,CHAT_STORE_COLLECTION=$CHAT_STORE_COLLECTION,CONTENT_BUCKET=$CONTENT_BUCKET" \
    --set-secrets="ANTHROPIC_API_KEY=$SECRET_NAME:latest"

echo ""
echo "Deployed. Service URL:"
gcloud run services describe "$SERVICE_NAME" \
    --project="$GCP_PROJECT_ID" \
    --region="$GCP_REGION" \
    --format="value(status.url)"
