# SevenSky Chat

A modern chat application built with ATProtocol, FastAPI, and React. This project allows ATProtocol users to send messages and images in real-time conversations.

## Features

- 💬 Real-time messaging between ATProtocol users
- 🖼️ Image sharing with automatic upload and display
- 🎨 Modern, responsive UI built with React and Tailwind CSS
- 🔐 Secure authentication using ATProtocol credentials
- 📱 Mobile-friendly design

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **ATProtocol** - Decentralized social protocol
- **uvicorn** - ASGI server
- **python-dotenv** - Environment variable management

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client
- **Lucide React** - Icon library

## Setup

### Prerequisites
- Python 3.12+
- Node.js 18+
- uv (Python package manager)
- ATProtocol account credentials

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd sevensky
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Create a `.env` file with your ATProtocol credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

4. Run the backend:
   ```bash
   uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

### Quick Start

Run both backend and frontend with a single command:
```bash
./run_dev.sh
```

This will start:
- Backend API on http://localhost:8000
- Frontend on http://localhost:5173

## API Endpoints

- `GET /` - Health check
- `GET /conversations` - List all conversations
- `GET /conversations/{convo_id}/messages` - Get messages for a conversation
- `POST /send-message-with-image` - Send a message with optional image
- `POST /create-conversation` - Create a new conversation
- `GET /profile` - Get current user profile

## Usage

1. **Set up your ATProtocol credentials** in the `.env` file
2. **Start the application** using `./run_dev.sh`
3. **Open your browser** to http://localhost:5173
4. **Start chatting** with other ATProtocol users!

## Development

### Backend Development
- The FastAPI backend includes automatic API documentation at http://localhost:8000/docs
- All ATProtocol interactions are handled through the `atproto` Python library
- Image uploads are processed through ATProtocol's blob system

### Frontend Development
- Built with React 18 and TypeScript for type safety
- Uses Tailwind CSS for styling
- Responsive design works on desktop and mobile
- Real-time message updates (polling-based)

## Project Structure

```
chat/
├── sevensky/                 # Backend (FastAPI)
│   ├── main.py              # Main application file
│   ├── pyproject.toml       # Python dependencies
│   └── .env.example         # Environment variables template
├── frontend/                # Frontend (React)
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API service layer
│   │   ├── types/           # TypeScript type definitions
│   │   └── App.tsx          # Main app component
│   └── package.json         # Node.js dependencies
└── run_dev.sh              # Development script
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built on the [ATProtocol](https://atproto.com/) by Bluesky
- Uses the [atproto Python library](https://github.com/MarshalX/atproto)
- Inspired by modern chat applications and decentralized social protocols
