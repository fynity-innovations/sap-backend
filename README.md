# AI Profile Evaluation Platform

Production-ready Django REST API backend for AI-powered student profile evaluation.

## Architecture

**Modular Design**:
- `profiles/` - Main app with models, views, serializers
- `profiles/services/` - Service layer (OTP, AI, SMS)
- `profiles/utils.py` - Utility functions

## Features

✅ **Phone-Based Authentication**: OTP verification system  
✅ **AI Evaluation**: OpenAI API integration for profile scoring  
✅ **Production Database**: MySQL with JSON field support  
✅ **Rate Limiting**: OTP request protection  
✅ **Session Management**: Secure profile data handling  
✅ **Comprehensive Validation**: Input sanitization and validation  
✅ **Error Handling**: Structured error responses  
✅ **Security Headers**: CORS, XSS, CSRF protection  

## Database Models

### StudentProfile
- UUID primary key
- Personal: name, email, phone (unique)
- Academic: countries (JSON), degree, fields (JSON), cgpa, grad_year
- Financial: budget_lakh
- AI Results: ai_score, ai_result (JSON)
- Metadata: is_verified, timestamps

### PhoneOTP
- UUID primary key
- phone, otp (6-digit), expires_at, is_used
- Redis-based with database fallback

## API Endpoints

### POST /api/profile/initiate/
Accepts complete profile data, validates input, generates OTP, sends SMS.

**Request:**
```json
{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "countries": ["United States", "Canada"],
    "degree": "Master of Science",
    "fields": ["Computer Science", "Data Science"],
    "cgpa": "3.75",
    "grad_year": "2023",
    "budget_lakh": 50
}
```

**Response:**
```json
{
    "success": true,
    "message": "OTP sent successfully",
    "phone": "7890",
    "details": "123456"  // Development mode only
}
```

### POST /api/profile/verify/
Verifies OTP, creates profile, runs AI evaluation.

**Request:**
```json
{
    "phone": "+1234567890",
    "otp": "123456"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Profile created and evaluated successfully",
    "profile": {...},
    "evaluation": {
        "score": 85,
        "best_countries": ["USA", "Canada", "UK"],
        "recommended_programs": ["MS CS", "Data Science MSc"],
        "improvement_tips": ["Improve English scores", "Gain experience"],
        "assessment_summary": "Strong academic profile..."
    }
}
```

### GET /api/profile/detail/<phone>/
Retrieves verified profile details.

## Services

### OTP Service
- 6-digit numeric generation
- Redis caching with 5-minute expiration
- Rate limiting (3 requests per hour)
- Database fallback

### SMS Service
- Twilio integration with development fallback
- Phone number validation
- Error handling and logging

### AI Service
- OpenAI GPT-3.5-turbo integration
- Structured JSON prompt engineering
- Fallback mock evaluation
- Comprehensive scoring algorithm

## Security Features

### Validation
- Phone number format validation
- Email format validation
- CGPA range validation (0.00-10.00)
- Field length limits
- Required field validation

### Rate Limiting
- OTP: 3 requests per hour per phone
- Redis-based storage
- Graceful fallback to database

### Data Protection
- Phone number masking in responses
- Session-based temporary storage
- No OTP exposure in production
- XSS and CSRF protection

## Production Setup

### Environment Variables
```bash
# Database
DB_NAME=ai_profile_db
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306

# OpenAI
OPENAI_API_KEY=sk-your-openai-key

# Twilio
TWILIO_ACCOUNT_SID=ACyour-sid
TWILIO_AUTH_TOKEN=your-token
TWILIO_PHONE_NUMBER=+1234567890

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-production-secret
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
```

### Database Migration
```bash
# Create database
CREATE DATABASE ai_profile_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Run migrations
python manage.py migrate
```

### Testing
```bash
# Run automated tests
python test_api.py

# Manual testing
curl -X POST http://localhost:8000/api/profile/initiate/ \
  -H "Content-Type: application/json" \
  -d @profile_data.json
```

## AI Evaluation Logic

The AI evaluation considers:
1. **Academic Performance** (40%): CGPA, degree relevance
2. **Budget Constraints** (20%): Financial feasibility
3. **Country Selection** (20%): Admission competitiveness
4. **Field Alignment** (15%): Market demand and job prospects
5. **Profile Completeness** (5%): Data quality

Returns structured JSON with:
- Overall score (0-100)
- Best matching countries
- Recommended programs
- Improvement suggestions
- Assessment summary

## Development Notes

- Uses SQLite for development, MySQL for production
- Mock AI evaluation when OpenAI API unavailable
- Console OTP display for development testing
- Comprehensive error logging
- Session-based profile data storage

## Admin Interface

Access at `/admin/` with:
- StudentProfile management
- PhoneOTP monitoring
- Full CRUD operations
- Search and filtering capabilities