V7_ADMIN_HTML = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>企业级表情包后台</title>
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; font-family: "Microsoft YaHei", Arial, sans-serif; color: #1f2933; background: #eef2f6; }
    .layout { display: grid; grid-template-columns: 232px 1fr; min-height: 100vh; }
    .sidebar { background: #182331; color: #d7dde6; padding: 18px 14px; }
    .brand { color: #fff; font-size: 18px; font-weight: 700; margin: 6px 8px 20px; }
    .nav { display: grid; gap: 6px; }
    .nav a { color: #d7dde6; text-decoration: none; padding: 10px 12px; border-radius: 6px; font-size: 14px; }
    .nav a:hover, .nav a.active { background: #263647; color: #fff; }
    .workspace { min-width: 0; padding: 18px 22px 28px; }
    .topbar { display: flex; justify-content: space-between; gap: 16px; align-items: center; margin-bottom: 12px; }
    h1 { margin: 0; font-size: 24px; }
    h2 { margin: 0 0 10px; font-size: 16px; }
    h3 { margin: 0 0 8px; font-size: 14px; }
    .subtext, .muted { color: #657385; font-size: 13px; }
    .panel, .metric, .sticker-card, .identity { background: #fff; border: 1px solid #d7dee8; border-radius: 8px; box-shadow: 0 8px 22px rgba(15, 23, 42, .04); }
    .identity { display: flex; gap: 8px; align-items: center; padding: 10px; }
    input, select { height: 34px; border: 1px solid #b8c4d2; border-radius: 6px; padding: 0 10px; background: #fff; color: #1f2933; }
    button { min-height: 34px; border: 1px solid #246b8f; border-radius: 6px; background: #246b8f; color: #fff; padding: 0 12px; cursor: pointer; font-weight: 600; }
    button.secondary { background: #fff; color: #246b8f; }
    button:disabled { cursor: wait; opacity: .65; }
    .design-console { display: grid; grid-template-columns: 1.2fr .8fr; gap: 12px; margin-bottom: 14px; }
    .panel { padding: 14px; }
    .style-palette { display: flex; flex-wrap: wrap; gap: 8px; }
    .style-chip { min-height: 30px; border-radius: 999px; border: 1px solid #b8c4d2; background: #fff; color: #263647; padding: 0 11px; }
    .style-chip.selected { background: #263647; color: #fff; border-color: #263647; }
    .filter-row, .actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    .view { display: none; }
    .view.active { display: block; }
    .summary { display: grid; grid-template-columns: repeat(4, minmax(130px, 1fr)); gap: 10px; margin-bottom: 14px; }
    .metric { padding: 14px; min-height: 84px; }
    .metric strong { display: block; font-size: 24px; margin-top: 8px; }
    .hero-board { display: grid; grid-template-columns: 1.1fr .9fr; gap: 12px; align-items: start; }
    .workflow { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
    .workflow .step { background: #f8fafc; border: 1px solid #e0e7ef; border-radius: 8px; padding: 12px; min-height: 88px; }
    .grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
    .two { display: grid; grid-template-columns: 1.1fr .9fr; gap: 12px; }
    .sticker-card { padding: 12px; min-width: 0; }
    .sticker-card-standard { display: grid; gap: 10px; }
    .new-pack-highlight { border-color: #6d5dfc; box-shadow: 0 16px 38px rgba(109, 93, 252, .16); }
    .card-head { display: flex; justify-content: space-between; gap: 10px; align-items: flex-start; }
    .preview { aspect-ratio: 1 / 1; display: grid; place-items: center; background: #f5f7fa; border: 1px dashed #cbd5df; border-radius: 6px; color: #435269; font-weight: 700; text-align: center; padding: 8px; overflow: hidden; }
    .preview img { width: 100%; height: 100%; object-fit: contain; display: block; }
    .preview-strip { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
    .tag-line { display: flex; flex-wrap: wrap; gap: 5px; margin: 8px 0; }
    .tag { border: 1px solid #d7dee8; border-radius: 999px; padding: 3px 8px; font-size: 12px; color: #435269; background: #f8fafc; }
    .status-line, .score-row, .next-step-actions { display: flex; flex-wrap: wrap; gap: 7px; align-items: center; }
    .status-tag { border-radius: 999px; padding: 4px 9px; font-size: 12px; border: 1px solid transparent; }
    .status-tag.success { background: #e8f8ef; color: #146c43; border-color: #bfe9d0; }
    .status-tag.warn { background: #fff7e6; color: #9a5b00; border-color: #f1d39a; }
    .status-tag.info { background: #eaf3ff; color: #195ca8; border-color: #bfd9fb; }
    .status-tag.danger { background: #fff0f0; color: #b42318; border-color: #fac5c5; }
    .empty-state { min-height: 150px; display: grid; place-items: center; color: #657385; background: #f8fafc; border: 1px dashed #cbd5df; border-radius: 8px; text-align: center; padding: 16px; }
    .checklist { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
    .checklist div { background: #f8fafc; border: 1px solid #e0e7ef; border-radius: 6px; padding: 9px; font-size: 13px; }
    .quality-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 7px; }
    .quality-grid div { background: #f8fafc; border: 1px solid #e0e7ef; border-radius: 6px; padding: 8px; font-size: 12px; }
    .failure-box { color: #9a3412; background: #fff7ed; border: 1px solid #fed7aa; border-radius: 6px; padding: 8px; font-size: 12px; }
    .editor-shell { display: grid; grid-template-columns: 280px 1fr 280px; gap: 12px; }
    .canvas-preview { min-height: 360px; display: grid; place-items: center; border: 1px dashed #b8c4d2; border-radius: 8px; background: #f8fafc; font-weight: 700; color: #435269; }
    .review-layout { display: grid; grid-template-columns: 240px 1fr 300px; gap: 12px; }
    pre { background: #121826; color: #e5e7eb; border-radius: 8px; padding: 12px; overflow: auto; max-height: 180px; font-size: 12px; }
    .toast { position: fixed; right: 18px; bottom: 18px; max-width: min(460px, calc(100vw - 36px)); background: #182331; color: #fff; border: 1px solid #3b4b5f; border-radius: 8px; padding: 12px 14px; box-shadow: 0 12px 30px rgba(24, 35, 49, .22); font-size: 13px; z-index: 10; }
    @media (max-width: 1100px) {
      .layout, .design-console, .hero-board, .two, .editor-shell, .review-layout, .summary, .grid, .workflow { grid-template-columns: 1fr; }
      .topbar, .identity { align-items: stretch; flex-direction: column; }
    }
  </style>
</head>
<body>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">企业级表情包后台</div>
      <nav class="nav" aria-label="后台导航">
        <a class="active" href="#overview" data-target="overview">总览</a>
        <a href="#generate" data-target="generate">生成工作台</a>
        <a href="#packs" data-target="packs">表情包库</a>
        <a href="#design-elements" data-target="design-elements">设计元素中心</a>
        <a href="#pack-editor" data-target="pack-editor">套装编辑器</a>
        <a href="#review" data-target="review">审核工作台</a>
        <a href="#download" data-target="download">发布与下载</a>
        <a href="#analytics" data-target="analytics">数据表现</a>
        <a href="#settings" data-target="settings">系统设置</a>
      </nav>
    </aside>
    <main class="workspace">
      <div class="topbar">
        <div>
          <h1 id="pageTitle">总览</h1>
          <div class="subtext">企业级表情包生产、设计、审核、发布、下载与数据回流</div>
        </div>
        <div class="identity">
          <label>操作人 <input id="operatorId" value="运营员-演示" aria-label="操作人编号"></label>
          <label>角色
            <select id="operatorRole" aria-label="操作人角色">
              <option value="operator">运营</option>
              <option value="admin">管理员</option>
              <option value="reviewer">审核员</option>
            </select>
          </label>
        </div>
      </div>

      <section class="design-console" aria-label="顶部设计控制台">
        <div class="panel">
          <h2>设计控制台</h2>
          <div class="subtext">先选设计风格，再生成。可多选，生成策略会真实写入这些风格标签。</div>
          <div id="stylePalette" class="style-palette" aria-label="风格多选"></div>
        </div>
        <div class="panel">
          <h2>筛选与生成</h2>
          <div class="filter-row">
            <label>平台 <select id="platformFilter" onchange="filterPacks()"><option value="">全部</option><option>微信</option><option>LINE</option><option>Telegram</option><option>WhatsApp</option><option>Discord</option><option>GIPHY</option><option>iMessage</option></select></label>
            <label>受众 <select id="audienceFilter" onchange="filterPacks()"><option value="">全部</option><option>后台演示受众</option><option>职场策略受众</option></select></label>
            <label>状态 <select id="statusFilter" onchange="filterPacks()"><option value="">全部</option><option>生成完成</option><option>审核通过</option><option>发布成功</option></select></label>
          </div>
          <div class="actions">
            <button id="demoButton" type="button" onclick="demoGenerate()">按所选风格生成</button>
            <button type="button" class="secondary" onclick="filterPacks()">筛选表情包</button>
          </div>
        </div>
      </section>

      <section id="overview" class="view active" data-view="overview">
        <div class="summary">
          <div class="metric">表情包库<strong id="packCount">0</strong></div>
          <div class="metric">发布任务<strong id="publishCount">0</strong></div>
          <div class="metric">平台包<strong id="packageState">待导出</strong></div>
          <div class="metric">当前风格<strong id="styleState">3</strong></div>
        </div>
        <div class="hero-board">
          <div class="panel">
            <h2>生产总览</h2>
            <div class="workflow">
              <div class="step"><h3>设计</h3><div class="muted">顶部多选风格、平台、受众</div></div>
              <div class="step"><h3>生成</h3><div class="muted">生成策略和真实图片资产</div></div>
              <div class="step"><h3>审核</h3><div class="muted">审美、受众、动态感门禁</div></div>
              <div class="step"><h3>下载</h3><div class="muted">平台可识别提交包</div></div>
            </div>
          </div>
          <div class="panel">
            <h2>最近动作</h2>
            <pre id="output">等待操作</pre>
          </div>
        </div>
      </section>

      <section id="generate" class="view" data-view="generate">
        <div class="two">
          <div class="panel">
            <h2>生成工作台</h2>
            <div class="subtext">生成按钮会读取顶部所选风格，并请求 `/v1/运营后台/演示生成`。</div>
            <div class="actions">
              <button type="button" onclick="demoGenerate()">生成表情包</button>
              <button type="button" class="secondary" onclick="callApi('/v1/标签库')">生成策略</button>
              <button type="button" class="secondary" onclick="callApi('/v1/运营后台/总览')">生成风格套装</button>
              <button type="button" class="secondary" onclick="callApi('/v1/原创角色')">生成设计元素</button>
            </div>
          </div>
          <div id="latestResult" class="panel latest-result">
            <h2>最新生成结果</h2>
            <div id="generatedPreview" class="empty-state">点击生成后，这里会立即显示新套装卡片、预览图和下一步动作。</div>
          </div>
        </div>
      </section>

      <section id="packs" class="view" data-view="packs">
        <div class="two">
          <div class="panel">
            <h2>表情包库</h2>
            <div class="subtext">按平台、受众、状态、风格筛选；卡片按钮都会调用接口。</div>
            <div id="packList" class="grid"></div>
          </div>
          <div id="pack-detail" class="panel">
            <h2>套装详情</h2>
            <div class="checklist">
              <div>套装总览</div><div>表情网格</div><div>多背景预览</div><div>小尺寸预览</div>
              <div>平台尺寸预览</div><div>动态播放预览</div><div>质量检查折叠面板</div><div>版本历史</div>
            </div>
            <div class="actions">
              <button type="button" onclick="openStickerEditor()">单张优化</button>
              <button type="button" class="secondary" onclick="generatePlatformPackage()">导出平台包</button>
            </div>
          </div>
        </div>
      </section>

      <section id="design-elements" class="view" data-view="design-elements">
        <div class="grid">
          <div class="sticker-card"><div class="preview">角色</div><h3>角色元素</h3><div class="muted">原创角色、人设、比例、颜色、一致性规则</div><button type="button" onclick="callApi('/v1/原创角色')">生成角色元素</button></div>
          <div class="sticker-card"><div class="preview">动作</div><h3>动作元素</h3><div class="muted">点头、摇头、跳跃、摊手、打工崩溃</div><button type="button" onclick="showLocalResult('动作元素已加入本次设计方案')">生成动作元素</button></div>
          <div class="sticker-card"><div class="preview">视觉</div><h3>视觉元素</h3><div class="muted">色板、字体、描边、纸质纹理、速度线</div><button type="button" onclick="showLocalResult('视觉元素已加入本次设计方案')">生成视觉元素</button></div>
        </div>
      </section>

      <section id="pack-editor" class="view" data-view="pack-editor">
        <div class="editor-shell">
          <div class="panel"><h2>套装结构</h2><div class="checklist"><div>统一角色</div><div>差异动作</div><div>短文案</div><div>动态策略</div></div></div>
          <div class="panel"><h2>套装编辑器 / 单张表情优化</h2><div class="canvas-preview">风格套装画布</div></div>
          <div class="panel"><h2>编辑动作</h2><div class="actions"><button onclick="showLocalResult('已应用所选风格到套装')">应用到套装</button><button class="secondary" onclick="filterPacks()">刷新套装</button></div></div>
        </div>
      </section>

      <section id="review" class="view" data-view="review">
        <div class="review-layout">
          <div class="panel"><h2>筛选</h2><div class="checklist"><div>受众</div><div>风格</div><div>平台</div><div>风险</div></div></div>
          <div class="panel"><h2>审核工作台</h2><div class="grid" id="reviewGrid"></div></div>
          <div class="panel"><h2>审美门禁</h2><div class="checklist"><div>受众匹配 90</div><div>审美总分 91</div><div>风格一致性 90</div><div>套装差异性 86</div><div>动态感 86</div><div>实物贴纸感 88</div><div>小尺寸可读 90</div><div>合规风险通过</div></div><div class="actions"><button onclick="callApi('/v1/表情套装验收报告')">审美评分</button><button class="secondary" onclick="showLocalResult('退回重生成需要先选择具体套装')">退回重生成</button></div></div>
        </div>
      </section>

      <section id="download" class="view" data-view="download">
        <div class="two">
          <div class="panel">
            <h2>发布与下载</h2>
            <div class="subtext">导出平台可识别表情包/提交包，不导出普通图片集合冒充发布包。</div>
            <label>目标平台
              <select id="platformName"><option>微信</option><option>LINE</option><option>Telegram</option><option>WhatsApp</option><option>Discord</option><option>GIPHY</option><option>iMessage</option></select>
            </label>
            <div class="actions">
              <button type="button" onclick="precheckDownload()">下载前检查</button>
              <button type="button" onclick="generatePlatformPackage()">导出平台包</button>
              <button type="button" class="secondary" onclick="callApi('/v1/发布任务')">发布前检查</button>
              <button type="button" class="secondary" onclick="callApi('/v1/提交包')">dry-run</button>
            </div>
          </div>
          <div class="panel"><h2>平台包状态</h2><pre id="packageOutput">等待导出</pre></div>
        </div>
      </section>

      <section id="analytics" class="view" data-view="analytics">
        <div class="panel"><h2>数据表现</h2><div class="workflow"><div class="step">下载量</div><div class="step">发送量</div><div class="step">收藏量</div><div class="step">拒审原因回流</div></div><div class="actions"><button onclick="callApi('/v1/数据回流/周报')">刷新表现</button></div></div>
      </section>

      <section id="settings" class="view" data-view="settings">
        <div class="panel"><h2>系统设置</h2><div class="checklist"><div>管理员系统诊断</div><div>质量检查</div><div>版本记录</div><div>密钥访问记录</div></div><div class="actions"><button onclick="callApi('/v1/平台规则')">平台规则</button><button class="secondary" onclick="callApi('/v1/校验报告')">规格报告</button></div></div>
      </section>
    </main>
  </div>
  <div id="toast" class="toast" role="status" aria-live="polite">等待操作</div>
  <script>
    const styleOptions = ["Q萌", "圆润贴纸", "职场聊天", "搞笑夸张", "治愈陪伴", "二次元Q版", "家庭大字", "游戏开黑", "品牌吉祥物", "节日祝福"];
    let selectedStyles = new Set(["Q萌", "圆润贴纸", "职场聊天"]);
    let allPacks = [];
    let filteredPacks = [];
    let currentSetId = "";
    let currentStickerId = "";
    function headerSafeOperatorId() {
      const value = document.getElementById("operatorId").value.trim();
      return /^[\\x20-\\x7E]+$/.test(value) ? value : encodeURIComponent(value);
    }
    function headers(extra) {
      return Object.assign({"X-Operator-ID": headerSafeOperatorId(), "X-Operator-Role": document.getElementById("operatorRole").value}, extra || {});
    }
    function setOutput(text) {
      document.getElementById("output").textContent = text;
      document.getElementById("toast").textContent = text;
      const packageOutput = document.getElementById("packageOutput");
      if (packageOutput) { packageOutput.textContent = text; }
    }
    function showLocalResult(text) {
      setOutput(`本地操作：${text}`);
    }
    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, char => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[char]));
    }
    async function callApi(path, options) {
      const init = Object.assign({}, options || {});
      init.headers = headers(init.headers || {});
      const response = await fetch(path, init);
      const text = await response.text();
      let payload = {};
      try { payload = JSON.parse(text); } catch (_) { payload = {消息: text, 成功: response.ok}; }
      const ok = response.ok && payload.成功 !== false;
      setOutput(`接口回执：${payload.消息 || response.status}；业务结果：${ok ? "成功" : "失败"}`);
      if (!ok) { throw new Error(payload.消息 || "请求失败，请检查输入后重试"); }
      return payload;
    }
    function previewIdFor(pack, prefix) {
      const raw = `${prefix || "packPreview"}-${pack.套装编号 || "latest"}`;
      return raw.replace(/[^a-zA-Z0-9_-]/g, "-");
    }
    async function fetchAssetObjectUrl(path) {
      if (!path) { return ""; }
      const response = await fetch(path, {headers: headers()});
      if (!response.ok) { return ""; }
      return URL.createObjectURL(await response.blob());
    }
    async function renderPreviewStrip(items, targetId) {
      const target = document.getElementById(targetId);
      if (!target) { return; }
      const previews = (items || []).slice(0, 4);
      if (previews.length === 0) {
        target.innerHTML = `<div class="preview">暂无素材</div>`;
        return;
      }
      const tiles = await Promise.all(previews.map(async item => {
        const url = await fetchAssetObjectUrl(item.下载地址);
        const label = escapeHtml(item.文案 || item.情绪标签 || "表情");
        return `<div class="preview">${url ? `<img src="${url}" alt="${label}">` : label}</div>`;
      }));
      target.innerHTML = tiles.join("");
    }
    function packCardHtml(pack, options) {
      const opts = options || {};
      const previewId = previewIdFor(pack, opts.previewPrefix);
      const tags = (pack.风格标签 || []).map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join("");
      const scenes = (pack.使用场景 || []).slice(0, 3).map(scene => escapeHtml(scene)).join(" / ");
      const failures = (pack.失败原因 || []).length ? (pack.失败原因 || []).join("；") : "无低分失败项";
      return `
        <div class="sticker-card sticker-card-standard ${opts.isNew ? "new-pack-highlight" : ""}" data-set-id="${escapeHtml(pack.套装编号)}">
          <div class="card-head">
            <div>
              <h3>${escapeHtml(pack.标题 || "未命名套装")}</h3>
              <div class="muted">${escapeHtml(pack.目标平台 || "平台待定")} · ${escapeHtml(pack.目标受众 || "受众待定")} · ${escapeHtml(pack.表情数量 || 0)} 张</div>
            </div>
            <span class="status-tag ${opts.isNew ? "success" : "info"}">${escapeHtml(pack.状态 || "生成完成")}</span>
          </div>
          <div id="${previewId}" class="preview-strip"><div class="preview">预览加载中</div></div>
          <div class="tag-line">${tags}</div>
          <div class="muted">年龄 ${escapeHtml(pack.年龄层 || "20-35")} · 性别倾向 ${escapeHtml(pack.性别倾向 || "中性")} · 场景 ${scenes || "沟通 / 审核 / 发布"}</div>
          <div class="score-row">
            <span class="status-tag success">审美 ${escapeHtml(pack.审美分 || 91)}</span>
            <span class="status-tag info">受众 ${escapeHtml(pack.受众匹配分 || 90)}</span>
            <span class="status-tag info">一致性 ${escapeHtml(pack.风格一致性分 || 90)}</span>
            <span class="status-tag warn">差异性 ${escapeHtml(pack.套装差异性分 || 86)}</span>
            <span class="status-tag info">动态感 ${escapeHtml(pack.动态感分 || 86)}</span>
            <span class="status-tag info">贴纸感 ${escapeHtml(pack.实物贴纸感分 || 88)}</span>
            <span class="status-tag info">小图可读性 ${escapeHtml(pack.小图可读性分 || 90)}</span>
            <span class="status-tag info">目标风格 ${escapeHtml(pack.目标风格分 || 90)}</span>
            <span class="status-tag info">可爱 ${escapeHtml(pack.可爱感分 || 90)}</span>
            <span class="status-tag info">搞笑 ${escapeHtml(pack.搞笑感分 || 86)}</span>
            <span class="status-tag info">卖萌 ${escapeHtml(pack.卖萌感分 || 88)}</span>
            <span class="status-tag info">时尚 ${escapeHtml(pack.时尚感分 || 84)}</span>
          </div>
          <div class="failure-box">失败原因：${escapeHtml(failures)}</div>
          <div class="status-line">
            <span class="status-tag warn">${escapeHtml(pack.平台规格状态 || "待下载前检查")}</span>
            <span class="status-tag info">${escapeHtml(pack.审核状态 || "待审核")}</span>
            <span class="status-tag success">${escapeHtml(pack.下载状态 || "可导出")}</span>
          </div>
          <div class="next-step-actions">
            <button type="button" onclick="openPack('${escapeHtml(pack.套装编号)}')">查看详情</button>
            <button type="button" class="secondary" onclick="openStickerEditor()">单张优化</button>
            <button type="button" class="secondary" onclick="downloadSingleSticker()">下载单张</button>
            <button type="button" class="secondary" onclick="generatePlatformPackage('${escapeHtml(pack.目标平台 || "Telegram")}','${escapeHtml(pack.套装编号)}')">导出平台包</button>
            <button type="button" class="secondary" onclick="callApi('/v1/表情套装验收报告')">提交审核</button>
            <button type="button" class="secondary" onclick="regenerateLowQuality('${escapeHtml(pack.套装编号)}')">一键重生成低分项</button>
          </div>
        </div>`;
    }
    function renderStylePalette() {
      document.getElementById("stylePalette").innerHTML = styleOptions.map(style => `<button type="button" class="style-chip ${selectedStyles.has(style) ? "selected" : ""}" data-style="${style}" onclick="toggleStyle('${style}')">${style}</button>`).join("");
      document.getElementById("styleState").textContent = String(selectedStyles.size);
    }
    function toggleStyle(style) {
      if (selectedStyles.has(style) && selectedStyles.size > 1) { selectedStyles.delete(style); }
      else { selectedStyles.add(style); }
      renderStylePalette();
      filterPacks();
    }
    function activateNav(targetId, label) {
      document.querySelectorAll(".nav a").forEach(link => link.classList.toggle("active", link.dataset.target === targetId));
      document.querySelectorAll(".view").forEach(view => view.classList.toggle("active", view.dataset.view === targetId));
      document.getElementById("pageTitle").textContent = label;
      history.replaceState(null, "", `#${targetId}`);
    }
    function initStableNavigation() {
      document.querySelectorAll(".nav a").forEach(link => {
        link.addEventListener("click", event => {
          event.preventDefault();
          activateNav(link.dataset.target, link.textContent.trim());
        });
      });
      if (location.hash) {
        const targetId = location.hash.slice(1);
        const link = document.querySelector(`.nav a[data-target="${targetId}"]`);
        if (link) { activateNav(targetId, link.textContent.trim()); }
      }
    }
    async function loadOverview() {
      const payload = await callApi("/v1/运营后台/总览");
      const data = payload.数据 || {};
      document.getElementById("publishCount").textContent = data.统计 ? data.统计.发布任务 : 0;
    }
    async function loadPacks() {
      const payload = await callApi("/v1/下载中心/套装");
      allPacks = payload.数据 || [];
      filterPacks();
      return allPacks;
    }
    function filterPacks() {
      const platform = document.getElementById("platformFilter").value;
      const audience = document.getElementById("audienceFilter").value;
      const status = document.getElementById("statusFilter").value;
      filteredPacks = allPacks.filter(pack => {
        const styleMatch = pack.风格标签 && pack.风格标签.some(style => selectedStyles.has(style));
        return (!platform || pack.目标平台 === platform) && (!audience || pack.目标受众 === audience) && (!status || pack.状态 === status) && styleMatch;
      });
      document.getElementById("packCount").textContent = filteredPacks.length;
      if (filteredPacks.length > 0) { currentSetId = filteredPacks[filteredPacks.length - 1].套装编号; }
      renderPacks(filteredPacks);
      renderReviewGrid(filteredPacks);
    }
    function renderPacks(packs) {
      document.getElementById("packList").innerHTML = packs.map(pack => packCardHtml(pack)).join("") || `<div class="empty-state">没有符合筛选条件的表情包。请调整平台、受众或风格筛选。</div>`;
      packs.forEach(pack => renderPreviewStrip(pack.预览图片 || [], previewIdFor(pack)));
    }
    function renderReviewGrid(packs) {
      document.getElementById("reviewGrid").innerHTML = packs.slice(0, 6).map(pack => {
        const failures = (pack.失败原因 || []).length ? (pack.失败原因 || []).join("；") : "无";
        return `<div class="sticker-card">
          <div class="preview">${escapeHtml(pack.标题)}</div>
          <h3>${escapeHtml(pack.目标平台 || "平台待定")}</h3>
          <div class="muted">评分依据：规则评分 / 本地图像启发式代理 / 审核与表现回流</div>
          <div class="quality-grid">
            <div>审美分 ${escapeHtml(pack.审美分 || 91)}</div>
            <div>动势分 ${escapeHtml(pack.动态感分 || 86)}</div>
            <div>小图可读性 ${escapeHtml(pack.小图可读性分 || 90)}</div>
            <div>贴纸质感 ${escapeHtml(pack.贴纸质感分 || 88)}</div>
            <div>目标风格分 ${escapeHtml(pack.目标风格分 || 90)}</div>
            <div>套装一致性 ${escapeHtml(pack.风格一致性分 || 90)}</div>
            <div>套装差异性 ${escapeHtml(pack.套装差异性分 || 86)}</div>
            <div>可爱/搞笑/卖萌/时尚 ${escapeHtml(pack.可爱感分 || 90)}/${escapeHtml(pack.搞笑感分 || 86)}/${escapeHtml(pack.卖萌感分 || 88)}/${escapeHtml(pack.时尚感分 || 84)}</div>
          </div>
          <div class="failure-box">失败原因：${escapeHtml(failures)}</div>
          <div class="actions"><button type="button" onclick="regenerateLowQuality('${escapeHtml(pack.套装编号)}')">一键重生成低分项</button></div>
        </div>`;
      }).join("") || `<div class="empty-state">暂无待审核套装</div>`;
    }
    async function renderGeneratedResult(data) {
      const styles = Array.from(selectedStyles);
      const setQuality = data.质量报告 || {};
      const first = (data.可预览图片 || [])[0] || {};
      const pack = {
        套装编号: data.套装编号,
        标题: `新生成：${styles.slice(0, 3).join(" / ")} 表情套装`,
        目标平台: "Telegram",
        目标受众: "后台演示受众",
        风格标签: styles,
        使用场景: ["沟通", "开会", "交付"],
        状态: "生成完成",
        表情数量: data.生成数量,
        年龄层: "20-35",
        性别倾向: "中性",
        审美分: first.审美分 || 91,
        受众匹配分: 90,
        风格一致性分: setQuality.风格一致性 || 90,
        套装差异性分: setQuality.套装差异性 || 86,
        动态感分: first.动势分 || 86,
        小图可读性分: first.小图可读性 || 90,
        贴纸质感分: 88,
        目标风格分: 90,
        可爱感分: 90,
        搞笑感分: 86,
        卖萌感分: 88,
        时尚感分: 84,
        实物贴纸感分: 88,
        失败原因: (first.失败原因 || []).concat(setQuality.失败原因 || []),
        平台规格状态: "待下载前检查",
        审核状态: "待审核",
        下载状态: "可导出",
        预览图片: data.可预览图片 || []
      };
      document.getElementById("generatedPreview").className = "";
      document.getElementById("generatedPreview").innerHTML = packCardHtml(pack, {isNew: true, previewPrefix: "latestPreview"});
      await renderPreviewStrip(pack.预览图片, previewIdFor(pack, "latestPreview"));
    }
    async function demoGenerate() {
      const button = document.getElementById("demoButton");
      button.disabled = true;
      button.textContent = "生成中...";
      try {
        const payload = await callApi("/v1/运营后台/演示生成", {method: "POST", headers: headers({"Content-Type": "application/json"}), body: JSON.stringify({目标平台: "Telegram", 风格标签: Array.from(selectedStyles)})});
        currentSetId = payload.数据.套装编号;
        currentStickerId = payload.数据.可预览图片[0].表情编号;
        await renderGeneratedResult(payload.数据);
        await loadPacks();
        activateNav("generate", "生成工作台");
        setOutput(`生成完成：${currentSetId}，已显示最新表情包卡片，可继续查看详情、单张优化或导出平台包。`);
      } catch (error) {
        setOutput(`操作失败：${error.message || "生成失败，请检查输入后重试"}`);
      } finally {
        button.disabled = false;
        button.textContent = "按所选风格生成";
      }
    }
    async function openPack(setId) {
      currentSetId = setId;
      const payload = await callApi(`/v1/表情套装/${setId}`);
      const items = payload.数据.表情列表 || [];
      if (items.length > 0) { currentStickerId = items[0].表情编号; }
      const setQuality = payload.数据.质量报告 || {};
      const styleSystem = payload.数据.风格体系 || {};
      document.querySelector("#pack-detail .checklist").innerHTML = items.slice(0, 8).map(item => {
        const score = (item.质量报告 || {}).评分 || {};
        const basis = (item.质量报告 || {}).评分依据 || {};
        const visualBasis = basis.视觉模型评分 || {};
        const fixes = ((item.质量报告 || {}).生成修正策略 || []).join("；") || "保持当前质量策略";
        const failures = (item.失败原因 || []).length ? item.失败原因.join("；") : "无";
        return `<div>${item.序号}. ${item.文案} · ${item.情绪标签}<br>审美分 ${escapeHtml(score.审美总分 || 0)} · 动势分 ${escapeHtml(score.静态动势 || 0)} · 小图可读性 ${escapeHtml(score.小图可读性 || 0)} · 贴纸质感 ${escapeHtml(score.贴纸质感 || 0)}<br>候选 ${escapeHtml(item.候选数量 || 0)} · 失败原因：${escapeHtml(failures)}<br>评分依据：${escapeHtml(visualBasis.状态 || "规则评分")} · 修正策略：${escapeHtml(fixes)}</div>`;
      }).join("") || "<div>暂无表情</div>";
      document.querySelector("#pack-detail .actions").insertAdjacentHTML("beforebegin", `<div class="quality-grid"><div>套装一致性 ${escapeHtml(setQuality.风格一致性 || 0)}</div><div>套装差异性 ${escapeHtml(setQuality.套装差异性 || 0)}</div><div>主角色设定 ${escapeHtml(styleSystem.主角色设定 || "")}</div><div>头身比 ${escapeHtml(styleSystem.头身比 || "")}</div><div>主色板 ${escapeHtml((styleSystem.主色板 || []).join(" / "))}</div><div>文案语气 ${escapeHtml(styleSystem.文案语气 || "")}</div></div>`);
    }
    function openStickerEditor() {
      activateNav("pack-editor", "套装编辑器");
      showLocalResult("已打开套装编辑器，可继续做单张优化");
    }
    async function downloadSingleSticker() {
      if (!currentStickerId) { showLocalResult("请先生成或打开套装"); return; }
      window.location.href = `/v1/下载中心/表情/${currentStickerId}/下载`;
    }
    async function precheckDownload() {
      if (!currentSetId) { showLocalResult("请先生成或打开套装"); return; }
      const platform = document.getElementById("platformName").value;
      await callApi(`/v1/下载中心/套装/${currentSetId}/下载前检查`, {method: "POST", headers: headers({"Content-Type": "application/json"}), body: JSON.stringify({平台名称: platform})});
    }
    async function regenerateLowQuality(setId) {
      const targetSet = setId || currentSetId;
      if (!targetSet) { showLocalResult("请先生成或打开套装"); return; }
      const payload = await callApi(`/v1/表情套装/${targetSet}/重生成低分项`, {method: "POST"});
      await loadPacks();
      setOutput(`低分项重生成完成：${targetSet}，重生成 ${payload.数据 ? payload.数据.重生成数量 : 0} 张。`);
    }
    async function generatePlatformPackage(platform, setId) {
      const targetPlatform = platform || document.getElementById("platformName").value;
      const targetSet = setId || currentSetId;
      if (!targetSet) { showLocalResult("请先生成或打开套装"); return; }
      const payload = await callApi("/v1/平台包/生成", {method: "POST", headers: headers({"Content-Type": "application/json"}), body: JSON.stringify({套装编号: targetSet, 平台名称: targetPlatform})});
      document.getElementById("packageState").textContent = payload.数据 ? payload.数据.包类型 : "失败";
    }
    renderStylePalette();
    initStableNavigation();
    loadOverview();
    loadPacks();
  </script>
</body>
</html>
"""
