/* eslint-disable @next/next/no-img-element */
import Link from "next/link";
import { notFound } from "next/navigation";
import { getContentDir } from "@/lib/contentDir";
import { getSourceById } from "@/lib/sources";
import { getSiteData } from "@/lib/site";

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

  const sourceAdvice = advice.filter((unit) => unit.source === source.id);
  const images = [source.thumbnail, ...source.images].filter(
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
          {source.titleKo}
        </h1>
        {source.speakers.length > 0 && (
          <p className="mt-3 text-sm text-ink-muted">{source.speakers.join(", ")}</p>
        )}
        <p className="mt-5 inline-flex rounded-full bg-focus-soft px-3 py-1.5 text-sm text-ink-muted">
          한국어 블로그 정리
        </p>
      </header>

      {images.length > 0 && (
        <div className="mt-8 grid gap-3 sm:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
          <img
            src={images[0]}
            alt={source.titleKo}
            className="aspect-video w-full rounded-xl border border-line object-cover"
          />
          {images.length > 1 && (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-1">
              {images.slice(1, 3).map((image) => (
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
                  {index > 0 && index % 2 === 0 && images.length > 0 && (
                    <figure className="mb-8">
                      <img
                        src={images[(index / 2) % images.length]}
                        alt=""
                        className="aspect-[16/7] w-full rounded-xl border border-line object-cover"
                      />
                      <figcaption className="mt-2 text-xs text-ink-muted">
                        {formatLabels[source.format]}에서 이어지는 장면과 자료
                      </figcaption>
                    </figure>
                  )}
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
            이 콘텐츠는 원문과 이미지 메타데이터만 수집되어 있어, 한국어 본문을 만들 근거 조언이 아직 없습니다. 한국어 가공이 완료되면 이 자리에서 블로그 형식으로 제공됩니다.
          </div>
        )}
      </section>

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
