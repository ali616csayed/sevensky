import os
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from atproto import Client, IdResolver, models
from dotenv import load_dotenv
from typing import List, Optional
import asyncio
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()
USERNAME = os.getenv("ATPROTO_USERNAME")
PASSWORD = os.getenv("ATPROTO_PASSWORD")

app = FastAPI(title="SevenSky Chat API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
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
    
    try:
        if client is None:
            logger.info("Creating new ATProtocol client...")
            client = Client()
            logger.info(f"Logging in with username: {USERNAME}")
            client.login(USERNAME, PASSWORD)
            logger.info("Successfully logged in to ATProtocol")
            
            dm_client = client.with_bsky_chat_proxy()
            dm = dm_client.chat.bsky.convo
            logger.info("Created chat proxy client")
        
        return client, dm
    except Exception as e:
        logger.error(f"Failed to create ATProtocol client: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def upload_image(client, image_data: bytes):
    """Upload an image file and return the blob reference"""
    try:
        logger.info("Uploading image blob...")
        blob_response = client.com.atproto.repo.upload_blob(image_data)
        logger.info(f"Successfully uploaded image blob: {blob_response.blob}")
        return blob_response.blob
    except Exception as e:
        logger.error(f"Failed to upload image: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

@app.get("/")
async def root():
    return {"message": "SevenSky Chat API is running!"}

@app.get("/conversations")
async def get_conversations():
    """Get all conversations for the current user"""
    try:
        logger.info("Getting conversations...")
        client, dm = await get_client()
        
        logger.info("Fetching conversation list from ATProtocol...")
        convo_list = dm.list_convos()
        logger.info(f"Found {len(convo_list.convos)} conversations")
        
        conversations = []
        for i, convo in enumerate(convo_list.convos):
            try:
                logger.info(f"Processing conversation {i+1}/{len(convo_list.convos)}: {convo.id}")
                
                # Get the last message for each conversation
                last_message = None
                try:
                    logger.info(f"Fetching last message for conversation {convo.id}")
                    messages = dm.get_messages(models.ChatBskyConvoGetMessages.Params(convo_id=convo.id, limit=1))
                    if messages.messages:
                        msg = messages.messages[0]
                        last_message = {
                            "id": msg.id,
                            "text": msg.text,
                            "author": {
                                "did": msg.sender.did,
                                "handle": msg.sender.did,
                                "displayName": getattr(msg.sender, 'displayName', None),
                                "avatar": getattr(msg.sender, 'avatar', None)
                            },
                            "createdAt": msg.sent_at,
                            "embed": getattr(msg, 'embed', None)
                        }
                        logger.info(f"Found last message: {msg.id}")
                    else:
                        logger.info(f"No messages found for conversation {convo.id}")
                except Exception as e:
                    logger.warning(f"Failed to get last message for conversation {convo.id}: {e}")
                
                conversation_data = {
                    "id": convo.id,
                    "members": [
                        {
                            "did": member.did,
                            "handle": member.handle,
                            "displayName": getattr(member, 'displayName', None),
                            "avatar": getattr(member, 'avatar', None)
                        }
                        for member in convo.members
                    ],
                    "lastMessage": last_message,
                    "unreadCount": 0  # TODO: Implement unread count
                }
                conversations.append(conversation_data)
                logger.info(f"Successfully processed conversation {convo.id}")
                
            except Exception as e:
                logger.error(f"Failed to process conversation {convo.id}: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Continue processing other conversations
                continue
        
        logger.info(f"Successfully processed {len(conversations)} conversations")
        return conversations
        
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

@app.get("/conversations/{convo_id}/messages")
async def get_messages(convo_id: str, limit: int = 50):
    """Get messages for a specific conversation"""
    try:
        logger.info(f"Getting messages for conversation {convo_id} with limit {limit}")
        client, dm = await get_client()
        
        logger.info(f"Fetching messages from ATProtocol for conversation {convo_id}")
        messages_response = dm.get_messages(models.ChatBskyConvoGetMessages.Params(convo_id=convo_id, limit=limit))
        logger.info(f"Found {len(messages_response.messages)} messages")
        
        messages = []
        for i, msg in enumerate(messages_response.messages):
            try:
                logger.info(f"Processing message {i+1}/{len(messages_response.messages)}: {msg.id}")
                logger.info(f"Sender attributes: {dir(msg.sender)}")
                
                message_data = {
                    "id": msg.id,
                    "text": msg.text,
                    "author": {
                        "did": msg.sender.did,
                        "handle": msg.sender.did,
                        "displayName": getattr(msg.sender, 'displayName', None),
                        "avatar": getattr(msg.sender, 'avatar', None)
                    },
                    "createdAt": msg.sent_at,
                    "embed": getattr(msg, 'embed', None)
                }
                messages.append(message_data)
                logger.info(f"Successfully processed message {msg.id}")
                
            except Exception as e:
                logger.error(f"Failed to process message {msg.id}: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                continue
        
        logger.info(f"Successfully processed {len(messages)} messages for conversation {convo_id}")
        return messages
        
    except Exception as e:
        logger.error(f"Failed to get messages for conversation {convo_id}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")

@app.post("/send-message-with-image")
@app.post("/send-message-with-image")
async def send_message_with_image_debug(
    convo_id: str,
    text: str,
    image: Optional[UploadFile] = File(None)
):
    """Debug version with detailed logging"""
    try:
        logger.info(f"=== SEND MESSAGE DEBUG ===")
        logger.info(f"convo_id: {convo_id}")
        logger.info(f"text: {text}")
        logger.info(f"image: {image}")
        if image:
            logger.info(f"image.filename: {image.filename}")
            logger.info(f"image.content_type: {image.content_type}")
        logger.info(f"=== END DEBUG ===")
        return await send_message_with_image(convo_id, text, image)
    except Exception as e:
        logger.error(f"Debug endpoint error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
async def send_message_with_image_original(
    convo_id: str,
    text: str,
    image: Optional[UploadFile] = File(None)
):
    """Send a message with optional image attachment"""
    try:
        logger.info(f"Sending message to conversation {convo_id}: {text[:50]}...")
        client, dm = await get_client()
        
        message_data = {
            "text": text,
            "createdAt": client.get_current_time_iso()
        }
        
        if image:
            logger.info(f"Processing image upload: {image.filename}")
            # Upload the image blob
            image_data = await image.read()
            blob = upload_image(client, image_data)
            
            message_data["embed"] = {
                "$type": "app.bsky.embed.images",
                "images": [{
                    "image": blob,
                    "alt": "Image attachment"
                }]
            }
            logger.info("Successfully added image to message")
        
        logger.info("Sending message to ATProtocol...")
        message = dm.send_message(
            models.ChatBskyConvoSendMessage.Data(
                convo_id=convo_id,
                message=models.ChatBskyConvoDefs.MessageInput(**message_data)
            )
        )
        
        logger.info(f"Successfully sent message: {message.id}")
        return {"message_id": message.id, "success": True}
        
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@app.post("/create-conversation")
async def create_conversation(user_handle: str):
    """Create a new conversation with a user"""
    try:
        logger.info(f"Creating conversation with user: {user_handle}")
        client, dm = await get_client()
        
        # Resolve the user handle to DID
        logger.info(f"Resolving handle {user_handle} to DID...")
        id_resolver = IdResolver()
        user_did = id_resolver.handle.resolve(user_handle)
        logger.info(f"Resolved {user_handle} to {user_did}")
        
        # Get current user DID
        current_user_did = client.me.did
        logger.info(f"Current user DID: {current_user_did}")
        
        # Create or get conversation between the two users
        logger.info("Creating/getting conversation...")
        convo = dm.get_convo_for_members(
            models.ChatBskyConvoGetConvoForMembers.Params(
                members=[current_user_did, user_did]
            )
        ).convo
        
        logger.info(f"Successfully created/got conversation: {convo.id}")
        return {"convo_id": convo.id, "success": True}
        
    except Exception as e:
        logger.error(f"Failed to create conversation with {user_handle}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")

@app.get("/profile")
async def get_profile():
    """Get current user profile"""
    try:
        logger.info("Getting current user profile...")
        client, dm = await get_client()
        
        logger.info(f"Fetching profile for user: {USERNAME}")
        profile = client.app.bsky.actor.get_profile({"actor": USERNAME})
        
        profile_data = {
            "did": profile.did,
            "handle": profile.handle,
            "displayName": getattr(profile, 'displayName', None),
            "avatar": getattr(profile, 'avatar', None),
            "description": getattr(profile, 'description', None)
        }
        
        logger.info(f"Successfully retrieved profile: {profile.handle}")
        return profile_data
        
    except Exception as e:
        logger.error(f"Failed to get profile: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")

def main() -> None:
    """Main function for testing - can be run independently"""
    import asyncio
    
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
            print("Make sure the user handles are valid and both users exist on ATProtocol")
    
    asyncio.run(test_main())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.post("/send-message-with-image")
async def send_message_with_image_old(
    convo_id: str,
    text: str,
    image: Optional[UploadFile] = File(None)
):
    """Send a message with optional image attachment - with detailed logging"""
    try:
        logger.info(f"=== SEND MESSAGE REQUEST ===")
        logger.info(f"convo_id: {convo_id}")
        logger.info(f"text: '{text}'")
        logger.info(f"text length: {len(text)}")
        logger.info(f"image: {image}")
        if image:
            logger.info(f"image.filename: {image.filename}")
            logger.info(f"image.content_type: {image.content_type}")
            logger.info(f"image.size: {image.size}")
        logger.info(f"=== END REQUEST ===")
        
        logger.info(f"Sending message to conversation {convo_id}: {text[:50]}...")
        client, dm = await get_client()
        
        message_data = {
            "text": text,
            "createdAt": client.get_current_time_iso()
        }
        logger.info(f"Created message_data: {message_data}")
        
        if image:
            logger.info(f"Processing image upload: {image.filename}")
            # Upload the image blob
            image_data = await image.read()
            logger.info(f"Read {len(image_data)} bytes from image")
            blob = upload_image(client, image_data)
            logger.info(f"Uploaded blob: {blob}")
            
            message_data["embed"] = {
                "$type": "app.bsky.embed.images",
                "images": [{
                    "image": blob,
                    "alt": "Image attachment"
                }]
            }
            logger.info("Successfully added image to message")
        
        logger.info(f"Final message_data: {message_data}")
        logger.info("Sending message to ATProtocol...")
        
        message = dm.send_message(
            models.ChatBskyConvoSendMessage.Data(
                convo_id=convo_id,
                message=models.ChatBskyConvoDefs.MessageInput(**message_data)
            )
        )
        
        logger.info(f"Successfully sent message: {message.id}")
        return {"message_id": message.id, "success": True}
        
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

from fastapi import Form

@app.post("/send-message-with-image")
async def send_message_with_image(
    convo_id: str = Form(...),
    text: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    """Send a message with optional image attachment - with detailed logging"""
    try:
        logger.info(f"=== SEND MESSAGE REQUEST ===")
        logger.info(f"convo_id: {convo_id}")
        logger.info(f"text: '{text}'")
        logger.info(f"text length: {len(text)}")
        logger.info(f"image: {image}")
        if image:
            logger.info(f"image.filename: {image.filename}")
            logger.info(f"image.content_type: {image.content_type}")
            logger.info(f"image.size: {image.size}")
        logger.info(f"=== END REQUEST ===")
        
        logger.info(f"Sending message to conversation {convo_id}: {text[:50]}...")
        client, dm = await get_client()
        
        message_data = {
            "text": text,
            "createdAt": client.get_current_time_iso()
        }
        logger.info(f"Created message_data: {message_data}")
        
        if image:
            logger.info(f"Processing image upload: {image.filename}")
            # Upload the image blob
            image_data = await image.read()
            logger.info(f"Read {len(image_data)} bytes from image")
            blob = upload_image(client, image_data)
            logger.info(f"Uploaded blob: {blob}")
            
            message_data["embed"] = {
                "$type": "app.bsky.embed.images",
                "images": [{
                    "image": blob,
                    "alt": "Image attachment"
                }]
            }
            logger.info("Successfully added image to message")
        
        logger.info(f"Final message_data: {message_data}")
        logger.info("Sending message to ATProtocol...")
        
        message = dm.send_message(
            models.ChatBskyConvoSendMessage.Data(
                convo_id=convo_id,
                message=models.ChatBskyConvoDefs.MessageInput(**message_data)
            )
        )
        
        logger.info(f"Successfully sent message: {message.id}")
        return {"message_id": message.id, "success": True}
        
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@app.post("/test-form")
async def test_form(
    convo_id: str = Form(...),
    text: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    """Test endpoint to debug form data"""
    logger.info(f"=== TEST FORM REQUEST ===")
    logger.info(f"convo_id: {convo_id}")
    logger.info(f"text: {text}")
    logger.info(f"image: {image}")
    if image:
        logger.info(f"image.filename: {image.filename}")
        logger.info(f"image.content_type: {image.content_type}")
    logger.info(f"=== END TEST ===")
    return {"success": True, "convo_id": convo_id, "text": text}

@app.post("/test-json")
async def test_json(data: dict):
    """Test endpoint for JSON data"""
    logger.info(f"=== TEST JSON REQUEST ===")
    logger.info(f"data: {data}")
    logger.info(f"=== END TEST ===")
    return {"success": True, "received": data}

@app.api_route("/debug-request", methods=["GET", "POST", "PUT", "DELETE"])
async def debug_request(request: Request):
    """Debug any request"""
    logger.info(f"=== DEBUG REQUEST ===")
    logger.info(f"Method: {request.method}")
    logger.info(f"URL: {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    if request.method == "POST":
        try:
            # Try to get form data
            form_data = await request.form()
            logger.info(f"Form data: {dict(form_data)}")
        except Exception as e:
            logger.info(f"Form data error: {e}")
        
        try:
            # Try to get JSON data
            json_data = await request.json()
            logger.info(f"JSON data: {json_data}")
        except Exception as e:
            logger.info(f"JSON data error: {e}")
    
    logger.info(f"=== END DEBUG ===")
    return {"success": True, "method": request.method}
