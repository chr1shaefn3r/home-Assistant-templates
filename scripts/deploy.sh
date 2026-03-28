#!/usr/bin/env bash
# Deploy templates to a running Home Assistant instance.
#
# Usage:
#   bash scripts/deploy.sh           # deploy only if templates changed
#   bash scripts/deploy.sh --force   # deploy regardless of changes
#
# Configuration: copy .env.example to .env and fill in the values.
set -euo pipefail

# ── Load .env if present ──────────────────────────────────────────────────────
if [ -f .env ]; then
  set -a; source .env; set +a
fi

# ── Required variables ────────────────────────────────────────────────────────
: "${HA_HOST:?HA_HOST is not set. Copy .env.example to .env and fill it in.}"
: "${HA_TOKEN:?HA_TOKEN is not set. Copy .env.example to .env and fill it in.}"

# ── Optional variables with defaults ─────────────────────────────────────────
HA_USER="${HA_USER:-root}"
HA_SSH_PORT="${HA_SSH_PORT:-22}"
HA_SSH_KEY="${HA_SSH_KEY:-${HOME}/.ssh/id_ecdsa}"
LAST_DEPLOYED_FILE=".last-deployed"

# ── Change detection ──────────────────────────────────────────────────────────
if [ -f "$LAST_DEPLOYED_FILE" ]; then
  LAST_COMMIT=$(cat "$LAST_DEPLOYED_FILE")
  CHANGED=$(git diff --name-only "$LAST_COMMIT" HEAD -- templates/ 2>/dev/null || echo "")
  if [ -z "$CHANGED" ]; then
    echo "No template changes since last deploy ($(git rev-parse --short "$LAST_COMMIT"))."
    if [ "${1:-}" != "--force" ]; then
      echo "Run with --force to deploy anyway."
      exit 0
    fi
    echo "Deploying anyway (--force)."
  else
    echo "Changed templates since last deploy:"
    echo "$CHANGED" | sed 's/^/  /'
  fi
else
  echo "No previous deploy recorded — deploying all templates."
fi

echo ""

# ── rsync templates/ → HA custom_templates/ ──────────────────────────────────
echo "Syncing templates to ${HA_HOST}..."
rsync -avz --delete \
  -e "ssh -i ${HA_SSH_KEY} -p ${HA_SSH_PORT} -o StrictHostKeyChecking=accept-new" \
  templates/ \
  "${HA_USER}@${HA_HOST}:/config/custom_templates/"

echo ""

# ── Trigger reload via REST API ───────────────────────────────────────────────
echo "Reloading custom templates on Home Assistant..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${HA_TOKEN}" \
  -H "Content-Type: application/json" \
  -X POST "http://${HA_HOST}:8123/api/services/homeassistant/reload_custom_templates")

if [ "$HTTP_STATUS" = "200" ]; then
  echo "Reload successful."
else
  echo "Reload returned HTTP ${HTTP_STATUS} — check your HA_TOKEN and HA_HOST." >&2
  exit 1
fi

# ── Record deployed commit ────────────────────────────────────────────────────
git rev-parse HEAD > "$LAST_DEPLOYED_FILE"
echo ""
echo "Deploy complete. Deployed commit: $(git rev-parse --short HEAD)"
