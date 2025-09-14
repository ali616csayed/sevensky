import asyncio
import os

from atproto import Client, IdResolver, models
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.account import router as account_router
from routes.messaging import messaging_router

load_dotenv()

USERNAME = os.getenv("ATPROTO_USERNAME")
PASSWORD = os.getenv("ATPROTO_PASSWORD")

app = FastAPI(title="SevenSky Chat API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5175",
        "http://localhost:3000",
    ],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(account_router)
app.include_router(messaging_router)

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


@app.get("/")
async def root():
    return {"message": "SevenSky Chat API is running!"}


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
