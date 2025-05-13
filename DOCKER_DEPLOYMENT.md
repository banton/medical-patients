# Docker Deployment Guide for Military Medical Exercise Patient Generator

This guide explains how to deploy the Military Medical Exercise Patient Generator using Docker containers in various environments.

## Prerequisites

- Docker Engine (v20.10.0+)
- Docker Compose (v2.0.0+)
- Git (to clone the repository)

## Setup Options

We provide several Docker Compose configurations for different deployment scenarios:

- Development Environment - `docker-compose.dev.yml`
- Production Environment - `docker-compose.prod.yml`
- Production with HTTPS - `docker-compose.traefik.yml`
- CLI Tool - `docker-compose.cli.yml`
- Large-Scale Deployment - `docker-compose.large-scale.yml`

## Basic Setup (Development)

1.  **Create a `.env` file (optional):**
    ```env
    # Optional environment variables
    PATIENT_GENERATOR_THREADS=4
    PATIENT_GENERATOR_MAX_MEMORY=2048
    ```

2.  **Build and start the development container:**
    ```bash
    docker-compose -f docker-compose.dev.yml up -d
    ```

3.  **Access the application:**
    - Web interface: http://localhost:8000
    - API documentation: http://localhost:8000/docs

## Production Deployment

For a production environment with optimized settings:

1.  **Create a `.env.prod` file:**
    ```env
    # Production settings
    PATIENT_GENERATOR_THREADS=4
    PATIENT_GENERATOR_MAX_MEMORY=4096
    ```

2.  **Deploy with the production configuration:**
    ```bash
    docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
    ```

## Deployment with HTTPS (Traefik)

For secure deployment with automatic HTTPS certificates:

1.  **Create required directories:**
    ```bash
    mkdir -p traefik/config traefik/acme
    touch traefik/acme/acme.json
    chmod 600 traefik/acme/acme.json
    ```

2.  **Copy the Traefik configuration files:**
    ```bash
    cp traefik.toml traefik/
    cp dashboard_auth.toml traefik/config/
    ```

3.  **Update the configuration:**
    - Replace `your-email@example.com` in `traefik.toml`
    - Update domain names in `dashboard_auth.toml` and `docker-compose.traefik.yml`
    - Generate a new password hash using `htpasswd` for the dashboard

4.  **Create the external network:**
    ```bash
    docker network create web
    ```

5.  **Deploy with Traefik:**
    ```bash
    docker-compose -f docker-compose.traefik.yml up -d
    ```

## Command-Line Usage

To run the patient generator CLI in a container:

1.  **Build and run the CLI container:**
    ```bash
    docker-compose -f docker-compose.cli.yml up
    ```

2.  **For custom parameters:**
    ```bash
    docker-compose -f docker-compose.cli.yml run --rm cli python run_generator.py --patients 2000 --output /app/output
    ```

## Large-Scale Deployment

For high-traffic scenarios with load balancing:

1.  **Create SSL certificates for NGINX:**
    ```bash
    mkdir -p nginx/certs
    # Place your certificate.crt and private.key in the certs directory
    ```

2.  **Copy the NGINX configuration:**
    ```bash
    mkdir -p nginx
    cp nginx.conf nginx/
    ```

3.  **Update domain names in the NGINX configuration.**

4.  **Deploy the large-scale setup:**
    ```bash
    docker-compose -f docker-compose.large-scale.yml up -d
    ```

## Managing Docker Volumes

The application outputs generated files to a Docker volume. To manage this:

1.  **List volumes:**
    ```bash
    docker volume ls
    ```

2.  **Access volume data:**
    ```bash
    docker run --rm -v military-patient-generator_output_data:/data -it alpine sh
    # Inside the container
    ls -la /data
    ```

3.  **Export data from volume:**
    ```bash
    docker run --rm -v military-patient-generator_output_data:/data -v $(pwd)/export:/export alpine sh -c "cp -r /data/* /export/"
    ```

## Monitoring and Logs

1.  **View container logs:**
    ```bash
    docker-compose -f docker-compose.prod.yml logs -f
    ```

2.  **Follow specific service logs:**
    ```bash
    docker-compose -f docker-compose.prod.yml logs -f web
