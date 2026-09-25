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
          한국어 핵심 정리
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
        <h2 className="text-xl font-semibold text-ink">핵심만 읽기</h2>
        {source.summary && (
          <p className="mt-4 text-[16px] leading-8 text-ink">{source.summary}</p>
        )}
        {sourceAdvice.length === 0 && !source.summary && (
          <p className="mt-4 text-[16px] leading-8 text-ink-muted">
            아직 한국어 요약이 등록되지 않은 콘텐츠입니다. 원문에서 확인할 수 있습니다.
          </p>
        )}
        {sourceAdvice.length > 0 && (
          <div className="mt-6 space-y-5">
            {sourceAdvice.map((unit, index) => (
              <section key={unit.id} className="rounded-xl border border-line bg-surface p-5">
                <p className="text-xs font-medium text-ink-muted">0{index + 1}</p>
                <h3 className="mt-2 text-lg font-semibold leading-snug text-ink">{unit.claim}</h3>
                <p className="mt-3 text-[15px] leading-7 text-ink">{unit.body}</p>
              </section>
            ))}
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
