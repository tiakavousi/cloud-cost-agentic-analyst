# frontend/Dockerfile

FROM node:20-alpine

# Set working directory
WORKDIR /app

# Install dependencies first (caching layer)
COPY package.json package-lock.json* ./
RUN npm install

# Copy the rest of the application
COPY . .

# Expose Next.js default port
EXPOSE 3000

# Run in development mode to enable Hot Reloading
CMD ["npm", "run", "dev"]