const exactTitles: Record<string, string> = {
  "You are not a model. Don’t price per token.": "당신은 모델이 아닙니다: 토큰 단위로 가격을 매기지 마세요",
  "You are not a model. Don't price per token.": "당신은 모델이 아닙니다: 토큰 단위로 가격을 매기지 마세요",
  "Lighthouse or Landgrab? How to Pick Your AI Sales Strategy": "등대 전략인가, 선점 전략인가? AI 영업 전략 고르기",
  "Why Ambitious Startup Ideas Are Actually Easier To Sell": "대담한 스타트업 아이디어가 오히려 팔기 쉬운 이유",
  "How to Get Your First 10 Customers": "첫 고객 10명 확보하는 법",
};

const topicRules: readonly [RegExp, string][] = [
  [/pric|packag|overcharg|undercharg/i, "가격 책정"],
  [/fundrais|funding|investor|venture capital|vc|equity/i, "투자 유치"],
  [/customer|user|client|sales|sell|selling/i, "고객과 영업"],
  [/growth|distribution|retention|launch/i, "스타트업 성장"],
  [/product|pmf|build|software/i, "제품과 시장 적합성"],
  [/hiring|hire|founder|team|culture/i, "창업자와 팀"],
  [/ai|generative|model/i, "AI 스타트업"],
  [/idea|problem|market/i, "아이디어와 시장"],
];

/** Returns a Korean display title without changing the original source title. */
export function toKoreanSourceTitle(
  title: string,
  titleKo = "",
  id = "",
): string {
  if (titleKo.trim()) return titleKo.trim();
  const exact = exactTitles[title.trim()];
  if (exact) return exact;

  const topic = topicRules.find(([pattern]) => pattern.test(`${title} ${id}`))?.[1] ?? "창업 인사이트";
  return `${topic} 핵심 정리`;
}
