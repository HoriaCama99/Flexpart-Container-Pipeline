#!/bin/bash
# Build FLEXPART container for ARM64 (Apple Silicon)
# Author: Horia Camarasan

CPATH=$(dirname $0)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
COMMIT=$(git log --pretty=format:'%h' -n 1)

# Number of precipitation fields (default: 3 for flex_extract/ERA5 compatibility)
# Set to 1 for standard data, 3 for ERA5/flex_extract data with additional precip fields
NUMPF=${NUMPF:-3}

echo "Building FLEXPART v10.4 for ARM64"
echo "Branch: $BRANCH"
echo "Commit: $COMMIT"
echo "NUMPF (precipitation fields): $NUMPF"
echo "================================="

cd $CPATH

# Build with ARM64 Dockerfile
docker build -f Dockerfile.arm64 \
    -t flexpart-v10.4-arm64:latest \
    --build-arg COMMIT=$COMMIT \
    --build-arg NUMPF=$NUMPF \
    ../

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ FLEXPART ARM64 container built successfully!"
    echo ""
    echo "Usage:"
    echo "  docker run -it flexpart-v10.4-arm64:latest"
    echo "  docker run -v /path/to/input:/options -v /path/to/output:/output flexpart-v10.4-arm64:latest"
    echo ""
    echo "Test the container:"
    echo "  docker run --rm flexpart-v10.4-arm64:latest"
else
    echo ""
    echo "❌ Build failed. Check the error messages above."
    exit 1
fi









