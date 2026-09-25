import type { EvidenceEntry } from "@/lib/evidence";

interface EvidenceChipProps {
  readonly evidence: EvidenceEntry;
  /** Shown next to the source title when this evidence matches "내 상황". */
  readonly matchesProfile?: boolean;
}

/** One piece of evidence: a claim, its source, and a link to the exact spot. */
export function EvidenceChip({ evidence, matchesProfile }: EvidenceChipProps) {
  return (
    <div className="rounded-lg border border-line bg-surface px-3.5 py-3">
      <p className="text-[14px] leading-relaxed text-ink">{evidence.claim}</p>
      <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-[12.5px] text-ink-muted">
        <span>{evidence.sourceTitle}</span>
        <span aria-hidden>·</span>
        <a
          href={evidence.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-focus underline decoration-focus-soft underline-offset-2 hover:decoration-focus"
        >
          {evidence.label}
        </a>
        {matchesProfile && (
          <span className="rounded-full bg-focus-soft px-1.5 py-0.5 text-[11px] text-focus">
            내 상황
          </span>
        )}
      </div>
    </div>
  );
}
