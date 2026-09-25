---
slug: revenue-metrics
title: 매출 지표
category: pricing
summary: 매출 지표에 관한 원문 근거 조언 8개를 모았습니다.
reviewed: false
advice:
- yc-youtube-b2b-startup-metrics-startup-school--05
- a16z-bottom-up-pricing-packaging-let-the-user-journey--08
- a16z-customers-want-predictability-in-usage-based-pricing-heres--13
- a16z-retention-is-all-you-need--05
- lightcone-how-ai-is-changing-enterprise--16
- yc-youtube-turning-your-users-into-paying-customers--08
- yc-youtube-b2b-startup-metrics-startup-school--06
- yc-youtube-b2b-startup-metrics-startup-school--07
images:
- src: https://i.ytimg.com/vi/_mKeVGSqQac/hqdefault.jpg
  alt: B2B Startup Metrics | Startup School
  source: yc-youtube-b2b-startup-metrics-startup-school
- src: https://d1lamhf6l6yk6d.cloudfront.net/uploads/2021/03/a16z_Graphics_FinTech-D_FA-NEW-COLORS-1200x630-1.jpg
  alt: 'Bottom Up Pricing & Packaging: Let the User Journey Be Your Guide'
  source: a16z-bottom-up-pricing-packaging-let-the-user-journey
- src: https://d1lamhf6l6yk6d.cloudfront.net/uploads/2024/03/Predictability-UBP-FB-Yoast.jpg
  alt: Customers Want Predictability in Usage-based Pricing. Here’s How to Help Them
    Get It.
  source: a16z-customers-want-predictability-in-usage-based-pricing-heres
- src: https://d1lamhf6l6yk6d.cloudfront.net/uploads/2025/09/Retention-X-Yoast.jpg
  alt: Retention Is All You Need
  source: a16z-retention-is-all-you-need
- src: https://i.ytimg.com/vi/aIKfA3gIXwo/hqdefault.jpg
  alt: How AI Is Changing Enterprise
  source: lightcone-how-ai-is-changing-enterprise
- src: https://i.ytimg.com/vi/9pQJXR0Tcos/hqdefault.jpg
  alt: Turning Your Users Into Paying Customers
  source: yc-youtube-turning-your-users-into-paying-customers
updated_at: '2026-09-25'
---
- **핵심 지표는 4~5개만, 도구는 가장 단순한 걸로** — 지표를 30~50개씩 늘어놓지 말고 정확하게 추적할 핵심 지표 4~5개만 고르세요. 개수는 회사가 크면서 자연스럽게 늘어나요. 도구도 거창할 필요 없어요. SQL로 가입자 수를 세는 정도면 충분하고, PostHog처럼 SQL DB 위에 바로 얹어 쓰는 도구도 있어요. {{advice:yc-youtube-b2b-startup-metrics-startup-school--05}}

- **매출 중심은 셀프서브에서 엔터프라이즈로 옮겨간다** — 엔터프라이즈 GTM 엔진이 자리를 잡을수록 매출의 중심과 성장 속도는 하위 티어에서 엔터프라이즈 티어로 넘어가요. 어떤 웹 인프라 회사는 처음 2년 동안 셀프서브가 매출 대부분이었고 매달 7%씩 꾸준히 성장했는데, ARR $10M 즈음 엔터프라이즈가 셀프서브를 앞질렀고 $15M에서는 전체의 70%까지 올라갔습니다. 오픈소스 데이터 툴링 회사에서는 이 전환이 $2M ARR에서 일어났다고 해요. {{advice:a16z-bottom-up-pricing-packaging-let-the-user-journey--08}}

- **고객의 사용량 예측을 도우면 우리 매출 예측도 쉬워진다** — 고객이 사용량을 더 잘 예측하도록 도와주다 보면, 공급자인 우리도 매출을 더 정확하게 추적할 기반이 생겨요. 예측 가능한 매출은 회사의 계획과 실행, 결국 기업 가치까지 좌우하는 핵심이에요. 고객에게 예측 가능성을 주는 일이 결국 우리 회사를 위한 일이기도 한 거죠. {{advice:a16z-customers-want-predictability-in-usage-based-pricing-heres--13}}

- **리텐션 이후엔 사용량 기반 과금으로 확장 매출을 잡아라** — 6~12개월쯤 지나면 남은 고객들이 새로운 워크플로를 붙이거나 다른 제품을 써보면서 사용량을 늘리기 시작해요. 사용량 기반 과금이 있어야 이 확장분을 매출로 가져올 수 있습니다. ChatGPT처럼 제품이 좋아지면서 떠났던 사용자가 돌아오는 '웃는' 리텐션 곡선이 나타나기도 한대요. {{advice:a16z-retention-is-all-you-need--05}}

- **BPO를 대체하는 AI라면 연간 계약에 목매지 말고 사용량 과금을 받아들여라** — 예전 YC 조언은 '파일럿이나 종량제 고객은 진짜 고객이 아니니 연간 계약으로 매출을 묶어라'였어요. 그런데 지난 1년 동안 가장 잘된 회사들을 보면 BPO 같은 서비스를 대체하는 경우가 많았고, 고객이 오히려 사용량 기반 과금을 원했고 매출은 계속 올라갔대요. AI는 완전히 탄력적이라 사람 채용 때문에 장기 계약이 필요하지 않고, 리드 1만 건도 몇 달이 아니라 일주일 만에 뽑아낼 수 있기 때문이에요. {{advice:lightcone-how-ai-is-changing-enterprise--16}}

- **프리미엄 모델은 업그레이드 제약과 전환율 추적이 있어야 통한다** — Slack 같은 프리미엄 모델도 충분히 좋은 모델이지만 조건이 두 가지 있어요. 사용자가 넘고 싶어 하는 제약(시트 수, 메시지, 저장 공간 등)이 있어야 하고, 무료 사용자가 얼마 만에 유료로 넘어오는지 꾸준히 추적해야 합니다. '2주 안에 추가 시트가 필요해지면 업그레이드할 것'처럼 가설을 세우고 검증하는 건 괜찮아요. 반면 '언젠가는 돈 내겠죠'라는 태도로 기능만 계속 늘리는 건 위험 신호입니다. {{advice:yc-youtube-turning-your-users-into-paying-customers--08}}

- **지표 정의는 팀 전체가 합의해서 문서로 남기세요** — 활성 유저를 '매일 쓰는 사람'으로 볼지 '주 1회 쓰는 사람'으로 볼지는 생각보다 덜 중요해요. 중요한 건 모두가 같은 정의를 쓰는 거예요. 마케팅팀은 이번 달 리드를 2,500개 넘겼다고 하고 영업팀은 자격 미달 리드라고 맞서면 회의만 망가져요. 정의를 한곳에 적어두고 다 같이 따르세요. {{advice:yc-youtube-b2b-startup-metrics-startup-school--06}}

- **숫자가 안 좋다고 지표 정의를 바꾸지 마세요** — 런칭 후 WAU가 기대에 못 미치면 MAU로 슬쩍 바꾸고 싶어지죠. 하지만 그건 자기 자신을 속이는 거예요. 정의가 계속 같아야 실제로 나아지고 있는지 알 수 있어요. Monzo는 주 1회 이상 거래한 사람을 활성 유저로 봤는데 경쟁사들은 정의가 제각각이었어요. 그래서 회사끼리 비교하는 건 의미가 없고, 내부 일관성이 제일 중요해요. {{advice:yc-youtube-b2b-startup-metrics-startup-school--07}}
