# JP Product Trend Dashboard

상품기획자에게 주간 전달할 **일본 시장 경쟁사 신상품 + 랭킹 + SNS 화제도** 자동 수집/대시보드 프로젝트.
(이전 이름: Competitor New Products)

## 개요

- **데이터 소스**: Qoo10.jp 경쟁사 공식샵 페이지 (mobile)
- **수집 기준**: 최근 30일 등록 + Qoo10 NEW 태그가 붙은 상품
- **카테고리**: 스킨케어 / 색조 / ETC(뷰티 디바이스)
- **양식**: 구글 시트 "타사 신제품" 컬럼 구조 미러
  ([sheet](https://docs.google.com/spreadsheets/d/19bS3Kh9-jXc8aNtAtR8z87OYfIvYrKSoqlg0fJVBZ4k/edit?gid=1194793994))

## 폴더 구조

```
competitor_new_products/
├── crawler/
│   ├── _brands.py              # 경쟁사 브랜드 ↔ Qoo10 셀러 사전
│   ├── qoo10_new_products.py   # 신상품 크롤러 (메인)
│   └── enrich_details.py       # 상품 상세 페이지 보강 (출시일/색상수 등)
├── data/
│   ├── new_products.json       # 통합 출력 (대시보드가 읽음)
│   └── _snapshots/             # 일자별 누적 스냅샷
├── dashboard/                  # Cloudflare Pages 정적 사이트
│   ├── index.html
│   ├── data/new_products.json  # dashboard 빌드 시 data/ 에서 복사됨
│   ├── css/style.css
│   └── js/app.js
└── .github/workflows/crawl.yml # 매일 1회 cron
```

## 로컬 실행

```powershell
# 의존성 0 (Python 표준 라이브러리만)
python crawler/qoo10_new_products.py
python crawler/enrich_details.py    # 선택 — 상세 보강 (느림)
```

## Cloudflare Pages 배포

```bash
# 1) GitHub repo 생성 후 push
# 2) Cloudflare → Pages → Connect to Git
#    Production branch: main
#    Build command:    (없음 — 정적)
#    Build output dir: dashboard
# 3) data/new_products.json 을 dashboard/data/ 로 복사 (GitHub Action이 처리)
```

## 데이터 양식 (시트 미러)

| 컬럼 | 색조 | 스킨 | ETC |
|---|---|---|---|
| 브랜드 | ✓ | ✓ | ✓ |
| 제품명 | ✓ | ✓ | ✓ |
| 런칭일 | ✓ | ✓ | ✓ |
| 구분 (신제품/색상/리뉴얼) | ✓ | ✓ | ✓ |
| 이미지 | ✓ | ✓ | ✓ |
| 참고가/판매가 | ✓ | ✓ | ✓ |
| 타임세일가/최종할인가 | ✓ | – | – |
| 출시 홋수 (색상 수) | ✓ | – | – |
| 효과/메인 성분 | – | ✓ | – |
| 기능 (LED/RF/MFU 등) | – | – | ✓ |
| 링크/랭킹/주요 후기 | ✓ | ✓ | ✓ |

## 관련

- 메인 대시보드 (자사 4브랜드): [`ad_dash_v5.9.15`](../../../Downloads/ad_dash_v5.9.15) (별도 git)
- 중국 EC: [`ec_dashboard_china`](../ec_dashboard_china) (별도 git)
