#!/bin/bash
# Build script for creating conda packages

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building BELY MQTT Framework conda package...${NC}"

# Check if conda-build is installed
if ! command -v conda-build &> /dev/null; then
    echo -e "${RED}conda-build is not installed. Installing...${NC}"
    conda install -y conda-build
fi

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf build/ dist/ *.egg-info/ 
conda build purge

# Set up local directory for final artifacts
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/.." && pwd )"
LOCAL_CONDA_BLD="${PROJECT_ROOT}/conda-bld"

# Remove existing conda-bld directory to ensure clean build
if [ -d "${LOCAL_CONDA_BLD}" ]; then
    echo -e "${YELLOW}Removing existing conda-bld directory...${NC}"
    rm -rf "${LOCAL_CONDA_BLD}"
fi
mkdir -p "${LOCAL_CONDA_BLD}"

# Use a temporary build directory outside the project
TEMP_BUILD_DIR=$(mktemp -d "${TMPDIR:-/tmp}/conda-build.XXXXXX")
export CONDA_BLD_PATH="${TEMP_BUILD_DIR}"

echo -e "${YELLOW}Using temporary build directory: ${CONDA_BLD_PATH}${NC}"
echo -e "${YELLOW}Final packages will be copied to: ${LOCAL_CONDA_BLD}${NC}"

# Build the package
echo -e "${YELLOW}Building conda package...${NC}"
conda build conda-recipe/ --output-folder "${CONDA_BLD_PATH}"

# Get the package path
PACKAGE_PATH=$(conda build conda-recipe/ --output-folder "${CONDA_BLD_PATH}" --output)

# Copy build artifacts to local directory
echo -e "${YELLOW}Copying build artifacts to project directory...${NC}"
cp -r "${CONDA_BLD_PATH}"/noarch "${LOCAL_CONDA_BLD}/" 2>/dev/null || true
cp -r "${CONDA_BLD_PATH}"/osx-arm64 "${LOCAL_CONDA_BLD}/" 2>/dev/null || true
cp -r "${CONDA_BLD_PATH}"/linux-64 "${LOCAL_CONDA_BLD}/" 2>/dev/null || true
cp -r "${CONDA_BLD_PATH}"/win-64 "${LOCAL_CONDA_BLD}/" 2>/dev/null || true

# Update package path to local directory
PACKAGE_NAME=$(basename "${PACKAGE_PATH}")
PACKAGE_PATH="${LOCAL_CONDA_BLD}/noarch/${PACKAGE_NAME}"

# Clean up temporary directory
rm -rf "${TEMP_BUILD_DIR}"

echo -e "${GREEN}Package built successfully!${NC}"
echo -e "${GREEN}Package location: ${PACKAGE_PATH}${NC}"

# Optional: Convert to other platforms (skip for noarch packages)
if [[ ! ${PACKAGE_PATH} == *"noarch"* ]]; then
    echo -e "${YELLOW}Converting package for other platforms...${NC}"
    # Use temp directory for conversion, then copy results
    TEMP_CONVERT_DIR=$(mktemp -d "${TMPDIR:-/tmp}/conda-convert.XXXXXX")
    conda convert -p all ${PACKAGE_PATH} -o "${TEMP_CONVERT_DIR}"
    cp -r "${TEMP_CONVERT_DIR}"/* "${LOCAL_CONDA_BLD}/" 2>/dev/null || true
    rm -rf "${TEMP_CONVERT_DIR}"
else
    echo -e "${YELLOW}Package is noarch - no platform conversion needed${NC}"
fi

echo -e "${GREEN}Build complete!${NC}"
echo ""
echo "To upload to your private conda channel:"
echo "  anaconda upload ${PACKAGE_PATH}"
echo ""
echo "To install locally:"
echo "  conda install -c local bely-mqtt-framework"
echo ""
echo "Or install from the local build directory:"
echo "  conda install -c file://${LOCAL_CONDA_BLD} bely-mqtt-framework"
echo ""
echo "Package files are located in: ${LOCAL_CONDA_BLD}"