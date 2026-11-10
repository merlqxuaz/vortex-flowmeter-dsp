// State
let pagesData = [];
let tocData = [];
let ocrData = [];
let figuresData = [];
let figuresByPage = {};
let figuresByNum = {};
let formulasData = [];
let formulasByPage = {};
let formulasByNum = {};

let currentPageIndex = 0;
let currentTheme = localStorage.getItem('vortex_reader_theme') || 'light';
let currentFontSize = parseInt(localStorage.getItem('vortex_reader_fontsize') || '16', 10);
let currentView = localStorage.getItem('vortex_reader_view') || 'image';

// DOM Elements
const body = document.body;
const progressBar = document.getElementById('readProgressBar');
const currentChapterLabel = document.getElementById('currentChapterLabel');
const tocSidebar = document.getElementById('tocSidebar');
const tocOverlay = document.getElementById('tocOverlay');
const tocList = document.getElementById('tocList');
const tocFilterInput = document.getElementById('tocFilterInput');
const btnToggleToc = document.getElementById('btnToggleToc');
const btnCloseToc = document.getElementById('btnCloseToc');
const btnOpenTocEdge = document.getElementById('btnOpenTocEdge');
const pagesContainer = document.getElementById('pagesContainer');
const pageJumpInput = document.getElementById('pageJumpInput');
const btnPrevPage = document.getElementById('btnPrevPage');
const btnNextPage = document.getElementById('btnNextPage');
const textContentContainer = document.getElementById('textContentContainer');
const searchModal = document.getElementById('searchModal');
const btnSearch = document.getElementById('btnSearch');
const btnCloseSearch = document.getElementById('btnCloseSearch');
const searchInput = document.getElementById('searchInput');
const searchStatus = document.getElementById('searchStatus');
const searchResultsList = document.getElementById('searchResultsList');
const btnTheme = document.getElementById('btnTheme');
const btnFontInc = document.getElementById('btnFontInc');
const btnFontDec = document.getElementById('btnFontDec');

// Mobile Bottom Bar
const mBtnToc = document.getElementById('mBtnToc');
const mBtnSearch = document.getElementById('mBtnSearch');
const mBtnView = document.getElementById('mBtnView');
const mBtnTop = document.getElementById('mBtnTop');

// Lightbox Elements
const lightboxModal = document.getElementById('lightboxModal');
const lightboxImg = document.getElementById('lightboxImg');
const lightboxCaption = document.getElementById('lightboxCaption');
const btnCloseLightbox = document.getElementById('btnCloseLightbox');

// OCR Elements
const ocrPageSelect = document.getElementById('ocrPageSelect');
const ocrPreviewImg = document.getElementById('ocrPreviewImg');
const ocrCanvas = document.getElementById('ocrCanvas');
const ocrTimeBadge = document.getElementById('ocrTimeBadge');
const ocrLineCountBadge = document.getElementById('ocrLineCountBadge');
const ocrResultList = document.getElementById('ocrResultList');

// Init
async function init() {
  applyTheme(currentTheme);
  applyFontSize(currentFontSize);
  switchView(currentView);

  // Restore Desktop TOC collapsed preference
  if (window.innerWidth > 860) {
    const isCollapsed = localStorage.getItem('vortex_toc_collapsed') === 'true';
    if (isCollapsed) {
      tocSidebar.classList.add('collapsed');
    }
  }

  // Load core data
  try {
    const [pagesRes, tocRes, figsRes, formsRes] = await Promise.all([
      fetch('data/pages_data.json').then(r => r.json()),
      fetch('data/toc.json').then(r => r.json()),
      fetch('data/figures.json').then(r => r.json()).catch(() => []),
      fetch('data/formulas.json').then(r => r.json()).catch(() => [])
    ]);
    pagesData = pagesRes;
    tocData = tocRes;
    figuresData = figsRes || [];
    formulasData = formsRes || [];

    // Index figures
    figuresData.forEach(fig => {
      const pIdx = fig.page_index;
      if (!figuresByPage[pIdx]) figuresByPage[pIdx] = [];
      figuresByPage[pIdx].push(fig);
      figuresByNum[fig.num] = fig;
    });

    // Index formulas
    formulasData.forEach(eq => {
      const pIdx = eq.page_index;
      if (!formulasByPage[pIdx]) formulasByPage[pIdx] = [];
      formulasByPage[pIdx].push(eq);
      formulasByNum[eq.num] = eq;
    });

  } catch (err) {
    console.error('Failed to load pages, figures, or formulas data', err);
  }

  // Load OCR data
  try {
    const ocrRes = await fetch('data/ocr_samples.json').then(r => r.json());
    ocrData = ocrRes;
    initOcrShowcase();
  } catch (e) {
    console.warn('OCR data not yet available or failed to load', e);
  }

  renderToc();
  renderImageStream();
  renderTextStream();
  setupEvents();
  setupIntersectionObservers();
}

// TOC Functions (Opening / Closing)
function isMobile() {
  return window.innerWidth <= 860;
}

function openToc() {
  if (isMobile()) {
    tocSidebar.classList.add('open');
    tocOverlay.classList.add('active');
  } else {
    tocSidebar.classList.remove('collapsed');
    localStorage.setItem('vortex_toc_collapsed', 'false');
  }
  btnToggleToc.classList.add('active');
}

function closeToc() {
  if (isMobile()) {
    tocSidebar.classList.remove('open');
    tocOverlay.classList.remove('active');
  } else {
    tocSidebar.classList.add('collapsed');
    localStorage.setItem('vortex_toc_collapsed', 'true');
  }
  btnToggleToc.classList.remove('active');
}

function toggleToc() {
  if (isMobile()) {
    if (tocSidebar.classList.contains('open')) {
      closeToc();
    } else {
      openToc();
    }
  } else {
    if (tocSidebar.classList.contains('collapsed')) {
      openToc();
    } else {
      closeToc();
    }
  }
}

// Render TOC
function renderToc(filterText = '') {
  tocList.innerHTML = '';
  const filter = filterText.trim().toLowerCase();

  tocData.forEach((item) => {
    if (filter && !item.title.toLowerCase().includes(filter)) {
      return;
    }

    const a = document.createElement('a');
    a.className = `toc-item level-${item.level}`;
    a.dataset.pageIndex = item.pdf_page_index;
    a.innerHTML = `
      <span class="toc-title">${escapeHtml(item.title)}</span>
      <span class="toc-page-num">${item.book_page ? 'p.' + item.book_page : ''}</span>
    `;

    a.addEventListener('click', (e) => {
      e.preventDefault();
      scrollToPage(item.pdf_page_index);
      if (isMobile()) {
        closeToc();
      }
    });

    tocList.appendChild(a);
  });
}

// Render Image Stream
function renderImageStream() {
  pagesContainer.innerHTML = '';

  pagesData.forEach((page, idx) => {
    const card = document.createElement('div');
    card.className = 'page-card';
    card.id = `img-page-${idx}`;
    card.dataset.pageIndex = idx;

    card.innerHTML = `
      <div class="page-card-header">
        <span>第 ${idx + 1} 页 / 共 ${pagesData.length} 页</span>
        <span>${getChapterForPage(idx)}</span>
      </div>
      <div class="page-card-img-wrap">
        <img data-src="${page.image}" alt="Page ${idx + 1}" loading="lazy" />
      </div>
    `;

    pagesContainer.appendChild(card);
  });
}

// Header/footer noise filter
function isHeaderOrFooter(line) {
  const t = line.trim();
  if (/^[·\s]*\d+[·\s]*涡街流量计/.test(t)) return true;
  if (/^第\s*\d+\s*章.*[·\s]*\d+[·\s]*$/.test(t)) return true;
  if (/^[·\s]*\d+[·\s]*$/.test(t)) return true;
  if (/^\d+\s*·\s*涡街流量计/.test(t)) return true;
  return false;
}

// Clean and normalize inline variables and typography
function normalizeTypography(text) {
  return text
    .replace(//g, '=')
    .replace(//g, '…')
    .replace(//g, '×')
    .replace(/\b1v\b/g, 'v₁')
    .replace(/\b2v\b/g, 'v₂')
    .replace(/\b0b\b/g, 'b₀')
    .replace(/\b1b\b/g, 'b₁')
    .replace(/\bmb\b/g, 'b_m')
    .replace(/\b0a\b/g, 'a₀')
    .replace(/\b1a\b/g, 'a₁')
    .replace(/\bka\b/g, 'a_k')
    .replace(/\s+([，。！？；：、）】”])/g, '$1')
    .replace(/([（【“])\s+/g, '$1')
    .replace(/\s*，\s*/g, '，')
    .replace(/\s*。\s*/g, '。')
    .replace(/\s*；\s*/g, '；')
    .replace(/\s*：\s*/g, '：');
}

// Render Text Stream with Natural Paragraphs, Embedded Formulas and Figures
function renderTextStream() {
  textContentContainer.innerHTML = '';

  pagesData.forEach((page, idx) => {
    const block = document.createElement('article');
    block.className = 'text-page-block';
    block.id = `text-page-${idx}`;
    block.dataset.pageIndex = idx;

    const pageFigs = figuresByPage[idx] || [];
    const pageForms = formulasByPage[idx] || [];
    const renderedFigNums = new Set();
    const renderedFormNums = new Set();

    const rawLines = (page.text || '').split('\n');
    let bodyHtml = '';
    let currentPara = '';

    function flushPara() {
      if (!currentPara.trim()) return;
      const cleanPara = normalizeTypography(currentPara.trim());
      if (/^[①②③④⑤⑥⑦⑧⑨⑩]|^（[0-9]+）|^\([0-9]+\)/.test(cleanPara)) {
        bodyHtml += `<div class="list-step-item">${escapeHtml(cleanPara)}</div>`;
      } else {
        bodyHtml += `<p class="book-paragraph">${escapeHtml(cleanPara)}</p>`;
      }
      currentPara = '';
    }

    rawLines.forEach(line => {
      const lineTrim = line.trim();
      if (!lineTrim) {
        flushPara();
        return;
      }

      // 1. Skip page headers/footers
      if (isHeaderOrFooter(lineTrim)) return;

      // 2. Check for Formula Card match: line ending with (x.y.z)
      const mEq = lineTrim.match(/\((\s*\d+[\.\-]\d+(?:[\.\-]\d+)?\s*)\)\s*$/);
      if (mEq && !['满足式', '由式', '按式', '见式', '如式', '代入式', '根据式', '基于式'].some(w => lineTrim.includes(w))) {
        const eqNum = mEq[1].replace(/\s+/g, '');
        const eqObj = formulasByNum[eqNum] || pageForms.find(f => f.num === eqNum);

        let introText = lineTrim.substring(0, mEq.index).trim();
        if (introText.includes('公式为') || introText.includes('关系为') || introText.includes('表示为') || introText.includes('可得')) {
          introText = introText.replace(/(公式为|关系为|表示为|可得).*/, '$1：');
          if (introText) {
            currentPara = currentPara ? (currentPara + ' ' + introText) : introText;
          }
        }
        flushPara();

        if (eqObj) {
          renderedFormNums.add(eqObj.num);
          bodyHtml += `
            <div class="formula-card" data-eq-num="${eqObj.num}">
              <div class="formula-img-wrap" onclick="openLightbox('${eqObj.image}', '公式 (${eqObj.num})')">
                <img src="${eqObj.image}" alt="公式 (${eqObj.num})" loading="lazy" />
              </div>
              <div class="formula-tag">
                <span class="formula-badge">公式</span>
                <span class="formula-num">(${eqObj.num})</span>
              </div>
            </div>
          `;
          return;
        }
      }

      // 3. Check for Figure Card match
      const mFig = lineTrim.match(/^图\s*(\d+\.\d+(?:\.\d+)?)\s*(.*)$/);
      if (mFig && !['所示', '见图', '如图', '表明', '中的', '中“', '由图', '从图'].some(w => lineTrim.includes(w))) {
        flushPara();
        const figNum = mFig[1];
        const figObj = figuresByNum[figNum] || pageFigs.find(f => f.num === figNum);

        if (figObj) {
          renderedFigNums.add(figObj.num);
          bodyHtml += `
            <figure class="text-figure-card" data-fig-num="${figObj.num}">
              <div class="figure-img-wrap" onclick="openLightbox('${figObj.image}', '${escapeHtml(figObj.title)}')">
                <img src="${figObj.image}" alt="${escapeHtml(figObj.title)}" loading="lazy" />
              </div>
              <figcaption class="figure-caption">
                <span class="fig-badge">插图</span>
                <span>${escapeHtml(figObj.title)}</span>
              </figcaption>
            </figure>
          `;
          return;
        }
      }

      // 4. Headings
      if (/^第\s*\d+\s*章\s+(.*)$/.test(lineTrim)) {
        flushPara();
        bodyHtml += `<h2 class="book-chap-title">${escapeHtml(lineTrim)}</h2>`;
        return;
      }
      if (/^\d+\.\d+\s+(.*)$/.test(lineTrim)) {
        flushPara();
        bodyHtml += `<h3 class="book-sec-title">${escapeHtml(lineTrim)}</h3>`;
        return;
      }
      if (/^\d+\.\d+\.\d+\s+(.*)$/.test(lineTrim)) {
        flushPara();
        bodyHtml += `<h4 class="book-subsec-title">${escapeHtml(lineTrim)}</h4>`;
        return;
      }

      // 5. Paragraph Flow: natural Chinese joining
      if (!currentPara) {
        currentPara = lineTrim;
      } else {
        const lastChar = currentPara.trim().slice(-1);
        if (['。', '！', '？'].includes(lastChar)) {
          flushPara();
          currentPara = lineTrim;
        } else {
          if (currentPara.endsWith('-')) {
            currentPara = currentPara.slice(0, -1) + lineTrim;
          } else if (/[\u4e00-\u9fa5]/.test(lastChar) && /[\u4e00-\u9fa5]/.test(lineTrim[0])) {
            currentPara += lineTrim;
          } else {
            currentPara += ' ' + lineTrim;
          }
        }
      }
    });

    flushPara();

    // Catch-up any figures on this page not yet inlined
    pageFigs.forEach(fig => {
      if (!renderedFigNums.has(fig.num)) {
        bodyHtml += `
          <figure class="text-figure-card" data-fig-num="${fig.num}">
            <div class="figure-img-wrap" onclick="openLightbox('${fig.image}', '${escapeHtml(fig.title)}')">
              <img src="${fig.image}" alt="${escapeHtml(fig.title)}" loading="lazy" />
            </div>
            <figcaption class="figure-caption">
              <span class="fig-badge">插图</span>
              <span>${escapeHtml(fig.title)}</span>
            </figcaption>
          </figure>
        `;
      }
    });

    // Catch-up any formulas on this page not yet inlined
    pageForms.forEach(eq => {
      if (!renderedFormNums.has(eq.num)) {
        bodyHtml += `
          <div class="formula-card" data-eq-num="${eq.num}">
            <div class="formula-img-wrap" onclick="openLightbox('${eq.image}', '公式 (${eq.num})')">
              <img src="${eq.image}" alt="公式 (${eq.num})" loading="lazy" />
            </div>
            <div class="formula-tag">
              <span class="formula-badge">公式</span>
              <span class="formula-num">(${eq.num})</span>
            </div>
          </div>
        `;
      }
    });

    if (!bodyHtml.trim()) {
      bodyHtml = '<p class="book-paragraph no-indent">（本页无独立文字流或为纯图表）</p>';
    }

    const figBadgeHtml = pageFigs.length > 0 
      ? `<span class="page-count-badge">${pageFigs.length} 幅插图</span>` 
      : '';
    const formBadgeHtml = pageForms.length > 0 
      ? `<span class="page-count-badge formula-badge-count">${pageForms.length} 个公式</span>` 
      : '';

    block.innerHTML = `
      <div class="text-page-header">
        <strong>第 ${idx + 1} 页 (${getChapterForPage(idx)})</strong>
        <div class="page-stats-group">
          ${figBadgeHtml}
          ${formBadgeHtml}
          <span style="font-variant-numeric: tabular-nums;">${page.char_count} 字符</span>
        </div>
      </div>
      <div class="text-page-body">${bodyHtml}</div>
    `;

    textContentContainer.appendChild(block);
  });
}

// Lightbox Functions
window.openLightbox = function(src, captionText) {
  lightboxImg.src = src;
  lightboxCaption.textContent = captionText || '';
  lightboxModal.classList.add('active');
};

function closeLightbox() {
  lightboxModal.classList.remove('active');
  lightboxImg.src = '';
}

// Intersection Observers
function setupIntersectionObservers() {
  const imgObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        if (img.dataset.src) {
          img.src = img.dataset.src;
          img.onload = () => img.classList.add('loaded');
          observer.unobserve(img);
        }
      }
    });
  }, { rootMargin: '300px 0px' });

  document.querySelectorAll('.page-card-img-wrap img').forEach(img => {
    imgObserver.observe(img);
  });

  const pageObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const pageIdx = parseInt(entry.target.dataset.pageIndex, 10);
        currentPageIndex = pageIdx;
        pageJumpInput.value = pageIdx + 1;
        updateActiveToc(pageIdx);
        updateProgressBar(pageIdx);
      }
    });
  }, { threshold: 0.2 });

  document.querySelectorAll('.page-card, .text-page-block').forEach(el => {
    pageObserver.observe(el);
  });
}

// Scroll to page
function scrollToPage(pageIndex) {
  if (pageIndex < 0) pageIndex = 0;
  if (pageIndex >= pagesData.length) pageIndex = pagesData.length - 1;

  currentPageIndex = pageIndex;
  pageJumpInput.value = pageIndex + 1;

  let targetEl = null;
  if (currentView === 'image') {
    targetEl = document.getElementById(`img-page-${pageIndex}`);
  } else if (currentView === 'text') {
    targetEl = document.getElementById(`text-page-${pageIndex}`);
  }

  if (targetEl) {
    targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  updateActiveToc(pageIndex);
  updateProgressBar(pageIndex);
}

// Update Active TOC & Chapter Label
function updateActiveToc(pageIndex) {
  let matchedChapter = '封面与扉页';
  let matchedItem = null;

  for (let i = tocData.length - 1; i >= 0; i--) {
    if (pageIndex >= tocData[i].pdf_page_index) {
      matchedItem = tocData[i];
      matchedChapter = tocData[i].title;
      break;
    }
  }

  currentChapterLabel.textContent = matchedChapter;

  document.querySelectorAll('.toc-item').forEach(el => {
    const pIdx = parseInt(el.dataset.pageIndex, 10);
    if (matchedItem && pIdx === matchedItem.pdf_page_index) {
      el.classList.add('active');
    } else {
      el.classList.remove('active');
    }
  });
}

function getChapterForPage(pageIndex) {
  for (let i = tocData.length - 1; i >= 0; i--) {
    if (pageIndex >= tocData[i].pdf_page_index) {
      return tocData[i].title;
    }
  }
  return '正文';
}

function updateProgressBar(pageIndex) {
  if (pagesData.length === 0) return;
  const pct = Math.min(100, Math.round(((pageIndex + 1) / pagesData.length) * 100));
  progressBar.style.width = pct + '%';
}

// Theme Handlers
function applyTheme(theme) {
  currentTheme = theme;
  body.setAttribute('data-theme', theme);
  localStorage.setItem('vortex_reader_theme', theme);
}

function cycleTheme() {
  const themes = ['light', 'sepia', 'dark'];
  const next = themes[(themes.indexOf(currentTheme) + 1) % themes.length];
  applyTheme(next);
}

// Font Size Handlers
function applyFontSize(size) {
  currentFontSize = Math.max(12, Math.min(24, size));
  document.documentElement.style.setProperty('--font-size-base', `${currentFontSize}px`);
  localStorage.setItem('vortex_reader_fontsize', currentFontSize);
}

// View Mode Switcher
function switchView(viewName) {
  currentView = viewName;
  body.setAttribute('data-view', viewName);
  localStorage.setItem('vortex_reader_view', viewName);

  document.querySelectorAll('.view-tab').forEach(tab => {
    if (tab.dataset.viewTarget === viewName) {
      tab.classList.add('active');
    } else {
      tab.classList.remove('active');
    }
  });

  document.querySelectorAll('.reader-view').forEach(view => {
    view.classList.remove('active-view');
  });

  const activeViewEl = document.getElementById(`${viewName}View`);
  if (activeViewEl) {
    activeViewEl.classList.add('active-view');
  }

  if (viewName !== 'ocr') {
    setTimeout(() => scrollToPage(currentPageIndex), 50);
  }
}

// Search
function openSearch() {
  searchModal.classList.add('active');
  searchInput.focus();
}

function closeSearch() {
  searchModal.classList.remove('active');
}

function handleSearch(query) {
  const q = query.trim().toLowerCase();
  searchResultsList.innerHTML = '';

  if (!q) {
    searchStatus.textContent = '输入关键词开始实时全文检索';
    return;
  }

  const results = [];
  pagesData.forEach((p, idx) => {
    const textLower = p.text.toLowerCase();
    const pos = textLower.indexOf(q);
    if (pos !== -1) {
      const start = Math.max(0, pos - 40);
      const end = Math.min(p.text.length, pos + q.length + 50);
      let snippet = p.text.substring(start, end);
      snippet = snippet.replace(new RegExp(escapeRegExp(query), 'gi'), (m) => `<mark>${m}</mark>`);
      results.push({
        pageIndex: idx,
        snippet: snippet,
        chapter: getChapterForPage(idx)
      });
    }
  });

  searchStatus.textContent = `找到 ${results.length} 处匹配（共 306 页）`;

  results.slice(0, 50).forEach(res => {
    const item = document.createElement('div');
    item.className = 'search-result-item';
    item.innerHTML = `
      <div class="search-result-header">第 ${res.pageIndex + 1} 页 · ${escapeHtml(res.chapter)}</div>
      <div class="search-result-snippet">...${res.snippet}...</div>
    `;

    item.addEventListener('click', () => {
      closeSearch();
      scrollToPage(res.pageIndex);
    });

    searchResultsList.appendChild(item);
  });
}

// OCR Showcase
function initOcrShowcase() {
  if (!ocrData || ocrData.length === 0) return;

  ocrPageSelect.innerHTML = '';
  ocrData.forEach((sample, idx) => {
    const opt = document.createElement('option');
    opt.value = idx;
    opt.textContent = `第 ${sample.page_number} 页 - ${sample.lines_count} 行文本 (耗时 ${sample.ocr_time_seconds}s)`;
    ocrPageSelect.appendChild(opt);
  });

  ocrPageSelect.addEventListener('change', () => {
    displayOcrSample(parseInt(ocrPageSelect.value, 10));
  });

  displayOcrSample(0);
}

function displayOcrSample(sampleIdx) {
  const sample = ocrData[sampleIdx];
  if (!sample) return;

  ocrTimeBadge.textContent = `耗时: ${sample.ocr_time_seconds}s`;
  ocrLineCountBadge.textContent = `识别行数: ${sample.lines_count}`;

  ocrPreviewImg.src = sample.image;
  ocrPreviewImg.onload = () => {
    drawOcrBoxes(sample);
  };

  ocrResultList.innerHTML = '';
  sample.results.forEach((line) => {
    const row = document.createElement('div');
    row.className = 'ocr-line-item';
    const confPct = Math.round(line.score * 100);
    row.innerHTML = `
      <span class="ocr-line-text">${escapeHtml(line.text)}</span>
      <span class="ocr-line-score">${confPct}%</span>
    `;
    ocrResultList.appendChild(row);
  });
}

function drawOcrBoxes(sample) {
  const img = ocrPreviewImg;
  const canvas = ocrCanvas;
  canvas.width = img.clientWidth;
  canvas.height = img.clientHeight;

  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const scaleX = canvas.width / img.naturalWidth;
  const scaleY = canvas.height / img.naturalHeight;

  ctx.strokeStyle = '#2563eb';
  ctx.lineWidth = 1.5;
  ctx.fillStyle = 'rgba(37, 99, 235, 0.12)';

  sample.results.forEach(item => {
    const box = item.box;
    if (box && box.length >= 4) {
      ctx.beginPath();
      ctx.moveTo(box[0][0] * scaleX, box[0][1] * scaleY);
      for (let i = 1; i < box.length; i++) {
        ctx.lineTo(box[i][0] * scaleX, box[i][1] * scaleY);
      }
      ctx.closePath();
      ctx.stroke();
      ctx.fill();
    }
  });
}

// Event Listeners
function setupEvents() {
  // TOC Button Click Handlers
  btnToggleToc.addEventListener('click', toggleToc);
  btnCloseToc.addEventListener('click', closeToc);
  if (btnOpenTocEdge) btnOpenTocEdge.addEventListener('click', openToc);
  tocOverlay.addEventListener('click', closeToc);

  tocFilterInput.addEventListener('input', (e) => {
    renderToc(e.target.value);
  });

  pageJumpInput.addEventListener('change', (e) => {
    const target = parseInt(e.target.value, 10) - 1;
    scrollToPage(target);
  });

  btnPrevPage.addEventListener('click', () => {
    scrollToPage(currentPageIndex - 1);
  });

  btnNextPage.addEventListener('click', () => {
    scrollToPage(currentPageIndex + 1);
  });

  btnTheme.addEventListener('click', cycleTheme);
  btnFontInc.addEventListener('click', () => applyFontSize(currentFontSize + 1));
  btnFontDec.addEventListener('click', () => applyFontSize(currentFontSize - 1));

  document.querySelectorAll('.view-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      switchView(tab.dataset.viewTarget);
    });
  });

  btnSearch.addEventListener('click', openSearch);
  btnCloseSearch.addEventListener('click', closeSearch);

  searchModal.addEventListener('click', (e) => {
    if (e.target === searchModal) closeSearch();
  });

  let searchTimeout = null;
  searchInput.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      handleSearch(e.target.value);
    }, 200);
  });

  // Lightbox Close
  btnCloseLightbox.addEventListener('click', closeLightbox);
  lightboxModal.addEventListener('click', (e) => {
    if (e.target === lightboxModal) closeLightbox();
  });

  // Mobile Bottom Bar
  mBtnToc.addEventListener('click', toggleToc);
  mBtnSearch.addEventListener('click', openSearch);

  mBtnView.addEventListener('click', () => {
    const views = ['image', 'text', 'ocr'];
    const next = views[(views.indexOf(currentView) + 1) % views.length];
    switchView(next);
  });

  mBtnTop.addEventListener('click', () => {
    scrollToPage(0);
  });

  // Keyboard Shortcuts (Esc to close overlays)
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeSearch();
      closeLightbox();
      if (isMobile()) closeToc();
    }
  });

  window.addEventListener('resize', () => {
    if (currentView === 'ocr') {
      const activeSample = parseInt(ocrPageSelect.value || '0', 10);
      if (ocrData[activeSample]) {
        drawOcrBoxes(ocrData[activeSample]);
      }
    }
  });
}

// Utilities
function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function escapeRegExp(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Run
window.addEventListener('DOMContentLoaded', init);
