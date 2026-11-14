#!/bin/bash
cd backend
source venv/bin/activate
echo "🚀 Starting Backend on localhost:8000"
uvicorn app.main:app --reload
