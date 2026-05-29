// 타사 신상품 대시보드 ─ 데이터 + 랭킹 + 방향성 분석 + 필터
(() => {
  const DATA_URL = './data/new_products.json';
  const DIRECTION_URL = './data/_direction.json';
  const CAT_LABEL = { skin: '스킨케어', color: '색조', device: 'ETC' };
  const KIND_CLASS = { '신제품': 'new', '신규 색상': 'newcolor', '리뉴얼': 'renewal' };

  // 자사 4브랜드 — 카테고리별 매핑 (대시보드 자사 액션 카드용)
  const SELF_BRANDS = {
    skin:  ['BOH (바이오힐보)', '브링그린'],
    color: ['웨이크메이크', '컬러그램'],
  };

  const state = {
    raw: null,
    direction: null,
    rows: [],
    filtered: [],
    catFilter: 'all',
    kindFilter: 'all',
    brandFilter: 'all',
    q: '',
    dcat: 'skin',
  };

  // ─── Helpers ────────────────────────────────────────────
  const $  = (s) => document.querySelector(s);
  const $$ = (s) => Array.from(document.querySelectorAll(s));
  const fmt = (n) => (n == null ? '-' : '¥' + Number(n).toLocaleString('ja-JP'));
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  // ─── Load ───────────────────────────────────────────────
  async function load() {
    try {
      const res = await fetch(DATA_URL, { cache: 'no-cache' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      state.raw = await res.json();
    } catch (e) {
      $('#meta-line').textContent = `데이터 로드 실패: ${e.message}. crawler 실행 필요.`;
      throw e;
    }
    try {
      const dres = await fetch(DIRECTION_URL, { cache: 'no-cache' });
      if (dres.ok) state.direction = await dres.json();
    } catch (e) { /* direction은 있으면 좋고 없어도 됨 */ }

    state.rows = [];
    for (const cat of ['skin', 'color', 'device']) {
      for (const r of (state.raw.categories?.[cat] ?? [])) {
        state.rows.push({ ...r, _cat: cat });
      }
    }
    state.filtered = state.rows;

    renderMeta();
    renderSummary();
    renderDirection();
    renderInsights();
    renderBrandSelect();
    renderSuspectList();
    bindFilters();
    applyFilters();
  }

  // ─── Meta line ──────────────────────────────────────────
  function renderMeta() {
    const ts = state.raw.last_updated || '-';
    const stats = state.raw.stats || {};
    $('#meta-line').textContent =
      `${ts.slice(0, 10)} ${ts.slice(11, 19)} JST · ` +
      `총 ${stats.total_new_products || 0}건 ` +
      `(스킨 ${stats.skin?.new_products || 0} / 색조 ${stats.color?.new_products || 0} / ETC ${stats.device?.new_products || 0})`;
    $('#footer-ts').textContent = ts;
  }

  // ─── Summary cards (수치 + 해석) ────────────────────────
  function renderSummary() {
    const stats = state.raw.stats || {};
    const total = stats.total_new_products || 0;
    const skin = stats.skin?.new_products || 0;
    const color = stats.color?.new_products || 0;
    const device = stats.device?.new_products || 0;

    // 평균 할인율 (신상품 중 할인 적용된 것)
    const discounts = state.rows.map(r => r['할인율%']).filter(d => d != null && d > 0);
    const avgDisc = discounts.length ? Math.round(discounts.reduce((a, b) => a + b, 0) / discounts.length) : 0;
    const maxDisc = discounts.length ? Math.max(...discounts) : 0;

    // 가장 활발한 브랜드 (신상품 수 Top)
    const brandCount = {};
    state.rows.forEach(r => { brandCount[r['브랜드']] = (brandCount[r['브랜드']] || 0) + 1; });
    const topBrand = Object.entries(brandCount).sort((a, b) => b[1] - a[1])[0];

    // 평균 판매가
    const prices = state.rows.map(r => r['판매가']).filter(p => p != null);
    const avgPrice = prices.length ? Math.round(prices.reduce((a, b) => a + b, 0) / prices.length) : 0;

    const cards = [
      {
        label: '신상품 합계 (30일)',
        value: total,
        interp: `스킨 ${skin}건 · 색조 ${color}건 · ETC ${device}건 — ` +
                (device === 0 ? '<span class="accent">디바이스 셀러 slug 누락으로 0건.</span> 운영팀에서 정식 slug 확보 필요'
                              : `디바이스 ${device}건 포함`)
      },
      {
        label: '최다 신상품 브랜드',
        value: topBrand ? topBrand[0] : '-',
        interp: topBrand
          ? `${topBrand[1]}건 출시 — 카테고리 공세 강도 1위. <span class="accent">자사 동일 카테고리 라인 비교 검토</span>`
          : '데이터 없음'
      },
      {
        label: '평균 판매가',
        value: fmt(avgPrice),
        interp: prices.length
          ? `${prices.length}개 신상품 기준. 일본 K-뷰티 진입가 ¥1,500~3,000대가 주류이므로 <span class="accent">자사 신제품 가격대 정합성 점검</span>`
          : '-'
      },
      {
        label: '평균 할인율',
        value: avgDisc + '%',
        interp: discounts.length
          ? `신상품 ${discounts.length}건이 출시 동시 할인. 최대 ${maxDisc}%. <span class="accent">${avgDisc >= 30 ? '시즌 캠페인(메가와리) 임박 신호' : '평시 신상 마케팅 강도'}</span>`
          : '할인 미적용 신상품만'
      },
    ];

    $('#summary-grid').innerHTML = cards.map(c => `
      <div class="card">
        <div class="label">${esc(c.label)}</div>
        <div class="value">${esc(c.value)}</div>
        <div class="interp">${c.interp}</div>
      </div>
    `).join('');
  }

  // ─── Direction (다음 상품 방향성) ───────────────────────
  function renderDirection() {
    const sec = $('#direction-section');
    if (!state.direction) {
      sec.style.display = 'none';
      return;
    }
    $$('#direction-section .dtab').forEach(b =>
      b.addEventListener('click', () => {
        $$('#direction-section .dtab').forEach(x => x.classList.remove('active'));
        b.classList.add('active');
        state.dcat = b.dataset.dcat;
        renderDirectionContent();
      }));
    renderDirectionContent();
  }

  function renderDirectionContent() {
    const root = $('#direction-content');
    const d = state.direction;
    if (state.dcat === 'skin') {
      const s = d.skin;
      const selfBrand = SELF_BRANDS.skin.join(' · ');
      root.innerHTML = `
        ${trendCard('🧪 핫 성분', `자사(${selfBrand}) 차기 신제품 성분 1순위 후보`, s.ingredients, true)}
        ${trendCard('💧 핫 제형', `토너 vs 세럼 vs 크림 — 어떤 제형으로 갈 것인가`, s.formulations)}
        ${trendCard('🎯 핫 효능 카테고리', `진정/수분/미백/안티에이징 중 어디로 갈 것인가`, s.concerns)}
      `;
    } else if (state.dcat === 'color') {
      const c = d.color;
      const selfBrand = SELF_BRANDS.color.join(' · ');
      root.innerHTML = `
        ${trendCard('💄 핫 카테고리', `자사(${selfBrand}) 차기 메이크업 SKU — 립/아이/베이스 어디로`, c.categories, true)}
        ${trendCard('✨ 핫 제형', `매트 vs 글로시 vs 시머 — 질감 트렌드`, c.formulations)}
        ${trendCard('🎨 핫 색 계열', `누드·핑크·베리·코랄·브라운 중 컬렉션 메인 색 결정`, c.color_families)}
        ${shadeReleaseCard(c.shade_releases)}
      `;
    } else if (state.dcat === 'actions') {
      const acts = d.self_action || [];
      root.innerHTML = `<div style="grid-column: 1 / -1;">${
        acts.map(a => `
          <div class="action-card">
            <div class="action-brand">${esc(a.for_brand)}</div>
            <div class="action-trend"><span class="action-cat">${esc(a.category)}</span>${esc(a.trend)}</div>
            <div class="action-evidence">📊 ${esc(a.evidence)}</div>
            <div class="action-do">→ ${esc(a.action)}</div>
          </div>
        `).join('')
      }</div>`;
    }
  }

  function trendCard(title, subtitle, items, showExamples) {
    if (!items || items.length === 0) {
      return `<div class="trend-card"><div class="trend-header"><span class="trend-title">${title}</span></div><p style="color:#9ca3af;font-size:12px">데이터 부족</p></div>`;
    }
    return `
      <div class="trend-card">
        <div class="trend-header">
          <span class="trend-title">${title}</span>
          <span class="trend-meta">${items.length}종</span>
        </div>
        <div class="trend-meta" style="margin-bottom:6px">${subtitle}</div>
        <ul>${items.slice(0, 8).map(it => `
          <li>
            <span>
              <span class="trend-name">${esc(it.name)}</span>
              ${it.brands_count ? `<span class="trend-sub">${it.brands_count}개 브랜드</span>` : ''}
            </span>
            <span class="trend-count">${it.count}건</span>
          </li>
          ${showExamples && it.examples && it.examples.length ? `
            <details>
              <summary>예시 ${it.examples.length}건</summary>
              <ul>${it.examples.slice(0, 3).map(e =>
                `<li>${esc(e.brand)} — ${esc(e.title)}</li>`
              ).join('')}</ul>
            </details>
          ` : ''}
        `).join('')}</ul>
      </div>
    `;
  }

  function shadeReleaseCard(shades) {
    if (!shades || shades.length === 0) return '';
    const avg = Math.round(shades.reduce((a, b) => a + b.shades, 0) / shades.length);
    return `
      <div class="trend-card">
        <div class="trend-header">
          <span class="trend-title">🌈 색조 호수 출시 패턴</span>
          <span class="trend-meta">평균 ${avg}색</span>
        </div>
        <div class="trend-meta" style="margin-bottom:6px">컬렉션 단위(10+색) vs 단품(1-3색) 전략 결정용</div>
        <ul>${shades.slice(0, 6).map(s => `
          <li>
            <span class="trend-name">${esc(s.brand)} — ${esc(s.title.slice(0, 30))}…</span>
            <span class="trend-count">${s.shades}색</span>
          </li>
        `).join('')}</ul>
      </div>
    `;
  }

  // ─── Insights (자동 생성) ───────────────────────────────
  function renderInsights() {
    const rows = state.rows;
    const insights = [];

    // ① 카테고리 편중
    const skinCnt = rows.filter(r => r._cat === 'skin').length;
    const colorCnt = rows.filter(r => r._cat === 'color').length;
    if (skinCnt + colorCnt > 0) {
      const skinPct = Math.round(100 * skinCnt / (skinCnt + colorCnt));
      const lean = skinPct >= 65 ? '스킨케어 신상품이 압도적' : skinPct <= 35 ? '색조 신상품이 압도적' : '스킨/색조 균형';
      insights.push({
        level: skinPct >= 65 || skinPct <= 35 ? 'mid' : 'low',
        title: `📊 카테고리 출시 편중 — ${lean}`,
        body: `최근 30일 경쟁사 신상품 ${skinCnt + colorCnt}건 중 스킨케어 ${skinCnt}건(${skinPct}%) · 색조 ${colorCnt}건(${100 - skinPct}%).`,
        action: skinPct >= 65
          ? '→ 자사 BOH/브링그린 신제품 출시 타이밍이 경쟁 적은 색조 슬롯과 겹치지 않게 점검'
          : skinPct <= 35
          ? '→ 자사 웨이크메이크/컬러그램이 색조 레드오션에 들어가는지 확인. 차별화 컨셉 강화'
          : '→ 양쪽 모두 활발. 자사 신상 일정과 충돌 셀러 확인'
      });
    }

    // ② 신규 색상 vs 신제품 비율 (색조 한정)
    const colorRows = rows.filter(r => r._cat === 'color');
    if (colorRows.length > 0) {
      const newColors = colorRows.filter(r => r['구분'] === '신규 색상').length;
      const newColorPct = Math.round(100 * newColors / colorRows.length);
      if (newColorPct >= 40) {
        insights.push({
          level: 'mid',
          title: `🎨 색조: 신규 색상 추가가 ${newColorPct}% — 라인 확장 트렌드`,
          body: `색조 신상품 ${colorRows.length}건 중 ${newColors}건이 기존 제품의 색상 추가 출시. 신제품 런칭보다 안전한 SKU 확장 전략.`,
          action: '→ 자사 컬러그램/웨이크메이크 베스트셀러 라인의 색상 확장(시즌 한정 등) 우선 검토'
        });
      }
    }

    // ③ 리뉴얼 트렌드
    const renewals = rows.filter(r => r['구분'] === '리뉴얼');
    if (renewals.length >= 5) {
      const renewalBrands = [...new Set(renewals.map(r => r['브랜드']))].slice(0, 5).join('·');
      insights.push({
        level: 'mid',
        title: `🔁 리뉴얼 ${renewals.length}건 — 처방/패키지 업그레이드 라운드`,
        body: `${renewalBrands} 등이 동시 리뉴얼. 1세대 → 2세대 처방 교체 사이클 진입 신호.`,
        action: '→ 자사 베스트셀러 처방·패키지 점검 시점 — 경쟁사가 먼저 움직임'
      });
    }

    // ④ 최저가 신상품 (미끼상품 가설)
    const lowest = rows.filter(r => r['판매가'] != null).sort((a, b) => a['판매가'] - b['판매가']).slice(0, 3);
    if (lowest.length > 0 && lowest[0]['판매가'] < 1500) {
      insights.push({
        level: 'high',
        title: `💴 ¥${lowest[0]['판매가'].toLocaleString()} 최저가 신상품 — ${lowest[0]['브랜드']}`,
        body: `${esc(lowest[0]['제품명'].slice(0, 60))}. 1,500엔 미만 신상은 ${lowest[0]._cat === 'color' ? '신규 유입용 미끼' : '리피트 유도 단가'} 전략 가능성.`,
        action: '→ 자사 진입 가격대(¥1,500~) 대비 격차. 미끼 SKU 1종 기획 검토'
      });
    }

    // ⑤ 고가 신상품 (프리미엄 진입 신호)
    const expensive = rows.filter(r => r['판매가'] != null && r['판매가'] >= 4000);
    if (expensive.length >= 3) {
      const expBrands = [...new Set(expensive.map(r => r['브랜드']))].slice(0, 3).join('·');
      insights.push({
        level: 'mid',
        title: `💎 ¥4,000+ 프리미엄 신상품 ${expensive.length}건 — ${expBrands}`,
        body: `K-뷰티 객단가 천장 ¥4,000을 넘는 신상품 다수. 매스 → 프리미엄 라인 확장 본격화.`,
        action: '→ 자사 프리미엄 라인업(BOH 시그니처 등) 가격 정합성 비교. 객단가 상향 룸 확인'
      });
    }

    // ⑥ 高할인 출시 (메가와리 임박 신호)
    const heavyDisc = rows.filter(r => r['할인율%'] != null && r['할인율%'] >= 30);
    if (heavyDisc.length >= 5) {
      insights.push({
        level: 'high',
        title: `⚡ 출시 동시 30%+ 할인 ${heavyDisc.length}건 — 메가와리 가격 사전 정렬`,
        body: `신상품임에도 정상가 ${Math.min(...heavyDisc.map(r => r['할인율%']))}~${Math.max(...heavyDisc.map(r => r['할인율%']))}% 할인 적용 출시. Qoo10 메가와리(Q2/Q3) 임박 신호.`,
        action: '→ 자사 다음 메가와리 신청 상태 확인. 신제품 할인폭 사전 시뮬'
      });
    }

    // ⑦ 신상 → 랭킹 진입 SKU (검증된 신상)
    const ranked = rows.filter(r => r['랭킹'] != null).sort((a, b) => a['랭킹'] - b['랭킹']);
    if (ranked.length >= 1) {
      const top3 = ranked.slice(0, 3);
      insights.push({
        level: 'high',
        title: `🔥 신상 ${ranked.length}건이 Qoo10 뷰티 Top 200 진입 — 시장 검증된 SKU`,
        body: `최상위: ${top3.map(r => `#${r['랭킹']} ${esc(r['브랜드'])} ${esc((r['제품명']||'').slice(0,28))}`).join(' / ')}. 출시 직후 랭킹 진입 = 광고+자연유입 모두 우호적.`,
        action: '→ 이 SKU들의 가격대·제형·소구 키워드 자사 차기 신제품에 벤치마크'
      });
    }

    // ⑧ 셀러 누락
    const suspectCount = (state.raw.suspect_slugs || []).length;
    if (suspectCount > 0) {
      const skinSus = state.raw.suspect_slugs.filter(s => s.category === 'skin').length;
      const colorSus = state.raw.suspect_slugs.filter(s => s.category === 'color').length;
      const devSus = state.raw.suspect_slugs.filter(s => s.category === 'device').length;
      insights.push({
        level: suspectCount >= 10 ? 'high' : 'mid',
        title: `⚠ ${suspectCount}개 셀러 slug 오류 — 핵심 경쟁사 누락 가능성`,
        body: `Qoo10 셀러 slug 불일치로 ${suspectCount}개 브랜드 미수집 (스킨 ${skinSus} / 색조 ${colorSus} / 디바이스 ${devSus}). 페리페라·클리오·힌스·페리페라·믹순·에스트라 등 주요 브랜드 포함 가능.`,
        action: '→ 운영팀이 Qoo10 셀러센터에서 정식 slug 확보 → crawler/_brands.py 업데이트'
      });
    }

    // 정렬: high → mid → low
    const order = { high: 0, mid: 1, low: 2 };
    insights.sort((a, b) => order[a.level] - order[b.level]);

    $('#insights-list').innerHTML = insights.map(ins => `
      <div class="insight ${ins.level}">
        <div class="insight-title">${ins.title}</div>
        <div class="insight-body">${ins.body}</div>
        <span class="insight-action">${ins.action}</span>
      </div>
    `).join('') || '<div class="insight low"><div class="insight-body">데이터 부족 — 크롤러 실행 후 다시 확인하세요.</div></div>';
  }

  // ─── Brand dropdown ─────────────────────────────────────
  function renderBrandSelect() {
    const brands = [...new Set(state.rows.map(r => r['브랜드']))].sort();
    const sel = $('#brand-select');
    brands.forEach(b => {
      const opt = document.createElement('option');
      opt.value = b; opt.textContent = b;
      sel.appendChild(opt);
    });
  }

  // ─── Suspect slugs section ──────────────────────────────
  function renderSuspectList() {
    const sl = state.raw.suspect_slugs || [];
    $('#suspect-list').innerHTML = sl.length === 0
      ? '<li>(없음 — 모든 셀러 정상 수집)</li>'
      : sl.map(s => `<li><strong>${esc(s.kr_label)}</strong> (현재 slug: <code>${esc(s.slug)}</code>) — ${esc(s.category)} · ${esc(s.reason)}</li>`).join('');
  }

  // ─── Filters ────────────────────────────────────────────
  function bindFilters() {
    $$('#category-chips .chip').forEach(b =>
      b.addEventListener('click', () => {
        $$('#category-chips .chip').forEach(x => x.classList.remove('active'));
        b.classList.add('active');
        state.catFilter = b.dataset.cat;
        applyFilters();
      }));
    $$('#kind-chips .chip').forEach(b =>
      b.addEventListener('click', () => {
        $$('#kind-chips .chip').forEach(x => x.classList.remove('active'));
        b.classList.add('active');
        state.kindFilter = b.dataset.kind;
        applyFilters();
      }));
    $('#brand-select').addEventListener('change', e => { state.brandFilter = e.target.value; applyFilters(); });
    $('#q').addEventListener('input', e => { state.q = e.target.value.trim().toLowerCase(); applyFilters(); });
    $('#copy-tsv').addEventListener('click', copyTSV);
  }

  function applyFilters() {
    state.filtered = state.rows.filter(r => {
      if (state.catFilter !== 'all' && r._cat !== state.catFilter) return false;
      if (state.kindFilter !== 'all' && r['구분'] !== state.kindFilter) return false;
      if (state.brandFilter !== 'all' && r['브랜드'] !== state.brandFilter) return false;
      if (state.q) {
        const hay = (r['제품명'] + ' ' + (r['_meta']?.new_markers || []).join(' ')).toLowerCase();
        if (!hay.includes(state.q)) return false;
      }
      return true;
    });
    $('#result-count').textContent = `${state.filtered.length}건`;
    renderTable();
  }

  // ─── Table ──────────────────────────────────────────────
  function renderTable() {
    const tbody = $('#products-tbody');
    if (state.filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;padding:32px;color:#9ca3af">조건 일치 신상품 없음</td></tr>';
      return;
    }
    tbody.innerHTML = state.filtered.map(r => {
      const kindCls = KIND_CLASS[r['구분']] || 'new';
      const markers = (r['_meta']?.new_markers || []).slice(0, 3)
        .map(m => `<span class="marker-tag">${esc(m)}</span>`).join('');
      const priceCell = r['타임세일가'] != null
        ? `<div class="price-orig">${fmt(r['참고가'])}</div><div>${fmt(r['타임세일가'])}</div>`
        : fmt(r['판매가']);
      const rank = r['랭킹'];
      let rankCell = '<span class="rank-badge unranked">Top200 외</span>';
      if (rank != null) {
        const cls = rank <= 10 ? 'top10' : rank <= 50 ? 'top50' : 'top200';
        rankCell = `<span class="rank-badge ${cls}">#${rank}</span>`;
      }
      const rs = r['리뷰_점수']; const rc = r['리뷰_수'];
      const reviewCell = (rs != null || rc != null)
        ? `<span class="review-score">★${rs ?? '-'}</span> <span class="review-count">(${rc ?? 0})</span>`
        : '-';
      return `
        <tr>
          <td><span class="cat-badge">${esc(CAT_LABEL[r._cat])}</span></td>
          <td class="brand-cell">${esc(r['브랜드'])}</td>
          <td>${r['이미지'] ? `<img class="thumb" src="${esc(r['이미지'])}" loading="lazy" alt="">` : '-'}</td>
          <td class="title-cell"><a href="${esc(r['링크'])}" target="_blank" rel="noopener">${esc(r['제품명'] || '-')}</a></td>
          <td><span class="kind-badge ${kindCls}">${esc(r['구분'])}</span></td>
          <td class="price-cell">${fmt(r['참고가'])}</td>
          <td class="price-cell">${priceCell}</td>
          <td class="price-cell">${r['할인율%'] != null ? `<span class="discount-pct">${r['할인율%']}%</span>` : '-'}</td>
          <td>${rankCell}</td>
          <td class="review-cell">${reviewCell}</td>
          <td class="markers-cell">${markers || '-'}</td>
          <td><a href="${esc(r['링크'])}" target="_blank" rel="noopener">열기 ↗</a></td>
        </tr>
      `;
    }).join('');
  }

  // ─── TSV copy (시트 붙여넣기용) ─────────────────────────
  function copyTSV() {
    const headers = ['카테고리', '브랜드', '런칭일', '구분', '이미지', '제품명',
                     '참고가', '판매가', '타임세일가', '최종할인가', '할인율%',
                     '소구포인트', '출시_홋수', '효과', '메인_성분', '기능',
                     '비고', '링크', '랭킹', '랭킹_카테고리', '리뷰_점수', '리뷰_수',
                     '주요_후기', '프로모션'];
    const lines = [headers.join('\t')];
    for (const r of state.filtered) {
      lines.push(headers.map(h => {
        const v = h === '카테고리' ? CAT_LABEL[r._cat] : r[h];
        return v == null ? '' : String(v).replace(/[\t\r\n]/g, ' ');
      }).join('\t'));
    }
    navigator.clipboard.writeText(lines.join('\n')).then(
      () => { const btn = $('#copy-tsv'); const orig = btn.textContent; btn.textContent = '✓ 복사완료 ' + state.filtered.length + '행'; setTimeout(() => btn.textContent = orig, 2000); },
      () => alert('복사 실패')
    );
  }

  load();
})();
