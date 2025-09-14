import asyncio
import os
from typing import Optional

from atproto import Client, IdResolver, models
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

USERNAME = os.getenv("ATPROTO_USERNAME")
PASSWORD = os.getenv("ATPROTO_PASSWORD")

app = FastAPI(title="SevenSky Chat API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5175", "http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global client instance
client = None
dm_client = None
dm = None


async def get_client():
    """Get or create ATProtocol client"""
    global client, dm_client, dm

    if client is None:
        client = Client()
        client.login(USERNAME, PASSWORD)
        dm_client = client.with_bsky_chat_proxy()
        dm = dm_client.chat.bsky.convo

    return client, dm


def upload_image(client: Client, image_data: bytes):
    """Upload an image file and return the blob reference"""
    blob_response = client.com.atproto.repo.upload_blob(image_data)
    return blob_response.blob


@app.get("/")
async def root():
    return {"message": "SevenSky Chat API is running!"}


@app.get("/conversations")
async def get_conversations():
    """Get all conversations for the current user"""
    try:
        client, dm = await get_client()
        convo_list = dm.list_convos()

        conversations = []
        for convo in convo_list.convos:
            # Get the last message for each conversation
            last_message = None
            try:
                messages = dm.list_messages(convo.id, limit=1)
                if messages.messages:
                    msg = messages.messages[0]
                    last_message = {
                        "id": msg.id,
                        "text": msg.text,
                        "author": {
                            "did": msg.sender.did,
                            "handle": msg.sender.handle,
                            "displayName": getattr(msg.sender, "displayName", None),
                            "avatar": getattr(msg.sender, "avatar", None),
                        },
                        "createdAt": msg.sent_at,
                        "embed": getattr(msg, "embed", None),
                    }
            except Exception as e:
                print(f"Error getting last message for convo {convo.id}: {e}")
                pass

            conversations.append(
                {
                    "id": convo.id,
                    "members": [
                        {
                            "did": member.did,
                            "handle": member.handle,
                            "displayName": getattr(member, "displayName", None),
                            "avatar": getattr(member, "avatar", None),
                        }
                        for member in convo.members
                    ],
                    "lastMessage": last_message,
                    "unreadCount": 0,  # TODO: Implement unread count
                }
            )

        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{convo_id}/messages")
async def get_messages(convo_id: str, limit: int = 50):
    """Get messages for a specific conversation"""
    try:
        client, dm = await get_client()
        messages_response = dm.list_messages(convo_id, limit=limit)

        messages = []
        for msg in messages_response.messages:
            messages.append(
                {
                    "id": msg.id,
                    "text": msg.text,
                    "author": {
                        "did": msg.sender.did,
                        "handle": msg.sender.handle,
                        "displayName": getattr(msg.sender, "displayName", None),
                        "avatar": getattr(msg.sender, "avatar", None),
                    },
                    "createdAt": msg.sent_at,
                    "embed": getattr(msg, "embed", None),
                }
            )

        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send-message-with-image")
async def send_message_with_image(
    convo_id: str, text: str, image: Optional[UploadFile] = File(None)
):
    """Send a message with optional image attachment"""
    try:
        client, dm = await get_client()

        message_data = {"text": text, "createdAt": client.get_current_time_iso()}

        if image:
            # Upload the image blob
            image_data = await image.read()
            blob = upload_image(client, image_data)

            message_data["embed"] = {
                "$type": "app.bsky.embed.images",
                "images": [{"image": blob, "alt": "Image attachment"}],
            }

        message = dm.send_message(
            models.ChatBskyConvoSendMessage.Data(
                convo_id=convo_id,
                message=models.ChatBskyConvoDefs.MessageInput(**message_data),
            )
        )

        return {"message_id": message.id, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/create-conversation")
async def create_conversation(user_handle: str):
    """Create a new conversation with a user"""
    try:
        client, dm = await get_client()

        # Resolve the user handle to DID
        id_resolver = IdResolver()
        user_did = id_resolver.handle.resolve(user_handle)

        # Get current user DID
        current_user_did = client.me.did

        # Create or get conversation between the two users
        convo = dm.get_convo_for_members(
            models.ChatBskyConvoGetConvoForMembers.Params(
                members=[current_user_did, user_did]
            )
        ).convo

        return {"convo_id": convo.id, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/profile")
async def get_profile():
    """Get current user profile"""
    try:
        client, dm = await get_client()
        profile = client.app.bsky.actor.get_profile({"actor": USERNAME})

        return {
            "did": profile.did,
            "handle": profile.handle,
            "displayName": getattr(profile, "displayName", None),
            "avatar": getattr(profile, "avatar", None),
            "description": getattr(profile, "description", None),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def main() -> None:
    """Main function for testing - can be run independently"""

    async def test_main():
        client, dm = await get_client()

        # List existing conversations
        convo_list = dm.list_convos()
        print(f"Your conversations ({len(convo_list.convos)}):")
        for convo in convo_list.convos:
            members = ", ".join(member.display_name for member in convo.members)
            print(f"- ID: {convo.id} ({members})")

        # Create resolver instance
        id_resolver = IdResolver()

        user1_handle = USERNAME
        user2_handle = "ali616c.bsky.social"

        try:
            # Resolve both user handles to DIDs
            user1_did = id_resolver.handle.resolve(user1_handle)
            user2_did = id_resolver.handle.resolve(user2_handle)

            print(f"Resolved {user1_handle} to {user1_did}")
            print(f"Resolved {user2_handle} to {user2_did}")

            # Create or get conversation between the two users
            convo = dm.get_convo_for_members(
                models.ChatBskyConvoGetConvoForMembers.Params(
                    members=[user1_did, user2_did]
                )
            ).convo

            print(f"\nConvo ID: {convo.id}")
            print("Convo members:")
            for member in convo.members:
                print(f"- {member.display_name} ({member.did})")

            # Send a text message
            text_message = dm.send_message(
                models.ChatBskyConvoSendMessage.Data(
                    convo_id=convo.id,
                    message=models.ChatBskyConvoDefs.MessageInput(
                        text="Hello! This is a text message.",
                    ),
                )
            )
            print(f"Text message sent! Message ID: {text_message.id}")

        except Exception as e:
            print(f"Error: {e}")
            print(
                "Make sure the user handles are valid and both users exist on ATProtocol"
            )

    asyncio.run(test_main())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
