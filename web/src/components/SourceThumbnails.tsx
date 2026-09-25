import type { Source } from "@/lib/types";

interface SourceThumbnailsProps {
  readonly sources: readonly Source[];
}

/** Thumbnails for every source a keyword page draws on, linking out to each. */
export function SourceThumbnails({ sources }: SourceThumbnailsProps) {
  const withThumbnails = sources.filter((source) => source.thumbnail);
  if (withThumbnails.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-3">
      {withThumbnails.map((source) => (
        <a
          key={source.id}
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          className="group flex w-40 flex-col gap-1.5"
          title={source.titleKo}
        >
          {/* External, unoptimizable thumbnails from source origins. */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={source.thumbnail ?? undefined}
            alt={source.titleKo}
            className="aspect-video w-full rounded-md border border-line object-cover transition-opacity group-hover:opacity-85"
          />
          <span className="line-clamp-2 text-[12.5px] text-ink-muted">
            {source.titleKo}
          </span>
        </a>
      ))}
    </div>
  );
}
