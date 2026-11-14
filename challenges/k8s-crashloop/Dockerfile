FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install kubectl and basic utilities
RUN apt-get update && apt-get install -y \
    curl \
    vim \
    ca-certificates \
    apt-transport-https \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/

# Create non-root user
RUN useradd -m -u 1000 challenger

# Create challenge directory
WORKDIR /challenge

# Copy challenge scripts
COPY setup.sh validate.sh /challenge/
RUN chmod +x /challenge/*.sh

# Ensure challenger user can write to necessary directories
RUN chown -R challenger:challenger /challenge

# Switch to non-root user
USER challenger

# Keep container running
CMD ["/bin/bash"]
