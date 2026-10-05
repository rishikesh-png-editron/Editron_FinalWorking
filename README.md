# CapGen — AI Caption Generator

A full-stack AI video caption generator with real word-level timestamps via faster-whisper. Upload any video/audio, generate word-timed captions in 82+ languages (including Telugu, Hindi, Tamil, and other Indic languages), add AI-suggested b-roll, an AI-generated hook title, clean up the audio, style everything, and export as SRT/VTT/TXT or a burned-in video at up to 1080p.

![CapGen](https://img.shields.io/badge/Next.js-16-black) ![TypeScript](https://img.shields.io/badge/TypeScript-5-blue) ![Tailwind](https://img.shields.io/badge/Tailwind-4-orange) ![Whisper](https://img.shields.io/badge/faster--whisper-1.2-purple)

---

## ✨ Features

### Transcription & Captions
- **Real word-level timestamps** via faster-whisper (not simulated)
- **82+ languages** — 14 Indian (Telugu, Hindi, Tamil, Kannada, Malayalam, Bengali, Punjabi, Gujarati, Marathi, Odia, Urdu + Roman variants) + 68 international
- **"small" multilingual model by default** — required for accurate Indic-language transcription (the lighter "tiny" model is effectively English-only and will silently mangle Telugu/Hindi/etc.)
- **Caption Studio** — edit word timings, text, start/end times inline
- **Style Studio** — 15 Google Fonts, font size, text/highlight colors, position (top/center/bottom), templates (active-word, boxed, outline, plain), bold/italic/uppercase, background opacity
- **Live Preview** — video player with synced caption overlay, auto-detects aspect ratio (9:16, 16:9, 1:1, etc.) from the source file
- **Words-per-caption control** — set 1–12 words per segment
- **Auto audio extraction** — ffmpeg extracts clean 16kHz mono WAV before transcription (handles MP4, MOV, MKV, WebM, etc.)
- **VAD filter** — removes silence automatically
- **Uploads up to 150MB**

### AI B-Roll (`/api/broll`)
- Analyzes the transcript in rolling ~6-second windows and extracts a search-friendly keyword phrase per window
- Queries **Pexels** and **Pixabay** (both free, real stock-video APIs) in parallel and shows thumbnail suggestions per window
- Click a thumbnail to assign it as a cutaway — shown live in the preview and burned into the exported video
- Cutaways always start from the clip's own beginning (not a random mid-clip frame) and are cover-cropped to fill the frame without stretching/warping, regardless of the source clip's own aspect ratio

### AI Hook Title (`/api/hook-title`)
- Toggle on to generate a short, punchy on-screen headline (à la Reels/Shorts) from the video's opening ~8 seconds
- Tries providers in order: **Groq → Gemini → Anthropic** (whichever has a key configured) → falls back to a local keyword+emoji heuristic if none are configured, so the feature always works with zero setup
- Editable inline; renders as a white rounded callout near the top, in both preview and export

### Clean Audio
- Real signal processing during export, not a cosmetic toggle: a high-pass filter (removes rumble/hum below ~90Hz) into a dynamics compressor (evens out volume swings) into a slight makeup gain
- Applies only at export time (no live preview) — toggling shows a confirmation toast; a failed audio graph falls back to your original unprocessed audio rather than exporting silently with no sound

### Export
- `.SRT` (SubRip subtitles)
- `.VTT` (WebVTT)
- `.TXT` (plain transcript)
- **Video export** — burned-in captions (+ b-roll cutaways + hook title, if enabled) via Canvas + MediaRecorder (WebM/MP4)
- **Quality selector** — 480p / 720p / 1080p, matched to the source's detected aspect ratio (portrait exports stay portrait, no pillarboxing)
- Uses `requestVideoFrameCallback` (with a `requestAnimationFrame` + stall-recovery fallback) to tie rendering to actual decoded video frames instead of the screen refresh rate — avoids the CPU overload that can otherwise cause an export to freeze on one frame partway through a longer/heavier clip

### Design
- Dark theme — black background, white text, orange (`#FF6B1A`) accents

---

## 📋 Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| **Node.js** | 18+ | Next.js runtime |
| **npm** (or bun) | latest | Package manager |
| **Python** | 3.10+ | faster-whisper transcription engine |
| **ffmpeg** | any recent | Audio extraction from video files |

### Install ffmpeg

**macOS (Homebrew):**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**Windows (Chocolatey):**
```powershell
choco install ffmpeg
```

Or download from https://ffmpeg.org/download.html

---

## 🚀 Quick Start

### 1. Install Node dependencies

```bash
cd capgen
npm install
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

> **Note:** The first time you run a transcription, faster-whisper will download the "small" model (~500MB) from Hugging Face. This takes 1–2 minutes. Subsequent runs use the cached model and start instantly.

### 3. Set up environment

```bash
cp .env.example .env
```

Fill in `PYTHON_BIN` (point it at the exact python3 that has `faster-whisper` installed — on Windows this must be a **full absolute path** to `python.exe`, not just `python`, since Node's file-existence check doesn't search `PATH`). Everything else has sensible defaults.

**Optional — enable B-Roll suggestions** (free, no credit card):
```
PEXELS_API_KEY=your_key       # https://www.pexels.com/api/
PIXABAY_API_KEY=your_key      # https://pixabay.com/api/docs/
```
Either one alone is enough; both is better coverage.

**Optional — enable AI-written Hook Titles** (free tier, no credit card — pick one):
```
GROQ_API_KEY=your_key         # https://console.groq.com (recommended: fast, generous free tier)
GEMINI_API_KEY=your_key       # https://aistudio.google.com
ANTHROPIC_API_KEY=your_key    # if you already have one
```
None of these are required — Hook Title works with a local heuristic if no key is set.

### 4. Run the dev server

```bash
npm run dev
```

Open **http://localhost:3000** in your browser.

---

## 🎬 How to Use

1. **Upload** a video or audio file (MP4, MOV, MKV, WebM, MP3, WAV, M4A — up to 150MB)
2. **Pick a language** from the dropdown (or let it auto-detect)
3. **Set words-per-caption** (1–12, default 6) — lower = more frequent caption pops
4. **Click "Generate Captions"** — takes a few seconds to a couple minutes depending on file length and language
5. **Edit captions** in the Captions tab — click any text to edit, adjust start/end times
6. **Add B-Roll** in the B-Roll tab — browse suggested clips per moment, click to assign
7. **Style captions** in the Style tab — font, colors, position, template
8. **Turn on AI Tools** (left panel) — AI Hook Title and/or Clean Audio
9. **Preview** in the Preview tab — play the video with captions, b-roll, and hook title all overlaid live
10. **Export**:
    - `.SRT` / `.VTT` / `.TXT` — subtitle files
    - **Export Video** — pick a quality (480p/720p/1080p), then export with everything burned in

---

## 🏗️ Project Structure

```
capgen/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── transcribe/route.ts       # POST: spawns Python whisper subprocess
│   │   │   ├── broll/route.ts            # POST: queries Pexels + Pixabay per transcript window
│   │   │   ├── hook-title/route.ts       # POST: Groq/Gemini/Anthropic → heuristic fallback
│   │   │   └── sample-transcript/route.ts
│   │   ├── globals.css                   # Dark theme + orange palette
│   │   ├── layout.tsx                    # Root layout, Google Fonts
│   │   └── page.tsx                       # Single-page app (all sections)
│   ├── components/
│   │   ├── ui/                            # shadcn/ui components (60+)
│   │   └── capgen/                        # CapGen section components
│   │       ├── navbar.tsx
│   │       ├── hero.tsx
│   │       ├── caption-studio.tsx        # The main working tool (upload, generate, edit, style, export)
│   │       ├── caption-preview.tsx        # Video preview + caption/b-roll/hook-title overlay
│   │       ├── style-panel.tsx            # Caption styling controls
│   │       ├── broll-panel.tsx            # B-Roll suggestion + assignment UI
│   │       ├── auto-trim.tsx
│   │       ├── stats.tsx
│   │       ├── templates.tsx
│   │       ├── pricing.tsx
│   │       ├── testimonials.tsx
│   │       ├── faq.tsx
│   │       ├── final-cta.tsx
│   │       ├── footer.tsx
│   │       └── logo.tsx
│   ├── hooks/
│   │   ├── use-toast.ts
│   │   └── use-mobile.ts
│   └── lib/
│       ├── captions.ts                   # SRT/VTT/TXT generators, timing helpers
│       ├── languages.ts                  # 82-language list + font catalog
│       ├── broll.ts                      # Transcript → keyword windows, active-broll lookup
│       ├── hook-title.ts                 # Local heuristic hook-title generator (no API key needed)
│       ├── db.ts                         # Prisma client (unused by the caption pipeline)
│       └── utils.ts
├── scripts/
│   └── transcribe.py                     # faster-whisper subprocess script
├── prisma/
│   └── schema.prisma
├── public/
│   └── logo.svg
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.ts
├── .env.example
└── README.md
```

---

## ⚙️ How Transcription Works

```
Browser (file upload)
    ↓ multipart/form-data
Next.js API /api/transcribe
    ↓ saves file to /tmp
    ↓ spawns Python subprocess
scripts/transcribe.py <file> <words_per_caption> <mode> <language>
    ↓ ffmpeg extracts audio to 16kHz mono WAV
    ↓ faster-whisper transcribes with word_timestamps=True + VAD filter
    ↓ groups words into caption segments
    ↓ outputs JSON to stdout
Next.js parses JSON → returns to browser
    ↓
Caption Studio renders editable segments
```

### Why a subprocess instead of a persistent service?

The Next.js API route spawns `python3 scripts/transcribe.py` per request. This is more reliable than a persistent Flask service because:
- No background process to manage/kill
- Clear lifecycle (process starts, runs, exits)
- Works in restricted sandbox environments
- The model loads in ~10s on first run, then the OS file cache makes subsequent loads fast (~2-3s)

---

## 🎞️ How B-Roll Works

```
Transcript (caption segments)
    ↓ src/lib/broll.ts: buildBrollWindows()
Rolling ~6s windows, each with a keyword search query
    ↓ POST /api/broll
Pexels Videos API + Pixabay Video API (parallel, per window)
    ↓ normalized clip list per window
BRollPanel — click a thumbnail to assign it
    ↓ stored as { windowId, start, end, previewUrl, ... }
Preview: <video> overlay swaps in during that time window (muted, looped)
Export: canvas cover-crops the clip's frames into that window, cut fresh
        from currentTime=0 each time (not wherever it happened to drift to)
```

Requires at least one of `PEXELS_API_KEY` / `PIXABAY_API_KEY` in `.env`. Without either, the B-Roll tab will show a clear error rather than fail silently.

---

## 🪝 How AI Hook Title Works

```
Caption segments (first ~8s = "the hook")
    ↓ POST /api/hook-title
Try Groq → try Gemini → try Anthropic (first configured key that succeeds wins)
    ↓ (none configured, or all fail)
Local heuristic: keyword-based emoji pick + trimmed opening line
    ↓
Returned title, editable, rendered as a white callout overlay
```

All three AI providers are optional. See [Quick Start → step 3](#3-set-up-environment) for free signup links.

---

## 🎨 Branding

| Token | Value | Usage |
|-------|-------|-------|
| Background | `#0a0a0a` | Page background (near-black) |
| Card | `#141414` | Cards, panels |
| Secondary | `#1a1a1a` | Muted surfaces |
| Accent | `#2a1a0d` | Dark orange tint (highlights) |
| Border | `#2a2a2a` | Dividers, borders |
| Primary | `#FF6B1A` | Orange — buttons, links, active states |
| Foreground | `#ffffff` | Headings |
| Muted text | `#a0a0a0` | Body text |

To change the brand color, edit the CSS variables in `src/app/globals.css` (`:root` block — change `--primary`, `--ring`, `--accent`).

---

## 🌍 Language Support

CapGen uses the **faster-whisper "small" model** by default, which supports 96+ languages, including Telugu, Hindi, Tamil, and other Indic languages in native script. When you pick a language from the dropdown, the API passes it as a hint to whisper:

| CapGen Code | Whisper Code | Language |
|-------------|--------------|----------|
| `en-US` | `en` | English |
| `te` / `telugish` | `te` | Telugu |
| `hi` / `hinglish` | `hi` | Hindi |
| `ta` / `tanglish` | `ta` | Tamil |
| `kn` / `kannadish` | `kn` | Kannada |
| ... | ... | + 77 more |

Roman variants (Hinglish, Telugish, etc.) use the same whisper code — the output will be in native script. For Roman output, use the **translate** mode (translates to English).

> ⚠️ **Do not switch `WHISPER_MODEL_SIZE` to `tiny`** if you need non-English languages — `tiny` is effectively English-only and will silently produce garbage or empty captions for Telugu/Hindi/etc. without an obvious error. Use `small` (default) or larger.

---

## 🐛 Troubleshooting

### "Transcription failed: Python dependency missing: faster_whisper"

Install the Python package:
```bash
pip install -r requirements.txt
```

If `python3` on your PATH doesn't have it, find the right Python and set `PYTHON_BIN` in `.env` to its **full path**:
```bash
python3 -c "import faster_whisper; print('OK')"
```
On Windows, `where python` gives you the full path — Node's check doesn't search PATH, so a bare `python` in `.env` will fail with "Python binary not found."

### Telugu/Hindi/etc. captions aren't generated (English works fine)

Check `.env` — if `WHISPER_MODEL_SIZE=tiny`, switch it to `small`. See the language support note above.

### "Transcription timed out"

The file is too long or the export/transcribe timeout is too low for your hardware. For longer files:
- Split the file into smaller clips
- Or reduce `WHISPER_BEAM_SIZE` to 1 in `.env` (faster but less accurate)

### MP4 transcription fails but MP3 works

Make sure `ffmpeg` is installed and on your PATH:
```bash
ffmpeg -version
```

### Vertical (9:16) video exports come out pillarboxed / captions too small

Make sure you're on the latest `caption-studio.tsx` — earlier versions re-read `video.videoWidth`/`videoHeight` at export time, which some phone-recorded vertical clips report inconsistently due to rotation metadata. The current version derives export canvas shape from the already-confirmed-correct `aspectRatio` state instead.

### B-roll footage looks stretched/warped after export

Fixed in the current version via cover-crop (`drawCover()`) instead of a naive full-canvas stretch — landscape stock footage is cropped, not squished, to fill a vertical canvas.

### Export freezes on one frame partway through

Fixed in the current version by switching the render loop to `requestVideoFrameCallback` (falls back to `requestAnimationFrame` + a stall-recovery watchdog on browsers without it). If you still see this on a low-powered machine with B-Roll + Clean Audio both enabled on a 1080p export, try 720p — it's a much lighter real-time CPU load.

### Clean Audio toggle seems to do nothing

Clean Audio has no live preview — it only applies when you click Export Video, and you should see a confirmation toast when you turn it on and when it applies during export. If you don't see the "Clean Audio applied" toast on export, check the browser console for an audio-graph error (it now falls back to unprocessed audio rather than exporting silently).

### Video export produces no audio

Browser security may block audio capture from `<video>` elements with cross-origin sources. The video export will still work (video + captions, just silent). For audio, use a same-origin video file.

### B-Roll tab shows "No b-roll API keys configured"

Add `PEXELS_API_KEY` and/or `PIXABAY_API_KEY` to `.env` — both are free, see [Quick Start](#3-set-up-environment).

### Hydration errors in console

Make sure you're not running browser extensions that inject HTML into the page. The framer-motion progress bars use `initial={false}` to avoid hydration mismatches.

---

## 📜 Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server on port 3000 |
| `npm run build` | Production build |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |

---

## 🔧 Tech Stack

- **Framework:** Next.js 16 (App Router, Turbopack)
- **Language:** TypeScript 5
- **Styling:** Tailwind CSS 4
- **UI:** shadcn/ui (New York) + Lucide icons
- **Animation:** Framer Motion
- **Database:** Prisma ORM + SQLite (present in the scaffold, not used by the caption pipeline)
- **Transcription:** faster-whisper (Python, CPU, int8)
- **Audio extraction:** ffmpeg
- **B-Roll sourcing:** Pexels Videos API, Pixabay Video API
- **AI Hook Title:** Groq / Google Gemini / Anthropic (first configured, with local heuristic fallback)
- **Audio cleanup:** Web Audio API (BiquadFilter highpass + DynamicsCompressorNode)
- **Video export:** Canvas + MediaRecorder API, driven by `requestVideoFrameCallback`

---

## 📝 License

MIT — build whatever you want with this.

---

## 🙏 Credits

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — the transcription engine
- [Pexels](https://www.pexels.com/) & [Pixabay](https://pixabay.com/) — free stock video for B-Roll
- [shadcn/ui](https://ui.shadcn.com/) — the component library
- [Next.js](https://nextjs.org/) — the framework
- Inspired by [FluxoCut](https://fluxocut.com/) — built with white & orange branding as CapGen
