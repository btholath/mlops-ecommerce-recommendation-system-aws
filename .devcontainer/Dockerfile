FROM mcr.microsoft.com/devcontainers/ruby:3.3

RUN mkdir /workspaces/mlops-ecommerce-recommendation-system-aws/dockerspace
WORKDIR /workspaces/mlops-ecommerce-recommendation-system-aws/dockerspace

# inside the Codespace dev-container
sudo groupadd -f docker                 # make sure the group exists
sudo usermod -aG docker $USER           # add vscode → docker
newgrp docker                           # refresh group membership for this shell
