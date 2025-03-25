# Use an official Node.js runtime as a parent image
FROM node:14

# Install Ganache CLI globally
RUN npm install -g ganache-cli

# Expose the default port used by Ganache CLI
EXPOSE 8545

# Define the entry point for your container
CMD ["ganache-cli"]
