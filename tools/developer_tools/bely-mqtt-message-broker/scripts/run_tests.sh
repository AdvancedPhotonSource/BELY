#!/bin/bash
# BELY MQTT Message Broker - Test Runner Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
RUN_UNIT=true
RUN_INTEGRATION=false
RUN_COVERAGE=false
USE_DOCKER=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            RUN_UNIT=true
            shift
            ;;
        --integration)
            RUN_INTEGRATION=true
            shift
            ;;
        --all)
            RUN_UNIT=true
            RUN_INTEGRATION=true
            shift
            ;;
        --coverage)
            RUN_COVERAGE=true
            shift
            ;;
        --docker)
            USE_DOCKER=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --unit          Run unit tests (default)"
            echo "  --integration   Run integration tests"
            echo "  --all           Run all tests"
            echo "  --coverage      Generate coverage report"
            echo "  --docker        Run tests in Docker environment"
            echo "  --verbose, -v   Verbose output"
            echo "  --help, -h      Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Function to check if MQTT broker is running
check_mqtt_broker() {
    if command -v mosquitto_sub &> /dev/null; then
        timeout 2 mosquitto_sub -h localhost -p 1883 -t '$SYS/#' -C 1 &> /dev/null
        return $?
    else
        # Try with Python
        python -c "
import socket
import sys
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('localhost', 1883))
    sock.close()
    sys.exit(0 if result == 0 else 1)
except:
    sys.exit(1)
" 2>/dev/null
        return $?
    fi
}

# Function to start MQTT broker with Docker
start_mqtt_broker() {
    echo -e "${YELLOW}Starting MQTT broker with Docker...${NC}"
    docker run -d --name mqtt-test-broker \
        -p 1883:1883 \
        -p 9001:9001 \
        eclipse-mosquitto:2 > /dev/null 2>&1
    
    # Wait for broker to be ready
    echo -n "Waiting for MQTT broker to be ready"
    for i in {1..30}; do
        if check_mqtt_broker; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    echo -e " ${RED}✗${NC}"
    echo -e "${RED}Failed to start MQTT broker${NC}"
    return 1
}

# Function to stop MQTT broker
stop_mqtt_broker() {
    echo -e "${YELLOW}Stopping MQTT broker...${NC}"
    docker stop mqtt-test-broker > /dev/null 2>&1 || true
    docker rm mqtt-test-broker > /dev/null 2>&1 || true
}

# Main test execution
main() {
    echo -e "${GREEN}=== BELY MQTT Message Broker Test Suite ===${NC}"
    echo ""
    
    # Check Python version
    python_version=$(python --version 2>&1 | cut -d' ' -f2)
    echo -e "Python version: ${YELLOW}$python_version${NC}"
    
    # Install dependencies if needed
    if [ ! -d "venv" ] && [ ! -f "/.dockerenv" ]; then
        echo -e "${YELLOW}Installing dependencies...${NC}"
        pip install -e ".[dev]" > /dev/null 2>&1
    fi
    
    # Prepare test command
    TEST_CMD="pytest"
    
    if [ "$VERBOSE" = true ]; then
        TEST_CMD="$TEST_CMD -vv"
    else
        TEST_CMD="$TEST_CMD -v"
    fi
    
    if [ "$RUN_COVERAGE" = true ]; then
        TEST_CMD="$TEST_CMD --cov=src/bely_mqtt --cov-report=term-missing --cov-report=html --cov-report=xml"
    fi
    
    # Run tests based on options
    if [ "$USE_DOCKER" = true ]; then
        echo -e "${YELLOW}Running tests in Docker environment...${NC}"
        docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
        docker-compose -f docker-compose.test.yml down
    else
        # Run unit tests
        if [ "$RUN_UNIT" = true ]; then
            echo ""
            echo -e "${YELLOW}Running unit tests...${NC}"
            $TEST_CMD tests/ -k "not integration" || {
                echo -e "${RED}Unit tests failed!${NC}"
                exit 1
            }
            echo -e "${GREEN}Unit tests passed!${NC}"
        fi
        
        # Run integration tests
        if [ "$RUN_INTEGRATION" = true ]; then
            echo ""
            echo -e "${YELLOW}Running integration tests...${NC}"
            
            # Check if MQTT broker is available
            if ! check_mqtt_broker; then
                echo -e "${YELLOW}MQTT broker not found. Starting one with Docker...${NC}"
                start_mqtt_broker || {
                    echo -e "${RED}Failed to start MQTT broker${NC}"
                    exit 1
                }
                BROKER_STARTED=true
            else
                echo -e "${GREEN}MQTT broker is already running${NC}"
                BROKER_STARTED=false
            fi
            
            # Run integration tests
            MQTT_BROKER_HOST=localhost MQTT_BROKER_PORT=1883 $TEST_CMD tests/integration/ || {
                echo -e "${RED}Integration tests failed!${NC}"
                if [ "$BROKER_STARTED" = true ]; then
                    stop_mqtt_broker
                fi
                exit 1
            }
            echo -e "${GREEN}Integration tests passed!${NC}"
            
            # Stop broker if we started it
            if [ "$BROKER_STARTED" = true ]; then
                stop_mqtt_broker
            fi
        fi
    fi
    
    # Show coverage report location if generated
    if [ "$RUN_COVERAGE" = true ]; then
        echo ""
        echo -e "${GREEN}Coverage report generated:${NC}"
        echo "  - HTML: htmlcov/index.html"
        echo "  - XML: coverage.xml"
    fi
    
    echo ""
    echo -e "${GREEN}=== All tests completed successfully! ===${NC}"
}

# Run main function
main