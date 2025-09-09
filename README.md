# Hotel Review Insight Platform

A comprehensive multi-agent platform for analyzing hotel reviews using Django, CrewAI, and HuggingFace APIs.

## Features

- **Multi-Agent Architecture**: Specialized agents for sentiment analysis, scoring, summarization, and search
- **Review Processing**: Automated sentiment classification and scoring
- **Smart Search**: Semantic search capabilities across reviews
- **Interactive Dashboard**: User-friendly interface with charts and analytics
- **Export Capabilities**: Generate PDF and Excel reports
- **Responsive Design**: Works on desktop and mobile devices

## Agents

1. **Review Classifier Agent**: Classifies reviews as positive, negative, or neutral
2. **Sentiment Scorer Agent**: Assigns numerical scores (0-5)
3. **Summary Agent**: Generates concise summaries of pros and cons
4. **Information Retrieval Agent**: Enables semantic search and filtering
5. **Security Agent**: Handles authentication and authorization

## Technology Stack

- **Backend**: Django 4.2, Django REST Framework
- **AI Framework**: CrewAI for multi-agent orchestration
- **ML Models**: HuggingFace Transformers
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js
- **Database**: SQLite (development), PostgreSQL (production)
- **Task Queue**: Celery with Redis
- **Deployment**: Docker, Gunicorn

## Installation

1. Clone the repository
2. Create virtual environment: `python -m venv .venv`
3. Activate virtual environment: `.venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure your API keys
6. Run migrations: `python manage.py migrate`
7. Create superuser: `python manage.py createsuperuser`
8. Start development server: `python manage.py runserver`

## Usage

1. Access the dashboard at `http://localhost:8000`
2. Upload CSV files with review data
3. View automated analysis results
4. Use search functionality to filter reviews
5. Export reports in PDF or Excel format

## Project Structure

```
hotel_review_platform/
├── agents/                 # AI Agents
├── apps/                  # Django Apps
├── core/                  # Core Django settings
├── static/               # Static files
├── templates/            # HTML templates
├── media/               # Uploaded files
└── utils/               # Utility functions
```

## License

MIT License
