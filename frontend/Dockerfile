# Stage 1: Build React app
FROM node:18-alpine AS build

WORKDIR /app

# Install dependencies
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

# Copy source code
COPY . .

# Build with backend URL pointing to /api (nginx will proxy)
ENV REACT_APP_BACKEND_URL=
RUN yarn build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built React app
COPY --from=build /app/build /usr/share/nginx/html

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
