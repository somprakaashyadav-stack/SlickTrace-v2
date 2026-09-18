FROM node:20-alpine AS base

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Build Next.js application
COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "start"]
