"""@cosme Top 10 데이터 일회성 부트스트랩 + 매칭 맵 생성.

본 프로젝트는 별도 @cosme 크롤러를 두지 않고 메인 ad_dash의 cosme_top.json을
일회성으로 참조 (GitHub Actions에서는 메인 repo 데이터 접근 어려우므로 본 프로젝트의
crawler/cosme_rank.py 별도 구현 필요. 일단 부트스트랩으로 시작.)

출력:
  data/cosme_top.json       ← 메인 데이터 일회성 카피
  data/_cosme_match.json    ← brand_normalized → ranked items 매핑
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lips_rank import normalize_brand, _norm  # 동일 매칭 로직 재사용

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
JST = timezone(timedelta(hours=9))

# 메인 ad_dash 경로 (로컬 부트스트랩 전용)
AD_DASH_COSME = Path(r"c:/Users/user/Downloads/ad_dash_v5.9.15/data/cosme_top.json")


def main() -> int:
    if not AD_DASH_COSME.exists():
        print(f"[COSME] {AD_DASH_COSME} not found — skip bootstrap")
        return 0
    src = json.loads(AD_DASH_COSME.read_text(encoding="utf-8"))
    recs = src.get("records", [])
    if not recs:
        print("[COSME] no records — skip")
        return 0

    # 가장 최근 N일(직전 7일)만 유지
    cutoff = (datetime.now(JST).date() - timedelta(days=14)).isoformat()
    recs = [r for r in recs if r.get("date", "") >= cutoff]

    payload = {
        "schema_version": 1,
        "source": "@cosme weekly top (bootstrap from ad_dash, 1-time only)",
        "last_updated": datetime.now(JST).isoformat(timespec="seconds"),
        "records": recs,
    }
    out = DATA / "cosme_top.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[COSME] bootstrap: {len(recs)} records (14day) -> {out}")

    # 매칭 맵 — brand_normalized → [items]
    by_brand: dict = {}
    for r in recs:
        b_norm = normalize_brand(r.get("brand") or "")
        if not b_norm:
            continue
        by_brand.setdefault(b_norm, []).append({
            "name_norm": _norm(r.get("item_name") or ""),
            "name_raw": r.get("item_name"),
            "rank": r.get("rank"),
            "date": r.get("date"),
            "url": r.get("url"),
            "image_url": r.get("image_url"),
        })
    # 같은 brand 내에서 가장 높은 rank만 유지 (중복 정리)
    for b, items in by_brand.items():
        items.sort(key=lambda x: (x.get("rank") or 9999))

    out2 = DATA / "_cosme_match.json"
    out2.write_text(json.dumps({
        "last_updated": datetime.now(JST).isoformat(timespec="seconds"),
        "by_brand": by_brand,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(len(v) for v in by_brand.values())
    print(f"[COSME] match map: {len(by_brand)} brands · {total} ranked items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
