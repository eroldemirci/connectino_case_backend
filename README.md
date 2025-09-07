# Notes Backend API

A FastAPI-based REST API for managing user notes with Supabase PostgreSQL database integration.

## 🚀 Quick Start Summary

**What you need:** Python 3.8+, the project files are ready

**Setup (3 minutes):**
1. Install dependencies: `pip install -r requirements.txt`
2. The `.env` file and database are already configured
3. Run: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
4. **Flutter baseUrl:** `http://YOUR-IP:8000` (find IP with `ipconfig`)
5. **Can't see in browser?** Try: `http://localhost:8000/docs#/`

**Features:** CRUD notes API, mobile-friendly, UUID users, async/high-performance

---

## Installation & Setup

### 1. Install Dependencies
```bash
# Create and activate virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install requirements
pip install -r requirements.txt
```

### 2. Run Application
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Access the API

**For local testing:**
- Health check: `http://localhost:8000`
- **Can't see anything in browser?** Use: `http://localhost:8000/docs#/` (Swagger UI)

**For mobile/Flutter apps:**
- Find your IP: Run `ipconfig` in terminal, look for "IPv4 Address"
- **Flutter baseUrl:** `http://YOUR-IP:8000` (example: `http://192.168.1.104:8000`)
- Base url env file -> lib>core>shared>env.dart

### 4. Database Schema (Reference)

The database is already configured. For reference, the `notes` table structure:

```sql
CREATE TABLE notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/notes/?user_id={uuid}` | Create note |
| GET | `/notes/?user_id={uuid}` | Get user's notes |
| GET | `/notes/{note_id}` | Get specific note |
| PUT | `/notes/{note_id}` | Update note |
| DELETE | `/notes/{note_id}` | Delete note |

### Request Examples

**Create Note:**
```bash
curl -X POST "http://localhost:8000/notes/?user_id=your-uuid" \
     -H "Content-Type: application/json" \
     -d '{"title": "My Note", "content": "Note content"}'
```

**Get User Notes:**
```bash
curl "http://localhost:8000/notes/?user_id=your-uuid"
```

## Mobile App Integration

**Flutter/Dio Example:**
```dart
class NotesApi {
  // Use your actual IP address here (find with ipconfig)
  static const String baseUrl = 'http://192.168.1.104:8000'; 
  late Dio _dio;

  NotesApi() {
    _dio = Dio(BaseOptions(baseUrl: baseUrl));
  }

  Future<List<dynamic>> getUserNotes(String userId) async {
    final response = await _dio.get('/notes/', queryParameters: {'user_id': userId});
    return response.data;
  }

  Future<Map<String, dynamic>> createNote(String userId, String title, String content) async {
    final response = await _dio.post('/notes/', 
      queryParameters: {'user_id': userId},
      data: {'title': title, 'content': content});
    return response.data;
  }
}
```

**Important:** Replace `192.168.1.104` with your actual IP address from `ipconfig`

## Troubleshooting

**Can't see anything in browser after starting server:**
- Try: `http://localhost:8000/docs#/` (Swagger UI interface)
- Or: `http://localhost:8000/health` (simple health check)

**Connection Refused from mobile app:** 
- Check server running with `--host 0.0.0.0`
- Verify IP address in mobile app matches your computer's IP
- Check firewall settings

**UUID Errors:**
- Use valid UUID format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

**Server not starting:**
- Make sure virtual environment is activated
- Check all dependencies installed: `pip install -r requirements.txt`

## Technical Details

**Ready-to-use:** Database and environment configuration already set up

**Dependencies:** FastAPI, uvicorn, SQLAlchemy, asyncpg, python-dotenv, pydantic

**API Documentation:** `http://localhost:8000/docs#/` (Swagger UI)

**File Structure:**
```
notes-backend/
├── main.py              # Main application (ready)
├── requirements.txt     # Dependencies list
├── .env                # Database config (ready)
└── README.md           # This file
```