# Voice Agent - Modern Web UI

A sleek, modern Next.js web interface for the Voice Agent application. This is a complete replacement for the Gradio UI with a premium, futuristic design.

## 🎨 Features

- **Modern Dark Theme**: Sophisticated dark gradient interface with animated backgrounds
- **Real-time Audio Waveform Visualization**: Animated waveform while recording
- **Drag & Drop Audio Upload**: Upload audio files with intuitive drag-and-drop support
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Smooth Animations**: Subtle animations and transitions for professional feel
- **Processing Indicators**: Visual feedback during audio processing
- **Clean Result Display**: Easy-to-read results with icons and proper formatting

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm/pnpm/yarn
- Python Voice Agent backend running on `http://localhost:8000`

### Installation

```bash
# Navigate to the UI directory
cd ui

# Install dependencies
npm install
# or
pnpm install
# or
yarn install
```

### Development

```bash
# Make sure your Python backend is running on port 8000
# In another terminal, in the ui directory:

npm run dev
# or
pnpm dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build

```bash
npm run build
npm start
```

## 📁 Project Structure

```
ui/
├── app.tsx                 # Main application component
├── page.tsx               # Next.js page component
├── layout.tsx             # Root layout with metadata
├── globals.css            # Global styles and animations
├── tailwind.config.ts     # Tailwind CSS configuration
├── next.config.ts         # Next.js configuration
├── postcss.config.mjs     # PostCSS configuration
├── tsconfig.json          # TypeScript configuration
├── api/
│   └── process-audio/     # API route handler
│       └── route.ts       # Handles audio processing requests
└── components/            # Reusable React components
    ├── waveform.tsx       # Audio waveform visualization
    ├── audio-uploader.tsx # File upload handler
    ├── result-card.tsx    # Result display card
    └── processing-indicator.tsx  # Loading state
```

## 🔧 Configuration

### Environment Variables

Create a `.env.local` file if your backend is not on the default address:

```env
# API endpoint for the Python backend
API_BASE_URL=http://localhost:8000
```

### Customization

- **Colors**: Edit `tailwind.config.ts` to change the color scheme
- **Animations**: Modify `globals.css` for animation timing and effects
- **Layout**: Adjust component spacing in individual component files

## 🎯 How It Works

1. **User Records or Uploads Audio**
   - Click "Start Recording" to record from microphone
   - Or drag & drop / click to upload an audio file

2. **Audio Processing**
   - The UI sends the audio to the FastAPI backend (`/process-audio`)
   - Shows a processing indicator while waiting

3. **Results Display**
   - Transcription: What the AI heard
   - Intent: What action was detected
   - Action: What was executed
   - Result: The outcome of the action

## 🎤 Microphone Permissions

The app requires microphone access to record audio. Browsers will prompt for permission on first use.

## 📱 Mobile Support

The UI is fully responsive and works on mobile devices. Note that mobile browsers have specific requirements for microphone access (usually HTTPS in production).

## 🔗 Integration with Python Backend

The Next.js API route (`api/process-audio/route.ts`) acts as a proxy to the FastAPI backend. It:

1. Receives audio from the client
2. Forwards it to the Python backend
3. Returns the results to the client

Ensure your Python backend is running and accessible at the configured API_BASE_URL.

## 🛠️ Tech Stack

- **Framework**: Next.js 16 (React 19)
- **Styling**: Tailwind CSS 3
- **Language**: TypeScript
- **State Management**: React Hooks
- **Build Tool**: Next.js built-in (Turbopack)

## 📦 Dependencies

- `next`: Modern React framework
- `react`: UI library
- `tailwindcss`: Utility-first CSS framework
- `autoprefixer`: CSS vendor prefixer
- `postcss`: CSS processor

## 🚀 Deployment

### Vercel (Recommended)

1. Push your code to GitHub
2. Connect to Vercel
3. Set environment variable: `API_BASE_URL=<your-backend-url>`
4. Deploy!

### Docker

Create a Dockerfile in the ui directory:

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

Then build and run:

```bash
docker build -t voice-agent-ui .
docker run -p 3000:3000 -e API_BASE_URL=http://backend:8000 voice-agent-ui
```

## 📝 Notes

- The UI requires the Python FastAPI backend to be running
- Audio files are processed locally in your browser for recording
- All audio processing happens in the Python backend
- No audio data is stored by the UI

## 🤝 Contributing

Feel free to customize and extend this UI! Some ideas:

- Add dark/light theme toggle
- Implement command history
- Add audio playback controls
- Create preset command buttons
- Add voice activity detection visualizer

## 📄 License

Same license as the main Voice Agent project.
