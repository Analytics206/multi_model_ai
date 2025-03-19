# Multi-Model AI API Integration System

A Python-based system with an OpenAPI chat interface to facilitate API calls to multiple AI model providers simultaneously.

## Features

- **Multi-Model API Support**: Call two AI models simultaneously (OpenAI, Anthropic, DeepSeek, Hugging Face, Google)
- **Prompt Management**: Transform and cache prompts to match each model's required format
- **User-Friendly Interface**: Select models, load saved prompts, and manage API keys
- **Flexible Deployment**: Run locally or deploy to the cloud

## Project Structure

The system is organized into several key components:

- **API Server**: FastAPI-based server with endpoints for model selection, prompt management, and API calls
- **Database Layer**: SQLite database for storing model configurations, prompts, and logs
- **Provider Integrations**: Adapters for each AI model provider's API
- **Prompt Engine**: Transforms prompts to match each model's required format
- **Frontend**: User interface for interacting with the system

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

#### Docker Setup (Recommended)
1. Clone the repository:
   ```
   git clone https://github.com/your-username/multi-model-ai.git
   cd multi-model-ai
   ```

2. Create a `.env` file based on the provided template:
   ```
   cp .env.example .env
   ```

3. Edit the `.env` file to add your API keys and configure the application.

4. Build and start the Docker containers:
   ```
   docker-compose up -d --build
   ```

#### Local Development (Alternative)
If you prefer to develop without Docker:
1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python main.py
   ```

### Running the Application

#### Local Development
Start the application:
```
python main.py
```

The server will start on http://localhost:8000 by default.

#### Docker Deployment
To run the application with Docker:

1. Make sure you have Docker and Docker Compose installed
2. Build and start the containers:
```
docker-compose up -d --build
```
3. To view logs:
```
docker-compose logs -f
```
4. To stop the containers:
```
docker-compose down
```

The server will be accessible at http://localhost:8000.

## Usage

1. Open your browser and navigate to http://localhost:8000
2. Select two AI models from the dropdown menus
3. Choose a saved prompt or create a new one
4. Provide API keys if needed
5. Submit your request and view the side-by-side responses

## Development

### Adding a New Model Provider

1. Create a new provider class in the `providers/` directory
2. Implement the required interface methods
3. Add the provider to the database through the admin interface

### Contribution Guidelines

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.