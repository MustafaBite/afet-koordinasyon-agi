# Frontend Dockerfile
FROM node:18-alpine

WORKDIR /app

# Bağımlılıkları kopyala ve yükle
COPY package*.json ./
RUN npm ci

# Uygulama kodunu kopyala
COPY . .

# Port
EXPOSE 5173

# Development modunda başlat
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
