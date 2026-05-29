"""Qoo10 검색에서 브랜드별 brandno 추출.

Qoo10 JP는 /shop/{slug} 외에 /gmkt.inc/Mobile/Search/Brand.aspx?brandno=N 으로
브랜드 단위 상품 페이지가 따로 존재. shop slug 못 찾는 브랜드는 brandno로 대체.

원리:
  1) m.qoo10.jp/gmkt.inc/Mobile/Search/Default.aspx?keyword=X&kwclick=P 검색
  2) HTML에서 brandno=N 추출 (브랜드 배너 링크에 노출됨)
  3) Brand.aspx?brandno=N&ga_priority=-1&ga_prdlist=srp 검증 fetch

출력: data/_brandno_map.json
    { "<brand_key>": { "brandno": N, "verified_at": ts, "name_kw": "..."} }
"""
from __future__ import annotations
import gzip
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _brands import ALL_COMPETITORS  # noqa: E402

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

JST = timezone(timedelta(hours=9))

UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
HEADERS_BASE = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
}

BRANDNO_RE = re.compile(r'brandno=(\d+)')


def fetch(url: str, referer: str | None = None, retries: int = 3) -> str | None:
    headers = dict(HEADERS_BASE)
    if referer:
        headers["Referer"] = referer
    last_err = None
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                html = raw.decode("utf-8", errors="replace")
                if "523 Error" in html and len(html) < 2000:
                    raise RuntimeError("523 error shell")
                if len(html) < 2000:
                    raise RuntimeError(f"redirect_stub ({len(html)} bytes)")
                return html
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(2.0 * attempt)
    print(f"  [FETCH-FAIL] {url}  -> {last_err}", flush=True)
    return None


# 모든 브랜드 + 추가 검색 키워드
SEARCH_KW_OVERRIDE = {
    "aestura":    ["AESTURA", "エストラ"],
    "isntree":    ["isntree", "イズントゥリー"],
    "mixsoon":    ["mixsoon", "ミクスーン"],
    "samu":       ["SAMU", "サミュ"],
    "fwee":       ["fwee", "プゥイ"],
    "abouttone":  ["About Tone", "アバウトトーン"],
    "dasique":    ["DASIQUE", "デイジーク"],
    "peripera":   ["peripera", "ペリペラ"],
    "hince":      ["hince", "ヒンス"],
    "millefee":   ["MilleFée", "millefee"],
    "2aN":        ["2aN"],
    "abib":       ["ABIB", "アビブ"],
    "tocobo":     ["TOCOBO", "トコボ"],
    "pyunkangyul":["PYUNKANG YUL", "ピョンガンユル"],
    "haruharu":   ["HARUHARU", "ハルハル"],
    "roundlab":   ["Round Lab", "ラウンドラボ"],
    "ongredients":["ONGREDIENTS"],
    "beautyofjoseon":["Beauty of Joseon", "ビューティーオブジョソン"],
    "drjart":     ["Dr.Jart+", "ドクタージャルト"],
    "laka":       ["LAKA", "ラカ"],
    "23yearsold": ["23 years old"],
    "clio":       ["CLIO", "クリオ"],
    "lilybyred":  ["lilybyred", "リリーバイレッド"],
    "bbia":       ["BBIA", "ピア"],
    "olens":      ["OLENS"],
    "etude":      ["ETUDE HOUSE", "エチュード"],
    "3ce":        ["3CE"],
    # 정상 shop slug 있는 브랜드도 brandno 함께 보유하면 좋음 (fallback용)
    "anua":       ["Anua", "アヌア"],
    "medicube":   ["medicube", "メディキューブ"],
    "romand":     ["rom&nd", "ロムアンド"],
    "cosrx":      ["COSRX"],
    "tirtir":     ["TIRTIR", "ティルティル"],
    "mediheal":   ["mediheal", "メディヒール"],
    "celimax":    ["celimax", "セリマックス"],
    "amuse":      ["AMUSE", "アミューズ"],
    "banilaco":   ["banila co", "バニラコ"],
    "skin1004":   ["skin1004"],
    "vt":         ["VTコス", "VT cosmetics"],
    "torriden":   ["torriden", "トリデン"],
    "kopher":     ["Kopher", "コーファー"],
    "dalba":      ["d'Alba", "ダルバ"],
    "manyo":      ["manyo", "マニョ", "魔女工場"],
    "biodance":   ["biodance", "バイオダンス"],
    "numbuzin":   ["numbuzin", "ナンバーズイン"],
    "dinto":      ["DINTO", "ディント"],
    "ohora":      ["ohora", "オホーラ"],
    "age20s":     ["AGE20"],
}


def search_brandno(keyword: str) -> tuple[int | None, dict]:
    enc = urllib.parse.quote(keyword)
    search_url = f"https://m.qoo10.jp/gmkt.inc/Mobile/Search/Default.aspx?keyword={enc}&kwclick=P"
    html = fetch(search_url, referer="https://m.qoo10.jp/")
    if not html:
        return None, {"error": "fetch_failed"}
    cands = BRANDNO_RE.findall(html)
    if not cands:
        return None, {"error": "no_brandno", "html_size": len(html)}
    # 가장 자주 나오는 brandno = 그 키워드의 매칭 브랜드
    from collections import Counter
    cnt = Counter(cands)
    top = cnt.most_common(3)
    return int(top[0][0]), {"top3": top, "total_hits": len(cands)}


def verify_brand_page(brandno: int, expected_keywords: list[str]) -> dict:
    url = f"https://m.qoo10.jp/gmkt.inc/Mobile/Search/Brand.aspx?brandno={brandno}&ga_priority=-1&ga_prdlist=srp"
    html = fetch(url, referer=f"https://m.qoo10.jp/gmkt.inc/Mobile/Search/Default.aspx?keyword={urllib.parse.quote(expected_keywords[0])}&kwclick=P")
    if not html:
        return {"valid": False, "reason": "fetch_failed", "products": 0}
    # 상품 수
    n_items = len(re.findall(r'class="list_v2_item', html))
    # 키워드 매칭 (브랜드명이 페이지 안에 있어야 함)
    kw_hit = sum(1 for kw in expected_keywords if kw.lower() in html.lower())
    return {
        "valid": n_items >= 5 and kw_hit >= 1,
        "products": n_items,
        "keyword_hits": kw_hit,
        "page_size": len(html),
    }


def main():
    print(f"[BRANDNO-FINDER] start {datetime.now(JST).isoformat(timespec='seconds')}")
    print(f"[BRANDNO-FINDER] checking {len(SEARCH_KW_OVERRIDE)} brands")

    results = {}
    for brand_key, keywords in SEARCH_KW_OVERRIDE.items():
        # 매칭 키워드 (검증용)
        meta = ALL_COMPETITORS.get(brand_key) or {}
        if not meta:
            for k, m in ALL_COMPETITORS.items():
                if brand_key.lower() == k.lower():
                    meta = m
                    break
        match_kw = meta.get("keywords", keywords)

        print(f"\n[{brand_key}]")
        best_brandno = None
        for kw in keywords:
            time.sleep(1.8)
            bno, dbg = search_brandno(kw)
            print(f"  search '{kw}' → brandno={bno}  ({dbg.get('top3', dbg.get('error'))})")
            if bno:
                best_brandno = bno
                used_kw = kw
                break

        verify = None
        if best_brandno:
            time.sleep(1.8)
            verify = verify_brand_page(best_brandno, match_kw)
            print(f"  verify brandno={best_brandno} → valid={verify['valid']}  products={verify['products']}  kw_hits={verify['keyword_hits']}")

        results[brand_key] = {
            "brandno": best_brandno if (verify and verify["valid"]) else None,
            "discovered_brandno": best_brandno,
            "verify": verify,
            "used_keyword": used_kw if best_brandno else None,
        }

    out = DATA / "_brandno_map.json"
    out.write_text(json.dumps({
        "last_updated": datetime.now(JST).isoformat(timespec="seconds"),
        "results": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[BRANDNO-FINDER] wrote {out}")

    print(f"\n[BRANDNO-FINDER] summary:")
    print(f"{'brand':<18} {'brandno':<10} {'products':<10} {'valid'}")
    print("-" * 60)
    valid_count = 0
    for k, r in results.items():
        v = r.get("verify") or {}
        mark = "✓" if r["brandno"] else "✗"
        if r["brandno"]:
            valid_count += 1
        print(f"{k:<18} {str(r['brandno'] or '-'):<10} {str(v.get('products', '-')):<10} {mark}")
    print(f"\nTotal valid brandno: {valid_count} / {len(results)}")


if __name__ == "__main__":
    main()
