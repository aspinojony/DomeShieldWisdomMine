# 1. 编译平台阶段
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install

# 拷贝所有代码并构建项目
COPY . .
RUN npm run build

# 2. 生产环境部署阶段
FROM nginx:alpine

# 将 vite 编译出来的产物放到 nginx 静态服务器目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 用自定义的 Nginx 配置覆盖默认配置（解决 Vue-Router 的 History 模式访问空白问题，并开启 gzip）
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html index.htm; \
    access_log /var/log/nginx/access.log; \
    error_log /var/log/nginx/error.log; \
    location / { \
    try_files $uri $uri/ /index.html; \
    } \
    # Optional: Gzip compression \
    gzip on; \
    gzip_types text/plain application/javascript text/css application/json; \
    }' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
