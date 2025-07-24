from flask import Flask, request, jsonify
from slack_sdk import WebClient
from dotenv import load_dotenv
from datetime import datetime
import os

# Load env variables
load_dotenv()

app = Flask(__name__)
client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

# Parse env variables
SOURCE_CHANNELS = os.environ["SOURCE_CHANNELS"].split(",")
TARGET_CHANNEL = os.environ["TARGET_CHANNEL"]
TRIGGER_EMOJI = os.environ.get("TRIGGER_EMOJI", "white_check_mark")

# In-memory tracker for forwarded message IDs
forwarded_messages = set()

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json(force=True)

    # Slack URL verification challenge
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data["challenge"]})

    event = data.get("event", {})
    if event.get("type") == "reaction_added" and event.get("reaction") == TRIGGER_EMOJI:
        channel = event["item"]["channel"]
        message_id = event["item"]["ts"]

        # Only forward from allowed source channels
        if channel in SOURCE_CHANNELS:
            # Prevent forwarding the same message twice
            if message_id in forwarded_messages:
                print(f"⚠️ Message {message_id} already forwarded.")
                return "", 200

            try:
                # Get the original message
                result = client.conversations_history(
                    channel=channel,
                    latest=message_id,
                    inclusive=True,
                    limit=1
                )
                message = result["messages"][0]
                text = message.get("text", "")
                user = message.get("user", "unknown")
                ts = float(message.get("ts", 0))
                date_sent = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

                # Forward to target channel
                client.chat_postMessage(
                    channel=TARGET_CHANNEL,
                    text=f"✅ *Forwarded message from <@{user}>* (sent on {date_sent}):\n> {text}"
                )

                # Mark as forwarded
                forwarded_messages.add(message_id)

            except Exception as e:
                print(f"❌ Error forwarding message {message_id}: {e}")

    return "", 200
