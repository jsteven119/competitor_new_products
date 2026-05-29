"""LIPS (lipscosme.com) 카테고리 랭킹 크롤러.

LIPS는 일본 10s~30s 여성 뷰티 SNS/리뷰 플랫폼. K-뷰티 트렌드 진입점.
각 카테고리(아이샤도우/립틴트/쿠션 등)별 Top 100 상품을 SSR HTML로 직접 노출.

상품 카드 구조 (확인됨):
  - class="ProductListArticle__rank-num"
  - class="ProductListArticle__productTitle-brandName"
  - class="ProductListArticle__productTitle-productName"
  - class="ratingStar__num"
  - class="ratingStar__ratesCount"
  - href="/products/{lips_product_id}"

출력:
  data/lips_rank.json     ← 카테고리별 Top 100 raw
  data/_lips_match.json   ← brand → ranked items 매칭 맵 (new_products 결합용)
"""
from __future__ import annotations
import gzip
import json
import re
import sys
import time
import unicodedata
import urllib.request
from datetime import datetime, timezone, timedelta
from html import unescape
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
JST = timezone(timedelta(hours=9))

UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
HEADERS_BASE = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
}

# 핵심 카테고리 — 자사 4브랜드 관련 (색조 우선, 스킨 일부)
CATEGORIES = [
    # 색조 ─ 립
    (129, "口紅",         "color_lip"),
    (133, "リップグロス",  "color_lip"),
    (506, "リップティント", "color_lip"),
    (132, "リップケア",    "color_lip"),
    # 색조 ─ 아이
    (63,  "アイシャドウ",  "color_eye"),
    (70,  "アイライナー",  "color_eye"),
    (74,  "マスカラ",     "color_eye"),
    (76,  "アイブロウ",   "color_eye"),
    # 색조 ─ 베이스
    (122, "ファンデーション", "color_base"),
    (117, "コンシーラー",  "color_base"),
    (81,  "化粧下地",     "color_base"),
    (72,  "チーク",       "color_face"),
    # 스킨
    (139, "化粧水",        "skin"),
    (145, "美容液",        "skin"),
    (148, "フェイスクリーム", "skin"),
    (149, "乳液",          "skin"),
    (156, "洗顔料",        "skin"),
    (165, "フェイスオイル",  "skin"),
    (130, "スキンケア基礎",  "skin"),
]

RANK_SPLIT_RE  = re.compile(r'class="ProductListArticle__rank-num"[^>]*>\s*(\d+)\s*<')
BRAND_RE       = re.compile(r'class="ProductListArticle__productTitle-brandName"[^>]*>\s*([^<]+)')
NAME_RE        = re.compile(r'class="ProductListArticle__productTitle-productName"[^>]*>\s*([^<]+)')
RATING_RE      = re.compile(r'class="ratingStar__num"[^>]*>\s*([\d.]+)')
COUNT_RE       = re.compile(r'class="ratingStar__ratesCount"[^>]*>\s*([\d,]+)')
PRODID_RE      = re.compile(r'href="/products/(\d+)')


def fetch(url: str, referer: str, retries: int = 2) -> str | None:
    headers = dict(HEADERS_BASE, Referer=referer)
    last_err = None
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                return raw.decode("utf-8", errors="replace")
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(2.0 * attempt)
    print(f"  [FETCH-FAIL] {url}  {last_err}", flush=True)
    return None


def parse_category(html: str) -> list[dict]:
    """카테고리 페이지에서 Top 상품 추출.

    페이지의 rank-num 시작점들을 모두 찾아서 각 시작점부터 다음 시작점까지를 1카드 블록으로.
    """
    matches = list(RANK_SPLIT_RE.finditer(html))
    items = []
    seen_ranks = set()
    for i, m in enumerate(matches):
        rank = int(m.group(1))
        if rank in seen_ranks:
            continue
        seen_ranks.add(rank)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        block = html[start:end]

        b_m = BRAND_RE.search(block)
        n_m = NAME_RE.search(block)
        pid_m = PRODID_RE.search(block)
        rt_m = RATING_RE.search(block)
        rc_m = COUNT_RE.search(block)

        items.append({
            "rank": rank,
            "brand": unescape(b_m.group(1)).strip() if b_m else None,
            "name": unescape(n_m.group(1)).strip() if n_m else None,
            "lips_product_id": pid_m.group(1) if pid_m else None,
            "rating": float(rt_m.group(1)) if rt_m else None,
            "review_count": int(rc_m.group(1).replace(",", "")) if rc_m else None,
            "url": f"https://lipscosme.com/products/{pid_m.group(1)}" if pid_m else None,
        })
    items.sort(key=lambda x: x["rank"])
    return items


def _norm(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.lower()
    s = re.sub(r"[【】\[\]\(\)（）\s・/,.+&_-]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# 브랜드명 다양한 표기 통합 (LIPS 카타카나 ↔ Qoo10 영문)
BRAND_ALIAS = {
    "ペリペラ": "peripera", "peripera": "peripera",
    "ロムアンド": "rom&nd", "romand": "rom&nd",
    "クリオ": "clio", "clio": "clio",
    "ヒンス": "hince", "hince": "hince",
    "ピア": "bbia", "bbia": "bbia",
    "リリーバイレッド": "lilybyred", "lilybyred": "lilybyred",
    "コスアールエックス": "cosrx", "cosrx": "cosrx",
    "メディキューブ": "medicube", "medicube": "medicube",
    "アヌア": "anua", "anua": "anua",
    "アバウトトーン": "about tone", "about tone": "about tone",
    "デイジーク": "dasique", "dasique": "dasique",
    "ティルティル": "tirtir", "tirtir": "tirtir",
    "ダルバ": "d'alba", "d'alba": "d'alba",
    "メディヒール": "mediheal", "mediheal": "mediheal",
    "魔女工場": "manyo", "マニョ": "manyo", "マニョファクトリー": "manyo",
    "エチュード": "etude", "etude": "etude",
    "アミューズ": "amuse", "amuse": "amuse",
    "バニラコ": "banila co", "banila co": "banila co",
    "ラネージュ": "laneige", "laneige": "laneige",
    "カヒ": "kahi", "kahi": "kahi",
    "イニスフリー": "innisfree", "innisfree": "innisfree",
    "アイオペ": "iope", "iope": "iope",
    "セリマックス": "celimax", "celimax": "celimax",
    "トコボ": "tocobo", "tocobo": "tocobo",
    "ハルハル": "haruharu", "haruharu wonder": "haruharu",
    "ナンバーズイン": "numbuzin", "numbuzin": "numbuzin",
    "ディント": "dinto", "dinto": "dinto",
    # 일본 색조
    "キャンメイク": "canmake", "canmake": "canmake",
    "セザンヌ": "cezanne", "cezanne": "cezanne",
    "ケイト": "kate", "kate": "kate",
    "ヴィセ": "visee", "visee": "visee",
    "エクセル": "excel", "excel": "excel",
    "キスミー": "kissme", "ヒロインメイク": "kissme", "kissme": "kissme",
    "シピシピ": "cipicipi", "cipicipi": "cipicipi",
    # 일본 스킨
    "肌ラボ": "hada labo", "hada labo": "hada labo",
    "雪肌精": "sekkisei", "sekkisei": "sekkisei",
    "キュレル": "curel", "curel": "curel", "curél": "curel",
    "ファンケル": "fancl", "fancl": "fancl",
    # 기타
    "VT": "vt", "vt": "vt",
    "プゥイ": "fwee", "fwee": "fwee",
    "ラカ": "laka", "laka": "laka",
    "ABIB": "abib", "アビブ": "abib", "abib": "abib",
    "TIRTIR": "tirtir",
    "TORRIDEN": "torriden", "torriden": "torriden", "トリデン": "torriden",
    "Kopher": "kopher", "kopher": "kopher", "コーファー": "kopher",
    "biodance": "biodance", "バイオダンス": "biodance",
    "skin1004": "skin1004", "スキン1004": "skin1004",
    "MilleFée": "millefee", "millefee": "millefee", "ミルフィー": "millefee",
}


def normalize_brand(b: str) -> str:
    if not b:
        return ""
    b = b.strip()
    if b in BRAND_ALIAS:
        return BRAND_ALIAS[b]
    nb = _norm(b)
    return BRAND_ALIAS.get(nb, nb)


def build_match_map(categories: list[dict]) -> dict:
    """brand_normalized → [{rank, category, rating, review_count, name_norm, ...}]"""
    out: dict = {}
    for cat in categories:
        for it in cat["items"]:
            b_norm = normalize_brand(it.get("brand"))
            if not b_norm:
                continue
            out.setdefault(b_norm, []).append({
                "name_norm": _norm(it.get("name") or ""),
                "name_raw": it.get("name"),
                "rank": it.get("rank"),
                "category_id": cat["category_id"],
                "category_name": cat["category_name"],
                "group": cat["group"],
                "rating": it.get("rating"),
                "review_count": it.get("review_count"),
                "lips_product_id": it.get("lips_product_id"),
                "url": it.get("url"),
            })
    return out


def main() -> int:
    print(f"[LIPS] start {datetime.now(JST).isoformat(timespec='seconds')}")
    print(f"[LIPS] crawling {len(CATEGORIES)} categories")
    out_cats: list[dict] = []
    for cat_id, cat_name, group in CATEGORIES:
        time.sleep(2.0)
        url = f"https://lipscosme.com/rankings/{cat_id}"
        html = fetch(url, referer="https://lipscosme.com/rankings")
        if not html or len(html) < 5000:
            print(f"  [{cat_id:>3}] {cat_name:<14}  X fetch failed")
            continue
        items = parse_category(html)
        out_cats.append({
            "category_id": cat_id,
            "category_name": cat_name,
            "group": group,
            "items_count": len(items),
            "items": items[:100],
            "fetched_at": datetime.now(JST).isoformat(timespec="seconds"),
        })
        top_brand = items[0].get('brand') if items else '-'
        print(f"  [{cat_id:>3}] {cat_name:<14}  OK {len(items):>3} items  top1={top_brand}")

    payload = {
        "last_updated": datetime.now(JST).isoformat(timespec="seconds"),
        "source": "lipscosme.com/rankings",
        "categories": out_cats,
    }
    out = DATA / "lips_rank.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[LIPS] wrote {out}")

    match_map = build_match_map(out_cats)
    out2 = DATA / "_lips_match.json"
    out2.write_text(json.dumps({
        "last_updated": datetime.now(JST).isoformat(timespec="seconds"),
        "by_brand": match_map,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(len(v) for v in match_map.values())
    print(f"[LIPS] match map: {len(match_map)} brands · {total} ranked items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
