import asyncio
from typing import Optional

from atproto import IdResolver, models
from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(prefix="/messaging", tags=["messaging"])


async def upload_image(client, image_data: bytes):
    """Upload an image file and return the blob reference"""
    loop = asyncio.get_event_loop()
    blob_response = await loop.run_in_executor(
        None, client.com.atproto.repo.upload_blob, image_data
    )
    return blob_response.blob


@router.get("/conversations")
async def get_conversations():
    """Get all conversations for the current user"""
    from main import get_client

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


@router.get("/conversations/{convo_id}/messages")
async def get_messages(convo_id: str, limit: int = 50):
    """Get messages for a specific conversation"""
    from main import get_client

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


@router.post("/send-message-with-image")
async def send_message_with_image(
    convo_id: str, text: str, image: Optional[UploadFile] = File(None)
):
    """Send a message with optional image attachment"""
    from main import get_client

    try:
        client, dm = await get_client()

        message_data = {"text": text, "createdAt": client.get_current_time_iso()}

        if image:
            # Upload the image blob
            image_data = await image.read()
            blob = await upload_image(client, image_data)

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


@router.post("/create-conversation")
async def create_conversation(user_handle: str):
    """Create a new conversation with a user"""
    from main import get_client

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
