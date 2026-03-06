#!/bin/bash
set -e

# Install dependencies
echo "ubuntu" | sudo -S apt-get update
echo "ubuntu" | sudo -S apt-get install -y cmake build-essential git tshark curl clang libclang-dev

# Install rustup if not present
if ! command -v rustup &> /dev/null; then
    echo "Installing Rustup..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
fi

source "$HOME/.cargo/env"

cd ~/ELEC-7321/AdvancedNetworking/assignments/task-quic

# Clone quiche if not already present
if [ ! -d "quiche" ]; then
    git clone -b 0.24.5 --recurse-submodules https://github.com/cloudflare/quiche.git
fi

# Build quiche workspace.
# quiche-server and quiche-client are [[bin]] targets inside the apps/ workspace member,
# not [[example]] targets — do not use --examples.
cd quiche
cargo build

# Create 100 KiB test files (explicit byte count for portability across shell versions)
yes A | head -c 102400 > file-A.txt
yes B | head -c 102400 > file-B.txt
yes C | head -c 102400 > file-C.txt

echo "Setup complete!"
