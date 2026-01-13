# Multi-stage Dockerfile for React Frontend

# Stage 1: Build
FROM node:20-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY vite.config.ts ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build application
RUN npm run build

# Stage 2: Production
FROM node:20-alpine

WORKDIR /app

# Install dependencies for dev container use
COPY package*.json ./
RUN npm install

# Install serve for production
RUN npm install -g serve

# Copy built files from builder
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000 || exit 1

# Serve the application
CMD ["serve", "-s", "dist", "-l", "3000"]
