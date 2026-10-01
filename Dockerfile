FROM node:22-bookworm-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY tsconfig.json server.ts ./
COPY types ./types
RUN npm run build
FROM python:3.13-slim-bookworm
WORKDIR /app
COPY --from=build /usr/local/bin/node /usr/local/bin/node
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json server.py backup.py ./
COPY web ./web
RUN useradd --uid 10001 --create-home appuser && mkdir -p /app/data && chown -R appuser /app
USER appuser
ENV PORT=3000 APP_DB=/app/data/app.sqlite3
EXPOSE 3000
CMD ["node", "dist/server.js"]
