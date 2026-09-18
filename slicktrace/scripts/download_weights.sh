#!/usr/bin/env bash
# SlickTrace v2 — Download Pre-trained ML Weights
# This script downloads official weights for UNet++, DeepLabV3+, and Look-alike XGBoost.
set -euo pipefail

WEIGHTS_DIR="${ML_WEIGHTS_DIR:-./ml/weights}"
mkdir -p "$WEIGHTS_DIR"

echo "====================================================="
echo "SlickTrace ML Weights Downloader"
echo "Target Directory: $WEIGHTS_DIR"
echo "====================================================="

# Base URL for public release assets
BASE_URL="https://github.com/somprakaashyadav-stack/SlickTrace-v2/releases/download/v2.0-weights"

download_file() {
    local filename="$1"
    local url="$2"
    local dest="$WEIGHTS_DIR/$filename"

    if [ -f "$dest" ]; then
        echo "[EXISTS] $filename already present."
    else
        echo "[DOWNLOADING] $filename from $url ..."
        if curl -fSL --progress-bar "$url" -o "$dest"; then
            echo "[SUCCESS] Saved $filename"
        else
            echo "[WARNING] Could not fetch $filename from remote. Place manually at $dest"
        fi
    fi
}

download_file "unetplusplus_resnet50_sar.pth" "$BASE_URL/unetplusplus_resnet50_sar.pth"
download_file "deeplabv3plus_resnet50_sar.pth" "$BASE_URL/deeplabv3plus_resnet50_sar.pth"
download_file "lookalike_xgb.ubj" "$BASE_URL/lookalike_xgb.ubj"

echo "====================================================="
echo "Weights check complete."
