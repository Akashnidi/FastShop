# Multi-stage Dockerfile for React frontend with Vite
# Stage 1: Builder - build the React app
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Install terser and build the app
RUN npm install terser && npm run build

# Stage 2: Runtime - serve with lightweight HTTP server
FROM node:18-alpine

WORKDIR /app

# Install lightweight HTTP server
RUN npm install -g serve

# Copy built app from builder
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000 || exit 1

# Start server
CMD ["serve", "-s", "dist", "-l", "3000"]
