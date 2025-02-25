# ResumeMatcher

A web application that displays real-time job listings and helps users create tailored resumes for specific jobs.

## Project Structure

```
resume-matcher/
├── frontend/                 # Next.js frontend
├── backend/                  # Python FastAPI backend
```

## Getting Started

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Run the backend server:
   ```
   python app/main.py
   ```
   
   The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Run the development server:
   ```
   npm run dev
   ```
   
   The frontend will be available at `http://localhost:3000`

## Current Features

- Display job listings with filtering by category
- Expandable job cards showing details and requirements
- Simple and clean UI built with Next.js and Tailwind CSS

## Future Features

- Job scanning functionality
- Resume builder with templates
- AI-powered resume customization based on job descriptions
- User authentication
- Application tracking
- Job saving and comparison

## Tech Stack

- **Frontend**: Next.js, React, TypeScript, Tailwind CSS
- **Backend**: Python, FastAPI
- **Future Additions**: Database integration, authentication, resume generation