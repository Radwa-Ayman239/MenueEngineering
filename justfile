# ============================================================================
# Menu_Engineering Justfile
# Description: Unified task runner for Docker-based workflows
# Usage: just <recipe>
# ============================================================================
# ----------------------------------------------------------------------------
# Global Configuration
# ----------------------------------------------------------------------------

set shell := ["powershell.exe", "-NoProfile", "-Command"]
set dotenv-load := true

# ----------------------------------------------------------------------------
# Variables
# ----------------------------------------------------------------------------

PROJECT_NAME := "menu_engineering"
ENV := env_var_or_default("ENV", "development")
DOCKER := "docker"
COMPOSE := "docker compose"

# ----------------------------------------------------------------------------
# Default / Help
# ----------------------------------------------------------------------------

# List all available commands (default behavior)
default:
    @just --list

# Explicit help command
help:
    @just --list

# ----------------------------------------------------------------------------
# Development - Docker
# ----------------------------------------------------------------------------

# Start containers in detached mode
up:
    @echo "Starting Docker containers (ENV={{ ENV }})..."
    {{ COMPOSE }} up -d

# Stop containers
down:
    @echo "Stopping Docker containers..."
    {{ COMPOSE }} down

# Stop containers and remove volumes (DANGEROUS)
down-volumes:
    @echo "WARNING: This will remove all containers AND volumes."
    @Read-Host "Press ENTER to continue or CTRL+C to abort"
    {{ COMPOSE }} down -v

# Build all images
build:
    @echo "Building Docker images..."
    {{ COMPOSE }} build

# Build images and start containers
up-build:
    @echo "Building and starting Docker containers..."
    {{ COMPOSE }} up --build -d

# Restart containers
restart:
    @echo "Restarting Docker containers..."
    {{ COMPOSE }} restart

# Restart a specific service
restart-service service:
    @if (-not ({{ COMPOSE }} config --services | Select-String -Quiet "^{{ service }}$")) { Write-Error "Service '{{ service }}' does not exist."; exit 1 }
    {{ COMPOSE }} restart {{ service }}

# Restart several services:
restart-services services:
    @echo "Restarting services: {{ services }}"
    {{ COMPOSE }} restart {{ services }}

# Create superuser
createsuperuser:
    @echo "Please complete the required data..."
    {{ COMPOSE }} exec backend python manage.py createsuperuser

# Makes migrations
makemigrations:
    @echo "Making migrations..."
    {{ COMPOSE }} exec backend python manage.py makemigrations

# Migrates
migrate:
    @echo "Migrating..."
    {{ COMPOSE }} exec backend python manage.py migrate

# ----------------------------------------------------------------------------
# Aliases (Ergonomics)
# ----------------------------------------------------------------------------

# Start Containers
start: up

# Stop Containers
stop: down

# Restart a specific service
rs service:
    just restart-service {{ service }}

# ----------------------------------------------------------------------------
# Status & Diagnostics
# ----------------------------------------------------------------------------

# Show container status
ps:
    {{ COMPOSE }} ps

# Show container logs (optionally for a specific service)
logs service="":
    @if ("{{ service }}" -ne "") { {{ COMPOSE }} logs {{ service }} } else { {{ COMPOSE }} logs }

# ----------------------------------------------------------------------------
# Testing
# ----------------------------------------------------------------------------

# Run all tests
test-backend:
    @echo "Running all tests..."
    {{ COMPOSE }} exec backend python manage.py test

# Run tests for a specific app or test case
test-backend-target target:
    @echo "Running target tests on {{ target }}..."
    {{ COMPOSE }} exec backend python manage.py test {{ target }}

# Run tests with coverage
test-backend-cover:
    @echo "Running tests with coverage..."
    {{ COMPOSE }} exec backend coverage run manage.py test

# View coverage summary in terminal
cover-report:
    @echo "Fetching coverage report..."
    {{ COMPOSE }} exec backend coverage report

# Generate the HTML report
cover-html:
    @echo "Writing coverage report into HTML file..."
    {{ COMPOSE }} exec backend coverage html

# ----------------------------------------------------------------------------
# Security
# ----------------------------------------------------------------------------

# Pip-Audit security
pip-audit:
    @echo "Running pip-audit on backend..."
    {{ COMPOSE }} exec backend pip-audit

# Bandit Static Code Security Analysis
bandit:
    @echo "Running bandit on backend..."
    {{ COMPOSE }} exec backend bandit -r users --exclude users/tests

# ----------------------------------------------------------------------------
# CI / Automation
# ----------------------------------------------------------------------------

# Verify Docker and Compose availability
check:
    {{ DOCKER }} --version
    {{ COMPOSE }} version
