FROM python:3-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY .streamlit/ .streamlit/
COPY static/ static/
COPY app.py .

CMD [ "streamlit", "run", "app.py" ]
