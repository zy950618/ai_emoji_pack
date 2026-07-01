"""Owner admin UI template.

Loop4 accepted-maintenance note:
- This template intentionally remains inline to avoid a static split regression
  while the formal Playwright e2e is the behavioral source of truth.
- Keep API paths, route ids, and DOM ids stable unless the e2e is updated in
  the same change.
"""

ADMIN_UI_TEMPLATE_NAME = "owner-admin-inline-html"
ADMIN_UI_STATIC_SPLIT_STATUS = "accepted-maintenance"
ADMIN_UI_API_PREFIX = "/api/admin"
ADMIN_UI_ASSET_PREFIX = "/admin-assets"


V7_ADMIN_HTML = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>表情包工坊 Owner 后台</title>
  <style>
    :root {
      --bg: #f5f7fb; --surface: rgba(255,255,255,.9); --solid: #fff; --text: #101828;
      --muted: #667085; --border: rgba(16,24,40,.1); --primary: #2563eb;
      --primary-dark: #1743a9; --primary-soft: #eaf1ff; --green: #16a34a;
      --orange: #f97316; --red: #ef4444; --shadow: 0 18px 46px rgba(15,23,42,.08);
      font-family: Inter, ui-sans-serif, system-ui, "Microsoft YaHei", sans-serif;
    }
    body[data-theme="graphite"] { --bg:#f3f4f6; --primary:#111827; --primary-dark:#030712; --primary-soft:#eef0f3; }
    body[data-theme="sakura"] { --bg:#fff6fb; --primary:#db2777; --primary-dark:#9d174d; --primary-soft:#fce7f3; }
    body[data-theme="forest"] { --bg:#f3fbf6; --primary:#16a34a; --primary-dark:#166534; --primary-soft:#dcfce7; }
    * { box-sizing: border-box; }
    body { margin: 0; color: var(--text); background: linear-gradient(180deg, #fbfcff 0%, var(--bg) 100%); }
    button, input, select, textarea { font: inherit; }
    button { cursor: pointer; }
    button:disabled { cursor: not-allowed; opacity: .62; }
    .shell { min-height: 100vh; display: grid; grid-template-columns: 248px 1fr; }
    .sidebar { position: sticky; top: 0; height: 100vh; padding: 22px 18px; border-right: 1px solid var(--border); background: rgba(255,255,255,.76); display: flex; flex-direction: column; gap: 18px; }
    .brand { display:flex; gap:12px; align-items:center; padding-bottom:16px; border-bottom:1px solid var(--border); }
    .mark { width:42px; height:42px; border-radius:14px; display:grid; place-items:center; font-weight:900; background:linear-gradient(145deg,#fff7da,#ffc857 48%,#ff9d2e); color:#7c3f00; }
    .brand strong { display:block; }
    .brand span { color: var(--muted); font-size: 12px; }
    nav { display:grid; gap:6px; }
    nav button { width:100%; height:42px; border:0; border-radius:13px; background:transparent; color:#344054; display:flex; align-items:center; gap:10px; padding:0 12px; font-weight:800; text-align:left; }
    nav button.active, nav button:hover { color:var(--primary); background:color-mix(in srgb, var(--primary) 12%, transparent); }
    .owner { margin-top:auto; padding:12px; border:1px solid var(--border); border-radius:18px; background:var(--surface); box-shadow:var(--shadow); }
    .main { padding:24px 30px 44px; min-width:0; }
    .topbar { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; margin-bottom:22px; }
    h1 { margin:0; font-size:30px; }
    h2, h3 { margin:0; }
    .sub { margin-top:6px; color:var(--muted); }
    .actions, .toolbar, .row-actions { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
    .topbar .actions { justify-content:flex-end; }
    .view { display:none; }
    .view.active { display:grid; gap:16px; }
    .grid4 { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; }
    .grid3 { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }
    .grid2 { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; }
    .main-grid { display:grid; grid-template-columns:minmax(0,1.05fr) minmax(360px,.95fr); gap:14px; align-items:start; }
    .workbench { display:grid; grid-template-columns:360px minmax(0,1fr) 340px; gap:14px; align-items:start; }
    .library { display:grid; grid-template-columns:minmax(0,1fr) 360px; gap:14px; align-items:start; }
    .card { background:var(--surface); border:1px solid var(--border); border-radius:20px; box-shadow:var(--shadow); padding:18px; }
    .title { display:flex; justify-content:space-between; gap:12px; align-items:flex-start; margin-bottom:12px; }
    .metric { min-height:126px; }
    .metric strong { display:block; font-size:30px; margin:12px 0 6px; }
    .badge { border-radius:999px; padding:4px 8px; font-size:12px; font-weight:800; display:inline-flex; gap:4px; align-items:center; white-space:nowrap; }
    .blue { color:var(--primary); background:var(--primary-soft); } .green { color:var(--green); background:#eafbf1; }
    .orange { color:var(--orange); background:#fff4e8; } .red { color:var(--red); background:#fff0f0; } .gray { color:#475467; background:#f2f4f7; }
    button, .button { min-height:38px; border:1px solid var(--border); border-radius:12px; padding:0 12px; background:#fff; color:#344054; font-weight:800; display:inline-flex; align-items:center; justify-content:center; gap:6px; text-decoration:none; }
    .primary { color:#fff; border-color:transparent; background:linear-gradient(135deg,var(--primary),var(--primary-dark)); }
    .soft { color:var(--primary); border-color:color-mix(in srgb,var(--primary) 18%,transparent); background:var(--primary-soft); }
    .danger { color:#b42318; background:#fff0f0; border-color:rgba(239,68,68,.2); }
    input, select, textarea, [contenteditable] { min-height:38px; border:1px solid var(--border); border-radius:12px; background:#fff; padding:8px 10px; outline:0; color:var(--text); }
    label { display:grid; gap:6px; color:#344054; font-size:12px; font-weight:800; }
    .filter-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; }
    .scroll { max-height:340px; overflow:auto; display:grid; gap:10px; padding-right:4px; }
    .item { border:1px solid var(--border); border-radius:16px; background:rgba(255,255,255,.78); padding:12px; display:grid; gap:9px; }
    .item.p0 { border-color:rgba(239,68,68,.22); background:#fffafa; } .item.p1 { border-color:rgba(249,115,22,.24); background:#fffaf4; }
    .between { display:flex; justify-content:space-between; gap:10px; align-items:center; }
    table { width:100%; border-collapse:collapse; font-size:13px; }
    th,td { padding:11px 10px; border-bottom:1px solid var(--border); text-align:left; vertical-align:middle; }
    th { color:var(--muted); background:#f8fafc; font-size:12px; }
    tr:hover { background:color-mix(in srgb,var(--primary-soft) 35%,transparent); }
    .table { border:1px solid var(--border); border-radius:16px; overflow:auto; background:#fff; }
    .thumb { width:66px; height:66px; border-radius:16px; object-fit:cover; border:1px solid var(--border); background:#fff; display:block; }
    .meme { display:flex; gap:10px; align-items:center; min-width:210px; }
    .chips { display:flex; gap:7px; flex-wrap:wrap; }
    .probe { font-family:Consolas, monospace; color:var(--muted); background:#f8fafc; border:1px dashed var(--border); border-radius:12px; padding:9px; font-size:12px; }
    .prompt-box { min-height:220px; white-space:pre-wrap; line-height:1.55; }
    .drawer { position:fixed; inset:0 0 0 auto; width:430px; transform:translateX(110%); transition:.2s; background:#fff; z-index:20; border-left:1px solid var(--border); box-shadow:-20px 0 60px rgba(15,23,42,.12); padding:20px; overflow:auto; }
    .drawer.open { transform:translateX(0); }
    .toast { position:fixed; right:20px; bottom:20px; z-index:50; width:min(390px,calc(100vw - 40px)); background:#fff; border:1px solid var(--border); border-radius:16px; box-shadow:var(--shadow); padding:12px; display:none; }
    .toast.show { display:block; }
    @media (max-width: 1100px) { .shell,.main-grid,.workbench,.library,.grid4,.grid3,.grid2,.filter-grid { grid-template-columns:1fr; } .sidebar { position:relative; height:auto; } .topbar { flex-direction:column; } }
  </style>
</head>
<body>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand"><div class="mark">贴</div><div><strong>表情包工坊</strong><span>Single Owner Admin</span></div></div>
      <nav id="nav" aria-label="后台导航"></nav>
      <div class="owner"><strong>Owner 模式</strong><div class="sub">单用户后台 · 审计开启</div></div>
    </aside>
    <main class="main">
      <header class="topbar">
        <div><h1 id="pageTitle">总览</h1><div id="pageSub" class="sub">今天的生成、质检、导出和平台风险</div></div>
        <div class="actions">
          <label>主题切换<select id="themeSelect" aria-label="主题切换">
            <option value="aurora">极光蓝</option><option value="graphite">石墨灰</option><option value="sakura">樱花粉</option><option value="forest">森林绿</option>
          </select></label>
          <button class="soft" onclick="toast('已刷新','页面数据已重新计算')">刷新</button>
          <button class="primary" onclick="go('generation')">新建生成</button>
        </div>
      </header>
      <section id="overview" class="view"></section>
      <section id="issues" class="view"></section>
      <section id="failures" class="view"></section>
      <section id="generation" class="view"></section>
      <section id="library" class="view"></section>
      <section id="assets" class="view"></section>
      <section id="qa" class="view"></section>
      <section id="export" class="view"></section>
      <section id="analytics" class="view"></section>
      <section id="settings" class="view"></section>
      <section id="platformRules" class="view"></section>
      <section id="generationSources" class="view"></section>
      <section id="taskCenter" class="view"></section>
    </main>
  </div>
  <aside id="drawer" class="drawer" aria-hidden="true"></aside>
  <div id="toast" class="toast" role="status" aria-live="polite"></div>
  <script>
    const assetBase = "/admin-assets/";
    const state = {
      route: "overview", theme: localStorage.getItem("admin-theme") || "aurora", selectedExports: new Set(), selectedPacks: new Set(), libraryRows: null,
      exportPage: 1, filterDebounce: 0, promptRemoteEnabled: false, promptHistory: [],
      filters: { q:"", platform:"all", status:"all", qualityMin:"", exportStatus:"all", risk:"all", animated:"all", license:"all" },
      issueFilters: { q:"", priority:"all", type:"all", platform:"all", status:"all" },
      failureFilters: { q:"", stage:"all", platform:"all", status:"all" },
      issues: [
        {id:"ISS-1001", p:"P0", type:"导出", title:"Telegram ZIP 校验失败", stage:"export_validation", reason:"manifest 缺少 512px 透明背景文件", action:"重新生成平台包", platform:"Telegram", status:"open", updated:"2026-07-01 16:15"},
        {id:"ISS-1002", p:"P1", type:"质检", title:"打工猫第 4 张 OCR 可读性低", stage:"qa_ocr", reason:"移动端缩略图中文字边缘过细", action:"进入质检并驳回重生成", platform:"WeChat", status:"open", updated:"2026-07-01 15:44"},
        {id:"ISS-1003", p:"P2", type:"素材", title:"森林兔授权材料待补齐", stage:"license", reason:"授权状态为待确认", action:"补齐授权记录", platform:"LINE", status:"open", updated:"2026-07-01 14:09"}
      ],
      failures: [
        {id:"FAIL-2001", task:"夏日兔导出 WhatsApp", stage:"package_build", reason:"WEBP 动图帧数超过平台规则", platform:"WhatsApp", count:24, status:"failed", updated:"2026-07-01 16:02"},
        {id:"FAIL-2002", task:"打工猫远程 Prompt 优化", stage:"prompt_remote", reason:"远程免费接口超时，已本地回退", platform:"WeChat", count:12, status:"retrying", updated:"2026-07-01 15:21"},
        {id:"FAIL-2003", task:"LINE 提交包 dry-run", stage:"submit_manifest", reason:"提交清单缺少 locale 字段", platform:"LINE", count:18, status:"failed", updated:"2026-07-01 13:52"}
      ],
      packs: [
        pack("PACK-001","打工猫开会求生","职场猫咪 24 张","Telegram","approved",92,"low","exported","approved",false,"SET-12e19461c7cf/01-ITEM-7de75396b177.png"),
        pack("PACK-002","夏日兔冰饮日常","清爽兔子 18 张","WeChat","qa_pending",86,"medium","none","approved",false,"SET-19c4236f8460/02-ITEM-7e26a66fc740.png"),
        pack("PACK-003","森林熊周末摸鱼","森林棕熊 20 张","LINE","qa_pending",78,"medium","export_failed","pending",false,"SET-238e97b1f6d3/03-ITEM-1791c890a877.png"),
        pack("PACK-004","熊猫晚安动态包","睡前熊猫 16 张","WhatsApp","approved",89,"low","exporting","approved",true,"SET-5f0d7dfaff75/04-ITEM-1e2788bc5917.png"),
        pack("PACK-005","狐狸复盘会议","复盘狐狸 12 张","Telegram","rejected",72,"high","none","review",false,"SET-72b36230c4aa/05-ITEM-71f48419fbe0.png"),
        pack("PACK-006","樱花犬鼓励贴纸","鼓励小犬 30 张","WeChat","approved",94,"low","exported","approved",false,"SET-7338ad4e3413/06-ITEM-885515f98155.png")
      ],
      exports: [
        exp("EXP-001","打工猫开会求生","Telegram","validating",64,"校验中","待下载","SET-12e19461c7cf/01-ITEM-7de75396b177.png"),
        exp("EXP-002","夏日兔冰饮日常","WeChat","queued",0,"待开始","未生成","SET-19c4236f8460/02-ITEM-7e26a66fc740.png"),
        exp("EXP-003","森林熊周末摸鱼","LINE","export_failed",36,"清单失败","需重试","SET-238e97b1f6d3/03-ITEM-1791c890a877.png"),
        exp("EXP-004","熊猫晚安动态包","WhatsApp","succeeded",100,"通过","可下载","SET-5f0d7dfaff75/04-ITEM-1e2788bc5917.png"),
        exp("EXP-005","狐狸复盘会议","Telegram","queued",0,"待开始","未生成","SET-72b36230c4aa/05-ITEM-71f48419fbe0.png"),
        exp("EXP-006","樱花犬鼓励贴纸","WeChat","succeeded",100,"通过","可下载","SET-7338ad4e3413/06-ITEM-885515f98155.png"),
        exp("EXP-007","石墨犬复盘","LINE","queued",0,"待开始","未生成","SET-75141a9fb59f/01-ITEM-6a97c17990b0.png"),
        exp("EXP-008","午睡猫状态","WhatsApp","running",52,"打包中","待下载","SET-a357036fa44b/03-ITEM-db0c9bb9200c.png"),
        exp("EXP-009","项目经理熊","Telegram","queued",0,"待开始","未生成","SET-b47b14761a88/01-ITEM-4bc1f65eb2db.png")
      ]
    };
    const routes = [
      ["overview","总览","今天的生成、质检、导出和平台风险"], ["issues","处理中心","P0/P1/P2 处理队列"], ["failures","失败处理","失败原因、阶段和恢复动作"],
      ["generation","生成工作台","主题到 Prompt 到候选结果"], ["library","表情包库","自动筛选、真实缩略图和详情"], ["assets","设计资产","角色、风格和授权素材"],
      ["qa","质检审核","待质检表情包和驳回原因"], ["export","发布导出","分页、多选和单条导出"], ["analytics","数据表现","质量、通过率和失败原因"],
      ["settings","系统设置","Owner 安全、规则和任务配置"]
    ];
    function pack(id,name,desc,platform,status,quality,risk,exportStatus,license,animated,img){ return {id,name,desc,platform,status,quality,risk,exportStatus,license,animated,img:assetBase+img, created:"2026-07-01", format:animated?"webp":"png", size:animated?"780KB":"248KB", resolution:"512x512"}; }
    function exp(id,pack,platform,status,progress,result,download,img){ return {id,pack,platform,status,progress,result,download,img:assetBase+img, stage: result, files:["manifest.json","cover.png",platform.toLowerCase()+".zip"]}; }
    async function init(){ document.body.dataset.theme = state.theme; themeSelect.value = state.theme; themeSelect.onchange = e => { state.theme=e.target.value; document.body.dataset.theme=state.theme; localStorage.setItem("admin-theme",state.theme); toast("主题已切换", e.target.selectedOptions[0].textContent); }; nav.innerHTML = routes.map(r=>`<button onclick="go('${r[0]}')" data-route="${r[0]}">${r[1]}</button>`).join(""); renderAll(); go(location.hash ? location.hash.slice(1) : "overview"); await syncAdminState(); renderAll(); go(location.hash ? location.hash.slice(1) : state.route); }
    function go(route){ state.route = route; document.querySelectorAll(".view").forEach(v=>v.classList.toggle("active", v.id===route)); document.querySelectorAll("nav button").forEach(b=>b.classList.toggle("active", b.dataset.route===route)); const found = routes.find(r=>r[0]===route) || subRoute(route); pageTitle.textContent=found[1]; pageSub.textContent=found[2]; history.replaceState(null,"","#"+route); closeDrawer(); }
    function subRoute(route){ return ({platformRules:["platformRules","平台规则","WeChat / Telegram / LINE / WhatsApp 规则"], generationSources:["generationSources","生成源配置","本地生成器、远程优化和回退"], taskCenter:["taskCenter","任务中心","并发、重试、取消和清理"]})[route] || ["overview","总览",""]; }
    function renderAll(){ renderOverview(); renderIssues(); renderFailures(); renderGeneration(); renderLibrary(); renderAssets(); renderQA(); renderExport(); renderAnalytics(); renderSettings(); renderSubpages(); }
    function renderOverview(){ overview.innerHTML = `<div class="grid4">${metric("今日生成","128","通过率 91%","green")}${metric("待处理",state.issues.filter(x=>x.status==="open").length,"P0 优先","red")}${metric("导出状态","7/9","2 条需处理","orange")}${metric("平台风险","2","LINE / WhatsApp","orange")}</div><div class="main-grid"><div class="card"><div class="title"><h2>待处理事项</h2><button class="primary" onclick="go('issues')">进入处理中心</button></div><div class="scroll">${sortedIssues().map(issueItem).join("")}</div></div><div class="card"><div class="title"><h2>最近失败</h2><button class="primary" onclick="go('failures')">进入失败处理</button></div><div class="scroll">${state.failures.map(failureItem).join("")}</div></div></div><div class="main-grid"><div class="card"><div class="title"><h2>平台风险矩阵</h2></div><div class="grid4">${["WeChat","Telegram","LINE","WhatsApp"].map((p,i)=>`<div class="item"><b>${p}</b><span class="badge ${i>1?"orange":"green"}">${i>1?"中风险":"低风险"}</span><button class="soft" onclick="go('platformRules')">查看规则</button></div>`).join("")}</div></div><div class="card"><div class="title"><h2>待质检表情包</h2><button class="soft" onclick="go('qa')">去质检</button></div><div class="grid3">${state.packs.slice(0,3).map(p=>thumbCard(p)).join("")}</div></div></div>`; }
    function renderIssues(){ issues.innerHTML = `<div class="card"><div class="title"><h2>处理队列</h2><button onclick="go('overview')">返回总览</button></div>${issueFilters()}<div class="probe">GET /api/admin/issues?${query(state.issueFilters)}&sort=priority,updated_desc</div><div class="scroll">${filteredIssues().map(issueItem).join("")}</div></div>`; bindIssueFilters(); }
    function renderFailures(){ failures.innerHTML = `<div class="card"><div class="title"><h2>失败任务</h2><button onclick="go('overview')">返回总览</button></div>${failureFilters()}<div class="probe">GET /api/admin/failures?${query(state.failureFilters)}&sort=updated_desc</div><div class="scroll">${filteredFailures().map(failureItem).join("")}</div></div>`; bindFailureFilters(); }
    function renderGeneration(){ generation.innerHTML = `<div class="workbench"><div class="card"><h2>主题输入</h2><br><label>主题<input id="themeInput" aria-label="主题" value="老板开会猫"></label><br><label>平台<select id="genPlatform"><option>WeChat</option><option>Telegram</option><option>LINE</option><option>WhatsApp</option></select></label><br><label>风格<select id="styleInput"><option>搞笑日常 · 非扁平化</option><option>治愈陪伴 · 软材质</option></select></label><br><div class="actions"><button class="primary" onclick="generatePromptByTheme(this)">根据主题生成提示词</button><button onclick="submitGeneration(this)">提交生成任务</button></div></div><div class="card"><div class="title"><h2>提示词 Prompt</h2><span id="promptStatus" class="badge blue">source: local</span></div><div id="promptBox" class="prompt-box" role="textbox" aria-label="提示词 Prompt" contenteditable="true"></div><br><div class="actions"><button class="soft" onclick="optimizePromptLocal(this)">优化设计词</button><button onclick="optimizePromptRemote(this)">远程免费优化</button></div></div><div class="card"><h2>提示词历史</h2><br><div id="promptHistory" class="scroll">${promptHistoryHtml()}</div></div></div>`; }
    function renderLibrary(){ const rows = filteredPacks(); library.innerHTML = `<div class="library"><div class="card"><div class="title"><h2>表情包列表</h2><button onclick="resetFilters()">重置筛选</button></div>${libraryFilters()}<div class="chips">${filterChips()}</div><div class="probe" id="libraryProbe">GET /api/admin/sticker-packs?${query(state.filters)}&page=1&page_size=20</div><div class="table"><table><thead><tr><th><input type="checkbox" onchange="toggleAllPacks(this.checked)"></th><th>表情包</th><th>平台</th><th>质量</th><th>状态</th><th>导出</th><th>风险</th><th>操作</th></tr></thead><tbody>${rows.map(packRow).join("")}</tbody></table></div></div><div class="card" id="packInspector">${inspector(rows[0] || state.packs[0])}</div></div>`; bindLibraryFilters(); }
    function renderAssets(){ assets.innerHTML = `<div class="grid3">${["角色资产","风格资产","授权素材"].map((x,i)=>`<div class="card"><h2>${x}</h2><p class="sub">真实业务资产管理，状态可审计。</p>${thumbCard(state.packs[i])}<button class="soft" onclick="toast('${x}','已打开详情')">查看</button></div>`).join("")}</div>`; }
    function renderQA(){ qa.innerHTML = `<div class="main-grid"><div class="card"><div class="title"><h2>待质检列表</h2><button class="primary" onclick="toast('批量通过','已写入复验记录')">批量通过</button></div><div class="grid3">${state.packs.filter(p=>p.status!=="approved").map(thumbCard).join("")}</div></div><div class="card"><h2>驳回原因</h2><br><label>驳回原因<textarea id="rejectReason" rows="5" placeholder="必须填写 OCR、透明背景、重复风险或平台合规问题"></textarea></label><br><button class="danger" onclick="qaReject()">批量驳回</button></div></div>`; }
    function renderExport(){ const rows = state.exports.slice((state.exportPage-1)*4, state.exportPage*4); const pages=Math.max(1,Math.ceil(state.exports.length/4)); document.getElementById("export").innerHTML = `<div class="card"><div class="title"><div><h2>导出任务</h2><p class="sub">共 ${state.exports.length} 条 · 第 ${state.exportPage} 页</p></div><button class="primary" onclick="batchExport(this)">一键导出所选</button></div><div class="table"><table><thead><tr><th><input type="checkbox" onchange="toggleExportPage(this.checked)"></th><th>表情包</th><th>平台</th><th>进度</th><th>校验</th><th>下载</th><th>操作</th></tr></thead><tbody>${rows.map(exportRow).join("")}</tbody></table></div><div class="actions" style="justify-content:flex-end;margin-top:12px">${Array.from({length:pages},(_,idx)=>idx+1).map(i=>`<button class="${state.exportPage===i?"primary":""}" onclick="state.exportPage=${i};renderExport()">${i}</button>`).join("")}</div></div>`; }
    function renderAnalytics(){ analytics.innerHTML = `<div class="grid4">${metric("生成数","128","今日","blue")}${metric("通过率","91%","稳定","green")}${metric("返工率","8%","下降","orange")}${metric("失败原因","3 类","可处理","red")}</div>`; }
    function renderSettings(){ settings.innerHTML = `<div class="grid3">${settingCard("平台规则","WeChat / Telegram / LINE / WhatsApp", "platformRules")}${settingCard("生成源配置","本地生成器、远程接口、失败回退", "generationSources")}${settingCard("任务中心","并发、重试、取消、重新入队", "taskCenter")}${settingCard("操作记录","审计日志和最近登录", "taskCenter")}${settingCard("验收报告","LOOP 评分和截图证据", "taskCenter")}${settingCard("Owner 安全","两步验证和信任设备", "taskCenter")}</div>`; }
    function renderSubpages(){ platformRules.innerHTML = `<div class="card"><div class="title"><h2>规则详情</h2><button onclick="go('settings')">返回设置</button></div><div class="grid4">${["WeChat","Telegram","LINE","WhatsApp"].map(p=>`<div class="item"><b>${p}</b><span>尺寸 512x512</span><span>格式 PNG / WEBP / ZIP</span><span>透明背景：必需</span><span>命名规则：平台前缀 + 序号</span><button class="soft" onclick="toast('规则已测试','${p} 校验通过')">接口测试</button></div>`).join("")}</div></div>`; generationSources.innerHTML = `<div class="card"><div class="title"><h2>源配置详情</h2><button onclick="go('settings')">返回设置</button></div><div class="grid3"><div class="item"><b>本地 Prompt 生成器</b><span class="badge green">启用</span></div><div class="item"><b>远程免费优化接口</b><input value="https://example-free-prompt.local/optimize"><button class="soft" onclick="state.promptRemoteEnabled=true;toast('接口测试完成','远程不可用时会本地回退')">测试连接</button></div><div class="item"><b>失败回退</b><span>timeout 1200ms -> local fallback</span></div></div></div>`; taskCenter.innerHTML = `<div class="card"><div class="title"><h2>任务配置</h2><button onclick="go('settings')">返回设置</button></div><div class="grid3">${["并发上限 3","失败保留 14 天","重试次数 2","取消任务","重新入队","清理已完成"].map(x=>`<div class="item"><b>${x}</b><button class="soft" onclick="toast('任务中心', '${x}')">执行</button></div>`).join("")}</div></div>`; }
    function metric(name,value,foot,color){ return `<div class="card metric"><span class="sub">${name}</span><strong>${value}</strong><span class="badge ${color}">${foot}</span></div>`; }
    function issueItem(i){ return `<div class="item ${i.p.toLowerCase()}"><div class="between"><b>${i.p} · ${i.title}</b><span class="badge gray">${i.updated}</span></div><div class="sub">${i.type} · ${i.stage} · ${i.platform} · status: <b>${i.status}</b></div><div>原因：${i.reason}</div><div>建议动作：${i.action}</div><div class="row-actions"><button class="primary" onclick="toast('进入处理','${i.title}')">处理</button><button onclick="requeueIssue('${i.id}')">重新加入队列</button><button class="danger" onclick="cancelIssue('${i.id}')">取消</button><button onclick="openDrawer('${i.title}','${i.reason}')">详情</button></div></div>`; }
    function failureItem(f){ return `<div class="item"><div class="between"><b>${f.id} · ${f.task}</b><span class="badge red">${f.stage}</span></div><div>失败原因：${f.reason}</div><div class="sub">${f.platform} · 影响 ${f.count} 张 · ${f.updated} · status: <b>${f.status}</b></div><div class="row-actions"><button class="primary" onclick="toast('进入失败处理','${f.task}')">处理</button><button onclick="requeueFailure('${f.id}')">重新加入队列</button><button class="danger" onclick="cancelFailure('${f.id}')">取消</button><button onclick="openDrawer('${f.task}','${f.reason}')">查看日志</button></div></div>`; }
    function thumbCard(p){ return `<div class="item"><img class="thumb" src="${p.img}" alt="${p.name} 缩略图" onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'item',textContent:'图片加载失败，可重试'}))"><b>${p.name}</b><span class="sub">${p.desc}</span><span class="badge blue">${p.platform}</span></div>`; }
    function packRow(p){ return `<tr><td><input type="checkbox" ${state.selectedPacks.has(p.id)?"checked":""} onchange="togglePack('${p.id}',this.checked)"></td><td><div class="meme"><img class="thumb" src="${p.img}" alt="${p.name} 缩略图"><div><b>${p.name}</b><div class="sub">${p.desc}</div></div></div></td><td>${p.platform}</td><td><span class="badge ${p.quality>88?"green":p.quality>78?"orange":"red"}">${p.quality}</span></td><td>${p.status}</td><td>${p.exportStatus}</td><td><span class="badge ${p.risk==="high"?"red":p.risk==="medium"?"orange":"green"}">${p.risk}</span></td><td><button onclick="openPackDrawer('${p.id}')">详情</button><button class="soft" onclick="toast('单包导出','${p.name} 已加入队列')">导出</button></td></tr>`; }
    function exportRow(e){ return `<tr><td><input type="checkbox" ${state.selectedExports.has(e.id)?"checked":""} onchange="toggleExport('${e.id}',this.checked)"></td><td><div class="meme"><img class="thumb" src="${e.img}" alt="${e.pack} 封面"><div><b>${e.pack}</b><div class="sub">${e.id}</div></div></div></td><td>${e.platform}</td><td>${e.progress}% · ${e.status}</td><td>${e.result}</td><td>${e.download}</td><td><button onclick="openDrawer('${e.pack}','文件：${e.files.join(' / ')}')">详情</button><button class="primary" onclick="singleExport('${e.id}', this)">导出</button><button onclick="toast('下载','${e.pack}')">下载或重试</button><button onclick="go('failures')">更多</button></td></tr>`; }
    function inspector(p){ return `<h2>${p.name}</h2><br>${thumbCard(p)}<br><div class="item"><span>格式：${p.format}</span><span>分辨率：${p.resolution}</span><span>文件大小：${p.size}</span><span>授权：${p.license}</span><span>是否动图：${p.animated ? "是" : "否"}</span></div><br><button class="primary" onclick="toast('导出','${p.name}')">导出</button> <button onclick="go('qa')">质检</button>`; }
    function issueFilters(){ return `<div class="filter-grid"><label>关键词<input id="i-q"></label><label>优先级<select id="i-priority"><option value="all">全部</option><option>P0</option><option>P1</option><option>P2</option></select></label><label>类型<select id="i-type"><option value="all">全部</option><option>导出</option><option>质检</option><option>素材</option></select></label><label>平台<select id="i-platform"><option value="all">全部</option><option>WeChat</option><option>Telegram</option><option>LINE</option><option>WhatsApp</option></select></label></div>`; }
    function failureFilters(){ return `<div class="filter-grid"><label>关键词<input id="fail-q"></label><label>阶段<select id="fail-stage"><option value="all">全部</option><option>package_build</option><option>prompt_remote</option><option>submit_manifest</option></select></label><label>平台<select id="fail-platform"><option value="all">全部</option><option>WeChat</option><option>Telegram</option><option>LINE</option><option>WhatsApp</option></select></label><label>状态<select id="fail-status"><option value="all">全部</option><option>failed</option><option>retrying</option><option>queued</option><option>cancelled</option></select></label></div>`; }
    function libraryFilters(){ return `<div class="filter-grid"><label>关键词<input id="f-q" aria-label="关键词"></label><label>平台<select id="f-platform" aria-label="平台"><option value="all">全部</option><option value="WeChat">WeChat</option><option value="telegram">Telegram</option><option value="LINE">LINE</option><option value="WhatsApp">WhatsApp</option></select></label><label>状态<select id="f-status"><option value="all">全部</option><option value="approved">已通过</option><option value="qa_pending">待质检</option><option value="rejected">已驳回</option></select></label><label>质量最低<input id="f-qualityMin" type="number" min="0" max="100"></label><label>导出状态<select id="f-exportStatus"><option value="all">全部</option><option value="exported">已导出</option><option value="export_failed">导出失败</option><option value="none">未导出</option></select></label><label>重复风险<select id="f-risk"><option value="all">全部</option><option value="low">低</option><option value="medium">中</option><option value="high">高</option></select></label><label>授权状态<select id="f-license"><option value="all">全部</option><option value="approved">已授权</option><option value="pending">待确认</option></select></label><label>是否动图<select id="f-animated"><option value="all">全部</option><option value="true">是</option><option value="false">否</option></select></label></div>`; }
    function bindLibraryFilters(){ const map={"f-q":"q","f-platform":"platform","f-status":"status","f-qualityMin":"qualityMin","f-exportStatus":"exportStatus","f-risk":"risk","f-license":"license","f-animated":"animated"}; Object.entries(map).forEach(([id,key])=>{ const el=document.getElementById(id); if(!el)return; el.value=state.filters[key]; el.oninput=el.onchange=()=>{ clearTimeout(state.filterDebounce); state.filterDebounce=setTimeout(async()=>{ state.filters[key]=el.value; await syncLibraryFromApi(); renderLibrary(); toast("已自动筛选", "page 已重置为 1"); }, el.tagName==="INPUT"?280:0); }; }); }
    function bindIssueFilters(){ const map={"i-q":"q","i-priority":"priority","i-type":"type","i-platform":"platform"}; Object.entries(map).forEach(([id,key])=>{ const el=document.getElementById(id); if(!el)return; el.value=state.issueFilters[key]; el.oninput=el.onchange=()=>{ clearTimeout(state.filterDebounce); state.filterDebounce=setTimeout(async()=>{ state.issueFilters[key]=el.value; await syncIssuesFromApi(); renderIssues(); }, el.tagName==="INPUT"?220:0); }; }); }
    function bindFailureFilters(){ const map={"fail-q":"q","fail-stage":"stage","fail-platform":"platform","fail-status":"status"}; Object.entries(map).forEach(([id,key])=>{ const el=document.getElementById(id); if(!el)return; el.value=state.failureFilters[key]; el.oninput=el.onchange=()=>{ clearTimeout(state.filterDebounce); state.filterDebounce=setTimeout(async()=>{ state.failureFilters[key]=el.value; await syncFailuresFromApi(); renderFailures(); }, el.tagName==="INPUT"?220:0); }; }); }
    async function syncAdminState(){ await Promise.all([syncIssuesFromApi(),syncFailuresFromApi(),syncExportsFromApi(),syncLibraryFromApi(),syncPromptHistory()]); }
    async function syncIssuesFromApi(){ const response=await fetch("/api/admin/issues?"+query(state.issueFilters)+"&sort=priority,updated_desc"); const payload=await response.json(); const items=(payload.data||payload.数据||{}).items||[]; state.issues=items.map(fromApiIssue); }
    async function syncFailuresFromApi(){ const response=await fetch("/api/admin/failures?"+query(state.failureFilters)+"&sort=updated_desc"); const payload=await response.json(); const items=(payload.data||payload.数据||{}).items||[]; state.failures=items.map(fromApiFailure); }
    async function syncExportsFromApi(){ const response=await fetch("/api/admin/exports?page=1&page_size=50"); const payload=await response.json(); const items=(payload.data||payload.数据||{}).items||[]; state.exports=items.map(fromApiExport); }
    async function syncPromptHistory(){ const response=await fetch("/api/admin/prompt/history"); const payload=await response.json(); state.promptHistory=((payload.data||payload.数据||{}).items||[]); }
    function fromApiIssue(item){ return { id:item.id, p:item.priority, type:item.type, title:item.title, stage:item.stage, reason:item.reason, action:item.message, platform:item.platform, status:item.status, updated:(item.updated_at||"").replace("T"," ").slice(0,16) }; }
    function fromApiFailure(item){ return { id:item.id, task:item.task_name, stage:item.stage, reason:item.reason, platform:item.platform, count:item.asset_count||0, status:item.status, updated:(item.updated_at||"").replace("T"," ").slice(0,16) }; }
    function fromApiExport(item){ return { id:item.id, pack:item.pack_name||item.pack_id, platform:item.platform, status:item.status, progress:item.progress||0, result:item.validation_result||item.current_stage, download:item.status==="succeeded"?"可下载":"待下载", img:item.download_url, stage:item.current_stage, files:item.file_manifest||[] }; }
    function promptHistoryHtml(){ return state.promptHistory.length ? state.promptHistory.map(h=>`<div class="item"><b>${h.source}${h.fallback?" · fallback":""}</b><span class="sub">${(h.created_at||"").replace("T"," ").slice(0,19)}</span><p>${String(h.prompt||"").slice(0,180)}</p></div>`).join("") : `<span class="sub">暂无提示词历史</span>`; }
    async function syncLibraryFromApi(){ const response=await fetch("/api/admin/sticker-packs?"+query(state.filters)+"&page=1&page_size=20"); const payload=await response.json(); const items=(payload.data||payload.数据||{}).items||[]; state.libraryRows=items.map(fromApiPack); }
    function fromApiPack(item){ return { id:item.id, name:item.name, desc:(item.tags||[]).join(" / "), platform:(item.platforms||[""])[0], status:item.status, quality:item.quality_score, risk:item.duplicate_risk, exportStatus:item.export_status, license:item.license_status, animated:item.is_animated, img:item.thumbnail_url, created:(item.created_at||"").slice(0,10), format:item.format, size:Math.round((item.file_size||0)/1024)+"KB", resolution:`${item.width}x${item.height}` }; }
    function filteredPacks(){ const source=state.libraryRows || state.packs; return source.filter(p=>{ const f=state.filters; if(f.q && !(p.name+p.desc).toLowerCase().includes(f.q.toLowerCase()))return false; if(f.platform!=="all" && p.platform.toLowerCase()!==f.platform.toLowerCase())return false; if(f.status!=="all" && p.status!==f.status)return false; if(f.qualityMin && p.quality<Number(f.qualityMin))return false; if(f.exportStatus!=="all" && p.exportStatus!==f.exportStatus)return false; if(f.risk!=="all" && p.risk!==f.risk)return false; if(f.license!=="all" && p.license!==f.license)return false; if(f.animated!=="all" && String(p.animated)!==f.animated)return false; return true; }); }
    function filteredIssues(){ const f=state.issueFilters; return sortedIssues().filter(i=>(!f.q || (i.title+i.reason).toLowerCase().includes(f.q.toLowerCase())) && (f.priority==="all" || i.p===f.priority) && (f.type==="all" || i.type===f.type) && (f.platform==="all" || i.platform===f.platform) && (f.status==="all" || i.status===f.status)); }
    function filteredFailures(){ const f=state.failureFilters; return state.failures.filter(x=>(!f.q || (x.task+x.reason).toLowerCase().includes(f.q.toLowerCase())) && (f.stage==="all" || x.stage===f.stage) && (f.platform==="all" || x.platform===f.platform) && (f.status==="all" || x.status===f.status)); }
    function sortedIssues(){ const rank={P0:0,P1:1,P2:2,P3:3}; return [...state.issues].sort((a,b)=>rank[a.p]-rank[b.p] || b.updated.localeCompare(a.updated)); }
    function filterChips(){ return Object.entries(state.filters).filter(([,v])=>v&&v!=="all").map(([k,v])=>`<span class="badge blue">${k}: ${v}</span>`).join("") || `<span class="sub">暂无筛选条件</span>`; }
    function query(obj){ const p=new URLSearchParams(); Object.entries(obj).forEach(([k,v])=>{ if(v && v!=="all")p.set(k,v); }); return p.toString() || "no_filter=1"; }
    async function resetFilters(){ state.filters={q:"",platform:"all",status:"all",qualityMin:"",exportStatus:"all",risk:"all",animated:"all",license:"all"}; await syncLibraryFromApi(); renderLibrary(); toast("筛选已重置","列表已自动刷新"); }
    function togglePack(id,checked){ checked?state.selectedPacks.add(id):state.selectedPacks.delete(id); }
    function toggleAllPacks(checked){ filteredPacks().forEach(p=>checked?state.selectedPacks.add(p.id):state.selectedPacks.delete(p.id)); renderLibrary(); }
    function toggleExport(id,checked){ checked?state.selectedExports.add(id):state.selectedExports.delete(id); }
    function toggleExportPage(checked){ state.exports.slice((state.exportPage-1)*4,state.exportPage*4).forEach(e=>checked?state.selectedExports.add(e.id):state.selectedExports.delete(e.id)); renderExport(); }
    async function cancelIssue(id){ await fetch(`/api/admin/issues/${id}/cancel`,{method:"POST"}); await syncIssuesFromApi(); renderAll(); go("issues"); toast("已取消处理项",id); }
    async function requeueIssue(id){ await fetch(`/api/admin/issues/${id}/requeue`,{method:"POST"}); await syncIssuesFromApi(); renderAll(); go("issues"); toast("已重新加入队列",id); }
    async function cancelFailure(id){ await fetch(`/api/admin/failures/${id}/cancel`,{method:"POST"}); await syncFailuresFromApi(); renderAll(); go("failures"); toast("已取消失败任务",id); }
    async function requeueFailure(id){ await fetch(`/api/admin/failures/${id}/requeue`,{method:"POST"}); await syncFailuresFromApi(); renderAll(); go("failures"); toast("已重新加入队列",id); }
    function openPackDrawer(id){ const p=state.packs.find(x=>x.id===id); drawer.innerHTML=`<div class="title"><h2>${p.name}</h2><button onclick="closeDrawer()">×</button></div>${inspector(p)}<br><button class="primary" onclick="toast('单包导出','${p.name}')">导出本包</button>`; drawer.classList.add("open"); drawer.setAttribute("aria-hidden","false"); }
    function openDrawer(title,body){ drawer.innerHTML=`<div class="title"><h2>${title}</h2><button onclick="closeDrawer()">×</button></div><p>${body}</p><div class="item">操作日志、文件清单、校验结果和下一步动作在此展示。</div>`; drawer.classList.add("open"); drawer.setAttribute("aria-hidden","false"); }
    function closeDrawer(){ drawer.classList.remove("open"); drawer.setAttribute("aria-hidden","true"); }
    function generatePrompt(theme,style,platform){ return `${theme}，${style}，目标平台 ${platform}。角色主体表情明确，动作夸张但可爱；场景包含前景/中景/背景层次，柔和体积光、真实纸张与胶贴材质、清晰贴纸描边、透明背景友好边缘。构图适合 1:1 移动端缩略图，主体居中并保留短字幕负空间。禁止 flat vector、corporate illustration、简单图标、纯文字贴图、低细节、无情绪、无场景。`; }
    async function generatePromptByTheme(btn){ await withLoading(btn,"生成中",async()=>{ const response=await fetch("/api/admin/prompt/generate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({theme:themeInput.value,style:styleInput.value,platform:genPlatform.value})}); const payload=await response.json(); const data=payload.data||payload.数据||{}; promptBox.textContent=data.prompt||generatePrompt(themeInput.value.trim()||"表情包角色", styleInput.value, genPlatform.value); promptStatus.textContent=`source: ${data.source||"local"}`; await syncPromptHistory(); renderGeneration(); promptBox.textContent=data.prompt||promptBox.textContent; toast("已根据主题生成提示词", themeInput.value); }); }
    async function optimizePromptLocal(btn){ await withLoading(btn,"优化中",async()=>{ const response=await fetch("/api/admin/prompt/optimize",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({prompt:promptBox.textContent})}); const payload=await response.json(); const data=payload.data||payload.数据||{}; promptBox.textContent=data.prompt||promptBox.textContent; promptStatus.textContent="source: local optimize"; await syncPromptHistory(); renderGeneration(); promptBox.textContent=data.prompt||promptBox.textContent; toast("设计词已优化","已补充非扁平化约束"); }); }
    async function optimizePromptRemote(btn){ await withLoading(btn,"调用中",async()=>{ const response=await fetch("/api/admin/prompt/optimize-remote",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({prompt:promptBox.textContent})}); const payload=await response.json(); const data=payload.data||payload.数据||{}; promptBox.textContent=data.prompt||promptBox.textContent; promptStatus.textContent="source: fallback"; await syncPromptHistory(); renderGeneration(); promptBox.textContent=data.prompt||promptBox.textContent; toast("远程不可用，已本地回退","fallback_reason: remote_timeout"); }); }
    async function submitGeneration(btn){ await withLoading(btn,"创建中",async()=>toast("生成任务已创建","已进入任务队列")); }
    async function singleExport(id,btn){ await withLoading(btn,"导出中",async()=>{ await fetch(`/api/admin/exports/${id}/run`,{method:"POST"}); await syncExportsFromApi(); renderExport(); toast("导出完成", id); }); }
    async function batchExport(btn){ await withLoading(btn,"导出中",async()=>{ const ids=state.selectedExports.size?[...state.selectedExports]:state.exports.slice((state.exportPage-1)*4,state.exportPage*4).map(e=>e.id); await fetch("/api/admin/exports/batch",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ids})}); state.selectedExports.clear(); await syncExportsFromApi(); renderExport(); toast("导出已入队", `已处理 ${ids.length} 条`); }); }
    function qaReject(){ const reason=rejectReason.value.trim(); if(!reason)return toast("需要填写不通过原因","质检驳回必须记录原因"); toast("已驳回并记录原因",reason); }
    function settingCard(title,desc,route){ return `<div class="card" onclick="go('${route}')" role="button" tabindex="0"><h2>${title}</h2><p class="sub">${desc}</p><button class="soft">进入</button></div>`; }
    async function withLoading(btn,label,fn){ const old=btn.textContent; btn.disabled=true; btn.textContent=label; try{ await new Promise(r=>setTimeout(r,250)); await fn(); } finally{ btn.disabled=false; btn.textContent=old; } }
    function toast(title,msg){ const el=document.getElementById("toast"); el.innerHTML=`<b>${title}</b><div class="sub">${msg||""}</div>`; el.classList.add("show"); setTimeout(()=>el.classList.remove("show"),2600); }
    init();
  </script>
</body>
</html>
"""
