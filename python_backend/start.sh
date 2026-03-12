#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Trap to handle script exit
cleanup() {
    print_info "Shutting down gracefully..."
    exit 0
}

trap cleanup SIGTERM SIGINT

# Check Python version
print_info "Checking Python version..."
python_version=$(python3 --version 2>&1)
print_success "Python: $python_version"

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Make sure environment variables are set."
else
    print_success ".env file found"
fi

# Check required environment variables
print_info "Checking required environment variables..."
required_vars=("SUPABASE_URL" "SERVICE_ROLE_KEY" "SECRET_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    print_error "Missing required environment variables: ${missing_vars[*]}"
    print_info "Please set these in your .env file or environment"
    exit 1
fi

print_success "All required environment variables are set"

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p /tmp/uploads /tmp/images /tmp/audio
print_success "Directories created"

# Function to start uvicorn with auto-reload
start_server() {
    print_info "Starting Stud AI Backend Server..."
    print_info "Server will auto-reload on code changes"
    print_info "Press CTRL+C to stop"
    echo ""
    
    # Start uvicorn with auto-reload
    # --reload: Enable auto-reload on code changes
    # --reload-dir: Watch specific directories
    # --log-level: Set log level
    exec uvicorn main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        --reload-dir /app \
        --log-level info \
        --access-log \
        --use-colors
}

# Retry logic for server startup
MAX_RETRIES=5
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if start_server; then
        # Server exited normally
        exit 0
    else
        EXIT_CODE=$?
        RETRY_COUNT=$((RETRY_COUNT + 1))
        
        if [ $EXIT_CODE -eq 130 ]; then
            # SIGINT (Ctrl+C) - exit gracefully
            print_info "Server stopped by user"
            exit 0
        elif [ $EXIT_CODE -eq 143 ]; then
            # SIGTERM - exit gracefully
            print_info "Server stopped by signal"
            exit 0
        else
            print_error "Server crashed with exit code $EXIT_CODE"
            
            if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                print_warning "Retrying in 5 seconds... (Attempt $RETRY_COUNT/$MAX_RETRIES)"
                sleep 5
            else
                print_error "Max retries reached. Exiting."
                exit 1
            fi
        fi
    fi
done
