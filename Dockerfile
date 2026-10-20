# ==========================================================
# AFI Vision Builder - Dockerfile
# Optimized for Dokploy Deployment & Persistent Data Mounts
# ==========================================================

FROM python:3.11-slim

# Prevent interactive prompts and write bytecode
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    VISONODE_APP_DATA_DIR=/app/data \
    VISONODE_WEB_HOST=0.0.0.0 \
    VISONODE_WEB_PORT=8765 \
    ALLOWED_HOSTS=* \
    OPENBLAS_NUM_THREADS=1 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1

WORKDIR /app

# 1. Install system dependencies for OpenCV, PyTorch, git (CLIP), and healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefer-binary -r requirements.txt

# 3. Copy application source code
COPY . .

# 4. Prepare directory structure & seed backups for initial volume populating
RUN mkdir -p /app/data/models \
             /app/data/uploads \
             /app/data/outputs \
             /app/data/projects \
             /app/data/faces \
             /app/weights \
             /app/initial_models && \
    if [ -d "/app/data/models" ] && [ "$(ls -A /app/data/models 2>/dev/null)" ]; then \
        cp -rn /app/data/models/* /app/initial_models/ 2>/dev/null || true; \
    fi && \
    if [ -f "/app/data/cameras.json" ]; then \
        cp /app/data/cameras.json /app/default_cameras.json; \
    fi && \
    if [ -f "/app/data/projects.json" ]; then \
        cp /app/data/projects.json /app/default_projects.json; \
    fi && \
    chmod +x /app/entrypoint.sh

# 5. Expose application port
EXPOSE 8765

# 6. Container healthcheck
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=20s \
    CMD curl -f http://127.0.0.1:8765/api/cctv-cameras || exit 1

# 7. Start container with persistence initializer entrypoint
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
