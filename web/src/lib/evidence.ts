import type { Advice, Source } from "./types";

export interface EvidenceLink {
  readonly url: string;
  readonly label: string;
}

/**
 * Formats a second count as `m:ss` (or `h:mm:ss` past an hour), e.g.
 * `750` -> `"12:30"`. Used for the "12:30부터 보기" evidence link label.
 */
export function formatTimestamp(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = Math.floor(totalSeconds % 60);
  const paddedSeconds = String(seconds).padStart(2, "0");
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, "0")}:${paddedSeconds}`;
  }
  return `${minutes}:${paddedSeconds}`;
}

/**
 * Builds the evidence link the UI renders for one advice unit, per
 * `docs/content-schema.md`: a timestamp anchor points at the exact second
 * on YouTube; a paragraph anchor (or a timestamp advice missing a
 * `youtube_id`) falls back to the source's own URL.
 */
export function buildEvidenceLink(advice: Advice, source: Source): EvidenceLink {
  if (advice.anchor.kind === "timestamp") {
    const label = `${formatTimestamp(advice.anchor.start)}부터 보기`;
    if (source.youtubeId) {
      const url = `https://www.youtube.com/watch?v=${source.youtubeId}&t=${advice.anchor.start}s`;
      return { url, label };
    }
    return { url: source.url, label };
  }
  return { url: source.url, label: "원문에서 보기" };
}
