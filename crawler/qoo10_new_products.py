"""Qoo10.jp 경쟁사 신상품 크롤러 — 셀러 페이지 단위로 신상품 후보 추출.

설계:
  - 각 경쟁사 공식샵 모바일 페이지 1회 fetch
  - list_v2_item 컨테이너에서 상품 카드 정보 추출
  - 신상품 판정:
      A) 상품명에 NEW / 新発売 / 新着 / 【新】 / リニューアル 마커
      B) 셀러 페이지 "NEW商品" 섹션에 등장
      C) 등록일 ≤ 오늘 - 30일 (상세 페이지 fetch 필요 — 다음 단계 enrich_details.py)
  - 출력 양식은 구글 시트 "타사 신제품" 컬럼 미러 (스킨/색조/ETC)

출력:
  data/new_products.json
      {
        "last_updated": ISO,
        "windows": "추출일 기준 30일",
        "categories": {
          "skin":   [{ ...product fields...}, ...],
          "color":  [...],
          "device": [...]
        }
      }

  data/_snapshots/{YYYY-MM-DD}.json
      당일 raw 크롤 결과 (백업 / 후속 diff 분석용)
"""
from __future__ import annotations
import gzip
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path

try:
    from _brands import ALL_COMPETITORS, classify_shop_slug, get_all_shops_by_category
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _brands import ALL_COMPETITORS, classify_shop_slug, get_all_shops_by_category

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SNAPS = DATA / "_snapshots"
DATA.mkdir(parents=True, exist_ok=True)
SNAPS.mkdir(parents=True, exist_ok=True)

JST = timezone(timedelta(hours=9))
NOW_JST = datetime.now(JST)
TODAY = NOW_JST.date().isoformat()
CUTOFF_DATE = (NOW_JST.date() - timedelta(days=30)).isoformat()

UA_MOBILE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
             "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
HEADERS = {
    "User-Agent": UA_MOBILE,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://m.qoo10.jp/",
}

# ─── 정규식 ────────────────────────────────────────────────
GOODSCODE_RE   = re.compile(r'goodscode=(\d+)')
IMG_RE         = re.compile(r'gd_src="(https://gd\.image-qoo10\.jp/[^"]+)"')
TITLE_RE       = re.compile(r'class="list_v2_title[^"]*"[^>]*>\s*([^<]+)')
BRAND_RE       = re.compile(r'class="common_ui_seller_brand[^"]*"[^>]*>\s*([^<]+)')
SALE_PRICE_RE  = re.compile(r'class="price_final_value"[^>]*>\s*([\d,]+)')
ORIG_PRICE_RE  = re.compile(r'class="price_origin_value[^"]*"[^>]*>\s*([\d,]+)')
DISCOUNT_RE    = re.compile(r'class="price_final_deco"[^>]*>\s*(\d{1,2})%OFF')

# 신상품 마커 — 상품명에 포함되면 candidate
# 강한 마커 → 단독 만으로 신상품 인정
NEW_MARKERS = [
    "【NEW】", "【新】", "【新発売】", "【新商品】", "【新登場】",
    "NEW商品", "新発売", "新登場", "新着", "Newly",
    "リニューアル", "リニュアル", "新色", "新カラー",
    "新作", "新製品", "新ライン", "新シリーズ", "新パッケージ",
    "先行発売", "先行販売", "先行リリース", "Qoo10先行",
    "月新作", "月新商品",
]
# 약한 마커 (혼자서는 부족하지만 함께 있으면 가중)
WEAK_MARKERS = ["NEW", "★NEW", "✨NEW", "🆕"]

CATEGORY_LABEL = {
    "skin":   "스킨케어",
    "color":  "색조",
    "device": "ETC (디바이스)",
}


def fetch(url: str, retries: int = 3, delay: float = 2.0) -> str | None:
    last_err = None
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                html = raw.decode("utf-8", errors="replace")
                if "523 Error" in html and len(html) < 2000:
                    raise RuntimeError("523 error shell")
                return html
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(delay * attempt)
    print(f"  [FETCH-FAIL] {url}  -> {last_err}", flush=True)
    return None


def is_new_product(title: str) -> tuple[bool, list[str], str]:
    """상품명에서 신상품 마커 탐지.

    Returns: (is_new, matched_markers, classification)
        classification: '신제품' / '리뉴얼' / '신규 색상' / ''
    """
    if not title:
        return False, [], ""
    matched = []
    classification = ""
    # 강한 마커
    for m in NEW_MARKERS:
        if m in title:
            matched.append(m)
            if "リニューアル" in m or "リニュアル" in m or "リニュパッケ" in m or "新パッケージ" in m:
                if not classification:
                    classification = "리뉴얼"
            elif "新色" in m or "新カラー" in m:
                classification = "신규 색상"  # 강하게 덮어쓰기
            elif not classification:
                classification = "신제품"
    # 약한 마커는 강한 마커가 이미 있을 때만 보조
    if matched:
        for m in WEAK_MARKERS:
            if m in title and m not in matched:
                matched.append(m)
    else:
        # 약한 마커 단독 — 두 개 이상이거나 위치가 시작부에 있으면 candidate
        for m in WEAK_MARKERS:
            if m in title:
                matched.append(m)
                classification = "신제품"
                break
    return bool(matched), matched, classification


def parse_products(html: str, source_section: str) -> list[dict]:
    """list_v2_item 컨테이너 단위로 상품 카드 추출.

    source_section: 'top' (셀러 페이지 메인) / 'new_arrival' (新着順) 등 표시용.
    """
    parts = re.split(r'(?=<div\s+class="list_v2_item")', html)
    products: list[dict] = []
    seen: set[str] = set()
    for body in parts[1:]:
        next_idx = body.find('<div class="list_v2_item"', 1)
        if next_idx > 0:
            body = body[:next_idx]
        gc_m = GOODSCODE_RE.search(body)
        if not gc_m:
            continue
        gc = gc_m.group(1)
        if gc in seen:
            continue
        seen.add(gc)

        img_m  = IMG_RE.search(body)
        ttl_m  = TITLE_RE.search(body)
        brd_m  = BRAND_RE.search(body)
        prc_m  = SALE_PRICE_RE.search(body)
        org_m  = ORIG_PRICE_RE.search(body)
        dsc_m  = DISCOUNT_RE.search(body)

        title = unescape(ttl_m.group(1)).strip() if ttl_m else None
        is_new, markers, classification = is_new_product(title or "")

        products.append({
            "goodscode": gc,
            "url": f"https://m.qoo10.jp/gmkt.inc/Mobile/goods/goods.aspx?goodscode={gc}",
            "image": img_m.group(1) if img_m else None,
            "title": title,
            "brand_label_raw": unescape(brd_m.group(1)).strip() if brd_m else None,
            "sale_price": int(prc_m.group(1).replace(",", "")) if prc_m else None,
            "list_price": int(org_m.group(1).replace(",", "")) if org_m else None,
            "discount_pct": int(dsc_m.group(1)) if dsc_m else None,
            "is_new_candidate": is_new,
            "new_markers": markers,
            "classification": classification,
            "source_section": source_section,
        })
    return products


def validate_shop_match(products: list[dict], expected_keywords: list[str]) -> dict:
    """셀러 페이지가 진짜 그 브랜드의 shop인지 판정.

    Qoo10이 invalid slug 일 때 "유사 검색" 페이지를 200개 잡탕으로 응답하는 경우 차단.

    기준:
      - brand_label_raw 가 있는 상품 중, expected_keywords에 매치되는 비율 ≥ 30%
      - 또는 brand_label_raw 가 대다수 비어있고 (셀러 직접 등록 = 자사 브랜드 추정)
    """
    if not products:
        return {"valid": True, "reason": "empty page", "match_ratio": 0.0}
    with_brand = [p for p in products if p.get("brand_label_raw")]
    if not with_brand:
        return {"valid": True, "reason": "no brand labels (self-listed)", "match_ratio": None}

    kw_lc = [k.strip().lower() for k in expected_keywords if k.strip()]
    matched = 0
    for p in with_brand:
        b = (p.get("brand_label_raw") or "").lower()
        if any(k in b for k in kw_lc):
            matched += 1
    ratio = matched / len(with_brand) if with_brand else 0.0
    return {
        "valid": ratio >= 0.30,
        "reason": f"{matched}/{len(with_brand)} branded products match expected keywords",
        "match_ratio": round(ratio, 2),
    }


def crawl_shop(slug: str, kr_label: str, expected_keywords: list[str]) -> dict:
    """한 셀러 페이지에서 신상품 후보 추출.

    두 번 fetch:
      1) 기본 페이지 (인기 정렬 — NEW商品 섹션 포함될 수 있음)
      2) 新着順 정렬 페이지 (gd_no 정렬)

    expected_keywords: 브랜드 식별 키워드. shop slug가 invalid해서 검색결과로 리다이렉트된 경우 차단.
    """
    results: list[dict] = []
    page_sizes: list[int] = []

    # 1) 기본 페이지
    url_default = f"https://m.qoo10.jp/shop/{slug}"
    html = fetch(url_default)
    if html:
        page_sizes.append(len(html))
        results.extend(parse_products(html, source_section="top"))

    # 2) 신착순 페이지 — qoo10 mobile shop의 정렬 파라미터
    time.sleep(1.5)
    url_new = f"https://m.qoo10.jp/shop/{slug}?sortby=neworder"
    html2 = fetch(url_new)
    if html2:
        page_sizes.append(len(html2))
        new_products = parse_products(html2, source_section="new_arrival")
        existing_codes = {p["goodscode"] for p in results}
        for p in new_products:
            if p["goodscode"] in existing_codes:
                continue
            results.append(p)
            existing_codes.add(p["goodscode"])

    validity = validate_shop_match(results, expected_keywords)

    return {
        "slug": slug,
        "kr_label": kr_label,
        "fetched_at": NOW_JST.isoformat(timespec="seconds"),
        "products_total": len(results),
        "products": results if validity["valid"] else [],
        "validity": validity,
        "page_size_bytes": sum(page_sizes),
    }


def to_sheet_row(product: dict, brand_label: str, kr_label: str, category: str) -> dict:
    """크롤 결과 → 구글 시트 "타사 신제품" 컬럼 양식으로 변환."""
    sp = product.get("sale_price")
    lp = product.get("list_price")
    # 참고가 / 판매가 / 타임세일가 추정
    # - list_price 있으면 → 참고가
    # - sale_price → 판매가 (혹은 타임세일가)
    # - 할인율 추정
    참고가 = lp if lp else sp
    판매가 = sp
    타임세일가 = None
    if lp and sp and sp < lp:
        타임세일가 = sp
        판매가 = lp  # 정상 판매가는 list_price
    할인율 = product.get("discount_pct")

    base = {
        "카테고리": CATEGORY_LABEL.get(category, category),
        "브랜드": kr_label or brand_label,
        "브랜드_원문": brand_label,
        "런칭일": None,            # enrich_details.py에서 채움
        "구분": product.get("classification") or "신제품",
        "이미지": product.get("image"),
        "제품명": product.get("title"),
        "참고가": 참고가,
        "판매가": 판매가,
        "타임세일가": 타임세일가,
        "최종할인가": None,        # 쿠폰가 — enrich_details에서
        "할인율%": 할인율,
        "소구포인트": None,        # enrich_details에서 detail 페이지 description에서
        "출시_홋수": None,         # 색조 전용 — enrich_details에서 option 수
        "효과": None,              # 스킨 전용 — enrich_details에서
        "메인_성분": None,         # 스킨 전용
        "기능": None,              # 디바이스 전용
        "비고": None,
        "링크": product.get("url"),
        "랭킹": None,
        "주요_후기": None,         # enrich_details에서 top review
        "프로모션": None,
        "_meta": {
            "goodscode": product.get("goodscode"),
            "new_markers": product.get("new_markers"),
            "source_section": product.get("source_section"),
            "crawled_at": NOW_JST.isoformat(timespec="seconds"),
        },
    }
    return base


def main() -> int:
    print(f"[NEW-PRODUCTS] start  {NOW_JST.isoformat(timespec='seconds')}")
    print(f"[NEW-PRODUCTS] cutoff date (등록 30일 추정): {CUTOFF_DATE}")
    shops_by_cat = get_all_shops_by_category()
    total_shops = sum(len(v) for v in shops_by_cat.values())
    print(f"[NEW-PRODUCTS] target shops: skin={len(shops_by_cat['skin'])} "
          f"color={len(shops_by_cat['color'])} device={len(shops_by_cat['device'])} "
          f"(total {total_shops})")

    all_snapshots: dict = {"date": TODAY, "shops": []}
    output: dict = {
        "last_updated": NOW_JST.isoformat(timespec="seconds"),
        "window_days": 30,
        "cutoff_date": CUTOFF_DATE,
        "schema": {
            "columns": [
                "카테고리", "브랜드", "런칭일", "구분", "이미지", "제품명",
                "참고가", "판매가", "타임세일가", "최종할인가", "할인율%",
                "소구포인트", "출시_홋수", "효과", "메인_성분", "기능",
                "비고", "링크", "랭킹", "주요_후기", "프로모션",
            ],
            "note": "구글 시트 '타사 신제품' 컬럼 미러",
        },
        "categories": {"skin": [], "color": [], "device": []},
        "stats": {},
    }

    suspect_slugs: list[dict] = []  # slug 유효성 실패 셀러 추적
    for category, shops in shops_by_cat.items():
        print(f"\n[{category.upper()}] crawling {len(shops)} shops ...")
        for shop in shops:
            slug = shop["slug"]
            time.sleep(2.0)
            expected_kw = ALL_COMPETITORS.get(shop["key"], {}).get("keywords", [shop["label"]])
            r = crawl_shop(slug, shop["kr_label"], expected_kw)
            all_snapshots["shops"].append({
                "slug": slug,
                "category": category,
                "products": r["products"],
                "products_total": r["products_total"],
                "validity": r.get("validity"),
            })
            if not r.get("validity", {}).get("valid", True):
                suspect_slugs.append({
                    "slug": slug,
                    "kr_label": shop["kr_label"],
                    "category": category,
                    "reason": r["validity"]["reason"],
                    "match_ratio": r["validity"]["match_ratio"],
                    "raw_product_count": r["products_total"],
                })
                print(f"  [{shop['kr_label']:<14} ({slug:<18})] ✗ INVALID slug — {r['validity']['reason']}  ratio={r['validity']['match_ratio']}")
                continue
            new_only = [p for p in r["products"] if p["is_new_candidate"]]
            for p in new_only:
                row = to_sheet_row(p, shop["label"], shop["kr_label"], category)
                output["categories"][category].append(row)
            print(f"  [{shop['kr_label']:<14} ({slug:<18})] total={r['products_total']:>3}  new_candidates={len(new_only):>2}  match={r['validity']['match_ratio']}")

    output["suspect_slugs"] = suspect_slugs
    print(f"\n[NEW-PRODUCTS] suspect slugs to fix: {len(suspect_slugs)}")
    for s in suspect_slugs:
        print(f"  ✗ {s['kr_label']:<14} ({s['slug']:<18}) [{s['category']}]  ratio={s['match_ratio']}  raw={s['raw_product_count']}")

    # 통계
    for cat in ("skin", "color", "device"):
        rows = output["categories"][cat]
        output["stats"][cat] = {
            "new_products": len(rows),
            "brands_represented": len({r["브랜드"] for r in rows}),
        }
    output["stats"]["total_new_products"] = sum(
        v["new_products"] for v in output["stats"].values()
    )

    # 출력 저장
    out_path = DATA / "new_products.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[NEW-PRODUCTS] wrote {out_path}")

    snap_path = SNAPS / f"{TODAY}.json"
    snap_path.write_text(json.dumps(all_snapshots, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[NEW-PRODUCTS] wrote snapshot {snap_path}")

    print(f"\n[NEW-PRODUCTS] summary:")
    for cat in ("skin", "color", "device"):
        s = output["stats"][cat]
        print(f"  {cat:<7} {CATEGORY_LABEL[cat]:<15} new={s['new_products']:>3}  brands={s['brands_represented']:>2}")
    print(f"  TOTAL new candidates: {output['stats']['total_new_products']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
