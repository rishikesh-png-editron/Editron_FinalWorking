# 🎬 CapGen B-Roll Engine: Complete Technical Documentation

## 1. Overview
The CapGen B-Roll Engine is a high-performance, automated visual overlay system designed for short-form AI video editing (TikTok, Reels, Shorts). Its primary purpose is to analyze a video transcript, identify high-value keywords, and automatically overlay relevant stock footage to maintain high viewer retention through "pattern interrupts."

---

## 2. How the Engine Works (The Pipeline)

The engine operates through a multi-stage pipeline that connects the frontend UI to the server-side rendering process.

### Stage A: Transcript Windowing & Keyword Extraction
The engine doesn't look at the whole video at once. It uses a **Dynamic Pacing Window** approach:
1. **Windowing**: The transcript is split into small time windows (default: 6 seconds).
2. **Dynamic Clip Density**: Instead of a fixed number of clips, the engine calculates the required number of B-rolls based on the total video duration and a `TARGET_BROLL_INTERVAL` (e.g., 1 clip every 10 seconds). This ensures a consistent "pattern interrupt" frequency regardless of video length.
3. **Extraction**: A custom NLP logic filters out "stopwords" (the, a, is, etc.) and extracts 1-3 content-bearing keywords from each window.
4. **Query Generation**: These keywords are used as the search terms for stock footage APIs.

### Stage B: The Intelligence Layer (Smart Fetching)
Instead of a simple search, the engine uses a **Bulk-Fetch & Cache** strategy:
1. **Multi-Source Fetching**: The engine queries both **Pexels** and **Pixabay** APIs simultaneously to maximize the variety of clips.
2. **Bulk Retrieval**: It fetches up to **40 clips per keyword** (20 from each source).
3. **Local Caching**: To avoid API rate-limit bans and ensure instant loading, results are stored in a local JSON cache (`storage/broll_cache/`) with a 7-day expiration (TTL).

### Stage C: User Selection & Carousel
Users can refine the AI's suggestions through a professional gallery interface:
- **Circular Carousel**: If a user dislikes a clip, they can "Regenerate." The engine cycles through the cached bulk list (`index + 1 % total_clips`), ensuring they see every available option without repeated API calls.
- **Manual Override**: Users can manually select any clip from the gallery or remove a B-roll entirely.

### Stage D: Server-Side Rendering (The Final Cut)
The final video is rendered using **FFmpeg** on the server:
1. **Resolution Detection**: The engine uses `ffprobe` to detect the source video's dimensions.
2. **Fill & Cover Logic**: B-roll clips are dynamically scaled and cropped (`scale=force_original_aspect_ratio=increase,crop`) to perfectly fill the screen regardless of original aspect ratio.
3. **Opaque Overlay**: Clips are overlaid using the `overlay` filter with precise `between(t,start,end)` timestamps.
4. **Audio Preservation**: The original audio stream is mapped directly (`-c:a copy`), ensuring zero desync.

---

## 3. Key Features

| Feature | Description | Benefit |
| :--- | :--- | :--- |
| **4s Pacing Cap** | Every B-roll clip is capped at a maximum of 4 seconds. | Prevents viewer boredom; maintains high retention. |
| **Semantic Gallery** | A horizontal scrollable list of 40+ clips per keyword. | Gives users total control over the visual vibe. |
| **Circular Looping** | "Regenerate" cycles through available clips infinitely. | Instant feedback without loading spinners. |
| **Resolution Independence** | Dynamic cropping for 9:16, 16:9, or 1:1 videos. | Professional look across all social platforms. |
| **B-Roll Cache** | JSON-based local storage of API responses. | Prevents API bans; makes the tool feel "instant." |

---

## 4. Updates & Improvements Made

As part of the senior engineering overhaul, the following critical updates were implemented:

### 🛠 Performance & Stability
- **Moved from keyword-only to Bulk Fetching**: Increased results from 2 clips to 40 per keyword.
- **Implemented Local Caching**: Reduced API dependency and eliminated rate-limit risks.
- **Fixed the "Regenerate Loop"**: Replaced repeated API calls with a local index-based carousel.

### 🎨 Visual & UX Enhancements
- **Standardized Pacing**: Introduced the `BROLL_CONFIG` system to strictly enforce the 4-second "sweet spot" for cutaways.
- **Gallery UI**: replaced the single-thumbnail view with a professional horizontal scrollable gallery.
- **Surgical UI Labels**: Updated timestamps to show the actual clip duration rather than the window duration.

### ⚙️ Backend Optimization
- **Surgical FFmpeg Pipeline**: Added `trim` and `setpts` filters to the rendering chain to ensure millisecond-perfect timing.
- **Memory Efficiency**: Optimized the render pipeline to avoid loading unnecessary assets into RAM.

---

## 5. Developer Quick-Start
To test the engine:
1. Ensure `PEXELS_API_KEY` and `PIXABAY_API_KEY` are in `.env`.
2. Run the `whisper-service` for transcription.
3. Execute the pipeline: `python render_pipeline.py <video_path> <style_id>`.
4. Check the output at `output_final.mp4`.
