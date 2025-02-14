#!/bin/bash

# Install NFS client
sudo apt update && sudo apt install -y nfs-common

# Create a mount point
sudo mkdir -p /mnt/shared_storage

# Mount the shared storage
sudo mount -t nfs $NFS_STORAGE_HOST:/mnt/shared_storage /mnt/shared_storage

# Make it permanent (add to /etc/fstab)
echo "$NFS_STORAGE_HOST:/mnt/shared_storage /mnt/shared_storage nfs defaults 0 0" | sudo tee -a /etc/fstab

echo "NFS mount completed successfully!"