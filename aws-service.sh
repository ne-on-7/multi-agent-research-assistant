#!/bin/bash
# Manage the ECS Express Mode service for the pause-between-demos cycle.
#
#   ./aws-service.sh up      # create the service (reads secrets from .env)
#   ./aws-service.sh down    # delete the service (stops Fargate + load balancer -> ~$0)
#   ./aws-service.sh url     # print the public Application URL
#   ./aws-service.sh status  # show the service status
#
# Notes:
#   - Secrets are read from .env at runtime; nothing is hardcoded here.
#   - `up` forces QDRANT_PATH="" so the app uses Qdrant Cloud (persistent), not local disk.
#   - Each `up` produces a NEW URL. Your ingested docs live in Qdrant Cloud and survive down/up.
set -euo pipefail
cd "$(dirname "$0")"

SERVICE="research-assistant"
CLUSTER="default"

# Derive account/region at runtime so no AWS account ID is hardcoded in the repo.
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
REGION="$(aws configure get region)"
IMAGE="${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/${SERVICE}:latest"
EXEC_ROLE="arn:aws:iam::${ACCOUNT}:role/service-role/ecsTaskExecutionRole"
INFRA_ROLE="arn:aws:iam::${ACCOUNT}:role/service-role/ecsInfrastructureRoleForExpressServices"

service_arn() {
  aws ecs list-services --cluster "$CLUSTER" \
    --query "serviceArns[?contains(@,'/${SERVICE}')]|[0]" --output text 2>/dev/null
}

case "${1:-}" in
  up)
    if [ ! -f .env ]; then echo "ERROR: .env not found." >&2; exit 1; fi
    # Load .env into the environment (handles quoted values), then build the
    # container JSON from those vars with python3 (safe JSON escaping).
    set -a; . ./.env; set +a
    CONTAINER_JSON="$(python3 - <<'PY'
import json, os
# Include these if present in .env; QDRANT_PATH is always sent empty (-> Qdrant Cloud).
optional = ["ANTHROPIC_API_KEY","GOOGLE_API_KEY","TAVILY_API_KEY",
            "LANGFUSE_PUBLIC_KEY","LANGFUSE_SECRET_KEY","LANGFUSE_BASE_URL",
            "QDRANT_URL","QDRANT_API_KEY","LLM_PRIMARY","LLM_FALLBACK",
            "CLAUDE_MODEL","GEMINI_MODEL","EMBEDDING_MODEL"]
env = [{"name": k, "value": os.environ[k]} for k in optional if os.environ.get(k)]
env.append({"name": "QDRANT_PATH", "value": ""})  # force external Qdrant Cloud
print(json.dumps({
    "image": os.environ["IMAGE"],
    "containerPort": 8080,
    "environment": env,
}))
PY
)"
    echo "==> Creating Express Mode service '${SERVICE}'..."
    IMAGE="$IMAGE" aws ecs create-express-gateway-service \
      --service-name "$SERVICE" \
      --execution-role-arn "$EXEC_ROLE" \
      --infrastructure-role-arn "$INFRA_ROLE" \
      --primary-container "$CONTAINER_JSON" \
      --cpu 2 --memory 4 \
      --health-check-path "/api/health" \
      --scaling-target '{"minTaskCount":1,"maxTaskCount":20}' \
      --monitor-resources
    echo ""; echo "When ACTIVE, get the URL with: ./aws-service.sh url"
    ;;

  down)
    ARN="$(service_arn)"
    if [ -z "$ARN" ] || [ "$ARN" = "None" ]; then echo "No '${SERVICE}' service found."; exit 0; fi
    echo "==> Deleting ${ARN} (stops Fargate + load balancer)..."
    aws ecs delete-express-gateway-service --service-arn "$ARN" --monitor-resources
    echo "✅ Deleted. Image stays in ECR; run './aws-service.sh up' before your next demo."
    ;;

  url)
    ARN="$(service_arn)"
    if [ -z "$ARN" ] || [ "$ARN" = "None" ]; then echo "No '${SERVICE}' service running."; exit 1; fi
    EP="$(aws ecs describe-express-gateway-service --service-arn "$ARN" \
        --query 'service.activeConfigurations[0].ingressPaths[0].endpoint' --output text)"
    echo "https://${EP}"
    ;;

  status)
    ARN="$(service_arn)"
    if [ -z "$ARN" ] || [ "$ARN" = "None" ]; then echo "No '${SERVICE}' service running."; exit 1; fi
    aws ecs describe-express-gateway-service --service-arn "$ARN" \
      --query 'service.{name:serviceName,status:status.statusCode,url:activeConfigurations[0].ingressPaths[0].endpoint}' \
      --output table
    ;;

  *)
    echo "Usage: ./aws-service.sh {up|down|url|status}" >&2
    exit 1
    ;;
esac
