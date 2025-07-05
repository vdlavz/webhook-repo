import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from threading import Lock
import threading
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_webhook_secret")

webhook_data = []
webhook_lock = Lock()


class WebhookStore:

    def __init__(self):
        self.data = []
        self.lock = Lock()

    def add_webhook(self, payload):
        with self.lock:
            webhook_entry = {
                'timestamp': datetime.now(),
                'payload': payload,
                'id': len(self.data) + 1
            }
            self.data.append(webhook_entry)
            logger.info(f"Added webhook entry with ID: {webhook_entry['id']}")
            return webhook_entry

    def get_recent_webhooks(self, hours=1):
        cutoff_time = datetime.now() - timedelta(hours=hours)
        with self.lock:
            recent = [
                entry for entry in self.data
                if entry['timestamp'] >= cutoff_time
            ]
            return sorted(recent, key=lambda x: x['timestamp'], reverse=True)

    def cleanup_old_webhooks(self, hours=1):
        cutoff_time = datetime.now() - timedelta(hours=hours)
        with self.lock:
            old_count = len(self.data)
            self.data = [
                entry for entry in self.data
                if entry['timestamp'] >= cutoff_time
            ]
            new_count = len(self.data)
            if old_count > new_count:
                logger.info(
                    f"Cleaned up {old_count - new_count} old webhook entries")

    def get_stats(self):
        cutoff_time = datetime.now() - timedelta(hours=1)
        with self.lock:
            total_count = len(self.data)
            recent_count = len([
                entry for entry in self.data
                if entry['timestamp'] >= cutoff_time
            ])
            last_received = max([entry['timestamp'] for entry in self.data
                                 ]) if self.data else None
            return {
                'total_count': total_count,
                'recent_count': recent_count,
                'last_received': last_received
            }


webhook_store = WebhookStore()


def cleanup_worker():
    while True:
        try:
            webhook_store.cleanup_old_webhooks(1)
            time.sleep(300)
        except Exception as e:
            logger.error(f"Error in cleanup worker: {e}")
            time.sleep(60)


cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
cleanup_thread.start()


@app.route('/')
def index():
    try:
        recent_webhooks = webhook_store.get_recent_webhooks(1)
        stats = webhook_store.get_stats()
        return render_template('index.html',
                               webhooks=recent_webhooks,
                               stats=stats)
    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        return render_template('index.html',
                               webhooks=[],
                               stats={
                                   'total_count': 0,
                                   'recent_count': 0,
                                   'last_received': None
                               },
                               error="Error loading webhook data")


@app.route('/webhook', methods=['POST'])
def webhook_endpoint():
    try:
        if not request.is_json:
            logger.warning(f"Invalid content type: {request.content_type}")
            return jsonify({
                'error': 'Content-Type must be application/json',
                'received_content_type': request.content_type
            }), 400

        try:
            payload = request.get_json()
        except Exception as json_error:
            logger.error(f"JSON parsing error: {json_error}")
            return jsonify({
                'error': 'Invalid JSON payload',
                'details': str(json_error)
            }), 400

        if payload is None:
            logger.warning("Empty JSON payload received")
            return jsonify({'error': 'Empty JSON payload'}), 400

        webhook_entry = webhook_store.add_webhook(payload)
        logger.info(
            f"Webhook received and stored successfully. ID: {webhook_entry['id']}"
        )

        return jsonify({
            'status': 'success',
            'message': 'Webhook received and stored',
            'webhook_id': webhook_entry['id'],
            'timestamp': webhook_entry['timestamp'].isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Unexpected error processing webhook: {e}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


@app.route('/stats')
def stats():
    try:
        stats = webhook_store.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': 'Error retrieving statistics'}), 500


@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    logger.info("Starting webhook listener on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
