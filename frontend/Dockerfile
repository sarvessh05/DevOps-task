FROM node:20-alpine

WORKDIR /workspace

# Install dependencies first (cache layer)
COPY package*.json /workspace/
RUN npm install

# Copy source code
COPY . /workspace/

# Expose Vite default port
EXPOSE 5173

# Run vite dev server hosting public network inside container
CMD ["npm", "run", "dev", "--", "--host"]
