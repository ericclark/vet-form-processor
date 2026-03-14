# Local Development Setup

This guide provides instructions for running the Vet Form Processor application on your local machine.

## Option 1: Native Local Development (Recommended for offline testing)

This method uses SQLite, local storage, and mock extraction, removing the need for GCP credentials.

### 1. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```
The frontend will typically be accessible at `http://localhost:5173`.

---

## Option 2: Docker Compose

Use this option to run the full stack including a PostgreSQL database.

### 1. Prerequisites
Ensure you have Docker and Docker Compose installed.

### 2. Configuration
The current `docker-compose.yml` is configured for GCP integration. If you wish to use it with local mocks, you should update the environment variables in `docker-compose.yml`:
- `USE_LOCAL_STORAGE: "true"`
- `USE_MOCK_EXTRACTION: "true"`

### 3. Start the application
```bash
docker-compose up --build
```
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8080`
