# Hotel Review Sentiment Analysis Platform 🏨📊

A comprehensive **Django-based multi-agent system** for intelligent hotel review analysis using **CrewAI framework** and **HuggingFace AI models**. This platform provides real-time sentiment analysis, automated scoring, and business intelligence insights for hospitality management.

## 🎯 Project Overview

This platform combines **artificial intelligence** with **web application development** to create a production-ready system that helps hotels understand customer feedback at scale. Built with modern architecture principles and real AI integration.
<img width="1741" height="821" alt="IRWA" src="https://github.com/user-attachments/assets/0bb8cabb-4ed1-44bf-b894-c1bcf5ee9ea0" />




## 🤖 Multi-Agent Architecture

### **Three Specialized AI Agents:**

#### 1. **Classifier Agent** 🔍
- **Purpose**: Advanced sentiment classification
- **Technology**: HuggingFace RoBERTa transformer model
- **Capabilities**: 
  - Real-time sentiment detection (Positive/Negative/Neutral)
  - Confidence scoring with professional fallback logic
  - Batch processing optimization

#### 2. **Scorer Agent** ⭐
- **Purpose**: Review quality assessment and rating prediction
- **Technology**: HuggingFace BERT model + intelligent scoring
- **Capabilities**:
  - 1-5 star rating prediction
  - Quality metrics analysis
  - Confidence-based scoring

#### 3. **Summarizer Agent** 📝
- **Purpose**: Business intelligence and insight generation
- **Technology**: Pattern recognition and text analytics
- **Capabilities**:
  - Executive summary generation
  - Key theme extraction
  - Actionable business insights

### **Orchestrator System** 🎼
- **ReviewProcessingOrchestrator**: Coordinates all agents in optimized workflows
- **Single Review Pipeline**: Individual review processing
- **Batch Processing**: Efficient handling of large datasets
- **Status Monitoring**: Real-time workflow tracking

## ⚡ Key Features

### **Core Functionality**
- 🔄 **Real-time Sentiment Analysis**: Instant processing of customer reviews
- 📈 **Analytics Dashboard**: Interactive visualizations and business metrics
- 📊 **Batch Processing**: Efficient handling of CSV uploads with progress tracking
- 🎯 **Multi-dimensional Analysis**: Sentiment, scoring, and summarization in one platform
- 📱 **Responsive Web Interface**: Modern, professional dashboard design

### **Technical Excellence**
- 🏗️ **Django Architecture**: Scalable web framework with proper app separation
- 🧠 **AI Integration**: Real HuggingFace models (not rule-based implementations)
- 🔌 **REST API**: Complete API endpoints for external integrations
- 📊 **Database Design**: Comprehensive models for hotels, reviews, analytics
- 🚀 **Production Ready**: Proper logging, error handling, and deployment configuration

## 🛠️ Technology Stack

### **Backend Framework**
- **Django 4.2**: Web framework and ORM
- **Django REST Framework**: API development
- **SQLite/PostgreSQL**: Database systems

### **AI & Machine Learning**
- **CrewAI**: Multi-agent framework and orchestration
- **HuggingFace Transformers**: Pre-trained AI models
- **PyTorch**: Deep learning backend
- **NLTK/SpaCy**: Natural language processing utilities

### **Frontend & UI**
- **HTML5/CSS3**: Modern responsive design
- **JavaScript**: Interactive dashboard functionality  
- **Chart.js**: Data visualization and analytics
- **Bootstrap**: Professional UI components

### **Data & Analytics**
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Matplotlib/Seaborn**: Statistical plotting
- **Plotly**: Interactive visualizations

### **Production Tools**
- **Gunicorn**: WSGI HTTP server
- **WhiteNoise**: Static file serving
- **python-dotenv**: Environment configuration
- **Celery/Redis**: Asynchronous task processing

## 🚀 Quick Start Guide

### **Prerequisites**
- Python 3.8+ 
- Git
- HuggingFace Account (for API access)

### **Installation**

```bash
# 1. Clone Repository
git clone https://github.com/iiTzIsh/multiagent-review-sentiment-ai.git
cd multiagent-review-sentiment-ai

# 2. Create Virtual Environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux  
source .venv/bin/activate

# 3. Install Dependencies
pip install -r requirements.txt

# 4. Environment Configuration
# Create .env file (see .env.example)
echo "HUGGINGFACE_API_KEY=your_huggingface_token_here" > .env

# 5. Database Setup
python manage.py migrate
python manage.py createsuperuser

# 6. Run Development Server
python manage.py runserver
```

### **Access the Application**
- **Main Dashboard**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/api

## � Application Features

### **Dashboard Interface**
- **System Overview**: Agent status and performance metrics
- **Review Management**: Upload, process, and analyze reviews
- **Analytics Visualization**: Interactive charts and business insights
- **Batch Operations**: Efficient processing of large review datasets

### **Management Commands**
```bash
# Process reviews with AI agents
python manage.py process_with_crewai --batch-size 50

# Clean processed reviews
python manage.py clean_reviews --confirm

# System health check
python manage.py shell
```

### **API Endpoints**
- `GET /api/reviews/` - Review data with filters
- `POST /api/reviews/analyze/` - Process single review
- `GET /api/analytics/trends/` - Sentiment trends
- `POST /api/reviews/batch/` - Batch processing

## 🏗️ Project Architecture

```
multiagent-review-sentiment-ai/
├── agents/                          # 🤖 AI Agent System
│   ├── classifier/                  #   Sentiment Classification
│   ├── scorer/                      #   Review Scoring
│   ├── summarizer/                  #   Business Intelligence
│   ├── orchestrator.py              #   Multi-agent Coordinator
│   └── django_integration.py       #   Django Integration Layer
├── apps/                            # 📱 Django Applications
│   ├── dashboard/                   #   Web Interface & Views
│   ├── reviews/                     #   Core Review Management
│   ├── analytics/                   #   Business Intelligence
│   └── api/                         #   REST API Endpoints
├── hotel_review_platform/           # ⚙️ Django Configuration
│   ├── settings.py                  #   Application Settings
│   ├── urls.py                      #   URL Routing
│   ├── wsgi.py                      #   WSGI Configuration
│   └── asgi.py                      #   ASGI Configuration
├── static/                          # 🎨 Static Assets
│   ├── css/dashboard.css            #   Professional Styling
│   └── js/enhanced-dashboard.js     #   Interactive Features
├── templates/                       # 📄 HTML Templates
├── utils/                          # 🛠️ Utility Functions
├── logs/                           # 📋 Application Logs
├── requirements.txt                # 📦 Dependencies
├── manage.py                       # 🚀 Django Management
└── sample_reviews.csv             # 📊 Demo Data
```

## � Use Cases & Applications

### **Hotel Management**
- **Guest Feedback Analysis**: Understand customer satisfaction trends
- **Reputation Management**: Monitor and respond to review patterns  
- **Service Improvement**: Identify specific areas for enhancement
- **Competitive Analysis**: Benchmark against industry standards

### **Business Intelligence**
- **Executive Dashboards**: High-level insights for management decisions
- **Trend Analysis**: Historical sentiment and quality patterns
- **Performance Metrics**: KPIs for customer satisfaction
- **Automated Reporting**: Scheduled business intelligence reports

## 🔧 Configuration & Deployment

### **Environment Variables**
Create `.env` file with:
```env
HUGGINGFACE_API_KEY=your_huggingface_token_here
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

## 🙏 Acknowledgments

- **HuggingFace**: For providing excellent transformer models
- **CrewAI**: For the multi-agent framework
- **Django Community**: For the robust web framework
- **Open Source AI**: For making advanced AI accessible

---

**Built with ❤️ for the hospitality industry**
