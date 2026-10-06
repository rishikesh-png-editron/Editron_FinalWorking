# Editron — AI Caption Generator

A full-stack AI video caption generator with real word-level timestamps via faster-whisper. Upload any video/audio, generate word-timed captions in 82+ languages (including Telugu, Hindi, Tamil, and other Indic languages), add AI-suggested or custom B-roll, an AI-generated hook title, clean up the audio, style everything, and export as SRT/VTT/TXT or a burned-in video at up to 1080p.

![Editron](https://img.shields.io/badge/Next.js-16-black) ![TypeScript](https://img.shields.io/badge/TypeScript-5-blue) ![Tailwind](https://img.shields.io/badge/Tailwind-4-orange) ![Whisper](https://img.shields.io/badge/faster--whisper-1.2-purple)

---

## ✨ Features

### Transcription & Captions
- **Real word-level timestamps** via faster-whisper (not simulated)
- **82+ languages** — 14 Indian (Telugu, Hindi, Tamil, Kannada, Malayalam, Bengali, Punjabi, Gujarati, Marathi, Odia, Urdu + Roman variants) + 68 international
- **"small" multilingual model by default** — required for accurate Indic-language transcription
- **Caption Studio** — edit word timings, text, start/end times inline
- **Style Studio** — 15 Google Fonts, font size, text/highlight colors, position, templates, and more
- **Live Preview** — video player with synced caption overlay, auto-detects aspect ratio (9:16, 16:9, 1:1, etc.)
- **Words-per-caption control** — set 1–12 words per segment
- **Auto audio extraction** — ffmpeg extracts clean 16kHz mono WAV before transcription
- **VAD filter** — removes silence automatically
- **Uploads up to 150MB**

### Professional B-Roll System (`/api/broll`)
- **AI-Powered Discovery**: Analyzes transcript in rolling windows, extracting high-intent entities and bigrams (e.g., "thyroid problem" instead of just "problem") for precise stock footage matching.
- **Multi-Source Sourcing**: Queries **Pexels** and **Pixabay** in parallel, providing curated thumbnail suggestions.
- **Custom Asset Uploads**: Direct upload support for photos and videos, essential for Real Estate, Medical, and niche industries where generic stock footage isn't enough.
- **Manual Precision Search**: A dedicated search interface allowing users to manually enter keywords to find the perfect clip when AI suggestions need refinement.
- **Visual Timeline**: B-roll markers are clearly visible on the scrubber bar, ensuring a professional editing workflow.
- **Smart Rendering**: Cutaways are cover-cropped to fill the frame perfectly without stretching, regardless of the source aspect ratio.

### AI Hook Title (`/api/hook-title`)
- Toggle on to generate a short, punchy on-screen headline from the video's opening ~8 seconds.
- Multi-provider failover: **Groq → Gemini → Anthropic** $\rightarrow$ local heuristic fallback.
- Editable inline; renders as a white rounded callout in preview and export.

### Clean Audio
- Real signal processing during export: High-pass filter (removes rumble/hum) $\rightarrow$ Dynamics compressor (evens volume) $\rightarrow$ Makeup gain.
- Applies only at export time to ensure maximum quality without slowing down the live preview.

### Export
- `.SRT` (SubRip), `.VTT` (WebVTT), `.TXT` (plain transcript)
- **Video export** — burned-in captions, B-roll cutaways, and hook titles via Canvas + MediaRecorder.
- **Quality selector** — 480p / 720p / 1080p, matched to the source's detected aspect ratio.
- **Frame-Accurate Rendering**: Uses `requestVideoFrameCallback` to tie rendering to actual decoded frames, preventing freezes on high-resolution exports.

### Design
- Dark theme — black background, white text, orange (`#FF6B1A`) accents.

---

## 📋 Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| **Node.js** | 18+ | Next.js runtime |
| **npm** (or bun) | latest | Package manager |
| **Python** | 3.10+ | faster-whisper transcription engine |
| **ffmpeg** | any recent | Audio extraction from video files |

### Install ffmpeg
- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt install ffmpeg`
- **Windows**: `choco install ffmpeg` or download from https://ffmpeg.org/download.html

---

## 🚀 Quick Start

### 1. Install Node dependencies
```bash
npm install
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```
*Note: The first transcription will download the "small" model (~500MB) from Hugging Face.*

### 3. Set up environment
```bash
cp .env.example .env
```
Fill in `PYTHON_BIN` (absolute path to `python.exe` on Windows).

**Optional API Keys:**
- **B-Roll**: `PEXELS_API_KEY`, `PIXABAY_API_KEY`
- **AI Hooks**: `GROQ_API_KEY`, `GEMINI_API_KEY`, or `ANTHROPIC_API_KEY`

### 4. Run the dev server
```bash
npm run dev
```
Open **http://localhost:3000** in your browser.

---

## 🎬 How to Use

1. **Upload** a video or audio file (up to 150MB).
2. **Pick a language** (or let it auto-detect).
3. **Generate Captions** — faster-whisper processes the audio into timed segments.
4. **Edit captions** — adjust text and timings in the Caption Studio.
5. **Manage B-Roll** — use AI suggestions, manually search for clips, or upload your own professional assets.
6. **Style & AI Tools** — customize fonts/colors and enable the AI Hook Title or Clean Audio.
7. **Preview** — watch the final result with all overlays live.
8. **Export** — download subtitle files or a high-quality burned-in video.

---

## 🏗️ Project Structure

```
capgen/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── transcribe/route.ts       # Python whisper subprocess
│   │   │   ├── broll/route.ts            # Pexels + Pixabay search
│   │   │   ├── broll/upload/route.ts     # User asset upload handler
│   │   │   └── hook-title/route.ts       # LLM-based headline generator
│   │   ├── globals.css                   # Theme & palette
│   │   └── page.tsx                      # Single-page app entry
│   ├── components/
│   │   └── capgen/
│   │       ├── caption-studio.tsx        # Core editor (Upload, Style, Export)
│   │       ├── caption-preview.tsx        # Render engine for overlays
│   │       ├── broll-panel.tsx            # B-Roll management UI
│   │       └── segment-card.tsx           # Individual segment controls & upload
│   └── lib/
│       ├── captions.ts                   # SRT/VTT/TXT logic
│       ├── broll.ts                      # Keyword extraction & windowing
│       └── hook-title.ts                 # Local heuristic fallback
├── scripts/
│   └── transcribe.py                     # faster-whisper script
└── storage/
    └── user_uploads/                     # Directory for custom B-roll assets
```

---

## ⚙️ How it Works

### Transcription
`Browser` $\rightarrow$ `API` $\rightarrow$ `Python Subprocess` $\rightarrow$ `ffmpeg` $\rightarrow$ `faster-whisper` $\rightarrow$ `JSON` $\rightarrow$ `UI`.
A subprocess model is used for reliability, avoiding the need for a persistent background service.

### B-Roll Engine
`Transcript` $\rightarrow$ `Bigram/Entity Extraction` $\rightarrow$ `Parallel API Query` $\rightarrow$ `User Selection/Upload` $\rightarrow$ `Canvas Cover-Crop`.
The engine prioritizes multi-word phrases to ensure that a search for "thyroid problem" doesn't just return generic "problem" footage.

### AI Hook Title
`First 8s of Transcript` $\rightarrow$ `LLM (Groq/Gemini/Anthropic)` $\rightarrow$ `Punchy Headline`.
Falls back to a local keyword-based heuristic if no API keys are provided.

---

## 🎨 Branding
| Token | Value | Usage |
|-------|-------|-------|
| Background | `#0a0a0a` | Page background |
| Primary | `#FF6B1A` | Brand Orange — Action items |
| Border | `#2a2a2a` | UI Dividers |

---

## 🌍 Language Support
Uses **faster-whisper "small"** for native support of 96+ languages.
**Warning:** Do not use `tiny` for non-English languages as it will produce inaccurate results.

---

## 🐛 Troubleshooting
- **Python Dependency Error**: Run `pip install -r requirements.txt` and ensure `PYTHON_BIN` is an absolute path.
- **Indic Language Issues**: Ensure `WHISPER_MODEL_SIZE` is set to `small` or larger.
- **Export Freezes**: Reduce quality to 720p if your CPU is struggling with B-Roll and Clean Audio simultaneously.
- **B-Roll Keys**: Add keys to `.env` to enable AI suggestions.

---

## 🔧 Tech Stack
- **Framework:** Next.js 16 (App Router)
- **Language:** TypeScript 5
- **Styling:** Tailwind CSS 4
- **Transcription:** faster-whisper (Python)
- **B-Roll:** Pexels, Pixabay, and Local Storage
- **Video Export:** Canvas + MediaRecorder API (`requestVideoFrameCallback`)

---

## 📝 License
MIT — build whatever you want with this.
