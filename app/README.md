# Email refresh UI

The app sends refresh requests and receives progress over the `/emails` API and
WebSocket routes. During Vite development, those routes are proxied to
`http://127.0.0.1:8000` by default. Set `VITE_API_PROXY_TARGET` in an app `.env`
file to use a different backend address.

In production, serve the app and proxy `/emails` to the FastAPI server on the
same origin so both HTTP requests and WebSocket connections are forwarded.
