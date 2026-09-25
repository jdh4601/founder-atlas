/**
 * Shown on a keyword page until a human has reviewed it
 * (`reviewed: false` in the page's frontmatter).
 */
export function ReviewBadge() {
  return (
    <span className="inline-flex items-center rounded-full border border-caution-line bg-caution-bg px-2.5 py-0.5 text-[12px] text-caution-ink">
      AI 정리 · 검수 전
    </span>
  );
}
