# Vertex RAG Flask

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Tests](https://github.com/cherninlab/vertex-rag-flask/actions/workflows/ci.yml/badge.svg)

Flask application for building RAG (Retrieval Augmented Generation) systems using Google Vertex AI. Process PDFs with layout-aware parsing, chat with documents in multiple languages, and build AI-powered document analysis systems.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/cherninlab/vertex-rag-flask.git
cd vertex-rag-flask
```

2. Set up Python environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install --upgrade pip
```

3. Install the project:

```bash
pip install -e ".[dev]"
```

4. Configure environment:

```bash
cp .env.example .env
# Edit .env with your configuration:
# - Add your Google Cloud Project ID
# - Set path to service account credentials
```

5. Run the application:

```bash
flask run
```

## Google Cloud Setup

1. Create a new project in [Google Cloud Console](https://console.cloud.google.com/)

2. Enable required APIs:

```bash
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com

# Enable Cloud Storage API
gcloud services enable storage.googleapis.com

# Enable IAM API
gcloud services enable iam.googleapis.com
```

3. Create and configure service account:

```bash
# Create service account
gcloud iam service-accounts create vertex-rag-sa --display-name="Vertex RAG Service Account"

# Grant Vertex AI user role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:vertex-rag-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" --role="roles/aiplatform.user"

# Grant Storage Admin role (for bucket and file management)
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:vertex-rag-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" --role="roles/storage.admin"

# Download credentials
gcloud iam service-accounts keys create credentials.json --iam-account=vertex-rag-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

**Important Notes:**

- Keep your credentials.json secure and never commit it to version control
- The service account needs both Vertex AI and Storage permissions to function properly
- You can use more granular permissions instead of storage.admin if needed

## Usage

1. Start the application:

```bash
flask run
```

2. Open http://localhost:5000 in your browser

3. Upload a document

4. After processing, you'll be redirected to the chat interface

## Development

### Project Structure

```
vertex-rag-flask/
├── src/
│   ├── app/
│   │   ├── routes/      # API and web routes
│   │   ├── services/    # Business logic
│   │   ├── templates/   # HTML templates
│   │   └── utils/       # Helper functions
│   └── config/          # Configuration
├── tests/               # Test files
├── uploads/             # Temporary upload directory
├── credentials.json     # GCP service account key
├── pyproject.toml       # Project dependencies
└── README.md
```

### System Requirements

- Python 3.11+
- Google Cloud Project with enabled APIs
- Service account with appropriate permissions

### Running Tests

```bash
# Run pytest
pytest

# Run type checking
mypy .

# Run linting
flake8 .
```

### Code Style

The project uses several tools to maintain code quality:

- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Style guide enforcement
- **mypy**: Static type checking

These are automatically run as pre-commit hooks when you commit changes.

### Using Dev Containers

If you use VS Code:

1. Install the "Remote - Containers" extension
2. Open the project
3. Click "Reopen in Container" when prompted
4. VS Code will set up the development environment automatically

## Troubleshooting

### Common Issues

1. **Permission Denied Errors**

   - Verify that your service account has all required roles
   - Check if credentials.json is properly configured
   - Ensure APIs are enabled in your project

2. **Upload Failures**

   - Verify the file format is supported
   - Check if the selected bucket exists
   - Ensure your service account has storage permissions

3. **Chat Not Working**
   - Verify Vertex AI API is enabled
   - Check if the model has access to your document
   - Ensure proper network connectivity

## Contributing

Contributions are welcome!

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

⭐ If you find this project useful, please consider giving it a star! It helps make the project more visible and encourages development.
