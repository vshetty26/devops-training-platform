FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary tools for YAML validation
RUN apt-get update && apt-get install -y \
    curl \
    vim \
    nano \
    python3 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install yamllint for YAML syntax validation
RUN pip3 install yamllint

# Create non-root user
RUN useradd -m -u 1000 challenger

# Create challenge directory and GitHub Actions structure
WORKDIR /challenge
RUN mkdir -p /home/challenger/.github/workflows

# Copy challenge scripts
COPY setup.sh validate.sh /challenge/
RUN chmod +x /challenge/*.sh

# Ensure challenger user can write to necessary directories
RUN chown -R challenger:challenger /challenge /home/challenger

# Switch to non-root user
USER challenger

# Set working directory to user's home
WORKDIR /home/challenger

# Keep container running
CMD ["/bin/bash"]
