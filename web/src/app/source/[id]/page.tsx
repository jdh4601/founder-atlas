/* eslint-disable @next/next/no-img-element */
import Link from "next/link";
import { notFound } from "next/navigation";
import ReactMarkdown from "react-markdown";
import { getContentDir } from "@/lib/contentDir";
import { getSourceById } from "@/lib/sources";
import { getSiteData } from "@/lib/site";
import { loadSourceArticle } from "@/lib/sourceArticles";
import { relatedSources } from "@/lib/relatedSources";

interface SourcePageProps {
  readonly params: Promise<{ id: string }>;
}

const originLabels = {
  "yc-youtube": "YC",
  lightcone: "Lightcone",
  "paul-graham": "Paul Graham",
  a16z: "a16z",
} as const;

const formatLabels = {
  video: "영상",
  essay: "에세이",
  blog: "아티클",
  podcast: "팟캐스트",
} as const;

export default async function SourcePage({ params }: SourcePageProps) {
  const { id } = await params;
  const { advice, sources } = getSiteData(getContentDir());
  const source = getSourceById(sources, id);
  if (!source) notFound();
  const article = loadSourceArticle(getContentDir(), id);

  const sourceAdvice = advice.filter((unit) => unit.source === source.id);
  const related = relatedSources(source, sources, advice);
  const images = [...new Set([source.thumbnail, ...source.images])].filter(
    (value): value is string => Boolean(value),
  );

  return (
    <article className="mx-auto max-w-[900px] px-5 pb-24 pt-10 sm:pt-14">
      <Link href="/explore" className="text-sm text-ink-muted hover:text-ink">
        ← 콘텐츠 탐색으로 돌아가기
      </Link>

      <header className="mt-7 border-b border-line pb-8">
        <p className="text-xs font-medium uppercase tracking-[0.16em] text-ink-muted">
          {originLabels[source.origin]} · {formatLabels[source.format]}
          {source.published ? ` · ${source.published}` : ""}
        </p>
        <h1 className="mt-3 max-w-[760px] text-[30px] font-semibold leading-tight text-ink sm:text-[42px]">
          {article?.titleKo ?? source.titleKo}
        </h1>
        {source.speakers.length > 0 && (
          <p className="mt-3 text-sm text-ink-muted">{source.speakers.join(", ")}</p>
        )}
      </header>

      {article?.tldr && (
        <div className="mt-8 max-w-[760px] rounded-xl border border-line bg-surface px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-ink-muted">한 줄 요약</p>
          <p className="mt-2 text-[17px] font-medium leading-7 text-ink">{article.tldr}</p>
        </div>
      )}

      {images.length > 0 && (
        <div className={`mt-8 grid gap-3 ${images.length > 1 ? "sm:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]" : ""}`}>
          <img
            src={images[0]}
            alt={article?.titleKo ?? source.titleKo}
            className="aspect-video w-full rounded-xl border border-line object-cover"
          />
          {images.length > 1 && (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-1">
              {images.slice(1).map((image) => (
                <img
                  key={image}
                  src={image}
                  alt=""
                  className="aspect-video w-full rounded-xl border border-line object-cover"
                />
              ))}
            </div>
          )}
        </div>
      )}

      {article ? (
        <section className="mt-10 max-w-[720px]">
          <p className="border-l-2 border-focus pl-5 text-[18px] leading-8 text-ink">
            {article.lead}
          </p>
          <div className="mt-10 space-y-5 text-[16px] leading-8 text-ink">
            <ReactMarkdown
              components={{
                h2: ({ children }) => <h2 className="mt-12 text-[24px] font-semibold leading-snug">{children}</h2>,
                p: ({ children }) => <p>{children}</p>,
              }}
            >
              {article.body}
            </ReactMarkdown>
          </div>
        </section>
      ) : (
      <section className="mt-10 max-w-[720px]">
        <h2 className="text-xl font-semibold text-ink">이 글에서 얻어갈 것</h2>
        {source.summary && (
          <p className="mt-4 text-[16px] leading-8 text-ink">{source.summary}</p>
        )}
        {sourceAdvice.length > 0 && (
          <>
            <ol className="mt-5 space-y-2 border-l-2 border-focus-soft pl-5 text-sm text-ink-muted">
              {sourceAdvice.slice(0, 8).map((unit) => (
                <li key={unit.id}>{unit.claim}</li>
              ))}
            </ol>
            <div className="mt-10 space-y-10">
              {sourceAdvice.map((unit, index) => (
                <div key={unit.id}>
                  <section>
                    <p className="text-xs font-medium tracking-[0.14em] text-ink-muted">
                      {String(index + 1).padStart(2, "0")}
                    </p>
                    <h3 className="mt-2 text-[22px] font-semibold leading-snug text-ink">
                      {unit.claim}
                    </h3>
                    <p className="mt-3 text-[16px] leading-8 text-ink">{unit.body}</p>
                    <a
                      href={adviceHref(source.url, source.youtubeId, unit.anchor)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-3 inline-block text-xs text-ink-muted underline underline-offset-4"
                    >
                      원문 근거 보기 →
                    </a>
                  </section>
                </div>
              ))}
            </div>
          </>
        )}
        {sourceAdvice.length === 0 && !source.summary && (
          <div className="mt-5 rounded-xl border border-line bg-surface p-5 text-[15px] leading-7 text-ink-muted">
            원문 transcript는 수집되어 있지만 아직 한국어 번역이 등록되지 않은 콘텐츠입니다. 번역이 완료되면 원문의 구조와 맥락을 유지한 본문으로 제공됩니다.
          </div>
        )}
      </section>
      )}

      <footer className="mt-12 border-t border-line pt-6">
        <a
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm font-medium text-focus underline underline-offset-4"
        >
          원문 열기 →
        </a>
      </footer>

      {related.length > 0 && (
        <section className="mt-12 border-t border-line pt-8" aria-labelledby="related-heading">
          <h2 id="related-heading" className="text-xl font-semibold text-ink">관련 콘텐츠</h2>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {related.map((item) => (
              <Link
                key={item.id}
                href={`/source/${item.id}`}
                className="rounded-xl border border-line bg-surface p-5 transition-colors hover:border-focus"
              >
                <p className="text-xs text-ink-muted">{item.origin} · {item.format}</p>
                <h3 className="mt-2 text-[17px] font-semibold leading-snug text-ink">{item.title}</h3>
                {item.tags.length > 0 && (
                  <p className="mt-3 text-xs text-ink-muted">{item.tags.slice(0, 3).map((tag) => `#${tag}`).join("  ")}</p>
                )}
              </Link>
            ))}
          </div>
        </section>
      )}
    </article>
  );
}

function adviceHref(
  sourceUrl: string,
  youtubeId: string | null,
  anchor: { kind: string; start?: number },
): string {
  if (anchor.kind === "timestamp" && youtubeId && anchor.start != null) {
    return `https://www.youtube.com/watch?v=${youtubeId}&t=${anchor.start}s`;
  }
  return sourceUrl;
}
