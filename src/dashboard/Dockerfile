# Dashboard Dockerfile
# Build: docker build -f src/dashboard/Dockerfile -t nep-dashboard .
# Used by docker-compose.full-stack.yml dashboard service

FROM node:20-alpine

WORKDIR /app

COPY src/dashboard/package*.json .
RUN npm ci --production

COPY src/dashboard/ .

ENV NODE_ENV=production
ENV PORT=3000

EXPOSE 3000

CMD ["npm", "start"]
