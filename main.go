package main

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"os/exec"
	"strings"
)

func main() {
	ctx := context.Background()

	cmd := exec.CommandContext(ctx, "streamlit", "run", "app.py")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	go func() {
		if err := cmd.Run(); err != nil {
			panic(err)
		}
	}()

	targetURL, _ := url.Parse("http://localhost:8501")

	proxy := &httputil.ReverseProxy{
		Rewrite: func(r *httputil.ProxyRequest) {
			r.SetURL(targetURL)
			r.Out.Host = r.In.Host
		},
	}

	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method == "GET" && r.URL.Path == "/" {
			resp, err := http.Get("http://localhost:8501")

			if err != nil {
				http.Error(w, err.Error(), http.StatusBadGateway)
				return
			}

			defer resp.Body.Close()

			if resp.StatusCode != http.StatusOK {
				http.Error(w, http.StatusText(resp.StatusCode), http.StatusBadGateway)
				return
			}

			data, err := io.ReadAll(resp.Body)

			if err != nil {
				http.Error(w, err.Error(), http.StatusBadGateway)
				return
			}

			link := `<link rel="manifest" href="/manifest.json" />`
			link += `<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">`

			text := string(data)
			text = strings.Replace(text, "</head>", link+"</head>", 1)

			w.Header().Set("Content-Type", "text/html")
			w.Write([]byte(text))
			return
		}

		if r.Method == "GET" && r.URL.Path == "/manifest.json" {
			title := os.Getenv("TITLE")

			if title == "" {
				title = "Chat"
			}

			manifest := map[string]any{
				"name":             title,
				"short_name":       title,
				"start_url":        "/",
				"display":          "standalone",
				"background_color": "rgb(14, 17, 23)",
				"icons": []map[string]any{
					{
						"src":   "/app/static/logo.png",
						"sizes": "800x800",
						"type":  "image/png",
					},
				},
			}

			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(manifest)
			return
		}

		proxy.ServeHTTP(w, r)
	})

	http.ListenAndServe(":8000", handler)
}
