# Django Project

This is a Django project that is containerized using Docker and deployed using Azure Pipelines.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- Docker: You need to have Docker installed on your machine to run this project. You can download Docker from the official Docker website.
- Python: This project is built with Python. Make sure you have it installed on your machine.

### Installation and Running Locally

1. Clone the repository to your local machine.

2. Build and run the Docker container:
```bash
docker-compose up --build
```
The application will be accessible at `localhost:8000`.

### Deployment
This project is deployed using Azure Pipelines. The `azure-pipelines.yml` file contains the configuration for the deployment pipeline.