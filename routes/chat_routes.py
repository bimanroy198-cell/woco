from flask import Blueprint, request, jsonify
from datetime import datetime
from database import messages_collection, workers_collection, contractors_collection

chat_bp = Blueprint("chat_bp", __name__)

@chat_bp.route("/chat/send", methods=["POST"])
def send_message():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Invalid JSON"}), 400

        sender_phone = data.get("sender_phone")
        receiver_phone = data.get("receiver_phone")
        message = data.get("message")

        if not sender_phone or not receiver_phone or not message:
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        now_iso = datetime.utcnow().isoformat()

        msg_data = {
            "sender_phone": sender_phone,
            "receiver_phone": receiver_phone,
            "message": message,
            "timestamp": now_iso,
            "read": False
        }

        messages_collection.insert_one(msg_data)
        msg_data.pop("_id", None)

        return jsonify({
            "success": True,
            "message_data": msg_data
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@chat_bp.route("/chat/history", methods=["GET"])
def get_chat_history():
    try:
        user1 = request.args.get("user1")
        user2 = request.args.get("user2")
        
        limit_val = request.args.get("limit", 100, type=int)
        skip_val = request.args.get("skip", 0, type=int)

        if not user1 or not user2:
            return jsonify({"success": False, "message": "user1 and user2 required"}), 400

        # Find all messages where (sender=user1 AND receiver=user2) OR (sender=user2 AND receiver=user1)
        query = {
            "$or": [
                {"sender_phone": user1, "receiver_phone": user2},
                {"sender_phone": user2, "receiver_phone": user1}
            ]
        }

        # Fetch latest messages first, then reverse them to maintain chronological order
        messages_cursor = messages_collection.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip_val).limit(limit_val)
        messages = list(messages_cursor)
        messages.reverse() # Reverse so oldest in this chunk is first

        # Mark unread messages as read if receiver is user1
        messages_collection.update_many(
            {"sender_phone": user2, "receiver_phone": user1, "read": False},
            {"$set": {"read": True}}
        )

        return jsonify({
            "success": True,
            "messages": messages
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


def get_user_details(phone):
    worker = workers_collection.find_one({"phone_number": phone}, {"_id": 0, "name": 1, "profile_photo_url": 1, "role": 1})
    if worker:
        return worker
    contractor = contractors_collection.find_one({"phone_number": phone}, {"_id": 0, "name": 1, "profile_photo_url": 1, "role": 1})
    if contractor:
        return contractor
    return {"name": "Unknown User", "profile_photo_url": None, "role": "unknown"}

@chat_bp.route("/chat/inbox", methods=["GET"])
def get_inbox():
    try:
        phone = request.args.get("phone")
        if not phone:
            return jsonify({"success": False, "message": "phone required"}), 400

        # Find all messages sent or received by this user
        query = {
            "$or": [
                {"sender_phone": phone},
                {"receiver_phone": phone}
            ]
        }

        # Sort by timestamp descending so we process the newest first
        messages = list(messages_collection.find(query, {"_id": 0}).sort("timestamp", -1))

        inbox_map = {}

        for msg in messages:
            other_user = msg["receiver_phone"] if msg["sender_phone"] == phone else msg["sender_phone"]
            
            # Since we sorted by descending, the first time we see an 'other_user', it's their latest message
            if other_user not in inbox_map:
                user_details = get_user_details(other_user)
                inbox_map[other_user] = {
                    "contact_phone": other_user,
                    "contact_name": user_details.get("name"),
                    "contact_photo": user_details.get("profile_photo_url"),
                    "contact_role": user_details.get("role"),
                    "latest_message": msg["message"],
                    "timestamp": msg["timestamp"],
                    "unread_count": 0
                }
            
            # Count unread messages from this contact
            if msg["sender_phone"] == other_user and not msg.get("read", False):
                inbox_map[other_user]["unread_count"] += 1

        inbox_list = list(inbox_map.values())
        # The inbox map might not be perfectly sorted by timestamp anymore because of dictionary insertion order
        # So we sort it explicitly before returning
        inbox_list.sort(key=lambda x: x["timestamp"], reverse=True)

        return jsonify({
            "success": True,
            "inbox": inbox_list
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
