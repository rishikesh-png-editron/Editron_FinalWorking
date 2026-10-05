// CapGen B-Roll — transcript-to-keyword windowing + shared types.
// Groups caption segments into ~N-second windows and extracts a short,
// stock-footage-friendly search query for each window.

import { BROLL_CONFIG } from "./broll-config";

export type BRollClip = {

  id: string; // unique per assignment (windowId + clipId)
  windowId: string;
  start: number; // seconds — when this b-roll should appear
  end: number; // seconds — when it should end
  source: "pexels" | "pixabay";
  previewUrl: string; // direct playable mp4 URL
  thumbnail: string;
  query: string;
  durationHint?: number; // source clip's own duration, for info only
};

export type BRollWindow = {
  id: string;
  start: number;
  end: number;
  text: string;
  query: string;
};

// Small stopword list — enough to filter filler words across English and
// Romanized Indian-language text (Hinglish/Telugish etc. lean heavily on
// English function words too).
const STOPWORDS = new Set([
  "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "be", "been",
  "being", "to", "of", "in", "on", "at", "for", "with", "by", "about", "as",
  "it", "its", "this", "that", "these", "those", "i", "you", "he", "she", "we",
  "they", "them", "his", "her", "our", "your", "their", "what", "which", "who",
  "so", "if", "then", "than", "just", "not", "no", "yes", "do", "does", "did",
  "have", "has", "had", "will", "would", "can", "could", "should", "may",
  "might", "must", "here", "there", "now", "very", "really", "like", "okay",
  "ok", "um", "uh", "hmm", "also", "into", "out", "up", "down", "over", "again",
  "one", "all", "some", "when", "how", "why", "because", "get", "got", "let",
  "us", "my", "me", "am", "im", "youre", "its",
]);

function cleanWord(w: string): string {
  return w.toLowerCase().replace(/[^a-z0-9']/g, "").replace(/'s$/, "");
}

/** Extract 1-3 content-bearing keywords from a chunk of caption text. */
export function extractKeywords(text: string, max = 3): string[] {
  const words = text.split(/\s+/).map(cleanWord).filter(Boolean);
  const seen = new Set<string>();
  const keywords: string[] = [];
  for (const w of words) {
    if (w.length < 4 || STOPWORDS.has(w) || seen.has(w)) continue;
    seen.add(w);
    keywords.push(w);
    if (keywords.length >= max) break;
  }
  // Fallback: if everything got filtered (e.g. very short segment), just use
  // the longest raw words so we still get a usable search query.
  if (keywords.length === 0) {
    return words
      .filter((w) => w.length >= 3)
      .sort((a, b) => b.length - a.length)
      .slice(0, max);
  }
  return keywords;
}

/**
 * Group caption segments into rolling time windows and produce
 * a search query per window. Skips windows with no usable keywords.
 * Dynamically calculates the number of windows based on video duration
 * to maintain a professional pacing ratio.
 */
export function buildBrollWindows(
  segments: CaptionSegment[],
  opts: { windowSeconds?: number; maxWindows?: number; videoDuration?: number } = {}
): BRollWindow[] {
    const windowSeconds = opts.windowSeconds ?? BROLL_CONFIG.DEFAULT_WINDOW_SIZE;

    // Calculate maxWindows dynamically based on video duration and target interval.
    // Fallback to 20 if duration is not provided.
    const maxWindows = opts.videoDuration
      ? Math.ceil(opts.videoDuration / BROLL_CONFIG.TARGET_BROLL_INTERVAL)
      : (opts.maxWindows ?? 20);

  if (!segments.length) return [];

  const totalEnd = segments[segments.length - 1].end;
  const windows: BRollWindow[] = [];

  let winStart = segments[0].start;
  while (winStart < totalEnd && windows.length < maxWindows) {
    const winEnd = Math.min(winStart + windowSeconds, totalEnd);
    const covered = segments.filter((s) => s.start < winEnd && s.end > winStart);
    if (covered.length) {
      const text = covered.map((s) => s.text).join(" ");
      const keywords = extractKeywords(text, 3);
      if (keywords.length) {
        windows.push({
          id: `w-${winStart.toFixed(1)}`,
          start: winStart,
          end: winEnd,
          text,
          query: keywords.join(" "),
        });
      }
    }
    winStart += BROLL_CONFIG.TARGET_BROLL_INTERVAL;
  }
  return windows;
}

/** Find the b-roll clip (if any) that should be showing at time t. */
export function activeBrollAt(brolls: BRollClip[], t: number): BRollClip | null {
  for (const b of brolls) {
    if (t >= b.start && t < b.end) return b;
  }
  return null;
}