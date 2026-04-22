# ============================================================
# Stage 1 — Build: install dependencies (including devDeps)
# ============================================================
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

# ============================================================
# Stage 2 — Production: slim runtime image
# ============================================================
FROM node:20-alpine AS production

# Security — run as non-root
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

# Copy only production dependencies from build stage
COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force

# Copy application source
COPY app.js ./
COPY views/ ./views/

# Fix ownership of all files
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:3000/ || exit 1

CMD ["node", "app.js"]
