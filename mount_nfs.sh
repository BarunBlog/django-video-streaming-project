#!/bin/bash

# Load environment variables
source /etc/environment  # OR source ~/.bashrc (depending on where you define $NFS_STORAGE_HOST)

# Ensure the variable is loaded
if [ -z "$NFS_STORAGE_HOST" ]; then
  echo "Error: NFS_STORAGE_HOST is not set!"
  exit 1
fi

# Install NFS client
sudo apt update && sudo apt install -y nfs-common

# Create a mount point
sudo mkdir -p /mnt/shared_storage

# Mount the shared storage
sudo mount -t nfs $NFS_STORAGE_HOST:/mnt/shared_storage /mnt/shared_storage

# Make it permanent (add to /etc/fstab) if it's not already there
if ! grep -q "$NFS_STORAGE_HOST:/mnt/shared_storage" /etc/fstab; then
  echo "$NFS_STORAGE_HOST:/mnt/shared_storage /mnt/shared_storage nfs defaults 0 0" | sudo tee -a /etc/fstab
fi

echo "NFS mount completed successfully!"