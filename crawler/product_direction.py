"""다음 상품 방향성 분석 — 신상품 제품명을 파싱해서 트렌드 추출.

추출 차원:
  스킨케어:
    - 성분 (나이아신아마이드/비타민C/PDRN/시카 등)
    - 제형 (토너/세럼/크림/마스크/오일/패드/미스트 등)
    - 효능 카테고리 (진정/수분/미백/안티에이징/모공)
  메이크업:
    - 카테고리 (립/아이/베이스/페이스 + 세부)
    - 제형 (틴트/립스틱/글로스/오일/밤 + 섀도우/라이너/마스카라 등)
    - 색조 계열 (누드/핑크/베리/코랄/레드/브라운/오렌지 등)

출력:
  data/_direction.json
    {
      "skin": {
        "ingredients": [{name, count, examples_top5, total_brands}],
        "formulations": [...],
        "concerns": [...]
      },
      "color": {
        "categories": [...],
        "formulations": [...],
        "color_families": [...]
      },
      "rising": [...],   # 최근 30일 출시에서 가장 많이 등장한 키워드 Top 10 (전체)
      "self_action": [...]  # 자사 BOH/브링그린/웨이크메이크/컬러그램용 액션 제안
    }
"""
from __future__ import annotations
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
JST = timezone(timedelta(hours=9))

# ─── 스킨케어 사전 ──────────────────────────────────────────
SKIN_INGREDIENTS = {
    # 미백 / 톤업
    "ナイアシンアミド": ["ナイアシンアミド", "ナイアシン", "niacinamide"],
    "ビタミンC": ["ビタミンC", "ビタミン C", "vitamin c", "アスコルビン酸"],
    "アルブチン": ["アルブチン", "arbutin"],
    "トラネキサム酸": ["トラネキサム酸", "tranexamic"],
    "コウジ酸": ["コウジ酸", "kojic"],
    # 진정 / 트러블
    "シカ (CICA)": ["CICA", "シカ", "ツボクサ", "centella"],
    "アゼライン酸": ["アゼライン酸", "azelaic"],
    "プロポリス": ["プロポリス", "propolis"],
    "茶 / 緑茶": ["緑茶", "ティーツリー", "tea tree", "green tea"],
    "甘草": ["甘草", "licorice", "グリチル"],
    # 수분 / 보습
    "ヒアルロン酸": ["ヒアルロン酸", "hyaluronic", "hyaluron"],
    "セラミド": ["セラミド", "ceramide"],
    "パンテノール": ["パンテノール", "panthenol"],
    "豆乳 / 大豆": ["豆乳", "大豆", "soy"],
    # 안티에이징 / 펩타이드
    "PDRN": ["PDRN", "ぺプチドコラーゲン"],
    "ペプチド": ["ペプチド", "peptide"],
    "コラーゲン": ["コラーゲン", "collagen"],
    "レチノール": ["レチノール", "retinol"],
    "バクチオール": ["バクチオール", "bakuchiol"],
    # 모공 / 각질
    "PHA / AHA / BHA": ["PHA", "AHA", "BHA", "サリチル酸", "salicylic", "glycolic"],
    "プロバイオティクス": ["プロバイオ", "プロバイオティクス", "probiotic"],
}

SKIN_FORMULATIONS = {
    "トナー": ["トナー", "toner", "化粧水"],
    "セラム / 美容液": ["セラム", "serum", "美容液", "アンプル", "ampule"],
    "クリーム": ["クリーム", "cream"],
    "ジェル": ["ジェル", "gel"],
    "マスク / シート": ["マスク", "mask", "シート"],
    "パッド / 拭き取り": ["パッド", "pad", "拭き取り"],
    "ミスト / スプレー": ["ミスト", "mist", "スプレー", "spray"],
    "オイル": ["オイル", "oil"],
    "クレンザー / 洗顔": ["クレンザー", "cleanser", "洗顔", "cleansing"],
    "エッセンス": ["エッセンス", "essence"],
    "アイクリーム / アイ": ["アイクリーム", "eye cream", "eye serum"],
    "ボディ": ["ボディ", "body", "ハンド"],
}

SKIN_CONCERNS = {
    "鎮静 / トラブル": ["鎮静", "トラブル", "敏感", "肌荒れ", "ニキビ", "ケア"],
    "保湿": ["保湿", "水分", "うるおい", "moisture"],
    "美白 / トーンアップ": ["美白", "ホワイトニング", "トーン", "whitening", "ブライト"],
    "毛穴 / 角質": ["毛穴", "角質", "縦毛穴", "pore"],
    "エイジング / ハリ": ["エイジング", "ハリ", "弾力", "アンチエイジング", "リフト", "シワ"],
    "ノニオイ / 無香料": ["無香料", "ノニオイ", "fragrance-free", "無添加"],
}

# ─── 색조 사전 ──────────────────────────────────────────────
COLOR_CATEGORIES = {
    "リップティント": ["ティント", "tint"],
    "リップスティック": ["リップスティック", "lipstick", "リップバー"],
    "リップグロス / オイル": ["グロス", "gloss", "リップオイル", "lip oil"],
    "リップバーム / トリート": ["リップバーム", "lip balm", "リップトリート"],
    "ペンシル / ライナー": ["リップライナー", "lip pencil", "ペンシル"],
    # 아이
    "アイシャドウ": ["アイシャドウ", "eye shadow", "シャドウパレット"],
    "アイライナー": ["アイライナー", "eyeliner"],
    "マスカラ": ["マスカラ", "mascara"],
    "アイブロウ": ["アイブロウ", "eyebrow", "ブロウ", "眉"],
    # 베이스
    "クッション": ["クッション", "cushion"],
    "ファンデーション": ["ファンデ", "foundation"],
    "コンシーラー": ["コンシーラー", "concealer"],
    "プライマー / ベース": ["プライマー", "primer", "メイクベース", "化粧下地"],
    "パウダー": ["パウダー", "powder"],
    "ハイライト / コントゥア": ["ハイライト", "highlight", "コントゥア"],
    "チーク / ブラッシャー": ["チーク", "ブラッシャー", "blush"],
    "フィクサー / セッティング": ["フィクサー", "fixer", "セッティング"],
}

COLOR_FORMULATIONS = {
    "리퀴드 / リキッド": ["リキッド", "liquid", "ウォータリー"],
    "ベルベット / 매트": ["ベルベット", "マット", "matte", "velvet"],
    "グロッシー / 윤기": ["グロッシー", "glossy", "ジューシー", "juicy", "シャイン", "shine"],
    "シマー / グリッター": ["シマー", "shimmer", "グリッター", "glitter", "パール"],
    "クリーミー": ["クリーミー", "creamy"],
    "パウダリー": ["パウダリー", "powdery"],
    "バーム / 밤": ["バーム", "balm"],
    "스틱 / ペン": ["スティック", "stick", "ペン"],
}

COLOR_FAMILIES = {
    "ヌード / 누드": ["ヌード", "nude", "ベージュ"],
    "핑크": ["ピンク", "pink", "rose", "ローズ"],
    "베리 / 와인": ["ベリー", "berry", "wine", "ワイン", "プラム"],
    "코랄 / 오렌지": ["コーラル", "coral", "オレンジ", "orange", "アプリコット", "apricot"],
    "레드": ["レッド", "red", "チェリー", "cherry"],
    "브라운": ["ブラウン", "brown", "チョコ", "choco", "モカ"],
    "퍼플 / 라일락": ["パープル", "purple", "ライラック", "lilac", "バイオレット"],
    "다채 / 멀티": ["多色", "全", "コレクション", "collection", "セット"],
    # 색조 호수 추출 (별도)
}

# 색상 호수/수치 추출
SHADE_COUNT_RE = re.compile(r'全(\d{1,3})色|(\d{1,3})\s*colors?|(\d{1,3})\s*shades?')


def match_keywords(title: str, dictionary: dict) -> list[str]:
    """제목에서 사전 키 중 매칭되는 것들."""
    if not title:
        return []
    tl = title.lower()
    matched = []
    for canonical, variants in dictionary.items():
        for v in variants:
            if v.lower() in tl:
                matched.append(canonical)
                break
    return matched


def extract_shade_count(title: str) -> int | None:
    """제목에서 색상 호수 추출 — 全36色 / 12 colors 등."""
    if not title:
        return None
    m = SHADE_COUNT_RE.search(title)
    if not m:
        return None
    for g in m.groups():
        if g:
            try:
                n = int(g)
                if 1 <= n <= 100:
                    return n
            except ValueError:
                continue
    return None


def _safe_price(r):
    p = r.get("판매가") or r.get("타임세일가") or r.get("참고가")
    if isinstance(p, (int, float)) and p > 0:
        return int(p)
    return None


def _avg(prices):
    prices = [p for p in prices if p]
    return round(sum(prices) / len(prices)) if prices else None


def analyze_skin(rows: list[dict]) -> dict:
    """스킨케어 신상품 분석 — 빈도 + 평균가."""
    ing_counter: Counter = Counter()
    form_counter: Counter = Counter()
    concern_counter: Counter = Counter()
    ing_examples: dict = defaultdict(list)
    ing_brands: dict = defaultdict(set)
    form_examples: dict = defaultdict(list)
    form_prices: dict = defaultdict(list)   # 제형별 가격 누적

    all_prices: list = []
    for r in rows:
        title = r.get("제품명") or ""
        brand = r.get("브랜드") or ""
        price = _safe_price(r)
        if price:
            all_prices.append(price)

        for ing in match_keywords(title, SKIN_INGREDIENTS):
            ing_counter[ing] += 1
            if len(ing_examples[ing]) < 5:
                ing_examples[ing].append({"brand": brand, "title": title[:60], "url": r.get("링크")})
            ing_brands[ing].add(brand)

        for form in match_keywords(title, SKIN_FORMULATIONS):
            form_counter[form] += 1
            if price:
                form_prices[form].append(price)
            if len(form_examples[form]) < 5:
                form_examples[form].append({"brand": brand, "title": title[:60]})

        for concern in match_keywords(title, SKIN_CONCERNS):
            concern_counter[concern] += 1

    return {
        "ingredients": [
            {"name": k, "count": c, "brands_count": len(ing_brands[k]),
             "examples": ing_examples[k]}
            for k, c in ing_counter.most_common(20) if c >= 2
        ],
        "formulations": [
            {"name": k, "count": c, "avg_price": _avg(form_prices[k]),
             "examples": form_examples[k]}
            for k, c in form_counter.most_common(15) if c >= 2
        ],
        "concerns": [
            {"name": k, "count": c}
            for k, c in concern_counter.most_common(10) if c >= 2
        ],
        "total_products": len(rows),
        "avg_price": _avg(all_prices),
        "price_count": len(all_prices),
    }


def analyze_color(rows: list[dict]) -> dict:
    """색조 신상품 분석 — 빈도 + 평균가."""
    cat_counter: Counter = Counter()
    form_counter: Counter = Counter()
    fam_counter: Counter = Counter()
    shade_counts: list = []
    cat_examples: dict = defaultdict(list)
    cat_prices: dict = defaultdict(list)        # 카테고리(립/아이/베이스)별 가격
    group_prices: dict = defaultdict(list)      # 대분류 그룹(립/아이/베이스/페이스)별 가격
    fam_prices: dict = defaultdict(list)        # 색계열별

    # 카테고리 → 대분류 매핑
    LIP_CATS  = {"リップティント", "リップスティック", "リップグロス / オイル",
                 "リップバーム / トリート", "ペンシル / ライナー"}
    EYE_CATS  = {"アイシャドウ", "アイライナー", "マスカラ", "アイブロウ"}
    BASE_CATS = {"クッション", "ファンデーション", "コンシーラー",
                 "プライマー / ベース", "パウダー"}
    FACE_CATS = {"ハイライト / コントゥア", "チーク / ブラッシャー", "フィクサー / セッティング"}

    all_prices: list = []
    for r in rows:
        title = r.get("제품명") or ""
        brand = r.get("브랜드") or ""
        price = _safe_price(r)
        if price:
            all_prices.append(price)

        matched_cats = match_keywords(title, COLOR_CATEGORIES)
        for cat in matched_cats:
            cat_counter[cat] += 1
            if price:
                cat_prices[cat].append(price)
            if len(cat_examples[cat]) < 5:
                cat_examples[cat].append({"brand": brand, "title": title[:60], "url": r.get("링크")})

        # 대분류 그룹 — 한 상품이 여러 그룹에 동시 매칭되지 않도록 우선 1개만
        if price:
            if any(c in LIP_CATS for c in matched_cats):
                group_prices["립"].append(price)
            elif any(c in EYE_CATS for c in matched_cats):
                group_prices["아이"].append(price)
            elif any(c in BASE_CATS for c in matched_cats):
                group_prices["베이스"].append(price)
            elif any(c in FACE_CATS for c in matched_cats):
                group_prices["페이스"].append(price)

        for form in match_keywords(title, COLOR_FORMULATIONS):
            form_counter[form] += 1

        for fam in match_keywords(title, COLOR_FAMILIES):
            fam_counter[fam] += 1
            if price:
                fam_prices[fam].append(price)

        sc = extract_shade_count(title)
        if sc:
            shade_counts.append({"brand": brand, "shades": sc, "title": title[:60]})

    return {
        "categories": [
            {"name": k, "count": c, "avg_price": _avg(cat_prices[k]),
             "examples": cat_examples[k]}
            for k, c in cat_counter.most_common(15) if c >= 1
        ],
        "category_groups": [
            {"name": g, "count": len(group_prices[g]), "avg_price": _avg(group_prices[g])}
            for g in ["립", "아이", "베이스", "페이스"] if group_prices[g]
        ],
        "formulations": [
            {"name": k, "count": c}
            for k, c in form_counter.most_common(15) if c >= 1
        ],
        "color_families": [
            {"name": k, "count": c, "avg_price": _avg(fam_prices[k])}
            for k, c in fam_counter.most_common(15) if c >= 1
        ],
        "shade_releases": sorted(shade_counts, key=lambda x: -x["shades"])[:10],
        "total_products": len(rows),
        "avg_price": _avg(all_prices),
        "price_count": len(all_prices),
    }


def build_self_action(skin_analysis: dict, color_analysis: dict) -> list[dict]:
    """자사 4브랜드(BOH·브링그린·웨이크메이크·컬러그램)용 액션 제안."""
    actions = []

    # 스킨 — Top 성분 → BOH/브링그린 액션
    if skin_analysis["ingredients"]:
        top3 = skin_analysis["ingredients"][:3]
        for t in top3:
            actions.append({
                "for_brand": "BOH / 브링그린 (스킨)",
                "category": "성분",
                "trend": t["name"],
                "evidence": f"30일간 경쟁사 신상품 {t['count']}건 ({t['brands_count']}개 브랜드)이 {t['name']} 채택",
                "action": f"자사 {t['name']} 함유 라인 점검 — 없으면 차기 기획 우선순위 검토, 있으면 마케팅 메시지 강화"
            })

    # 스킨 — Top 제형
    if skin_analysis["formulations"]:
        top_form = skin_analysis["formulations"][0]
        actions.append({
            "for_brand": "BOH / 브링그린 (스킨)",
            "category": "제형",
            "trend": top_form["name"],
            "evidence": f"30일 신상품 중 제형 1위 — {top_form['count']}건",
            "action": f"자사 차기 신제품 제형 결정 시 우선 검토. 단일 제형 vs 다제형 전략 토론"
        })

    # 색조 — Top 카테고리 → 웨이크메이크/컬러그램 액션
    if color_analysis["categories"]:
        top_cat = color_analysis["categories"][0]
        actions.append({
            "for_brand": "웨이크메이크 / 컬러그램 (색조)",
            "category": "카테고리",
            "trend": top_cat["name"],
            "evidence": f"30일 색조 신상품 중 1위 카테고리 — {top_cat['count']}건",
            "action": f"자사 {top_cat['name']} 라인 SKU 수 확인. 부족 시 추가 기획 / 충분 시 기존 라인 마케팅 강화"
        })

    # 색조 — 색상 호수 트렌드
    if color_analysis["shade_releases"]:
        avg_shades = sum(s["shades"] for s in color_analysis["shade_releases"]) / len(color_analysis["shade_releases"])
        max_release = color_analysis["shade_releases"][0]
        actions.append({
            "for_brand": "웨이크메이크 / 컬러그램 (색조)",
            "category": "색상 라인업",
            "trend": f"평균 {avg_shades:.0f}색 / 최대 {max_release['shades']}색 ({max_release['brand']})",
            "evidence": f"색조 신상품 중 색상 호수 발표가 명시된 {len(color_analysis['shade_releases'])}건 평균",
            "action": f"자사 색조 신제품 호수 전략 점검 — 컬렉션 단위(10+색) vs 단품(1-3색) 결정"
        })

    # 색조 — Top 색 계열
    if color_analysis["color_families"]:
        top_fam = color_analysis["color_families"][0]
        actions.append({
            "for_brand": "웨이크메이크 / 컬러그램 (색조)",
            "category": "색 계열",
            "trend": top_fam["name"],
            "evidence": f"30일 색조 신상품 색 계열 1위 — {top_fam['count']}건",
            "action": f"자사 색조 차기 컬렉션 메인 색 결정 시 우선 검토"
        })

    return actions


def main():
    src = DATA / "new_products.json"
    if not src.exists():
        print(f"[ERR] {src} not found. run qoo10_new_products.py first.")
        return 1
    data = json.loads(src.read_text(encoding="utf-8"))
    skin_rows = data["categories"]["skin"]
    color_rows = data["categories"]["color"]

    print(f"[DIRECTION] skin={len(skin_rows)} color={len(color_rows)}")
    skin_a = analyze_skin(skin_rows)
    color_a = analyze_color(color_rows)
    actions = build_self_action(skin_a, color_a)

    out = {
        "last_updated": datetime.now(JST).isoformat(timespec="seconds"),
        "skin": skin_a,
        "color": color_a,
        "self_action": actions,
    }
    dest = DATA / "_direction.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[DIRECTION] wrote {dest}")

    print(f"\n=== 스킨케어 Top 성분 ===")
    for i in skin_a["ingredients"][:5]:
        print(f"  {i['name']:<18}  {i['count']}건  ({i['brands_count']}개 브랜드)")
    print(f"\n=== 스킨케어 Top 제형 ===")
    for f in skin_a["formulations"][:5]:
        print(f"  {f['name']:<18}  {f['count']}건")
    print(f"\n=== 색조 Top 카테고리 ===")
    for c in color_a["categories"][:5]:
        print(f"  {c['name']:<18}  {c['count']}건")
    print(f"\n=== 색조 Top 색 계열 ===")
    for fa in color_a["color_families"][:5]:
        print(f"  {fa['name']:<18}  {fa['count']}건")
    print(f"\n=== 자사 액션 제안 {len(actions)}개 ===")
    for a in actions:
        print(f"  [{a['for_brand']}] {a['category']}: {a['trend']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
