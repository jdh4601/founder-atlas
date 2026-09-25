import type { EvidenceEntry } from "@/lib/evidence";

interface InlineEvidenceLinkProps {
  readonly evidence: EvidenceEntry;
}

/**
 * A compact `{{advice:id}}` marker rendered inline inside prose — the claim
 * is already stated in the surrounding sentence, so this only surfaces the
 * source and the exact spot to check. Safe inside a `<p>` (inline, no
 * block-level children), unlike the standalone `EvidenceChip` card.
 */
export function InlineEvidenceLink({ evidence }: InlineEvidenceLinkProps) {
  return (
    <a
      href={evidence.url}
      target="_blank"
      rel="noopener noreferrer"
      title={evidence.sourceTitle}
      className="inline-flex items-center gap-1 rounded-full border border-line bg-surface px-2 py-0.5 text-[12.5px] text-focus no-underline hover:border-focus"
    >
      {evidence.label}
    </a>
  );
}
