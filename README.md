# Acronis Cyber Protect Agent (Docker)

Dockerized Acronis Cyber Protect Agent for Linux – designed for multi‑tenant deployments with isolated data and persistent logs.

---

## Features

- **Auto‑generated unique identifiers** – on first start, the container generates a unique `machine-id` and MMS ID (from a template) to avoid conflicts between tenants.
- **Persistent state** – all configuration, databases, and logs are stored on host volumes, so you can upgrade or restart containers without losing registration.
- **Multi‑tenant ready** – run as many independent agents as needed using a single image and `docker-compose`.
- **Active Protection disabled** – automatically turned off at startup to ensure compatibility with container environments.
- **Version automation** – a helper script fetches the latest Linux agent version from Acronis mirrors.

---

## Building the Image

```bash
docker build -t acronis-cyber-protect-agent:latest \
  --build-arg AGENT_VERSION=26.6.42659 \
  --build-arg MIRROR_URL=https://it01-cloud.acronis.com \
  .
  ```
## Register
docker exec -it acronis_tenant1 /usr/lib/Acronis/RegisterAgentTool/RegisterAgent -a https://eu-cloud.acronis.com --token XXXX-XXXX-XXXX -o register -t cloud
docker exec -it acronis_tenant2 /usr/lib/Acronis/RegisterAgentTool/RegisterAgent -a https://eu-cloud.acronis.com --token YYYY-YYYY-YYYY -o register -t cloud
