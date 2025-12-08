FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV FLASK_APP=manage.py
CMD ["python", "manage.py", "run", "--host=0.0.0.0"]
