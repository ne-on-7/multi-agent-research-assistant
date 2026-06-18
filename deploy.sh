#!/bin/bash
# Build the Docker image and push it to AWS ECR.
# Re-run this any time you change code and want to ship a new image.
# After it finishes, redeploy (or unpause) the App Runner service to pick up :latest.
set -euo pipefail
cd "$(dirname "$0")"

REPO="research-assistant"
TAG="latest"

ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
REGION="$(aws configure get region)"
REGISTRY="${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com"
IMAGE_URI="${REGISTRY}/${REPO}:${TAG}"

echo "==> Account: ${ACCOUNT}  Region: ${REGION}"
echo "==> Target image: ${IMAGE_URI}"

# 1. Ensure the ECR repository exists (no-op if it already does)
if ! aws ecr describe-repositories --repository-names "${REPO}" >/dev/null 2>&1; then
  echo "==> Creating ECR repository '${REPO}'..."
  aws ecr create-repository --repository-name "${REPO}" >/dev/null
fi

# 2. Log Docker into ECR
echo "==> Logging Docker into ECR..."
aws ecr get-login-password --region "${REGION}" \
  | docker login --username AWS --password-stdin "${REGISTRY}"

# 3. Build for AWS (linux/amd64 — required when building on Apple Silicon)
echo "==> Building image (linux/amd64)... this is slow the first time (PyTorch)."
docker build --platform linux/amd64 -t "${REPO}:${TAG}" .

# 4. Tag + push
echo "==> Pushing to ECR..."
docker tag "${REPO}:${TAG}" "${IMAGE_URI}"
docker push "${IMAGE_URI}"

echo ""
echo "✅ Done. Image pushed:"
echo "   ${IMAGE_URI}"
echo ""
echo "Next: in App Runner, create the service from this image (port 8080,"
echo "health check /api/health), or click Deploy if the service already exists."
