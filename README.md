# Sentinel-GNN

## Project Overview
Sentinel-GNN is a comprehensive application designed to leverage Graph Neural Networks (GNNs) for analyzing and visualizing complex biological data. The project is structured into two main components: a backend service built with FastAPI and a frontend application developed using React. This application aims to provide an intuitive interface for users to upload data, visualize results, and interact with machine learning models.

## Architecture
The architecture of Sentinel-GNN consists of the following key components:

- **Backend**: 
  - Built with FastAPI, it handles data processing, model inference, and API endpoints for frontend interaction.
  - Utilizes Neo4j for graph database management, allowing efficient querying and data retrieval.
  - Implements various agents for data analysis and model training, ensuring modularity and scalability.

- **Frontend**: 
  - Developed using React, it provides a user-friendly interface for data upload, visualization, and interaction with the backend services.
  - Incorporates 3D visualizations and a chat interface for explainability, enhancing user engagement and understanding.

## Setup Instructions

### Backend
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the FastAPI server:
   ```bash
   uvicorn app.api.server:app --reload
   ```

### Frontend
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install the required Node.js dependencies:
   ```bash
   npm install
   ```
3. Start the React application:
   ```bash
   npm start
   ```

## CI/CD Workflows
The project includes automated CI/CD workflows defined in the `.github/workflows/ci-cd.yml` file. These workflows ensure that code changes are tested and deployed seamlessly, maintaining the integrity and reliability of the application.

## Documentation
Comprehensive documentation is available in the `docs` directory, including architecture diagrams and API specifications. This documentation serves as a guide for developers and users to understand the system's functionality and integration points.

## Contributing
Contributions to the Sentinel-GNN project are welcome! Please follow the standard Git workflow for submitting issues and pull requests. Ensure that your code adheres to the project's coding standards and includes appropriate tests.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.