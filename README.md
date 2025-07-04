# webhook-repo

A webhook listener built using Flask that receives and stores GitHub/webhook events and displays them in a real-time dashboard.

## Features

- Accepts JSON webhook payloads via `POST /webhook`
- Stores and displays events received in the last 1 hour
- Automatically cleans up old entries every 5 minutes
- Real-time dashboard UI with Bootstrap (Dark theme)
- Health check at `/health`, stats at `/stats`

## How to Run

Make sure you have Flask installed:

bash
pip install flask
