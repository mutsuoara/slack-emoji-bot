from flask import Flask, request, jsonify
from slack_sdk import WebClient
import os

app = Flask(__name__)
client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json(force=True)
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data["challenge"]})

    event = data.get("event", {})
    if event.get("type") == "reaction_added" and event.get("reaction") == os.environ["TRIGGER_EMOJI"]:
        if event["item"]["channel"] == os.environ["SOURCE_CHANNELS"].split(","):
            try:
                message = client.conversations_history(
                    channel=event["item"]["channel"],
                    latest=event["item"]["ts"],
                    inclusive=True,
                    limit=1
                )["messages"][0]
                text = message.get("text", "")
                user = message.get("user", "unknown")

                client.chat_postMessage(
                    channel=os.environ["TARGET_CHANNEL"],
                    text=f"✅ *Forwarded message from <@{user}>:*\n> {text}"
                )
            except Exception as e:
                print("Error:", e)

    return "", 200
