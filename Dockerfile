FROM golang:1 AS launcher

WORKDIR /src

COPY go.mod ./
RUN go mod download

COPY *.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -o launcher


FROM ghcr.io/adrianliechti/llama-streamlit

COPY --from=launcher /src/launcher /launcher

CMD ["/launcher"]