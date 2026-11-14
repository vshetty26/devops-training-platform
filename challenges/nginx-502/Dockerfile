FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Nginx and basic utilities
RUN apt-get update && apt-get install -y \
    nginx \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

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
