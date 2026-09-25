---
slug: first-customers
title: 첫 고객 확보
category: sales
summary: 초기 고객, 특히 엔터프라이즈 고객을 어떻게 처음 확보할지에 대한 조언 모음
reviewed: true
advice:
  - lightcone-sample-enterprise-first-customers--01
  - lightcone-sample-enterprise-first-customers--02
  - paul-graham-sample-do-things-that-dont-scale--01
images:
  - src: https://example.com/sample/thumbs/lightcone-first-customers.jpg
    alt: "[샘플] 첫 엔터프라이즈 고객 좌담 썸네일"
    source: lightcone-sample-enterprise-first-customers
updated_at: 2026-09-25
---
[샘플 데이터] 이 페이지는 web/ 개발용 예시이며, 실제 검수된 조언이 아닙니다.

확장 가능한 채널을 먼저 찾으려는 시도는 초기에는 시간 낭비가 되기 쉽다. 첫 사용자는 결국 한 명씩 직접
설득해서 데려와야 한다 {{advice:paul-graham-sample-do-things-that-dont-scale--01}}.

이름값 있는 고객 1~2곳은 매출보다 신뢰 신호가 더 크다. 파격적인 조건을 줘서라도 먼저 확보하는 편이 낫다
{{advice:lightcone-sample-enterprise-first-customers--01}}.

첫 엔터프라이즈 가격은 협상의 시작가일 뿐, 최종가라고 생각하지 않아도 된다
{{advice:lightcone-sample-enterprise-first-customers--02}}.

첫 고객을 어떻게 확보하느냐는 이후 [[pricing-strategy]]와 [[unit-economics]]에도 그대로 이어진다.

```mermaid
flowchart TD
    A[타겟 로고 리스트업] --> B[직접 컨택 + 데모]
    B --> C{계약 성사?}
    C -- 예 --> D[시작가로 제시, 협상 여지 남기기]
    C -- 아니오 --> E[피드백 반영 후 재접근]
```
