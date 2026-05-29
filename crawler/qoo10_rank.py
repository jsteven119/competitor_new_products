"""Qoo10.jp Bestsellers 랭킹 크롤러 — 뷰티 카테고리 Top 200.

기존 jp_ad_dash crawl_rank.py 패턴을 본 프로젝트로 독립화.
- 신상품 트래커가 각 상품의 현재 Top 200 랭킹을 표시할 수 있도록 매핑 생성
- 매일 09:00 JST cron으로 갱신

출력:
  data/rank_beauty.json  ← 일자별 누적 (최근 30일만 유지)
  data/_rank_map.json    ← goodscode → {rank, snapshot_date} 빠른 lookup
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

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

JST = timezone(timedelta(hours=9))
TODAY_JST = datetime.now(JST).date().isoformat()

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://www.qoo10.jp/",
}

TARGETS = {
    "beauty": ("https://www.qoo10.jp/gmkt.inc/Bestsellers/?g=2", "rank_beauty.json"),
}

LI_RE         = re.compile(r'<li id="g_(\d+)">(.*?)</li>', re.DOTALL)
RANK_RE       = re.compile(r'<span class="rank">(\d+)</span>')
URL_RE        = re.compile(r'<a class="thmb"\s+href="([^"]+)"')
IMG_RE        = re.compile(r'gd_src="([^"]+)"')
BRAND_RE      = re.compile(r'<a class="txt_brand"[^>]*title="([^"]+)"')
NAME_RE       = re.compile(r'<a class="tt"\s+href="[^"]+"\s+title="([^"]+)"')
LIST_PRICE_RE = re.compile(r'<del[^>]*>([^<]+)</del>')
SALE_PRICE_RE = re.compile(r'<strong[^>]*>([^<]+)</strong>')
PRICE_RE      = re.compile(r"([\d,]+)\s*円")


def fetch(url: str, retries: int = 3) -> str:
    last_err = None
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                html = raw.decode("utf-8", errors="replace")
            if len(html) < 10_000:
                raise RuntimeError(f"too small ({len(html)} bytes)")
            return html
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(2.0 * attempt)
    raise RuntimeError(f"failed: {last_err}")


def parse_price(text):
    if not text:
        return None
    m = PRICE_RE.search(unescape(text))
    return int(m.group(1).replace(",", "")) if m else None


def _first(pat, text):
    m = pat.search(text)
    return m.group(1) if m else None


def parse(html: str) -> list[dict]:
    records, seen = [], set()
    for li in LI_RE.finditer(html):
        gid, block = li.group(1), li.group(2)
        rs = _first(RANK_RE, block)
        if not rs:
            continue
        rank = int(rs)
        if rank in seen:
            continue
        seen.add(rank)
        name = _first(NAME_RE, block) or ""
        brand = _first(BRAND_RE, block)
        records.append({
            "date": TODAY_JST,
            "rank": rank,
            "goodscode": gid,
            "item_name": unescape(name).strip(),
            "brand": unescape(brand).strip() if brand else None,
            "list_price": parse_price(_first(LIST_PRICE_RE, block)),
            "sale_price": parse_price(_first(SALE_PRICE_RE, block)),
            "url": _first(URL_RE, block),
            "image_url": _first(IMG_RE, block),
        })
    records.sort(key=lambda r: r["rank"])
    return records


def upsert(path: Path, new_records: list[dict], category: str) -> dict:
    existing = {"records": []}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    # 같은 날짜 덮어쓰기
    kept = [r for r in existing.get("records", []) if r.get("date") != TODAY_JST]
    # 최근 30일만 유지
    cutoff = (datetime.now(JST).date() - timedelta(days=30)).isoformat()
    kept = [r for r in kept if r.get("date", "") >= cutoff]
    merged = kept + new_records
    merged.sort(key=lambda r: (r.get("date", ""), r.get("rank", 0)))
    payload = {
        "schema_version": 1,
        "category": category,
        "source": "qoo10.jp Bestsellers (Beauty)",
        "last_updated": datetime.now(JST).isoformat(timespec="seconds"),
        "records": merged,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"today_added": len(new_records), "total_records": len(merged)}


def write_lookup_map(records_today: list[dict]) -> None:
    """qoo10_new_products.py가 빠르게 lookup할 수 있도록 goodscode → rank 매핑 파일 생성."""
    m = {}
    for r in records_today:
        m[r["goodscode"]] = {
            "rank": r["rank"],
            "snapshot_date": r["date"],
            "category": "beauty",
        }
    out = DATA / "_rank_map.json"
    out.write_text(json.dumps({
        "last_updated": datetime.now(JST).isoformat(timespec="seconds"),
        "category": "beauty",
        "items": m,
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    print(f"[RANK] JST today = {TODAY_JST}")
    failed = 0
    today_records: list[dict] = []
    for category, (url, out_name) in TARGETS.items():
        print(f"\n--- {category} ---")
        try:
            html = fetch(url)
            records = parse(html)
            print(f"  parsed {len(records)} items (rank {records[0]['rank']}-{records[-1]['rank']})")
            stat = upsert(DATA / out_name, records, category)
            print(f"  saved → {out_name}  (today +{stat['today_added']}, total {stat['total_records']})")
            today_records.extend(records)
        except Exception as e:
            print(f"  [ERR] {type(e).__name__}: {e}")
            failed += 1

    if today_records:
        write_lookup_map(today_records)
        print(f"\n[RANK] _rank_map.json updated ({len(today_records)} items)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
