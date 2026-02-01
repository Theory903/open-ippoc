FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json pnpm-lock.yaml* ./

# Install pnpm and dependencies
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# Copy source
COPY . .

# Build
RUN pnpm build

# Runtime
FROM node:20-alpine

WORKDIR /app

RUN npm install -g pnpm

COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist

EXPOSE 3000

CMD ["pnpm", "start"]
