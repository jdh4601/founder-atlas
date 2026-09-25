import Link from "next/link";
import { EvidenceChip } from "./EvidenceChip";

export interface AskMatchedPage {
  readonly slug: string;
  readonly title: string;
  readonly summary: string;
}

export interface AskEvidenceItem {
  readonly adviceId: string;
  readonly claim: string;
  readonly sourceTitle: string;
  readonly url: string;
  readonly label: string;
}

export interface AskResultData {
  readonly answered: boolean;
  readonly answer: string | null;
  readonly matchedPages: readonly AskMatchedPage[];
  readonly evidence: readonly AskEvidenceItem[];
}

interface AskResultsProps {
  readonly result: AskResultData;
}

/** Renders the outcome of a question: a short answer, matched pages, and evidence. */
export function AskResults({ result }: AskResultsProps) {
  if (!result.answered) {
    return (
      <div className="mt-8 rounded-lg border border-line bg-surface px-4 py-3.5 text-[14px] text-ink-muted">
        아직 정리되지 않은 주제예요. 질문을 저장해 두었어요.
      </div>
    );
  }

  return (
    <div className="mt-8 space-y-6">
      {result.answer && (
        <div className="rounded-lg border-l-[3px] border-focus bg-surface px-4 py-3.5">
          <p className="text-[15px] leading-relaxed text-ink">{result.answer}</p>
        </div>
      )}

      {result.matchedPages.length > 0 && (
        <div className="space-y-3">
          {result.matchedPages.map((page) => (
            <Link
              key={page.slug}
              href={`/k/${page.slug}`}
              className="block rounded-lg border border-line bg-surface px-4 py-3.5 transition-colors hover:border-focus"
            >
              <p className="text-[15.5px] font-semibold text-ink">{page.title}</p>
              <p className="mt-1 text-[13.5px] leading-relaxed text-ink-muted">
                {page.summary}
              </p>
            </Link>
          ))}
        </div>
      )}

      {result.evidence.length > 0 && (
        <div className="space-y-2.5">
          {result.evidence.map((evidence) => (
            <EvidenceChip key={evidence.adviceId} evidence={evidence} />
          ))}
        </div>
      )}
    </div>
  );
}
