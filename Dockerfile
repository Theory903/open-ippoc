# syntax=docker/dockerfile:1
# IPPOC-OS Production Dockerfile

FROM rust:1.75-bookworm AS builder

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    libpq-dev \
    cmake \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

# Copy workspace
COPY Cargo.toml Cargo.lock ./
COPY apps/ ./apps/
COPY libs/ ./libs/
COPY schemas/ ./schemas/

# Build release
RUN cargo build --workspace --release

# Runtime image
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy binaries
COPY --from=builder /app/target/release/ippoc-node /usr/local/bin/

# Create non-root user
RUN useradd -r -u 1000 ippoc
USER ippoc

# Default port
EXPOSE 9000/udp
EXPOSE 9000/tcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9000/health || exit 1

ENTRYPOINT ["ippoc-node"]
CMD ["--port", "9000"]
