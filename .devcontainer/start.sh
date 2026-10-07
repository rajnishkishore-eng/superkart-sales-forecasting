#!/usr/bin/env bash
# Usage: start.sh containers | public | all
cd "$(dirname "$0")/.." || exit 1

start_containers() {
  # Wait for the Docker daemon (it starts asynchronously in Codespaces)
  for _ in $(seq 1 30); do docker info >/dev/null 2>&1 && break; sleep 2; done
  # Remove containers created manually with `docker run` so compose can manage them
  for c in superkart-backend superkart-frontend; do
    if docker inspect "$c" >/dev/null 2>&1 && \
       [ -z "$(docker inspect -f '{{ index .Config.Labels "com.docker.compose.project" }}' "$c")" ]; then
      docker rm -f "$c" >/dev/null
    fi
  done
  docker compose up -d --build
  docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
}

make_public() {
  [ -z "$CODESPACE_NAME" ] && { echo "Not running in a Codespace - skipping."; return 0; }
  for _ in $(seq 1 10); do
    if gh codespace ports visibility 7860:public 8501:public -c "$CODESPACE_NAME" 2>/dev/null; then
      echo "Ports 7860 and 8501 are now Public:"
      echo "  Backend : https://${CODESPACE_NAME}-7860.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
      echo "  Frontend: https://${CODESPACE_NAME}-8501.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
      return 0
    fi
    sleep 5
  done
  echo "Could not set port visibility automatically - set 7860/8501 to Public in the PORTS tab."
}

case "${1:-all}" in
  containers) start_containers ;;
  public)     make_public ;;
  *)          start_containers; make_public ;;
esac
