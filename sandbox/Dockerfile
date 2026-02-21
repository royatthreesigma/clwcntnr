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

WORKDIR /workspace

# Keep the container alive
CMD ["sleep", "infinity"]
