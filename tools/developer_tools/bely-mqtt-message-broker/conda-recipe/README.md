# Conda Recipe for BELY MQTT Framework

This directory contains the conda recipe for building the BELY MQTT Framework package.

## Prerequisites

- Conda or Miniconda installed
- conda-build package: `conda install conda-build`
- anaconda-client (for uploading): `conda install anaconda-client`

## Building the Package

### Quick Build

```bash
# Run the build script
./conda-recipe/build_conda_package.sh
```

### Manual Build

```bash
# Set build output directory (important if running from conda env in project)
export CONDA_BLD_PATH="${HOME}/conda-bld"

# Build for current platform
conda build conda-recipe/ --output-folder "${CONDA_BLD_PATH}"

# Build with specific Python version
conda build conda-recipe/ --python 3.11 --output-folder "${CONDA_BLD_PATH}"

# Build for all Python versions defined in conda_build_config.yaml
conda build conda-recipe/ --variants --output-folder "${CONDA_BLD_PATH}"
```

## Testing the Package

The package includes automated tests that run during the build process:
- Import tests for all modules
- CLI command tests
- Basic functionality tests

## Uploading to Private Repository

### To Anaconda Cloud (Private Channel)

```bash
# Login to Anaconda Cloud
anaconda login

# Upload the package
anaconda upload --user YOUR_ORG --channel YOUR_CHANNEL /path/to/package.tar.bz2

# Upload all built packages
anaconda upload --user YOUR_ORG --channel YOUR_CHANNEL ~/conda-bld/**/*.tar.bz2
```

### To Private Conda Server

```bash
# Example for Artifactory
curl -u username:password -T /path/to/package.tar.bz2 \
  "https://your-artifactory.com/artifactory/conda-local/linux-64/package.tar.bz2"
```

## Installing from Private Repository

### From Anaconda Cloud

```bash
# Add your private channel
conda config --add channels https://conda.anaconda.org/YOUR_ORG/YOUR_CHANNEL

# Install the package
conda install bely-mqtt-framework
```

### From Private Server

```bash
# Add your private repository
conda config --add channels https://your-server.com/conda/channel

# Install the package
conda install bely-mqtt-framework
```

## Package Variants

The recipe builds packages for multiple Python versions:
- Python 3.9
- Python 3.10
- Python 3.11
- Python 3.12

All packages are noarch (platform-independent).

## Optional Dependencies

To include optional dependencies (like apprise for notifications):

```bash
# Install with apprise support
conda install bely-mqtt-framework apprise
```

## Troubleshooting

### Build Failures

1. Check conda-build is up to date: `conda update conda-build`
2. Clear conda cache: `conda clean --all`
3. Check build logs in `~/conda-bld/work/`

### "Can't merge/copy source into subdirectory of itself" Error

This occurs when trying to build conda packages with the build directory inside the source tree. The build script automatically handles this by:

1. Using a temporary directory for the build process
2. Copying the final artifacts to `./conda-bld` in your project
3. Cleaning up the temporary directory

This allows you to keep build artifacts locally while avoiding the circular reference issue.

### Import Errors

1. Ensure all dependencies are available in your conda channels
2. Check for conflicting packages: `conda list | grep pydantic`

### Upload Issues

1. Verify anaconda-client is installed: `conda install anaconda-client`
2. Check authentication: `anaconda whoami`
3. Verify channel permissions