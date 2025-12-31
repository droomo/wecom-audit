#!/bin/bash
set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===== WeCom Audit Build & Publish Tool =====${NC}"

# Function to build the wheel package
build_wheel() {
    # Install necessary tools
    echo -e "${BLUE}Installing necessary tools...${NC}"
    pip install --upgrade pip setuptools wheel twine -i https://pypi.tuna.tsinghua.edu.cn/simple

    # Clean previous builds
    echo -e "${BLUE}Cleaning previous builds...${NC}"
    rm -rf build/ dist/ wecom_audit.egg-info/

    # Build source package and wheel package
    echo -e "${BLUE}Building source package and wheel package with manylinux2014 platform tag...${NC}"
    python setup.py sdist bdist_wheel

    # Verify the wheel has the correct platform tag
    if ls dist/*manylinux*.whl 1> /dev/null 2>&1; then
        echo -e "${GREEN}Success: Wheel has the correct manylinux platform tag.${NC}"
    else
        echo -e "${RED}Warning: Wheel does not have the manylinux platform tag.${NC}"
        echo -e "Please check the setup.py file to ensure the platform tag is set correctly."
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    # List the built wheel files
    echo -e "\n${BLUE}Built wheel files:${NC}"
    ls -lh dist/*.whl

    # Check package for issues
    echo -e "${BLUE}Checking package for issues...${NC}"
    twine check dist/*
}

# Function to publish to PyPI
publish_to_pypi() {
    # Check for .pypirc file
    if [ ! -f ~/.pypirc ] && [ ! -f ./.pypirc ]; then
        echo -e "${YELLOW}Warning: No .pypirc file found${NC}"
        echo -e "You need to create a .pypirc file to store your PyPI credentials"
        echo -e "You can create it based on the .pypirc.template file:"
        echo -e "cp .pypirc.template ~/.pypirc"
        echo -e "Then edit ~/.pypirc and fill in your tokens"
        
        read -p "Continue with build only (no publishing)? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
        # If user chooses to continue, only build the package
        build_wheel
        echo -e "${GREEN}Build completed, no publishing${NC}"
        echo -e "Wheel package is located in the dist/ directory"
        echo -e "You can install it with: ${BLUE}pip install dist/*.whl${NC}"
        exit 0
    else
        # Copy local .pypirc to home directory if it exists in current directory but not in home
        if [ -f ./.pypirc ] && [ ! -f ~/.pypirc ]; then
            echo -e "${BLUE}Found .pypirc in current directory, copying to home directory...${NC}"
            cp ./.pypirc ~/.pypirc
            chmod 600 ~/.pypirc
        fi
    fi

    # Build the wheel package
    build_wheel

    echo -e "${GREEN}========================================================"
    echo -e "Package is ready to be published to PyPI"
    echo -e "You can choose to publish to Test PyPI or Official PyPI:${NC}"
    echo
    echo -e "${YELLOW}Publish to Test PyPI (recommended for testing first):${NC}"
    echo -e "twine upload --repository testpypi dist/*"
    echo
    echo -e "${YELLOW}Publish to Official PyPI:${NC}"
    echo -e "twine upload dist/*"
    echo
    echo -e "${BLUE}Install from Test PyPI:${NC}"
    echo -e "pip install --index-url https://test.pypi.org/simple/ wecom-audit"
    echo
    echo -e "${BLUE}Install from Official PyPI:${NC}"
    echo -e "pip install wecom-audit"
    echo -e "${GREEN}========================================================${NC}"

    # Prompt user to choose publishing target
    echo
    echo -e "${YELLOW}Where would you like to publish?${NC}"
    echo "1) Test PyPI"
    echo "2) Official PyPI"
    echo "3) Build only (no publishing)"
    read -p "Please choose [1-3]: " choice

    case $choice in
        1)
            echo -e "${BLUE}Publishing to Test PyPI...${NC}"
            twine upload --verbose --repository testpypi --non-interactive dist/*
            ;;
        2)
            echo -e "${RED}Warning: You are about to publish to Official PyPI${NC}"
            read -p "Are you sure you want to continue? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${BLUE}Publishing to Official PyPI...${NC}"
                twine upload --non-interactive dist/*
            else
                echo -e "${YELLOW}Publishing cancelled${NC}"
            fi
            ;;
        3)
            echo -e "${GREEN}Build completed, no publishing${NC}"
            echo -e "Wheel package is located in the dist/ directory"
            echo -e "You can install it with: ${BLUE}pip install dist/*.whl${NC}"
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            ;;
    esac
}

# Main script execution
if [ "$1" == "build" ]; then
    # Only build the wheel
    build_wheel
    echo -e "${GREEN}Wheel package built successfully!${NC}"
    echo -e "The wheel file is located in the ${BLUE}dist/${NC} directory."
    echo -e "You can install it with: ${BLUE}pip install dist/*.whl${NC}"
elif [ "$1" == "publish" ]; then
    # Build and publish
    publish_to_pypi
else
    # No arguments or invalid arguments, show usage
    echo -e "${BLUE}Usage:${NC}"
    echo -e "  $0 build    - Only build the wheel package"
    echo -e "  $0 publish  - Build and publish the package to PyPI"
    echo
    # Ask user what they want to do
    echo -e "${YELLOW}What would you like to do?${NC}"
    echo "1) Build only"
    echo "2) Build and publish"
    read -p "Please choose [1-2]: " choice
    
    case $choice in
        1)
            build_wheel
            echo -e "${GREEN}Wheel package built successfully!${NC}"
            echo -e "The wheel file is located in the ${BLUE}dist/${NC} directory."
            echo -e "You can install it with: ${BLUE}pip install dist/*.whl${NC}"
            ;;
        2)
            publish_to_pypi
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            ;;
    esac
fi