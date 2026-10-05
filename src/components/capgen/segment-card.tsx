"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { X, Play, RefreshCw, Check, Film } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatClock } from "@/lib/captions";
import { BROLL_CONFIG } from "@/lib/broll-config";
import { toast } from "@/hooks/use-toast";
import type { CaptionSegment } from "@/lib/captions";
import type { BRollClip } from "@/lib/broll";

type SegmentCardProps = {
  segment: CaptionSegment & { deleted?: boolean };
  index: number;
  isActive: boolean;
  onUpdate: (id: string, patch: Partial<CaptionSegment>) => void;
  onDelete: (id: string) => void;
  onSeek: (t: number) => void;
  broll: BRollClip | null;
  onAssignBroll: (segmentId: string, clip: any) => void;
  onRegenerateBroll: (clip: BRollClip) => void;
  onRemoveBroll: (windowId: string) => void;
  suggestions: any; // SuggestionResult from BRollPanel
};

export function SegmentCard({
  segment,
  index,
  isActive,
  onUpdate,
  onDelete,
  onSeek,
  broll,
  onAssignBroll,
  onRegenerateBroll,
  onRemoveBroll,
  suggestions,
}: SegmentCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [text, setText] = useState(segment.text);

  const handleCommit = () => {
    onUpdate(segment.id, { text });
    setIsEditing(false);
  };

  const s = suggestions?.[segment.id] || suggestions?.[`w-${segment.start.toFixed(1)}`];
  const currentClip = broll;
  const clipIndex = s?.currentIndex || 0;
  const availableClips = s?.clips || [];

  return (
    <div
      className={cn(
        "group relative flex flex-col gap-3 rounded-xl border p-4 transition-all",
        isActive
          ? "border-[#FF6B1A] bg-[#1a1a1a] shadow-[0_0_15px_rgba(255,107,26,0.1)]"
          : "border-[#2a2a2a] bg-[#161616] opacity-80 hover:opacity-100",
        segment.deleted && "border-red-900/50 bg-red-950/10 opacity-50"
      )}
    >
      {/* Top Row: Time, Status, and Delete */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="grid size-6 place-items-center rounded bg-secondary text-[10px] font-bold text-primary">
            {index + 1}
          </span>
          <span className="font-mono text-xs text-muted-foreground">
            {formatClock(segment.start)} → {formatClock(segment.end)}
          </span>
          {broll && (
            <span className="flex items-center gap-1 rounded bg-[#FF6B1A]/10 px-1.5 py-0.5 text-[10px] font-medium text-[#FF6B1A]">
              <Check className="size-3" /> B-Roll Applied
            </span>
          )}
        </div>

        <button
          onClick={() => onDelete(segment.id)}
          className={cn(
            "grid size-7 place-items-center rounded transition-colors",
            segment.deleted ? "bg-green-500/20 text-green-500" : "text-muted-foreground hover:bg-red-500/20 hover:text-red-500"
          )}
          title={segment.deleted ? "Restore segment" : "Remove bad take"}
        >
          {segment.deleted ? <Check className="size-3.5" /> : <X className="size-3.5" />}
        </button>
      </div>

      {/* Middle Row: Text Editing */}
      <div className="flex items-start gap-3">
        <button
          onClick={() => onSeek(segment.start)}
          className="grid size-8 shrink-0 place-items-center rounded-full bg-secondary text-muted-foreground hover:bg-primary hover:text-white transition-colors"
        >
          <Play className="size-3.5 ml-0.5" />
        </button>

        <div className="flex-1">
          {isEditing ? (
            <Input
              autoFocus
              value={text}
              onChange={(e) => setText(e.target.value)}
              onBlur={handleCommit}
              onKeyDown={(e) => e.key === "Enter" && handleCommit()}
              className="h-9 border-primary bg-card text-sm"
            />
          ) : (
            <div
              onClick={() => {
                setText(segment.text);
                setIsEditing(true);
              }}
              className="cursor-text rounded-md border border-transparent px-2 py-1.5 text-sm text-white hover:border-border hover:bg-background transition-colors"
            >
              {segment.text}
            </div>
          )}
        </div>
      </div>

      {/* Bottom Row: B-Roll Controls */}
      <div className="flex items-center justify-between pt-2 border-t border-border/50">
        <div className="flex items-center gap-3">
          {currentClip ? (
            <div className="flex items-center gap-2">
              <div className="relative h-10 w-16 overflow-hidden rounded border border-border">
                <img
                  src={currentClip.thumbnail}
                  alt="B-roll"
                  className="h-full w-full object-cover"
                />
                <span className="absolute bottom-0 right-0 bg-black/70 px-1 text-[8px] text-white">
                  {currentClip.source.charAt(0).toUpperCase()}
                </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onRemoveBroll(currentClip.windowId)}
                className="h-7 px-2 text-xs text-muted-foreground hover:text-red-400"
              >
                <X className="size-3 mr-1" /> Remove
              </Button>
            </div>
          ) : (
            <div className="text-xs text-muted-foreground italic">
              No B-roll assigned
            </div>
          )}
        </div>

        {currentClip && availableClips.length > 1 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onRegenerateBroll(currentClip)}
            className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-primary"
          >
            <RefreshCw className="size-3" />
            Regenerate
          </Button>
        )}
      </div>
    </div>
  );
}
