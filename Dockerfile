# 1) React 프론트엔드 빌드
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# 2) FastAPI 백엔드 + 빌드된 프론트엔드 정적 서빙
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY core/ ./core/
COPY data/ ./data/
COPY config.py ./
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

ENV DATABASE_URL=sqlite:////app/backend/data/app.db
EXPOSE 8000
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
