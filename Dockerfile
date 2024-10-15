FROM golang:1 AS launcher

WORKDIR /src

COPY go.mod ./
RUN go mod download

COPY *.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -o launcher


FROM python:3.12-slim

WORKDIR /app

COPY /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=launcher /src/launcher /launcher

COPY /app/.streamlit/ .streamlit/
COPY /app/static/ static/
COPY /app/app.py .

CMD ["/launcher"]