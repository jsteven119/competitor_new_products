# 배포 & 운영 가이드

## 1️⃣ GitHub Repo 만들기

```powershell
# Cloudflare Pages는 GitHub 연동이 필수
cd "C:\Users\user\claude code\competitor_new_products"

# GitHub CLI로 신규 비공개 repo 생성 + push
gh repo create competitor_new_products --private --source=. --remote=origin --push
```

또는 GitHub 웹에서 신규 repo 생성 후:
```powershell
git remote add origin https://github.com/<USER>/competitor_new_products.git
git branch -M main
git push -u origin main
```

## 2️⃣ Cloudflare Pages 연결

1. https://dash.cloudflare.com → Workers & Pages → **Create application** → **Pages** → **Connect to Git**
2. GitHub 권한 부여 → `competitor_new_products` repo 선택
3. 빌드 설정:
   - **Project name**: `competitor-new-products` (서브도메인이 됨)
   - **Production branch**: `main`
   - **Framework preset**: None
   - **Build command**: (비워둠 — 정적)
   - **Build output directory**: `dashboard`
4. **Save and Deploy** → 30초~1분 후 `https://competitor-new-products.pages.dev` 접속

## 3️⃣ GitHub Actions 일일 크롤 자동화

이미 `.github/workflows/crawl.yml` 작성 완료 (00:00 UTC = 09:00 JST).

GitHub repo Settings → **Actions** → **General**:
- Workflow permissions: **Read and write permissions** 체크
- (Cloudflare Pages는 main 브랜치 push 자동 감지 → 새 데이터로 자동 재배포)

## 4️⃣ 수동 크롤 (테스트용)

```powershell
cd "C:\Users\user\claude code\competitor_new_products"
python crawler/qoo10_new_products.py
cp data/new_products.json dashboard/data/new_products.json
# 로컬 미리보기
python -m http.server 8765 -d dashboard
# 브라우저: http://localhost:8765
```

## 5️⃣ 로컬에서 dashboard만 확인

CORS 없이 file:// 로 열 수도 있지만 fetch JSON이 막힐 수 있어 위의 http.server 권장.

---

# 🔧 후속 과제 — Suspect Slug 19개 재확인

크롤러가 자동 검출한 잘못된 셀러 slug. Qoo10 셀러센터에서 정식 slug 확보 후
`crawler/_brands.py`의 `shop_slugs` 필드 업데이트 필요.

## 5월 29일 기준 누락 브랜드

### 스킨케어 (4)
| 브랜드 | 현재 slug | 비고 |
|---|---|---|
| 에스트라 | `aestura` | Qoo10이 검색결과 페이지로 리다이렉트 — slug 변경됨 |
| 이즈엔트리 | `isntree` | 셀러 페이지에 다른 브랜드 상품 표시 |
| 믹순 | `mixsoon` | 미존재 — `mixsoon_jp` 또는 `mixsoon_official` 일 가능성 |
| 사무 (SAMU) | `samu` | 미존재 — `samujp` 또는 `samu_official` 시도 |

### 색조 (7)
| 브랜드 | 현재 slug | 비고 |
|---|---|---|
| 프위 (fwee) | `fwee` | 신상품 후보는 떴으나 매칭 0% — 키워드 보강 또는 slug 재확인 |
| 어바웃톤 | `abouttone` | 검색 페이지 리다이렉트 |
| 데이지크 | `dasique` | 매칭 0% |
| **페리페라** | `peripera` | 검색 페이지 리다이렉트 (시트 핵심 브랜드) |
| **힌스** | `hince` | 검색 페이지 리다이렉트 |
| 밀르페 | `millefee` | 검색 페이지 리다이렉트 |
| **투에이엔 (2aN)** | `2anjp`, `2an` | 시트 핵심 브랜드 — 둘 다 실패 |

### ETC / 디바이스 (8)
대부분 Qoo10 JP에 공식샵 미입점 또는 다른 slug 사용.
| 브랜드 | 현재 slug | 비고 |
|---|---|---|
| 메디큐브 AGE-R | `medicube` | shop은 맞지만 medicube 일반 스킨과 분리 어려움 — 상품명 필터 추가 필요 |
| 엠티지 (MTG) | `mtg-online` | Qoo10 미입점 추정 |
| 파나소닉 뷰티 | `panasonic-beauty` | Qoo10 미입점 추정 |
| 뉴아·덴바·트라이폴라·마그니톤·뷰티리프트 | (여러) | Qoo10보다 Rakuten/Amazon 주력 — 별도 채널 검토 |

## 권장 해결 절차

### A. 셀러센터에서 정식 slug 찾기
1. https://m.qoo10.jp 접속
2. 검색창에 브랜드명 입력 (예: "페리페라" / "PERIPERA" / "ペリペラ")
3. 검색 결과 상단의 셀러 페이지 링크 클릭 → URL의 `/shop/{여기}` 확인
4. `crawler/_brands.py`의 `shop_slugs` 배열에 추가

### B. fallback: 브랜드 키워드 검색 크롤로 전환
slug가 안 잡히면 셀러 페이지가 아닌 **검색 결과 페이지** (`m.qoo10.jp/gmkt.inc/Mobile/Search/Default.aspx?keyword=peripera`)에서
상위 N개 상품을 가져오는 방식으로 fallback 가능 — 단, 정확도 ↓ (타 브랜드 혼입 위험).

### C. 디바이스 카테고리는 Rakuten + Amazon 채널로 전환
Qoo10 JP는 K-뷰티 스킨/색조가 주력. 일본 뷰티 디바이스는 Rakuten/Amazon이 압도적 점유.
디바이스 트래커는 별도 크롤러로 분리 권장 (이번 프로젝트 v2).

---

# 📊 1차 인사이트 — 상품기획팀 전달용 (2026-05-29 데이터)

수집: 스킨 80건 · 색조 34건 · ETC 0건 (디바이스 slug 누락)

### 즉시 액션 후보

1. **롬앤 (rom&nd) — 5/25 신규 색상 대량 출시 (豆乳カラーコレクション)**
   - 라스팅 티트 전36색 / 립 오일 전12색 / 브로우카라 추가
   - 자사 컬러그램 립 시즌 SKU 확장 검토 — 동일 시즌 노출 충돌 가능
   - 신규 색상 출시 패턴: 베스트셀러 라인의 **컬렉션 단위** 확장 (단품 X)

2. **COSRX — 5월 신작 "ザ・ブルーペプチド バクチオール" 라인 5SKU 일제 출시 (¥3,040)**
   - 縦毛穴(세로 모공) / 키메 / 하리 / 에이징케어 클러스터
   - 모공·탄력 동시 소구 — 단일 효능 아닌 **클러스터링 소구** 트렌드
   - 자사 BOH/브링그린 신제품 효능 메시지 1-효능 단순화 vs 2-3효능 클러스터 결정

3. **메디힐 — 신상 18건 폭발 (스킨 최다)**
   - 30일간 신규 SKU 18건 → 라인업 공세 진행중
   - 자사 마스크/시트 카테고리와 충돌 — 점유율 사수 필요
   - 메디힐 카테고리·가격대·소구 키워드 별도 디테일 분석 권장

4. **바닐라코 — 색조 14건 신규** + **어뮤즈 8건** + **롬앤 7건**
   - 색조 신상품 한 달 30+건 → **Q2 메가와리 사전 라인업** 신호
   - 자사 웨이크메이크 Q2 메가와리 신청 상태 + 신상품 일정 즉시 점검

5. **티르티르 — 23개 SKU 중 12개가 신상품 (52%)**
   - 상품 회전이 극도로 빠른 셀러. 단일 신상이 아닌 **전 라인업 리프레시** 페이스
   - 출시 → 광고 → 메가와리 → 신상 교체 사이클 짧음
   - 자사도 시즌 한정/리뉴얼 사이클 단축 검토 가능성

### 가격대 분포

- 신상품 평균가: 대시보드에서 확인 (filtered 결과)
- 최저가 신상: ¥1,000 미만 = 롬앤 신규 색상 일부 (¥969~)
- 최고가 신상: ¥4,000 이상 프리미엄 SKU 다수

### 카테고리 편중

- 스킨 80 / 색조 34 = **스킨이 70%** — 봄~여름 시즌 스킨케어 라인업 강화 라운드
- 자사 BOH/브링그린 스킨 신제품 일정이 경쟁 적은 윈도우 잡았는지 확인 필요

---

# 🔁 운영 흐름 (정착 후)

```
매일 09:00 JST
  ↓ GitHub Actions
qoo10_new_products.py 실행
  ↓
data/new_products.json + _snapshots/{date}.json
  ↓
dashboard/data/ 복사 → main push
  ↓ Cloudflare Pages 자동 재배포
브라우저 (상품기획팀)
```

**주간 정례**: 매주 월요일 대시보드 캡쳐 + 인사이트 TSV 복사 → 시트에 누적.
