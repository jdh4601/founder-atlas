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
  const fallbackSections = buildFallbackSections(source.titleKo, formatLabels[source.format]);
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
        {sourceAdvice.length === 0 && (
          <>
            <p className="mt-4 rounded-lg bg-caution-bg px-4 py-3 text-sm leading-6 text-caution-ink">
              아래 내용은 제목과 콘텐츠 형식을 바탕으로 만든 한국어 편집 초안입니다. 세부 사실은 원문에서 확인해 주세요.
            </p>
            <div className="mt-8 space-y-10">
              {fallbackSections.map((section, index) => (
                <section key={section.title}>
                  <p className="text-xs font-medium tracking-[0.14em] text-ink-muted">
                    {String(index + 1).padStart(2, "0")}
                  </p>
                  <h3 className="mt-2 text-[22px] font-semibold leading-snug text-ink">{section.title}</h3>
                  <p className="mt-3 text-[16px] leading-8 text-ink">{section.body}</p>
                </section>
              ))}
            </div>
          </>
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

function buildFallbackSections(title: string, format: string) {
  return [
    {
      title: "이 콘텐츠가 던지는 질문",
      body: `이 ${format}는 ‘${title}’라는 주제를 창업자의 관점에서 풀어봅니다. 아이디어를 멋지게 설명하는 데서 멈추지 않고, 실제 고객과 시장에서 어떤 선택을 해야 하는지 생각하게 만드는 내용으로 읽을 수 있습니다.`,
    },
    {
      title: "창업자라면 먼저 확인할 것",
      body: "가장 먼저 해결하려는 문제를 한 문장으로 줄여 보세요. 누가 이 문제를 반복해서 겪는지, 지금 어떤 대안을 쓰는지, 그 대안을 바꿀 만큼 불편한지 확인하면 막연한 관심을 실제 가설로 바꿀 수 있습니다.",
    },
    {
      title: "작게 실험하는 방법",
      body: "처음부터 큰 제품이나 복잡한 조직을 만들 필요는 없습니다. 짧은 인터뷰, 간단한 프로토타입, 작은 유료 테스트처럼 결과를 빨리 확인할 수 있는 방법을 고르고, 반응이 약하면 메시지·고객·제품 중 하나를 바꿔 다시 시도해 보세요.",
    },
    {
      title: "읽고 나서 실행할 체크리스트",
      body: "이번 주에 만날 고객을 정하고, 확인할 가설을 하나만 고르세요. 대화에서 들은 표현을 그대로 기록하고, 실제 사용이나 결제로 이어졌는지 측정하면 다음 의사결정이 훨씬 선명해집니다.",
    },
  ];
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
