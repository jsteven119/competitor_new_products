"""Qoo10 검색에서 브랜드별 정식 셀러 slug 자동 발견.

원리:
  1) m.qoo10.jp/gmkt.inc/Mobile/Search/Default.aspx?keyword=BRAND 검색
  2) 결과 페이지의 모든 list_v2_item 카드에서 sellerportal 또는 shop 링크 추출
  3) 가장 많이 등장한 셀러 slug 후보 = 그 브랜드의 공식샵 추정
  4) 추가 검증: 해당 슬러그 페이지 직접 fetch 후 브랜드 키워드 매칭 검증

출력: data/_slug_discovery.json
    { "<key>": {"current": "...", "discovered": [{"slug": "...", "count": N, "verified": bool}, ...]} }
"""
from __future__ import annotations
import gzip
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _brands import ALL_COMPETITORS  # noqa: E402
from qoo10_new_products import fetch, parse_products, validate_shop_match  # noqa: E402

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

JST = timezone(timedelta(hours=9))

# 검색 결과 페이지에서 셀러 링크 추출
SHOP_LINK_RE = re.compile(r'/shop/([A-Za-z0-9_\-]+)')

# 19개 suspect slugs — 검색 키워드 후보 (브랜드명을 영문+カナ로 다양하게)
SUSPECT_BRANDS = {
    # 스킨
    "aestura":    ["AESTURA", "エストラ", "aestura"],
    "isntree":    ["isntree", "イズントゥリー", "イズエントリ"],
    "mixsoon":    ["mixsoon", "ミクスーン"],
    "samu":       ["SAMU", "サミュ", "samu"],
    # 색조
    "fwee":       ["fwee", "プゥイ", "プイ"],
    "abouttone":  ["About Tone", "アバウトトーン"],
    "dasique":    ["DASIQUE", "デイジーク", "dasique"],
    "peripera":   ["PERIPERA", "ペリペラ", "peripera"],
    "hince":      ["hince", "ヒンス"],
    "millefee":   ["MilleFée", "ミルフィー", "millefee"],
    "2aN":        ["2aN", "ツーエーエヌ", "2an"],
    # 0건이지만 정식 slug 일 수도 있는 브랜드 (search로 한번 더 확인)
    "abib":       ["ABIB", "アビブ", "abib"],
    "tocobo":     ["TOCOBO", "トコボ", "tocobo"],
    "pyunkangyul":["PYUNKANG YUL", "ピョンガンユル", "pyunkang"],
    "haruharu":   ["HARUHARU", "ハルハル", "haruharu"],
    "roundlab":   ["Round Lab", "ラウンドラボ", "roundlab"],
    "ongredients":["ONGREDIENTS", "オングレディエンツ"],
    "beautyofjoseon":["Beauty of Joseon", "ビューティーオブジョソン"],
    "drjart":     ["Dr.Jart+", "ドクタージャルト"],
    "laka":       ["LAKA", "ラカ"],
    "23yearsold": ["23 years old", "23イヤーズオールド"],
    "clio":       ["CLIO", "クリオ"],
    "lilybyred":  ["lilybyred", "リリーバイレッド"],
    "bbia":       ["BBIA", "ピアジャパン", "bbia"],
    "olens":      ["OLENS", "オーレンズ"],
    "etude":      ["ETUDE HOUSE", "エチュードハウス", "etude"],
    "3ce":        ["3CE", "スリーシーイー"],
}

# 잡셀러 / 종합셀러 차단 (브랜드와 무관한 종합 셀러 slug)
GENERIC_BLACKLIST = {
    "rakuten24", "amzn", "auc-sasaki", "rakuten",
    "qoo10_master", "qoo10_event", "qoo10_japan",
    # 종합 K-뷰티 셀러 (특정 브랜드 단독 셀러 아님)
    "ksister", "yesstyle", "stylekorean", "stylekoreanjp",
    "qoo10global", "officialjp",
}


def search_brand(keyword: str) -> tuple[str | None, dict]:
    """검색 결과 페이지에서 가장 빈도 높은 셀러 slug 추출.

    Returns:
        (best_slug, debug_dict)
    """
    enc = urllib.parse.quote(keyword)
    url = f"https://m.qoo10.jp/gmkt.inc/Mobile/Search/Default.aspx?keyword={enc}"
    html = fetch(url)
    if not html:
        return None, {"error": "fetch_failed"}

    # 검색 페이지 카드들에서 /shop/X 추출
    candidates = SHOP_LINK_RE.findall(html)
    if not candidates:
        return None, {"error": "no_shop_links", "html_size": len(html)}

    # 카운트
    cnt = Counter(c for c in candidates if c not in GENERIC_BLACKLIST)
    if not cnt:
        return None, {"error": "all_blacklisted", "raw_count": len(candidates)}

    top3 = cnt.most_common(3)
    return top3[0][0], {"top3": top3, "total_hits": len(candidates)}


def verify_shop(slug: str, brand_meta: dict) -> dict:
    """발견된 slug가 실제 그 브랜드 셀러인지 검증."""
    html = fetch(f"https://m.qoo10.jp/shop/{slug}")
    if not html:
        return {"valid": False, "reason": "fetch_failed"}
    if len(html) < 5000:
        return {"valid": False, "reason": f"redirect_stub ({len(html)} bytes)"}
    products = parse_products(html, source_section="verify")
    v = validate_shop_match(products, brand_meta.get("keywords", []))
    v["products_total"] = len(products)
    v["page_size"] = len(html)
    return v


def main():
    print(f"[SLUG-FINDER] start {datetime.now(JST).isoformat(timespec='seconds')}")
    print(f"[SLUG-FINDER] checking {len(SUSPECT_BRANDS)} brands")

    results = {}
    for brand_key, keywords in SUSPECT_BRANDS.items():
        current_slug = None
        for k_lc, meta in ALL_COMPETITORS.items():
            if k_lc.lower() == brand_key.lower() or brand_key.lower() in [k.lower() for k in meta.get("keywords", [])]:
                current_slug = meta["shop_slugs"][0] if meta.get("shop_slugs") else None
                brand_meta = meta
                break
        else:
            brand_meta = {"keywords": keywords}

        print(f"\n[{brand_key}] current={current_slug}")
        attempts = []
        for kw in keywords:
            time.sleep(1.5)
            best, debug = search_brand(kw)
            attempts.append({"keyword": kw, "best": best, "debug": debug})
            print(f"  search '{kw}' → best={best}  {debug.get('top3', debug.get('error'))}")
            if best:
                break  # 첫 키워드에서 좋은 매치가 나오면 종료

        # 최종 후보 — 첫 성공
        candidate = next((a["best"] for a in attempts if a["best"]), None)
        verify_result = None
        if candidate:
            time.sleep(1.5)
            verify_result = verify_shop(candidate, brand_meta)
            print(f"  verify {candidate} → valid={verify_result['valid']}  "
                  f"products={verify_result.get('products_total')}  "
                  f"ratio={verify_result.get('match_ratio')}  "
                  f"reason={verify_result.get('reason')}")

        results[brand_key] = {
            "current_slug": current_slug,
            "discovered_slug": candidate,
            "verified": (verify_result or {}).get("valid", False),
            "verify_detail": verify_result,
            "attempts": attempts,
        }

    out = DATA / "_slug_discovery.json"
    out.write_text(json.dumps({
        "last_updated": datetime.now(JST).isoformat(timespec="seconds"),
        "results": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[SLUG-FINDER] wrote {out}")

    print(f"\n[SLUG-FINDER] summary:")
    print(f"{'brand':<18} {'current':<22} {'discovered':<22} {'verified'}")
    print("-" * 80)
    for k, r in results.items():
        mark = "✓" if r["verified"] else "✗"
        print(f"{k:<18} {(r['current_slug'] or '-'):<22} {(r['discovered_slug'] or '-'):<22} {mark}")


if __name__ == "__main__":
    main()
