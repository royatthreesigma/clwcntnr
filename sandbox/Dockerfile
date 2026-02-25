FROM python:3.12

# Useful tools for an LLM sandbox
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    git \
    jq \
    vim \
    less \
    tree \
    net-tools \
    iputils-ping \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# pip ready for the LLM to install whatever it needs
RUN pip install --upgrade pip
RUN pip install psycopg2-binary

# Shared libs (seeded into /workspace/lib on every start)
COPY lib/ /seed/lib/

# Ensure /workspace/lib imports resolve via PYTHONPATH
ENV PYTHONPATH="/workspace"

WORKDIR /workspace

# Seed shared libs, ensure dirs exist, then idle
CMD ["sh", "-c", "mkdir -p /workspace/tools /workspace/lib && cp -r /seed/lib/. /workspace/lib/ && exec sleep infinity"]
