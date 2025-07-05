# Webhook Listener

This is a Flask-based webhook listener that captures and displays webhook data in real-time with 1-hour filtering.

## Features
- Accepts POST requests at `/webhook` with JSON payloads
- Displays stats on home page (`/`)
- Filters webhook data from the last hour
- Auto-cleanup every 5 minutes
- Health check endpoint at `/health`
