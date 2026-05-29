"""누락 13개 브랜드 추가 검색 — 다양한 키워드/제품명으로 brandno 재시도."""
from __future__ import annotations
import sys
import time
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).resolve().parent))
from brandno_finder import search_brandno, verify_brand_page  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"

MISSING_EXPAND = {
    "pyunkangyul":   ["Pyunkang Yul", "PYUNKANGYUL", "편강율", "ピョンガンユル", "essence toner"],
    "haruharu":      ["HARUHARU WONDER", "haruharu wonder", "黒米", "BLACK RICE", "흑미"],
    "roundlab":      ["ROUND LAB", "round lab", "白樺", "자작나무", "1025"],
    "olens":         ["OLENS", "オーレンズ", "オレンズ", "olens lens"],
    "tocobo":        ["TOCOBO", "tocobo lab", "リップトリート tocobo"],
    "medicube_ager": ["MEDICUBE AGE-R", "AGE-R", "ブースタープロ", "AGE R booster"],
    "ya-man":        ["YA-MAN", "ヤーマン", "yaman", "メディリフト"],
    "mtg":           ["MTG ReFa", "ReFa", "リファカラット", "リファ"],
    "panasonic_beauty":["Panasonic Beauty", "パナソニック スチーマー"],
    "newaskin":      ["Newa", "ニューア", "newa lift"],
    "denba":         ["DENBA", "デンバ", "denba health"],
    "tripollar":     ["TriPollar", "トリポラ", "Stop X"],
    "magnitone":     ["Magnitone", "マグニートン"],
    "beautylift":    ["BeautyLift", "ビューティリフト"],
}

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main():
    print(f"[RECOVER] retrying {len(MISSING_EXPAND)} missing brands\n")
    results = {}
    for key, keywords in MISSING_EXPAND.items():
        print(f"[{key}]")
        best = None
        used = None
        for kw in keywords:
            time.sleep(1.8)
            bno, dbg = search_brandno(kw)
            print(f"  '{kw}' -> brandno={bno}  {dbg.get('top3', dbg.get('error'))}")
            if bno:
                best = bno
                used = kw
                break
        verify = None
        if best:
            time.sleep(1.8)
            verify = verify_brand_page(best, keywords)
            print(f"  verify {best} -> valid={verify['valid']}  products={verify['products']}  kw_hits={verify['keyword_hits']}")
        results[key] = {"brandno": best if (verify and verify["valid"]) else None,
                        "discovered": best, "verify": verify, "used_keyword": used}
        print()

    bmap_path = DATA / "_brandno_map.json"
    bmap = json.loads(bmap_path.read_text(encoding="utf-8")) if bmap_path.exists() else {"results": {}}
    for k, r in results.items():
        if r["brandno"]:
            bmap["results"][k] = {
                "brandno": r["brandno"],
                "discovered_brandno": r["discovered"],
                "verify": r["verify"],
                "used_keyword": r["used_keyword"],
                "recovered_at": True,
            }
    bmap_path.write_text(json.dumps(bmap, ensure_ascii=False, indent=2), encoding="utf-8")

    print("="*70)
    print("RECOVERY SUMMARY")
    print(f"{'brand':<18} {'brandno':<10} {'valid':<10} {'keyword used'}")
    print("-"*70)
    recovered = 0
    truly_missing = []
    for k, r in results.items():
        if r["brandno"]:
            recovered += 1
            print(f"{k:<18} {r['brandno']:<10} O          {r['used_keyword']}")
        else:
            truly_missing.append(k)
            print(f"{k:<18} -          X          (no_match)")
    print(f"\n복구: {recovered}/{len(MISSING_EXPAND)}")
    print(f"진짜 누락(Qoo10 미입점 추정): {truly_missing}")


if __name__ == "__main__":
    main()
