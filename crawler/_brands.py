"""경쟁사 브랜드 사전 — Qoo10.jp 매핑.

표시명 룰:
  - 영문 공식 브랜드명 그대로 사용 (번역/카타카나 변환 X)
  - 예: rom&nd, PERIPERA, COSRX (롬앤·페리페라·코스알엑스 X)
  - 한국어/카타카나 표기는 'keywords' 검색 매칭용으로만 보존

스키마:
    {
        "label": "공식 표시명 (영문)",
        "shop_slugs": ["qoo10 셀러 URL slug"],
        "keywords": ["검색 / brand 매칭용 다국어 표기"],
    }
"""

# ─── 기초 (스킨케어) ──────────────────────────────────────
COMPETITORS_SKIN = {
    "anua":          {"label": "Anua",          "shop_slugs": ["anua"],            "keywords": ["anua", "アヌア"]},
    "medicube":      {"label": "MEDICUBE",      "shop_slugs": ["medicube"],        "keywords": ["medicube", "メディキューブ"]},
    "dalba":         {"label": "d'Alba",        "shop_slugs": ["dalba"],           "keywords": ["dalba", "d'alba", "ダルバ"]},
    "vt":            {"label": "VT",            "shop_slugs": ["vtcosmetics"],     "keywords": [" VT ", "VTコス", "VTcosmetics"]},
    "skin1004":      {"label": "SKIN1004",      "shop_slugs": ["skin1004japan"],   "keywords": ["skin1004", "スキン1004"]},
    "cosrx":         {"label": "COSRX",         "shop_slugs": ["cosrx"],           "keywords": ["cosrx", "コスアールエックス"]},
    "kopher":        {"label": "Kopher",        "shop_slugs": ["kopher"],          "keywords": ["kopher", "コーファー"]},
    "manyo":         {"label": "MANYO",         "shop_slugs": ["manyofactory"],    "keywords": ["manyo", "マニョ", "魔女工場"]},
    "aestura":       {"label": "AESTURA",       "shop_slugs": ["aestura"],         "keywords": ["aestura", "エストラ"]},
    "biodance":      {"label": "Biodance",      "shop_slugs": ["biodance"],        "keywords": ["biodance", "バイオダンス"]},
    "numbuzin":      {"label": "numbuzin",      "shop_slugs": ["numbuzin"],        "keywords": ["numbuzin", "ナンバーズイン"]},
    "tirtir":        {"label": "TIRTIR",        "shop_slugs": ["tirtir"],          "keywords": ["tirtir", "ティルティル"]},
    "abib":          {"label": "ABIB",          "shop_slugs": ["abib"],            "keywords": ["abib", "アビブ"]},
    "tocobo":        {"label": "TOCOBO",        "shop_slugs": ["tocobo"],          "keywords": ["tocobo"]},
    "isntree":       {"label": "isntree",       "shop_slugs": ["isntree"],         "keywords": ["isntree", "イズントゥリー"]},
    "mixsoon":       {"label": "mixsoon",       "shop_slugs": ["mixsoon"],         "keywords": ["mixsoon", "ミクスーン"]},
    "mediheal":      {"label": "MEDIHEAL",      "shop_slugs": ["medihealofficial"],"keywords": ["mediheal", "メディヒール"]},
    "haruharu":      {"label": "HARUHARU",      "shop_slugs": ["haruharu"],        "keywords": ["haruharu wonder", "haruharu", "ハルハル"]},
    "samu":          {"label": "SAMU",          "shop_slugs": ["samu"],            "keywords": ["samu", "サミュ"]},
    "ongredients":   {"label": "ONGREDIENTS",   "shop_slugs": ["ongredients"],     "keywords": ["ongredients", "オングレディエンツ"]},
    "beautyofjoseon":{"label": "Beauty of Joseon", "shop_slugs": ["beautyofjoseon"], "keywords": ["beauty of joseon", "ビューティーオブジョソン"]},
    "torriden":      {"label": "TORRIDEN",      "shop_slugs": ["torriden"],        "keywords": ["torriden", "トリデン"]},
    "drjart":        {"label": "Dr.Jart+",      "shop_slugs": ["drjart"],          "keywords": ["dr.jart", "ドクタージャルト"]},
    # 미입점 PYUNKANG YUL/Round Lab/OLENS 대체 — Qoo10 JP 상위 K-뷰티 스킨
    "laneige":       {"label": "LANEIGE",       "shop_slugs": ["laneige"],         "keywords": ["laneige", "ラネージュ"]},
    "kahi":          {"label": "KAHI",          "shop_slugs": ["kahi"],            "keywords": ["kahi", "カヒ"]},
    "innisfree":     {"label": "innisfree",     "shop_slugs": ["innisfree"],       "keywords": ["innisfree", "イニスフリー"]},
    "iunik":         {"label": "iUNIK",         "shop_slugs": ["iunik"],           "keywords": ["iunik", "アイユニーク"]},
    "axisy":         {"label": "Axis-Y",        "shop_slugs": ["axisy"],           "keywords": ["axis-y", "axisy", "アクシスワイ"]},
    # 일본 현지 스킨 (가격대 겹치는 매스 브랜드 위주)
    "hadalabo":      {"label": "Hada Labo",     "shop_slugs": ["hadalabo"],        "keywords": ["肌ラボ", "hadalabo", "hada labo"]},
    "sekkisei":      {"label": "Sekkisei",      "shop_slugs": ["kose-cosmeport"],  "keywords": ["雪肌精", "sekkisei", "セッキセイ"]},
    "minon":         {"label": "MINON",         "shop_slugs": ["minon"],           "keywords": ["minon", "ミノン"]},
    "curel":         {"label": "Curél",         "shop_slugs": ["curel"],           "keywords": ["curel", "キュレル"]},
    "haba":          {"label": "HABA",          "shop_slugs": ["haba"],            "keywords": ["haba", "ハーバー"]},
    "fancl":         {"label": "FANCL",         "shop_slugs": ["fancl"],           "keywords": ["fancl", "ファンケル"]},
}

# ─── 색조 (color) ────────────────────────────────────────
COMPETITORS_COLOR = {
    "fwee":         {"label": "fwee",          "shop_slugs": ["fwee"],         "keywords": ["fwee", "プゥイ"]},
    "celimax":      {"label": "celimax",       "shop_slugs": ["celimax"],      "keywords": ["celimax", "セリマックス"]},
    "romand":       {"label": "rom&nd",        "shop_slugs": ["romand"],       "keywords": ["romand", "rom&nd", "ロムアンド"]},
    "abouttone":    {"label": "ABOUT TONE",    "shop_slugs": ["abouttone"],    "keywords": ["about tone", "アバウトトーン"]},
    "dasique":      {"label": "DASIQUE",       "shop_slugs": ["dasique"],      "keywords": ["dasique", "デイジーク"]},
    "peripera":     {"label": "PERIPERA",      "shop_slugs": ["peripera"],     "keywords": ["peripera", "ペリペラ"]},
    "banilaco":     {"label": "banila co",     "shop_slugs": ["banilaco"],     "keywords": ["banila co", "バニラコ"]},
    "amuse":        {"label": "AMUSE",         "shop_slugs": ["amuse"],        "keywords": ["amuse", "アミューズ"]},
    "laka":         {"label": "Laka",          "shop_slugs": ["laka"],         "keywords": ["laka", "ラカ"]},
    "dinto":        {"label": "DINTO",         "shop_slugs": ["dinto"],        "keywords": ["dinto", "ディント"]},
    "23yearsold":   {"label": "23 years old",  "shop_slugs": ["23yearsold"],   "keywords": ["23 years old", "23yearsold"]},
    "clio":         {"label": "CLIO",          "shop_slugs": ["clio"],         "keywords": ["clio", "クリオ"]},
    "hince":        {"label": "hince",         "shop_slugs": ["hince"],        "keywords": ["hince", "ヒンス"]},
    "lilybyred":    {"label": "lilybyred",     "shop_slugs": ["lilybyred"],    "keywords": ["lilybyred", "リリーバイレッド"]},
    "bbia":         {"label": "BBIA",          "shop_slugs": ["bbia"],         "keywords": ["bbia", "ピア"]},
    "millefee":     {"label": "MilleFée",      "shop_slugs": ["millefee"],     "keywords": ["millefee", "MilleFée", "ミルフィー"]},
    "olens":        {"label": "OLENS",         "shop_slugs": ["olens"],        "keywords": ["olens", "オーレンズ"]},
    "etude":        {"label": "ETUDE",         "shop_slugs": ["etude"],        "keywords": ["etude", "エチュード"]},
    "ohora":        {"label": "ohora",         "shop_slugs": ["ohora"],        "keywords": ["ohora", "オホーラ"]},
    "age20s":       {"label": "AGE20'S",       "shop_slugs": ["age20s"],       "keywords": ["age20", "エイジ20"]},
    "3ce":          {"label": "3CE",           "shop_slugs": ["3ce"],          "keywords": ["3ce", "3CE", "スリーシーイー"]},
    "2aN":          {"label": "2aN",           "shop_slugs": ["2anjp", "2an"], "keywords": ["2an", "2aN", "ツーエーエヌ"]},
    # OLENS 대체 — Qoo10 JP 상위 K-뷰티 색조
    "iope":         {"label": "IOPE",          "shop_slugs": ["iope"],         "keywords": ["iope", "アイオペ"]},
    "etudehouse":   {"label": "ETUDE HOUSE",   "shop_slugs": ["etudehouse"],   "keywords": ["etude house", "エチュードハウス"]},
    # 일본 현지 색조 (canmake 등) — 가격대·채널 겹치는 매스 브랜드 중심
    "canmake":      {"label": "canmake",       "shop_slugs": ["canmake"],      "keywords": ["canmake", "キャンメイク"]},
    "cezanne":      {"label": "CEZANNE",       "shop_slugs": ["cezanne"],      "keywords": ["cezanne", "セザンヌ"]},
    "kate":         {"label": "KATE",          "shop_slugs": ["kate-tokyo"],   "keywords": ["kate tokyo", "ケイト"]},
    "visee":        {"label": "Visée",         "shop_slugs": ["visee"],        "keywords": ["visee", "ヴィセ"]},
    "excel":        {"label": "excel",         "shop_slugs": ["excel"],        "keywords": ["excel makeup", "エクセル"]},
    "kissme":       {"label": "KissMe",        "shop_slugs": ["kissme"],       "keywords": ["kissme", "キスミー", "ヒロインメイク"]},
    "integrate":    {"label": "INTEGRATE",     "shop_slugs": ["integrate"],    "keywords": ["integrate", "インテグレート"]},
    "cipicipi":     {"label": "CipiCipi",      "shop_slugs": ["cipicipi"],     "keywords": ["cipicipi", "シピシピ"]},
    "opera":        {"label": "OPERA",         "shop_slugs": ["opera"],        "keywords": ["opera lip", "オペラ リップ"]},
}

# ─── ETC: 뷰티 디바이스 / 미용기기 ─────────────────────────
COMPETITORS_DEVICE = {
    "medicube_ager":  {"label": "MEDICUBE AGE-R", "shop_slugs": ["medicube"],     "keywords": ["age-r", "ager", "エイジアール"]},
    "ya-man":         {"label": "YA-MAN",         "shop_slugs": ["ya-man"],       "keywords": ["ya-man", "ヤーマン"]},
    "mtg":            {"label": "MTG",            "shop_slugs": ["mtg-online"],   "keywords": ["MTG", "リファ", "ReFa"]},
    "panasonic_beauty":{"label": "Panasonic Beauty","shop_slugs": ["panasonic-beauty"],"keywords": ["panasonic beauty", "パナソニック ビューティー"]},
    "newaskin":       {"label": "Newa",           "shop_slugs": ["newaskin"],     "keywords": ["newa", "ニューア"]},
    "denba":          {"label": "DENBA",          "shop_slugs": ["denba"],        "keywords": ["denba", "デンバ"]},
    "tripollar":      {"label": "TriPollar",      "shop_slugs": ["tripollar"],    "keywords": ["tripollar", "トリポラ"]},
    "magnitone":      {"label": "Magnitone",      "shop_slugs": ["magnitone"],    "keywords": ["magnitone"]},
    "beautylift":     {"label": "BeautyLift",     "shop_slugs": ["beautylift"],   "keywords": ["beautylift"]},
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
                    "category": meta["category"],
                }
    return None


def get_all_shops_by_category() -> dict:
    """카테고리 → [{slug, key, label}] 매핑. (kr_label 폐기 — label 공식명만 사용)"""
    out: dict = {"skin": [], "color": [], "device": []}
    for k, meta in ALL_COMPETITORS.items():
        for ss in meta["shop_slugs"]:
            out[meta["category"]].append({
                "slug": ss,
                "key": k,
                "label": meta["label"],
                "kr_label": meta["label"],  # backward compat — 동일값
            })
    return out


if __name__ == "__main__":
    print(f"SKIN  : {len(COMPETITORS_SKIN)} brands")
    print(f"COLOR : {len(COMPETITORS_COLOR)} brands")
    print(f"DEVICE: {len(COMPETITORS_DEVICE)} brands")
    print(f"TOTAL : {len(ALL_COMPETITORS)} brand entries")
