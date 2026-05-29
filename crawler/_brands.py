"""경쟁사 브랜드 사전 — Qoo10.jp 셀러 slug 매핑.

shop URL slug 우선(정확) + 텍스트 키워드 보조. 메인 ad_dash의 _brands.py 미러 + 디바이스/ETC 추가.

스키마:
    {
        "label": "표시명",
        "shop_slugs": ["qoo10 셀러 URL slug"],
        "keywords": ["fallback 텍스트 매칭"],
        "kr_label": "한국어 표기 (대시보드용)",  # 신규
    }
"""

# ─── 기초 (스킨케어) ──────────────────────────────────────
COMPETITORS_SKIN = {
    "anua":          {"label": "Anua",          "kr_label": "아누아",      "shop_slugs": ["anua"],            "keywords": ["anua", "アヌア"]},
    "medicube":      {"label": "medicube",      "kr_label": "메디큐브",    "shop_slugs": ["medicube"],        "keywords": ["medicube", "メディキューブ"]},
    "dalba":         {"label": "d'Alba",        "kr_label": "달바",        "shop_slugs": ["dalba"],           "keywords": ["dalba", "d'alba", "ダルバ"]},
    "vt":            {"label": "VT",            "kr_label": "VT",          "shop_slugs": ["vtcosmetics"],     "keywords": [" VT ", "VTコスメ", "ヴイティー"]},
    "skin1004":      {"label": "skin1004",      "kr_label": "스킨1004",    "shop_slugs": ["skin1004japan"],   "keywords": ["skin1004", "スキン1004"]},
    "cosrx":         {"label": "COSRX",         "kr_label": "코스알엑스",  "shop_slugs": ["cosrx"],           "keywords": ["cosrx", "コスアールエックス"]},
    "kopher":        {"label": "Kopher",        "kr_label": "코퍼",        "shop_slugs": ["kopher"],          "keywords": ["kopher", "コーファー"]},
    "manyo":         {"label": "MANYO",         "kr_label": "마녀공장",    "shop_slugs": ["manyofactory"],    "keywords": ["manyo", "マニョ", "魔女工場"]},
    "aestura":       {"label": "AESTURA",       "kr_label": "에스트라",    "shop_slugs": ["aestura"],         "keywords": ["aestura", "エストラ"]},
    "biodance":      {"label": "Biodance",      "kr_label": "바이오던스",  "shop_slugs": ["biodance"],        "keywords": ["biodance", "バイオダンス"]},
    "numbuzin":      {"label": "numbuzin",      "kr_label": "넘버즈인",    "shop_slugs": ["numbuzin"],        "keywords": ["numbuzin", "ナンバーズイン"]},
    "tirtir":        {"label": "TIRTIR",        "kr_label": "티르티르",    "shop_slugs": ["tirtir"],          "keywords": ["tirtir", "ティルティル"]},
    "abib":          {"label": "ABIB",          "kr_label": "아비브",      "shop_slugs": ["abib"],            "keywords": ["abib", "アビブ"]},
    "tocobo":        {"label": "TOCOBO",        "kr_label": "토코보",      "shop_slugs": ["tocobo"],          "keywords": ["tocobo"]},
    "pyunkangyul":   {"label": "PYUNKANG YUL",  "kr_label": "편강율",      "shop_slugs": ["pyunkangyul"],     "keywords": ["pyunkang yul", "ピョンガンユル"]},
    "isntree":       {"label": "isntree",       "kr_label": "이즈엔트리",  "shop_slugs": ["isntree"],         "keywords": ["isntree", "イズントゥリー"]},
    "mixsoon":       {"label": "mixsoon",       "kr_label": "믹순",        "shop_slugs": ["mixsoon"],         "keywords": ["mixsoon"]},
    "mediheal":      {"label": "mediheal",      "kr_label": "메디힐",      "shop_slugs": ["medihealofficial"],"keywords": ["mediheal", "メディヒール"]},
    "haruharu":      {"label": "haruharu",      "kr_label": "하루하루",    "shop_slugs": ["haruharu"],        "keywords": ["haruharu"]},
    "roundlab":      {"label": "Round Lab",     "kr_label": "라운드랩",    "shop_slugs": ["roundlab"],        "keywords": ["round lab", "ラウンドラボ"]},
    "samu":          {"label": "SAMU",          "kr_label": "사무",        "shop_slugs": ["samu"],            "keywords": ["samu", "サミュ"]},
    "ongredients":   {"label": "Ongredients",   "kr_label": "온그레디언츠","shop_slugs": ["ongredients"],     "keywords": ["ongredients", "オングレディエンツ"]},
    "beautyofjoseon":{"label": "BoJ",           "kr_label": "조선미녀",    "shop_slugs": ["beautyofjoseon"],  "keywords": ["beauty of joseon", "ビューティーオブジョソン"]},
    "torriden":      {"label": "TORRIDEN",      "kr_label": "토리든",      "shop_slugs": ["torriden"],        "keywords": ["torriden", "トリデン"]},
    "drjart":        {"label": "Dr.Jart+",      "kr_label": "닥터자르트",  "shop_slugs": ["drjart"],          "keywords": ["dr.jart", "ドクタージャルト"]},
}

# ─── 색조 (color) ────────────────────────────────────────
COMPETITORS_COLOR = {
    "fwee":         {"label": "fwee",          "kr_label": "프위",       "shop_slugs": ["fwee"],         "keywords": ["fwee"]},
    "celimax":      {"label": "celimax",       "kr_label": "셀리맥스",   "shop_slugs": ["celimax"],      "keywords": ["celimax", "セリマックス"]},
    "romand":       {"label": "rom&nd",        "kr_label": "롬앤",       "shop_slugs": ["romand"],       "keywords": ["romand", "rom&nd", "ロムアンド"]},
    "abouttone":    {"label": "ABOUT TONE",    "kr_label": "어바웃톤",   "shop_slugs": ["abouttone"],    "keywords": ["about tone", "アバウトトーン"]},
    "dasique":      {"label": "DASIQUE",       "kr_label": "데이지크",   "shop_slugs": ["dasique"],      "keywords": ["dasique", "ダシック"]},
    "peripera":     {"label": "PERIPERA",      "kr_label": "페리페라",   "shop_slugs": ["peripera"],     "keywords": ["peripera", "ペリペラ"]},
    "banilaco":     {"label": "banila co",     "kr_label": "바닐라코",   "shop_slugs": ["banilaco"],     "keywords": ["banila co", "バニラコ"]},
    "amuse":        {"label": "AMUSE",         "kr_label": "어뮤즈",     "shop_slugs": ["amuse"],        "keywords": ["amuse", "アミューズ"]},
    "laka":         {"label": "Laka",          "kr_label": "라카",       "shop_slugs": ["laka"],         "keywords": ["laka"]},
    "dinto":        {"label": "DINTO",         "kr_label": "딘토",       "shop_slugs": ["dinto"],        "keywords": ["dinto"]},
    "23yearsold":   {"label": "23 years old",  "kr_label": "23년차",     "shop_slugs": ["23yearsold"],   "keywords": ["23 years old", "23yearsold"]},
    "clio":         {"label": "CLIO",          "kr_label": "클리오",     "shop_slugs": ["clio"],         "keywords": ["clio", "クリオ"]},
    "hince":        {"label": "hince",         "kr_label": "힌스",       "shop_slugs": ["hince"],        "keywords": ["hince", "ヒンス"]},
    "lilybyred":    {"label": "lilybyred",     "kr_label": "릴리바이레드","shop_slugs": ["lilybyred"],    "keywords": ["lilybyred", "リリーバイレッド"]},
    "bbia":         {"label": "BBIA",          "kr_label": "삐아",       "shop_slugs": ["bbia"],         "keywords": ["bbia", "ピア"]},
    "millefee":     {"label": "MilleFée",      "kr_label": "밀르페",     "shop_slugs": ["millefee"],     "keywords": ["millefee", "ミルフィー"]},
    "olens":        {"label": "OLENS",         "kr_label": "올렌즈",     "shop_slugs": ["olens"],        "keywords": ["olens"]},
    "etude":        {"label": "ETUDE",         "kr_label": "에뛰드",     "shop_slugs": ["etude"],        "keywords": ["etude", "エチュード"]},
    "ohora":        {"label": "ohora",         "kr_label": "오호라",     "shop_slugs": ["ohora"],        "keywords": ["ohora"]},
    "age20s":       {"label": "AGE20'S",      "kr_label": "에이지투웨니스","shop_slugs": ["age20s"],       "keywords": ["age20", "エイジ20"]},
    "3ce":          {"label": "3CE",           "kr_label": "3CE",        "shop_slugs": ["3ce"],          "keywords": ["3ce", "3CE"]},
    "2aN":          {"label": "2aN",           "kr_label": "투에이엔",   "shop_slugs": ["2anjp", "2an"], "keywords": ["2an", "투에이엔"]},
    "tocobo_color": {"label": "TOCOBO",        "kr_label": "토코보",     "shop_slugs": ["tocobo"],       "keywords": ["tocobo lip", "tocobo balm"]},
}

# ─── ETC: 뷰티 디바이스 / 미용기기 ─────────────────────────
COMPETITORS_DEVICE = {
    "medicube_ager":  {"label": "medicube AGE-R", "kr_label": "메디큐브 에이지알", "shop_slugs": ["medicube"],     "keywords": ["age-r", "ager", "エイジアール"]},
    "ya-man":         {"label": "YA-MAN",         "kr_label": "야만",              "shop_slugs": ["ya-man"],       "keywords": ["ya-man", "ヤーマン"]},
    "mtg":            {"label": "MTG",            "kr_label": "엠티지",            "shop_slugs": ["mtg-online"],   "keywords": ["MTG", "リファ", "ReFa"]},
    "panasonic_beauty":{"label": "Panasonic Beauty","kr_label": "파나소닉 뷰티",   "shop_slugs": ["panasonic-beauty"],"keywords": ["パナソニック ビューティー"]},
    "newaskin":       {"label": "Newa",           "kr_label": "뉴아",              "shop_slugs": ["newaskin"],     "keywords": ["newa", "ニューア"]},
    "denba":          {"label": "DENBA",          "kr_label": "덴바",              "shop_slugs": ["denba"],        "keywords": ["denba", "デンバ"]},
    "tripollar":      {"label": "TriPollar",      "kr_label": "트라이폴라",        "shop_slugs": ["tripollar"],    "keywords": ["tripollar", "トリポラ"]},
    "magnitone":      {"label": "Magnitone",      "kr_label": "마그니톤",          "shop_slugs": ["magnitone"],    "keywords": ["magnitone"]},
    "beautylift":     {"label": "BeautyLift",     "kr_label": "뷰티리프트",        "shop_slugs": ["beautylift"],   "keywords": ["beautylift"]},
}

ALL_COMPETITORS = {
    **{k: {**v, "category": "skin"}   for k, v in COMPETITORS_SKIN.items()},
    **{k: {**v, "category": "color"}  for k, v in COMPETITORS_COLOR.items()},
    **{k: {**v, "category": "device"} for k, v in COMPETITORS_DEVICE.items()},
}


def classify_shop_slug(slug: str) -> dict | None:
    """shop URL slug → 경쟁사 분류. 매칭 안 되면 None."""
    if not slug:
        return None
    s = slug.lower()
    for k, meta in ALL_COMPETITORS.items():
        for ss in meta["shop_slugs"]:
            if ss.lower() == s or ss.lower() in s:
                return {
                    "key": k,
                    "label": meta["label"],
                    "kr_label": meta["kr_label"],
                    "category": meta["category"],
                }
    return None


def get_all_shops_by_category() -> dict:
    """카테고리 → [(slug, key, label, kr_label)] 매핑."""
    out: dict = {"skin": [], "color": [], "device": []}
    for k, meta in ALL_COMPETITORS.items():
        for ss in meta["shop_slugs"]:
            out[meta["category"]].append({
                "slug": ss,
                "key": k,
                "label": meta["label"],
                "kr_label": meta["kr_label"],
            })
    return out


if __name__ == "__main__":
    # quick sanity
    print(f"SKIN  : {len(COMPETITORS_SKIN)} brands")
    print(f"COLOR : {len(COMPETITORS_COLOR)} brands")
    print(f"DEVICE: {len(COMPETITORS_DEVICE)} brands")
    print(f"TOTAL : {len(ALL_COMPETITORS)} brand entries")
