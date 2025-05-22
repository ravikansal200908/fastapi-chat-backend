# FastAPI Chat API

A modern, scalable chat API built with FastAPI, PostgreSQL, and Redis.

## Features

- Create and manage chat conversations
- Branch conversations from any point in chat history
- PostgreSQL for relational data storage
- MongoDB for document storage
- Caching support
- Database migrations with Alembic

## Project Structure

```
fastapi_chat_api/
├── alembic/              # Database migrations
├── app/
│   ├── api/             # API endpoints
│   │   └── v1/
│   │       └── endpoints/
│   ├── core/            # Core functionality
│   │   ├── auth.py      # Authentication
│   │   ├── config.py    # Configuration
│   │   ├── errors.py    # Error handling
│   │   └── middleware.py # Middleware
│   ├── db/              # Database
│   │   └── postgres.py  # PostgreSQL setup
│   ├── models/          # Database models
│   │   └── models.py    # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   │   └── schemas.py   # Data validation
│   └── main.py          # Application entry point
├── alembic.ini          # Alembic configuration
├── requirements.txt     # Project dependencies
└── README.md           # Project documentation
```

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 6+

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/fastapi-chat-api.git
cd fastapi-chat-api
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```env
# API Settings
API_V1_PREFIX=/api/v1
PROJECT_NAME=FastAPI Chat API
VERSION=1.0.0
DESCRIPTION="A modern chat API built with FastAPI"
DEBUG=True

# Database Configuration
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=your_db_name
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=your_mongodb_name

# Security
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
CACHE_EXPIRE_TIME=300

# CORS Settings
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

5. Run database migrations:
```bash
./run_alembic.sh
```

## Running the Application

1. Start the server:
```bash
uvicorn app.main:app --reload
```

2. Access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/v1/token` - Get access token
- `POST /api/v1/users/` - Create new user

### Users
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update current user
- `GET /api/v1/users/{user_id}` - Get specific user

### Conversations
- `POST /api/v1/conversations/` - Create conversation
- `GET /api/v1/conversations/` - List conversations
- `GET /api/v1/conversations/{conversation_id}` - Get conversation
- `DELETE /api/v1/conversations/{conversation_id}` - Delete conversation

## Development

### Running Tests
```bash
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 