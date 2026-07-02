const navItems = [
  { key: 'overview', label: '总览', icon: '◎', title: '总览', sub: '今天的生成、质检、导出和平台风险' },
  { key: 'generation', label: '生成工作台', icon: '✦', title: '生成工作台', sub: '主题驱动生成 Prompt，创建非扁平化表情包任务' },
  { key: 'library', label: '表情包库', icon: '▣', title: '表情包库', sub: '自动筛选、真实缩略图、详情与导出' },
  { key: 'assets', label: '设计资产', icon: '◈', title: '设计资产', sub: '角色、风格板、字体、授权素材与参考模板' },
  { key: 'qa', label: '质检审核', icon: '✓', title: '质检审核', sub: '检查视觉质量、平台规格、重复风险与授权问题' },
  { key: 'export', label: '发布导出', icon: '⇧', title: '发布导出', sub: '分页、多选、一键导出和单条导出' },
  { key: 'analytics', label: '数据表现', icon: '⌁', title: '数据表现', sub: '生成质量、平台通过率、失败原因与返工效率' },
  { key: 'settings', label: '系统设置', icon: '⚙', title: '系统设置', sub: '平台规则、生成源配置、主题、安全与验收报告' }
];

const priorityRank = { P0: 0, P1: 1, P2: 2, P3: 3 };
const state = {
  route: 'overview',
  theme: 'aurora',
  selectedPackId: 'pack-001',
  selectedQAId: 'qa-001',
  selectedExportId: 'exp-001',
  exportPage: 1,
  exportPageSize: 4,
  selectedExportRows: new Set(['exp-001']),
  selectedRows: new Set(['pack-001']),
  filters: {
    q: '', platform: 'all', status: 'all', qualityMin: '', qualityMax: '', exportStatus: 'all', risk: 'all', created: '', type: 'all'
  },
  issueFilters: { q: '', priority: 'all', type: 'all', platform: 'all', status: 'open' },
  failureFilters: { q: '', stage: 'all', platform: 'all', status: 'open' },
  settingsPage: 'home',
  promptRemoteEnabled: false,
  promptEndpoint: 'https://example.com/free-prompt-optimize',
  packs: [
    { id:'pack-001', name:'夏日柴犬 2.0', desc:'阳光、沙滩、柴犬的夏日派对', count:24, quality:92, platform:['wechat','telegram','tiktok'], status:'exported', exportStatus:'success', risk:'low', created:'2026-07-01', type:'animated', face:'🐶', cls:'dog', caption:'夏日开摆' },
    { id:'pack-002', name:'猫星人日常', desc:'治愈系猫咪的日常生活', count:28, quality:78, platform:['wechat','telegram'], status:'approved', exportStatus:'partial', risk:'medium', created:'2026-06-30', type:'static', face:'🐱', cls:'cat', caption:'我太难了' },
    { id:'pack-003', name:'柯基的幸福时光', desc:'可爱柯基的快乐日常', count:20, quality:85, platform:['wechat','line'], status:'qa_pending', exportStatus:'none', risk:'low', created:'2026-06-30', type:'static', face:'🐕', cls:'dog', caption:'冲呀' },
    { id:'pack-004', name:'职场摸鱼图鉴', desc:'打工人的幽默日常', count:32, quality:65, platform:['wechat','telegram'], status:'rejected', exportStatus:'failed', risk:'high', created:'2026-06-29', type:'static', face:'🐱', cls:'cat', caption:'别催' },
    { id:'pack-005', name:'甜心兔兔', desc:'软萌兔兔的可爱瞬间', count:18, quality:90, platform:['line','whatsapp'], status:'approved', exportStatus:'success', risk:'low', created:'2026-06-29', type:'animated', face:'🐰', cls:'rabbit', caption:'收到' },
    { id:'pack-006', name:'熊猫滚滚系列', desc:'圆滚滚熊猫的放松日常', count:24, quality:71, platform:['wechat'], status:'qa_pending', exportStatus:'none', risk:'medium', created:'2026-06-28', type:'static', face:'🐼', cls:'panda', caption:'躺平' },
    { id:'pack-007', name:'狐狸灵感库', desc:'聪明狐狸的灵感瞬间', count:16, quality:88, platform:['telegram','whatsapp'], status:'approved', exportStatus:'success', risk:'low', created:'2026-06-28', type:'static', face:'🦊', cls:'fox', caption:'懂了' },
    { id:'pack-008', name:'熊老板会议室', desc:'会议场景的幽默表达', count:22, quality:73, platform:['wechat','line'], status:'draft', exportStatus:'none', risk:'medium', created:'2026-06-27', type:'static', face:'🐻', cls:'bear', caption:'开会中' }
  ],
  issues: [
    { id:'iss-001', p:'P0', type:'导出失败', title:'Telegram 表情包_20260701_01 打包超时', stage:'文件打包', reason:'ZIP 打包任务超过 180 秒，manifest 已生成但资源未完全写入。', action:'重试打包', target:'export', platform:'Telegram', status:'open', updated:'2026-07-01 14:52' },
    { id:'iss-002', p:'P0', type:'平台风险', title:'WeChat 存在 3 个高风险问题', stage:'平台规则校验', reason:'3 张图含透明边缘噪点，1 张 OCR 对比度不足。', action:'进入质检复验', target:'qa', platform:'WeChat', status:'open', updated:'2026-07-01 14:48' },
    { id:'iss-003', p:'P1', type:'质检驳回', title:'职场摸鱼图鉴文字对比度偏低', stage:'OCR 可读性', reason:'白字叠在浅色背景，移动端缩略图不可读。', action:'一键生成修复建议', target:'qa', platform:'WeChat', status:'open', updated:'2026-07-01 14:22' },
    { id:'iss-004', p:'P1', type:'失败队列', title:'LINE 上传 API 返回 429', stage:'平台提交', reason:'免费额度被限流，需要排队重试或取消任务。', action:'重新加入队列', target:'failureCenter', platform:'LINE', status:'open', updated:'2026-07-01 14:12' },
    { id:'iss-005', p:'P2', type:'资料缺失', title:'12 个表情包缺少标签', stage:'元数据补全', reason:'缺少标签会影响筛选、统计与平台提交清单。', action:'批量补标签', target:'library', platform:'All', status:'open', updated:'2026-07-01 13:41' },
    { id:'iss-006', p:'P2', type:'重复风险', title:'猫星人日常存在 2 张相似项', stage:'重复检测', reason:'构图和文字高度相似，需要替换或归档。', action:'打开相似项', target:'library', platform:'Telegram', status:'open', updated:'2026-07-01 13:10' }
  ],
  failures: [
    { id:'fail-001', task:'Telegram 气泡狗 16P', stage:'打包导出', reason:'文件打包超时', platform:'Telegram', status:'open', updated:'2026-07-01 14:32', action:'重新加入队列', target:'export' },
    { id:'fail-002', task:'LINE 摇摆猫 24P', stage:'上传平台', reason:'API 返回 429 限流', platform:'LINE', status:'open', updated:'2026-07-01 14:12', action:'排队重试', target:'failureCenter' },
    { id:'fail-003', task:'WhatsApp 职场系列 32P', stage:'生成缩略图', reason:'图片处理失败', platform:'WhatsApp', status:'open', updated:'2026-07-01 13:58', action:'重新生成缩略图', target:'generation' },
    { id:'fail-004', task:'WeChat 夏日清凉 20P', stage:'校验资源', reason:'尺寸不符合规范', platform:'WeChat', status:'open', updated:'2026-07-01 13:26', action:'进入平台规则', target:'platformRules' },
    { id:'fail-005', task:'会议发言猫 8P', stage:'内容质检', reason:'OCR 文字过小', platform:'WeChat', status:'cancelled', updated:'2026-07-01 12:40', action:'查看详情', target:'qa' }
  ],
  exports: [
    { id:'exp-001', pack:'夏日柴犬 2.0', platform:'微信表情开放平台', format:'ZIP', stage:'校验中', progress:40, result:'通过', download:'未生成', time:'2026-07-01 14:32', status:'running', face:'🐶', cls:'dog', selected:true },
    { id:'exp-002', pack:'猫咪收藏家 V2', platform:'LINE Creators Market', format:'ZIP', stage:'已完成', progress:100, result:'通过', download:'可下载', time:'2026-07-01 12:18', status:'success', face:'🐱', cls:'cat' },
    { id:'exp-003', pack:'冲浪柴犬系列', platform:'WhatsApp', format:'WEBP', stage:'提交中', progress:60, result:'通过', download:'可下载', time:'2026-07-01 11:05', status:'running', face:'🐕', cls:'dog' },
    { id:'exp-004', pack:'音乐猫咪 1.5', platform:'Telegram', format:'WEBP', stage:'失败', progress:100, result:'失败', download:'不可用', time:'2026-07-01 09:42', status:'failed', face:'🐱', cls:'cat' },
    { id:'exp-005', pack:'甜心兔兔', platform:'LINE Creators Market', format:'APNG ZIP', stage:'待导出', progress:0, result:'未校验', download:'未生成', time:'2026-06-30 19:42', status:'pending', face:'🐰', cls:'rabbit' },
    { id:'exp-006', pack:'熊猫滚滚系列', platform:'微信表情开放平台', format:'PNG ZIP', stage:'待导出', progress:0, result:'未校验', download:'未生成', time:'2026-06-30 17:22', status:'pending', face:'🐼', cls:'panda' },
    { id:'exp-007', pack:'狐狸灵感库', platform:'Telegram', format:'WEBP', stage:'已完成', progress:100, result:'通过', download:'可下载', time:'2026-06-29 16:11', status:'success', face:'🦊', cls:'fox' },
    { id:'exp-008', pack:'熊老板会议室', platform:'WhatsApp', format:'WEBP', stage:'失败', progress:100, result:'失败', download:'不可用', time:'2026-06-29 10:08', status:'failed', face:'🐻', cls:'bear' },
    { id:'exp-009', pack:'办公室海獭', platform:'LINE Creators Market', format:'ZIP', stage:'已完成', progress:100, result:'通过', download:'可下载', time:'2026-06-28 21:19', status:'success', face:'🦦', cls:'cat' }
  ]
};

const $ = (sel) => document.querySelector(sel);
const content = $('#content');

function init() {
  renderNav();
  bindChrome();
  go('overview');
}

function renderNav() {
  const nav = $('#nav');
  nav.innerHTML = navItems.map(item => `<button data-route="${item.key}"><span class="nav-icon">${item.icon}</span><span>${item.label}</span></button>`).join('');
  nav.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-route]');
    if (btn) go(btn.dataset.route);
  });
}

function bindChrome() {
  $('#refreshBtn').addEventListener('click', async () => {
    await withLoading($('#refreshBtn'), '刷新中', async () => {
      await wait(450);
      toast('success', '数据已刷新', '当前页面已按最新条件重新请求。');
      rerender();
    });
  });
  $('#newTaskBtn').addEventListener('click', () => go('generation'));
  $('#globalSearch').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      state.filters.q = e.target.value.trim();
      go('library');
      toast('info', '已跳转表情包库', `关键词：${state.filters.q || '全部'}`);
    }
  });
  $('#themeSelect').addEventListener('change', (e) => {
    state.theme = e.target.value;
    document.body.dataset.theme = state.theme;
    toast('success', '主题已切换', e.target.options[e.target.selectedIndex].textContent);
  });
}

function go(route, payload = {}) {
  state.route = route;
  const item = navItems.find(n => n.key === route) || internalRouteMeta(route);
  $('#pageTitle').textContent = item.title;
  $('#pageSubtitle').textContent = item.sub;
  document.querySelectorAll('#nav button').forEach(btn => btn.classList.toggle('active', btn.dataset.route === route));
  const map = {
    overview: renderOverview,
    generation: renderGeneration,
    library: renderLibrary,
    assets: renderAssets,
    qa: renderQA,
    export: renderExport,
    analytics: renderAnalytics,
    settings: renderSettings,
    issueCenter: renderIssueCenter,
    failureCenter: renderFailureCenter,
    platformRules: renderPlatformRules,
    generationSources: renderGenerationSources,
    taskCenter: renderTaskCenter
  };
  (map[route] || renderOverview)(payload);
}

function internalRouteMeta(route) {
  const meta = {
    issueCenter: { title:'处理中心', sub:'集中处理 P0 / P1 / P2，支持筛选、取消、跳转和重新入队' },
    failureCenter: { title:'失败处理', sub:'按阶段、平台和状态处理失败任务' },
    platformRules: { title:'平台规则', sub:'配置 WeChat、Telegram、LINE、WhatsApp 的导出与校验规则' },
    generationSources: { title:'生成源配置', sub:'配置 Prompt 优化、远程免费接口、本地回退和模型源' },
    taskCenter: { title:'任务中心', sub:'查看队列、重试、取消、并发和保留策略' }
  };
  return meta[route] || navItems[0];
}

function rerender() { go(state.route); }

function renderOverview() {
  const sortedIssues = sortedOpenIssues();
  content.innerHTML = `
    <div class="grid-4">
      ${kpiCard('今日生成', '1,248', '↑ 18.6%', '通过率 92.4%', '返工率 7.6%', 'blue')}
      ${kpiCard('待处理', String(sortedIssues.length), '按 P0/P1/P2', 'P0 2 · P1 2', 'P2 2', 'orange')}
      ${kpiCard('导出状态', '82%', '良好', '成功 16', '失败 4 · 进行中 3', 'green')}
      ${kpiCard('平台风险', '2', '高风险', 'WeChat 高风险', 'Telegram 中风险', 'red')}
    </div>

    <div class="grid-main">
      <div class="panel">
        <div class="card-title">
          <div><h2>待处理事项</h2><p>按 P0 / P1 / P2 和更新时间排序，列表可滚动；点击“处理”进入独立处理页面。</p></div>
          <button class="soft-button" onclick="go('issueCenter')">进入处理中心</button>
        </div>
        <div class="scroll-list">${sortedIssues.map(issueCard).join('')}</div>
      </div>
      <div class="panel">
        <div class="card-title"><div><h2>平台风险矩阵</h2><p>点击平台进入发布导出并携带平台条件。</p></div></div>
        ${riskTable()}
      </div>
    </div>

    <div class="grid-main">
      <div class="panel">
        <div class="card-title">
          <div><h2>最近失败</h2><p>每条失败必须有阶段、原因和可执行动作；点击处理进入失败页面。</p></div>
          <button class="soft-button" onclick="go('failureCenter')">进入失败处理</button>
        </div>
        <div class="scroll-list compact">${state.failures.filter(f => f.status !== 'resolved').map(failureCard).join('')}</div>
      </div>
      <div class="panel">
        <div class="card-title"><div><h2>待质检表情包</h2><p>优先处理高平台风险和高重复风险项目。</p></div><button class="link-button" onclick="go('qa')">查看全部</button></div>
        <div class="meme-grid">${state.packs.slice(0,4).map(p => memeCard(p)).join('')}</div>
      </div>
    </div>

    <div class="panel">
      <div class="card-title"><div><h2>快捷入口</h2><p>每个入口都带正确业务上下文和跳转目标。</p></div></div>
      <div class="grid-4">
        ${quick('新建生成','根据主题自动生成 Prompt','generation')}
        ${quick('处理中心','集中处理 P0/P1/P2','issueCenter')}
        ${quick('失败处理','取消或重新加入队列','failureCenter')}
        ${quick('平台规则','配置导出规格与校验','platformRules')}
      </div>
    </div>`;
}

function renderIssueCenter() {
  const issues = filterIssues();
  content.innerHTML = `
    <div class="panel filter-panel">
      <div class="card-title"><div><h2>处理中心筛选</h2><p>处理中心是独立页面；筛选后自动刷新列表，不需要点击应用。</p></div><button class="ghost-button" onclick="go('overview')">返回总览</button></div>
      <div class="filter-grid">
        <div class="field"><label>关键词</label><input id="i-q" value="${esc(state.issueFilters.q)}" placeholder="标题、原因、阶段"></div>
        <div class="field"><label>优先级</label><select id="i-priority">${opts(['all:全部','P0:P0','P1:P1','P2:P2','P3:P3'], state.issueFilters.priority)}</select></div>
        <div class="field"><label>类型</label><select id="i-type">${opts(['all:全部','导出失败:导出失败','平台风险:平台风险','质检驳回:质检驳回','失败队列:失败队列','资料缺失:资料缺失','重复风险:重复风险'], state.issueFilters.type)}</select></div>
        <div class="field"><label>平台</label><select id="i-platform">${opts(['all:全部平台','WeChat:WeChat','Telegram:Telegram','LINE:LINE','WhatsApp:WhatsApp','All:All'], state.issueFilters.platform)}</select></div>
      </div>
      <div class="network-probe">GET /api/admin/issues?${queryString(state.issueFilters)}&sort=priority,updated_desc</div>
    </div>
    <div class="panel">
      <div class="toolbar" style="margin-bottom:12px"><div><strong>待处理列表</strong> <span class="badge blue">${issues.length} 条</span></div><div><button class="danger-button" onclick="bulkCancelIssues()">批量取消低优先级</button> <button class="primary-button" onclick="bulkRequeueIssues()">重新加入队列</button></div></div>
      <div class="scroll-list" style="max-height:620px">${issues.length ? issues.map(issueCardLarge).join('') : emptyHtml('暂无待处理事项', '筛选条件下没有 P0/P1/P2 问题。')}</div>
    </div>`;
  bindIssueFilters();
}

function renderFailureCenter() {
  const failures = filterFailures();
  content.innerHTML = `
    <div class="panel filter-panel">
      <div class="card-title"><div><h2>失败处理筛选</h2><p>失败页面必须能取消、重新入队、跳转详情和查看阶段/原因。</p></div><button class="ghost-button" onclick="go('overview')">返回总览</button></div>
      <div class="filter-grid">
        <div class="field"><label>关键词</label><input id="fail-q" value="${esc(state.failureFilters.q)}" placeholder="任务、原因"></div>
        <div class="field"><label>阶段</label><select id="fail-stage">${opts(['all:全部阶段','打包导出:打包导出','上传平台:上传平台','生成缩略图:生成缩略图','校验资源:校验资源','内容质检:内容质检'], state.failureFilters.stage)}</select></div>
        <div class="field"><label>平台</label><select id="fail-platform">${opts(['all:全部平台','WeChat:WeChat','Telegram:Telegram','LINE:LINE','WhatsApp:WhatsApp'], state.failureFilters.platform)}</select></div>
        <div class="field"><label>状态</label><select id="fail-status">${opts(['all:全部状态','open:待处理','queued:已入队','cancelled:已取消','resolved:已解决'], state.failureFilters.status)}</select></div>
      </div>
      <div class="network-probe">GET /api/admin/failures?${queryString(state.failureFilters)}&sort=updated_desc</div>
    </div>
    <div class="panel">
      <div class="toolbar" style="margin-bottom:12px"><div><strong>失败任务</strong> <span class="badge red">${failures.length} 条</span></div><div><button class="danger-button" onclick="cancelVisibleFailures()">取消可见失败</button> <button class="primary-button" onclick="requeueVisibleFailures()">可见项重新入队</button></div></div>
      <div class="table-wrap"><table><thead><tr><th>任务</th><th>平台</th><th>失败阶段</th><th>失败原因</th><th>状态</th><th>更新时间</th><th style="text-align:right">动作</th></tr></thead><tbody>${failures.map(failureRow).join('')}</tbody></table></div>
    </div>`;
  bindFailureFilters();
}

function renderGeneration() {
  content.innerHTML = `
    <div class="grid-workbench">
      <div class="panel">
        <div class="card-title"><div><h2>任务配置</h2><p>输入主题后可自动生成 Prompt。</p></div></div>
        <div class="field"><label>主题</label><input id="themeInput" value="打工猫日常" placeholder="例如：夏日柴犬、老板开会、摸鱼失败"></div><br>
        <div class="field"><label>生成目标</label><select id="genType"><option>单图表情</option><option>多图系列</option><option>文字动图</option></select></div><br>
        <div class="field"><label>目标平台</label><select id="genPlatform"><option>WeChat</option><option>Telegram</option><option>LINE</option><option>WhatsApp</option></select></div><br>
        <div class="field"><label>风格选择</label><select id="styleInput"><option>搞笑日常 · 非扁平化</option><option>治愈可爱 · 非扁平化</option><option>电影感 · 非扁平化</option><option>夸张表情 · 贴纸质感</option></select></div><br>
        <div class="field"><label>输出数量</label><input id="genCount" type="number" value="4" min="1" max="24"></div><br>
        <button class="primary-button" style="width:100%" onclick="submitGeneration(this)">立即生成</button>
      </div>
      <div class="panel">
        <div class="card-title"><div><h2>Prompt 自生成与优化</h2><p>优先本地生成；可启用远程免费优化接口；失败必须本地回退。</p></div><span class="badge blue">可执行</span></div>
        <div class="art-preview meme-thumb cat" data-caption="拒绝扁平化" style="height:320px;font-size:92px"><span class="meme-face">🐱</span></div><br>
        <div class="field"><label>提示词 Prompt</label><textarea id="promptBox">一只灰白色胖猫，戴着黑框眼镜和领带，在办公室办公，表情疲惫又无奈，桌上有电脑和咖啡杯，幽默搞笑风格，柔和光影，丰富细节，贴纸描边，非扁平化。</textarea></div>
        <div class="prompt-actions">
          <button class="soft-button" onclick="generatePromptByTheme(this)">根据主题生成提示词</button>
          <button class="ghost-button" onclick="optimizePromptLocal(this)">优化设计词</button>
          <button class="ghost-button" onclick="optimizePromptRemote(this)">调用远程免费优化接口</button>
        </div>
        <div class="prompt-status" id="promptStatus">远程接口状态：${state.promptRemoteEnabled ? '已启用' : '未启用，本地回退'} · 可在系统设置 > 生成源配置中配置。</div>
      </div>
      <div class="panel">
        <div class="card-title"><div><h2>实时任务队列</h2><p>失败任务必须可重试、取消，并显示原因。</p></div></div>
        <div class="scroll-list compact">${state.failures.slice(0,4).map(failureCard).join('')}</div>
      </div>
    </div>
    <div class="panel">
      <div class="card-title"><div><h2>候选结果</h2><p>每个候选必须是真实表情包缩略图，不允许灰块或假图占位。</p></div><button class="soft-button" onclick="toast('success','已加入候选池','4 张候选已加入待质检。')">批量加入候选</button></div>
      <div class="meme-grid">${state.packs.slice(0,4).map(p => memeCard(p)).join('')}</div>
    </div>`;
}

function renderLibrary() {
  const filtered = getFilteredPacks();
  const selected = state.packs.find(p => p.id === state.selectedPackId) || filtered[0] || state.packs[0];
  content.innerHTML = `
    <div class="grid-library">
      <div class="content">
        <div class="panel filter-panel">
          <div class="card-title"><div><h2>自动筛选</h2><p>选择条件后立即筛选；无须手动提交条件，也不保留多余视图按钮。</p></div><button class="ghost-button" onclick="resetFilters()">重置</button></div>
          <div class="filter-grid">
            <div class="field"><label>关键词</label><input id="f-q" placeholder="搜索表情包名称、描述、标签" value="${esc(state.filters.q)}"></div>
            <div class="field"><label>平台</label><select id="f-platform">${opts(['all:全部平台','wechat:WeChat','telegram:Telegram','line:LINE','whatsapp:WhatsApp'], state.filters.platform)}</select></div>
            <div class="field"><label>状态</label><select id="f-status">${opts(['all:全部状态','draft:草稿','qa_pending:待质检','approved:已通过','rejected:不通过','exported:已导出'], state.filters.status)}</select></div>
            <div class="field"><label>类型</label><select id="f-type">${opts(['all:全部类型','static:静态表情','animated:动态表情'], state.filters.type)}</select></div>
            <div class="field"><label>最低质量</label><input id="f-qualityMin" type="number" placeholder="最低分" value="${esc(state.filters.qualityMin)}"></div>
            <div class="field"><label>最高质量</label><input id="f-qualityMax" type="number" placeholder="最高分" value="${esc(state.filters.qualityMax)}"></div>
            <div class="field"><label>导出状态</label><select id="f-exportStatus">${opts(['all:全部','success:成功','partial:部分成功','failed:失败','none:未导出'], state.filters.exportStatus)}</select></div>
            <div class="field"><label>重复风险</label><select id="f-risk">${opts(['all:全部','low:低','medium:中','high:高'], state.filters.risk)}</select></div>
          </div>
          <div class="filter-summary"><div class="chips">${filterChips()}</div><div class="badge blue">自动请求：${filtered.length} 条</div></div>
          <div class="network-probe" id="networkProbe">${requestPreview()}</div>
        </div>
        <div class="panel">
          <div class="toolbar" style="margin-bottom:12px"><div><strong>表情包列表</strong> <span class="badge blue">${filtered.length} 条</span></div><div>${state.selectedRows.size ? `<span class="badge blue">已选择 ${state.selectedRows.size} 项</span> <button class="ghost-button" onclick="toast('success','批量导出已加入队列','所选表情包将进入发布导出。')">批量导出</button>` : '<span style="color:var(--muted);font-size:13px">勾选后显示批量工具</span>'}</div></div>
          ${filtered.length ? libraryTable(filtered) : emptyHtml('未找到匹配表情包', '请调整筛选条件，或新建生成任务。')}
        </div>
      </div>
      <div class="panel" id="inspector">${inspector(selected)}</div>
    </div>`;
  bindLibraryFilters();
}

function renderExport() {
  const totalPages = Math.ceil(state.exports.length / state.exportPageSize);
  const pageItems = pagedExports();
  const selectedVisible = pageItems.length && pageItems.every(x => state.selectedExportRows.has(x.id));
  content.innerHTML = `
    <div class="grid-4">
      ${kpiCard('待导出','28','↑ 12.5%','较昨日 25','一键导出可用','blue')}
      ${kpiCard('导出中','8','队列正常','并发 3','平均 2m18s','green')}
      ${kpiCard('导出失败','3','需处理','可重新入队','可取消','red')}
      ${kpiCard('待提交平台','15','WeChat / LINE','Telegram / WhatsApp','平台规则已配置','purple')}
    </div>
    <div class="panel">
      <div class="toolbar" style="margin-bottom:14px">
        <div class="toolbar-left"><strong>发布导出任务</strong><span class="badge blue">共 ${state.exports.length} 条</span><span class="badge green">已选 ${state.selectedExportRows.size} 条</span></div>
        <div class="toolbar-right"><button class="primary-button" onclick="oneClickExportSelected(this)">一键导出所选</button><button class="ghost-button" onclick="go('failureCenter')">处理失败</button></div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th><input type="checkbox" ${selectedVisible ? 'checked' : ''} onchange="toggleExportPage(this.checked)"></th><th>表情包</th><th>目标平台</th><th>包格式</th><th>当前阶段</th><th>校验结果</th><th>下载状态</th><th>最后运行时间</th><th style="text-align:right">操作</th></tr></thead>
          <tbody>${pageItems.map(exportRow).join('')}</tbody>
        </table>
      </div>
      <div class="pagination">${pagination(totalPages)}</div>
    </div>
    <div class="panel">${exportDetail()}</div>`;
}

function renderSettings() {
  const cards = [
    ['平台规则','配置各平台尺寸、格式、体积、帧率和提交清单','platformRules','badge blue'],
    ['生成源配置','配置 Prompt 优化、本地回退、远程免费接口和生成源','generationSources','badge green'],
    ['任务中心','配置并发、重试、取消、保留天数和失败策略','taskCenter','badge orange'],
    ['主题外观','右上角可切换极光蓝、石墨灰、樱花粉、森林绿','settings','badge purple']
  ];
  content.innerHTML = `
    <div class="panel">
      <div class="card-title"><div><h2>系统设置状态栏</h2><p>平台规则、生成源配置、任务中心必须可点击并进入具体设计页面。</p></div><button class="primary-button" onclick="toast('success','设置已保存','所有设置已写入本地状态。')">保存设置</button></div>
      <div class="grid-4">${cards.map(c => `<button class="settings-card" onclick="go('${c[2]}')" style="text-align:left"><div class="row-between"><strong>${c[0]}</strong><span class="${c[3]}">进入</span></div><p style="color:var(--muted);margin:0">${c[1]}</p></button>`).join('')}</div>
    </div>
    <div class="grid-2">
      <div class="panel"><div class="card-title"><div><h2>Owner 安全设置</h2><p>单用户后台，只保留 Owner 安全，不做多用户组织管理。</p></div></div>${settingRows(['管理员账号 owner@example.com','两步验证 已启用','最近登录 2026-07-01 14:42','信任设备 3 台'])}</div>
      <div class="panel"><div class="card-title"><div><h2>验收报告中心</h2><p>Codex LOOP、截图、网络断言、评分结果。</p></div><button class="soft-button" onclick="toast('info','打开验收报告','真实项目中跳转到 /system/acceptance-report。')">查看详情</button></div><div class="kpi-number">96.8</div><span class="badge green">通过门禁</span></div>
    </div>
    <div class="panel"><div class="card-title"><div><h2>危险操作区</h2><p>必须二次确认，不允许无反馈。</p></div></div><div class="grid-3"><button class="danger-button" onclick="confirmDanger('清理历史任务')">清理历史任务</button><button class="danger-button" onclick="confirmDanger('重置所有设置')">重置所有设置</button><button class="danger-button" onclick="confirmDanger('注销当前账号')">注销当前账号</button></div></div>`;
}

function renderPlatformRules() {
  const rules = [
    ['WeChat','主图 240×240 / 透明背景 / ZIP 清单 / OCR 可读','已启用','green'],
    ['Telegram','静态 512×512 / WEBP / 一边必须 512 / 表情映射','已启用','green'],
    ['LINE','APNG 动态 / ZIP 包 / 主图与标签图 / 首帧表达明确','已启用','green'],
    ['WhatsApp','512×512 / WEBP / 文件体积限制 / tray icon','已启用','green']
  ];
  content.innerHTML = `
    <div class="panel"><div class="card-title"><div><h2>平台规则</h2><p>每个平台规则都可点击、编辑、测试连接、保存并生成验收报告。</p></div><button class="ghost-button" onclick="go('settings')">返回设置</button></div><div class="grid-4">${rules.map(([name,desc,status,color]) => `<button class="rule-card" onclick="openRuleDrawer('${name}')" style="text-align:left"><div class="row-between"><strong>${name}</strong><span class="badge ${color}">${status}</span></div><p style="color:var(--muted);margin:0">${desc}</p><span class="link-button">编辑规则 →</span></button>`).join('')}</div></div>
    <div class="grid-2"><div class="panel"><div class="card-title"><div><h2>规则校验项</h2><p>Codex 必须接入实际前后端校验。</p></div></div>${settingRows(['尺寸：必须根据平台动态切换','透明通道：必须检测边缘噪点','格式：PNG / WEBP / APNG / ZIP','体积：超限必须给出压缩建议','提交清单：必须包含文件名、MD5、SHA256'])}</div><div class="panel"><div class="card-title"><div><h2>规则测试</h2><p>每次保存后必须测试。</p></div><button class="primary-button" onclick="toast('success','平台规则测试通过','已模拟检测尺寸、格式、体积、透明通道和清单。')">运行规则测试</button></div><div class="network-probe">POST /api/admin/platform-rules/validate</div></div></div>`;
}

function renderGenerationSources() {
  content.innerHTML = `
    <div class="panel"><div class="card-title"><div><h2>生成源配置</h2><p>Prompt 优化必须支持本地生成、远程免费接口、失败回退和响应记录。</p></div><button class="ghost-button" onclick="go('settings')">返回设置</button></div>
      <div class="grid-2">
        <div class="source-card"><div class="row-between"><strong>本地 Prompt 生成器</strong><span class="badge green">默认启用</span></div><p style="color:var(--muted)">根据主题、风格、平台、角色生成结构化 Prompt。远程不可用时必须回退。</p><button class="soft-button" onclick="toast('success','本地生成器测试通过','主题：打工猫日常 → 已生成完整 Prompt。')">测试本地生成</button></div>
        <div class="source-card"><div class="row-between"><strong>远程免费优化接口</strong><span class="badge ${state.promptRemoteEnabled ? 'green' : 'gray'}">${state.promptRemoteEnabled ? '已启用' : '未启用'}</span></div><p style="color:var(--muted)">仅用于优化 Prompt 文案，不作为唯一依赖。接口失败不得阻塞生成。</p><div class="field"><label>接口地址</label><input id="remoteEndpoint" value="${esc(state.promptEndpoint)}"></div><br><button class="primary-button" onclick="saveRemotePromptConfig(this)">${state.promptRemoteEnabled ? '保存并测试' : '启用并测试'}</button></div>
      </div>
    </div>
    <div class="panel"><div class="card-title"><div><h2>生成源路由规则</h2><p>Codex 需要实现 adapter，不允许在 UI 里写死假成功。</p></div></div>${settingRows(['1. 优先本地生成 Prompt 草案','2. 如果启用远程接口，发送 theme/style/platform/context','3. 远程失败、超时、空结果时自动本地回退','4. 返回结果必须写入 prompt_source、prompt_version、fallback_reason','5. UI 必须显示来源：本地 / 远程 / 回退'])}</div>`;
}

function renderTaskCenter() {
  content.innerHTML = `<div class="panel"><div class="card-title"><div><h2>任务中心</h2><p>失败、取消、重试、队列和并发设置。</p></div><button class="ghost-button" onclick="go('settings')">返回设置</button></div><div class="grid-3">${assetStat('并发上限','3','当前可用配额 3','blue')}${assetStat('失败保留','30 天','过期自动归档','orange')}${assetStat('重试策略','2 次','指数退避','green')}</div></div><div class="panel"><div class="card-title"><div><h2>队列中的失败任务</h2><p>可以取消或重新入队。</p></div></div><div class="scroll-list">${state.failures.map(failureCard).join('')}</div></div>`;
}

function renderQA() {
  const selected = state.packs.find(p => p.id === state.selectedPackId) || state.packs[0];
  content.innerHTML = `
    <div class="grid-4">${kpiCard('待质检数量','156','↑ 22','较昨日 +16.4%','人工复检 18','blue')}${kpiCard('质检不通过','24','↑ 6','OCR/透明边缘','重复风险','red')}${kpiCard('待复检队列','18','↓ 5','AI 修复建议可用','需人工确认','orange')}${kpiCard('平台规则预警','7','↑ 3','WeChat / LINE','需处理','purple')}</div>
    <div class="grid-main">
      <div class="panel"><div class="card-title"><div><h2>待质检表情包</h2><p>点击任一表情包进入右侧质检。</p></div><button class="soft-button" onclick="go('issueCenter')">处理 P0/P1</button></div><div class="scroll-list">${state.packs.map(p => `<button class="issue-item" onclick="selectPack('${p.id}')" style="text-align:left"><div class="meme-inline"><div class="meme-thumb ${p.cls}" data-caption="${esc(p.caption)}"><span class="meme-face">${p.face}</span></div><div><div class="meme-title">${p.name}</div><div class="meme-sub">${p.count} 张 · 质量 ${p.quality} · ${statusText(p.status)}</div></div></div></button>`).join('')}</div></div>
      <div class="panel"><div class="card-title"><div><h2>质检评估</h2><p>通过/不通过必须有反馈，不通过必须填写原因。</p></div></div>${memeCard(selected)}<br>${settingRows(['视觉质量：通过','OCR 文字可读性：通过','透明背景 Alpha：通过','风格一致性：通过','重复风险：低','平台合规性：待评估'])}<div class="field"><label>不通过原因</label><textarea id="rejectReason" placeholder="不通过时必须填写原因"></textarea></div><br><div class="grid-2"><button class="success-button" onclick="qaApprove(this)">通过</button><button class="danger-button" onclick="qaReject(this)">不通过</button></div></div>
    </div>`;
}

function renderAssets() {
  content.innerHTML = `<div class="grid-3">${assetStat('角色资产','18','已授权 16 · 待确认 2','blue')}${assetStat('风格板','9','非扁平化模板 7','purple')}${assetStat('授权素材','124','可商用 112 · 风险 3','green')}</div><div class="panel"><div class="card-title"><div><h2>设计资产列表</h2><p>所有资产都必须有授权状态、用途和预览。</p></div></div><div class="meme-grid">${state.packs.slice(0,6).map(memeCard).join('')}</div></div>`;
}

function renderAnalytics() {
  content.innerHTML = `<div class="grid-4">${kpiCard('平均质量分','88.4','↑ 3.2','非扁平化达标 96%','OCR 通过 94%','green')}${kpiCard('平台通过率','92.4%','良好','WeChat 90%','Telegram 96%','blue')}${kpiCard('返工率','7.6%','↓ 1.1','主要来自 OCR','透明边缘','orange')}${kpiCard('失败恢复','84%','↑ 9%','重试成功率','队列健康','purple')}</div><div class="panel"><div class="card-title"><div><h2>失败原因排行</h2><p>数据表现页面要能指导优化，不做装饰图表。</p></div></div>${settingRows(['1. OCR 对比度不足：31%','2. 平台尺寸不合规：22%','3. 透明边缘噪点：18%','4. 远程接口限流：14%','5. 重复构图风险：9%'])}</div>`;
}

function kpiCard(label, num, trend, foot1, foot2, color) {
  return `<div class="card kpi"><div class="kpi-row"><div><div class="kpi-label">${label}</div><div class="kpi-number">${num}</div><span class="badge ${color}">${trend}</span></div><div class="kpi-icon">${label.slice(0,1)}</div></div><div class="kpi-foot"><span>${foot1}</span><span>${foot2}</span></div></div>`;
}

function sortedOpenIssues() {
  return [...state.issues].filter(i => i.status === 'open').sort((a,b) => priorityRank[a.p] - priorityRank[b.p] || b.updated.localeCompare(a.updated));
}
function issueCard(issue) {
  return `<div class="issue-item ${issue.p.toLowerCase()}"><div class="issue-top"><span class="pill ${issue.p.toLowerCase()}">${issue.p}</span><span class="issue-meta">${issue.updated}</span></div><div class="issue-title">${issue.title}</div><div class="issue-meta"><span>阶段：${issue.stage}</span><span>平台：${issue.platform}</span></div><p style="margin:0;color:var(--muted)">${issue.reason}</p><div class="issue-actions"><button class="primary-button" onclick="handleIssue('${issue.id}')">处理</button><button class="ghost-button" onclick="cancelIssue('${issue.id}')">取消</button></div></div>`;
}
function issueCardLarge(issue) {
  return `<div class="issue-item ${issue.p.toLowerCase()}"><div class="issue-top"><div><span class="pill ${issue.p.toLowerCase()}">${issue.p}</span> <span class="badge gray">${issue.type}</span></div><span class="issue-meta">更新时间：${issue.updated}</span></div><div class="issue-title">${issue.title}</div><div class="grid-3"><div><strong>阶段</strong><br><span class="issue-meta">${issue.stage}</span></div><div><strong>失败/风险原因</strong><br><span class="issue-meta">${issue.reason}</span></div><div><strong>建议动作</strong><br><span class="issue-meta">${issue.action}</span></div></div><div class="issue-actions"><button class="primary-button" onclick="handleIssue('${issue.id}')">处理</button><button class="ghost-button" onclick="requeueIssue('${issue.id}')">重新加入队列</button><button class="danger-button" onclick="cancelIssue('${issue.id}')">取消</button></div></div>`;
}
function failureCard(f) {
  return `<div class="failure-item"><div class="row-between"><strong>${f.task}</strong><span class="badge ${f.status === 'cancelled' ? 'gray' : 'red'}">${statusText(f.status)}</span></div><div class="issue-meta"><span>阶段：${f.stage}</span><span>平台：${f.platform}</span><span>${f.updated}</span></div><p style="margin:0;color:var(--muted)">原因：${f.reason}</p><div class="issue-actions"><button class="primary-button" onclick="handleFailure('${f.id}')">处理</button><button class="ghost-button" onclick="requeueFailure('${f.id}')">重新入队</button><button class="danger-button" onclick="cancelFailure('${f.id}')">取消</button></div></div>`;
}
function failureRow(f) {
  return `<tr><td><strong>${f.task}</strong></td><td>${f.platform}</td><td>${f.stage}</td><td>${f.reason}</td><td><span class="badge ${f.status === 'cancelled' ? 'gray' : 'red'}">${statusText(f.status)}</span></td><td>${f.updated}</td><td><div class="row-actions"><button class="soft-button" onclick="handleFailure('${f.id}')">处理</button><button class="ghost-button" onclick="requeueFailure('${f.id}')">重新入队</button><button class="danger-button" onclick="cancelFailure('${f.id}')">取消</button></div></td></tr>`;
}
function riskTable() {
  const rows = [['WeChat','高','中','高风险'],['Telegram','低','中','中风险'],['LINE','中','低','低风险'],['WhatsApp','低','低','低风险']];
  return `<div class="table-wrap"><table><thead><tr><th>平台</th><th>内容风险</th><th>技术风险</th><th>综合风险</th></tr></thead><tbody>${rows.map(r => `<tr onclick="state.filters.platform='${r[0].toLowerCase()}';go('export')"><td><strong>${r[0]}</strong></td><td><span class="badge ${riskClass(r[1])}">${r[1]}</span></td><td><span class="badge ${riskClass(r[2])}">${r[2]}</span></td><td><span class="badge ${riskClass(r[3])}">${r[3]}</span></td></tr>`).join('')}</tbody></table></div>`;
}
function quick(title, desc, route) { return `<button class="settings-card" onclick="go('${route}')" style="text-align:left"><strong>${title}</strong><p style="margin:6px 0 0;color:var(--muted)">${desc}</p></button>`; }
function memeCard(p) { return `<div class="meme-card"><div class="meme-thumb ${p.cls}" data-caption="${esc(p.caption)}"><span class="meme-face">${p.face}</span></div><strong>${p.name}</strong><div class="meme-sub">${p.desc}</div><div style="margin-top:8px"><span class="badge ${p.quality >= 85 ? 'green' : p.quality >= 75 ? 'orange' : 'red'}">${p.quality} 分</span> <span class="badge blue">${p.count} 张</span></div></div>`; }
function assetStat(name, value, sub, color) { return `<div class="card"><div class="kpi-label">${name}</div><div class="kpi-number">${value}</div><span class="badge ${color}">${sub}</span></div>`; }

function getFilteredPacks() {
  const f = state.filters;
  return state.packs.filter(p => {
    const q = f.q.trim().toLowerCase();
    if (q && !(p.name + p.desc + p.caption).toLowerCase().includes(q)) return false;
    if (f.platform !== 'all' && !p.platform.includes(f.platform)) return false;
    if (f.status !== 'all' && p.status !== f.status) return false;
    if (f.type !== 'all' && p.type !== f.type) return false;
    if (f.exportStatus !== 'all' && p.exportStatus !== f.exportStatus) return false;
    if (f.risk !== 'all' && p.risk !== f.risk) return false;
    if (f.created && p.created !== f.created) return false;
    if (f.qualityMin !== '' && p.quality < Number(f.qualityMin)) return false;
    if (f.qualityMax !== '' && p.quality > Number(f.qualityMax)) return false;
    return true;
  });
}
function libraryTable(rows) {
  return `<div class="table-wrap"><table><thead><tr><th><input type="checkbox" onchange="toggleAllPacks(this.checked)"></th><th>表情包</th><th>数量</th><th>质量评分</th><th>平台</th><th>状态</th><th>导出</th><th>重复风险</th><th style="text-align:right">操作</th></tr></thead><tbody>${rows.map(p => `<tr class="${state.selectedPackId === p.id ? 'active' : ''}" onclick="selectPack('${p.id}')"><td onclick="event.stopPropagation()"><input type="checkbox" ${state.selectedRows.has(p.id) ? 'checked' : ''} onchange="togglePack('${p.id}', this.checked)"></td><td><div class="meme-inline"><div class="meme-thumb ${p.cls}" data-caption="${esc(p.caption)}"><span class="meme-face">${p.face}</span></div><div><div class="meme-title">${p.name}</div><div class="meme-sub">${p.desc}</div></div></div></td><td>${p.count}</td><td><span class="badge ${p.quality >= 85 ? 'green' : p.quality >= 75 ? 'orange' : 'red'}">${p.quality}</span></td><td>${p.platform.map(platformBadge).join('')}</td><td><span class="badge gray">${statusText(p.status)}</span></td><td>${statusText(p.exportStatus)}</td><td><span class="badge ${riskClass(p.risk)}">${riskText(p.risk)}</span></td><td><div class="row-actions"><button class="soft-button" onclick="event.stopPropagation();openPackDrawer('${p.id}')">详情</button><button class="ghost-button" onclick="event.stopPropagation();singleExportPack('${p.id}')">导出</button></div></td></tr>`).join('')}</tbody></table></div>`;
}
function inspector(p) {
  return `<div class="card-title"><div><h2>${p.name}</h2><p>${p.desc}</p></div><button class="icon-button" onclick="openPackDrawer('${p.id}')">›</button></div>${memeCard(p)}<br><div class="grid-2"><button class="primary-button" onclick="singleExportPack('${p.id}')">导出</button><button class="ghost-button" onclick="go('qa')">质检</button></div><br>${settingRows(['数量：'+p.count+' 张','质量评分：'+p.quality,'平台：'+p.platform.join(', '),'状态：'+statusText(p.status),'重复风险：'+riskText(p.risk),'创建时间：'+p.created])}`;
}
function bindLibraryFilters() {
  const map = { 'f-q':'q', 'f-platform':'platform', 'f-status':'status', 'f-type':'type', 'f-qualityMin':'qualityMin', 'f-qualityMax':'qualityMax', 'f-exportStatus':'exportStatus', 'f-risk':'risk' };
  Object.entries(map).forEach(([id,key]) => {
    const el = document.getElementById(id);
    if (!el) return;
    const eventName = el.tagName === 'INPUT' && el.type !== 'date' ? 'input' : 'change';
    el.addEventListener(eventName, debounce(() => { state.filters[key] = el.value; renderLibrary(); toast('info', '已自动筛选', requestPreview()); }, eventName === 'input' ? 280 : 0));
  });
}
function resetFilters() { state.filters = { q:'', platform:'all', status:'all', qualityMin:'', qualityMax:'', exportStatus:'all', risk:'all', created:'', type:'all' }; renderLibrary(); toast('success','筛选已重置','列表已自动刷新。'); }
function filterChips() { return Object.entries(state.filters).filter(([k,v]) => v && v !== 'all').map(([k,v]) => `<span class="badge blue">${k}: ${esc(v)}</span>`).join('') || '<span style="color:var(--muted);font-size:13px">暂无筛选条件</span>'; }
function requestPreview() { return `GET /api/admin/sticker-packs?${queryString(state.filters)}&page=1&page_size=20`; }

function filterIssues() {
  const f = state.issueFilters;
  return [...state.issues].filter(i => {
    const q = f.q.trim().toLowerCase();
    if (q && !(i.title+i.reason+i.stage).toLowerCase().includes(q)) return false;
    if (f.priority !== 'all' && i.p !== f.priority) return false;
    if (f.type !== 'all' && i.type !== f.type) return false;
    if (f.platform !== 'all' && i.platform !== f.platform) return false;
    if (f.status !== 'all' && i.status !== f.status) return false;
    return true;
  }).sort((a,b) => priorityRank[a.p] - priorityRank[b.p] || b.updated.localeCompare(a.updated));
}
function bindIssueFilters() {
  const map = { 'i-q':'q', 'i-priority':'priority', 'i-type':'type', 'i-platform':'platform' };
  Object.entries(map).forEach(([id,key]) => { const el = document.getElementById(id); if (el) el.addEventListener(id === 'i-q' ? 'input' : 'change', debounce(() => { state.issueFilters[key] = el.value; renderIssueCenter(); }, id === 'i-q' ? 250 : 0)); });
}
function filterFailures() {
  const f = state.failureFilters;
  return state.failures.filter(x => {
    const q = f.q.trim().toLowerCase();
    if (q && !(x.task+x.reason+x.stage).toLowerCase().includes(q)) return false;
    if (f.stage !== 'all' && x.stage !== f.stage) return false;
    if (f.platform !== 'all' && x.platform !== f.platform) return false;
    if (f.status !== 'all' && x.status !== f.status) return false;
    return true;
  }).sort((a,b)=> b.updated.localeCompare(a.updated));
}
function bindFailureFilters() {
  const map = { 'fail-q':'q', 'fail-stage':'stage', 'fail-platform':'platform', 'fail-status':'status' };
  Object.entries(map).forEach(([id,key]) => { const el = document.getElementById(id); if (el) el.addEventListener(id === 'fail-q' ? 'input' : 'change', debounce(() => { state.failureFilters[key] = el.value; renderFailureCenter(); }, id === 'fail-q' ? 250 : 0)); });
}

function pagedExports() {
  const start = (state.exportPage - 1) * state.exportPageSize;
  return state.exports.slice(start, start + state.exportPageSize);
}
function exportRow(e) {
  const selected = state.selectedExportRows.has(e.id);
  return `<tr class="${state.selectedExportId === e.id ? 'active' : ''}" onclick="selectExport('${e.id}')"><td onclick="event.stopPropagation()"><input type="checkbox" ${selected ? 'checked' : ''} onchange="toggleExport('${e.id}', this.checked)"></td><td><div class="meme-inline"><div class="meme-thumb ${e.cls}" data-caption="${e.stage}"><span class="meme-face">${e.face}</span></div><div><div class="meme-title">${e.pack}</div><div class="meme-sub">ID: ${e.id}</div></div></div></td><td>${e.platform}</td><td>${e.format}</td><td><div>${e.stage}</div><div class="progress ${e.status === 'failed' ? 'red' : e.status === 'success' ? 'green' : ''}"><i style="width:${e.progress}%"></i></div></td><td><span class="badge ${e.result === '失败' ? 'red' : e.result === '通过' ? 'green' : 'gray'}">${e.result}</span></td><td>${e.download}</td><td>${e.time}</td><td><div class="row-actions"><button class="soft-button" onclick="event.stopPropagation();selectExport('${e.id}')">详情</button><button class="primary-button" onclick="event.stopPropagation();singleExport('${e.id}', this)">导出</button></div></td></tr>`;
}
function exportDetail() {
  const e = state.exports.find(x => x.id === state.selectedExportId) || state.exports[0];
  return `<div class="card-title"><div><h2>${e.pack}</h2><p>单条导出详情，必须显示流程、文件清单、校验结果和动作。</p></div><div><button class="primary-button" onclick="singleExport('${e.id}', this)">导出本条</button> <button class="ghost-button" onclick="go('failureCenter')">处理失败</button></div></div><div class="grid-4"><div>${memeCard({name:e.pack,desc:e.platform,count:24,quality:e.result==='失败'?62:92,cls:e.cls,face:e.face,caption:e.stage})}</div>${settingRows(['当前阶段：'+e.stage,'进度：'+e.progress+'%','校验结果：'+e.result,'下载状态：'+e.download,'格式：'+e.format,'最后运行：'+e.time])}</div>`;
}
function pagination(totalPages) {
  let html = '';
  for (let i=1;i<=totalPages;i++) html += `<button class="ghost-button ${i===state.exportPage?'active':''}" onclick="state.exportPage=${i};renderExport()">${i}</button>`;
  return html;
}

function opts(items, selected) { return items.map(x => { const [v,l] = x.split(':'); return `<option value="${v}" ${v === selected ? 'selected' : ''}>${l}</option>`; }).join(''); }
function statusText(s) { return ({ draft:'草稿', qa_pending:'待质检', approved:'已通过', rejected:'不通过', exported:'已导出', success:'成功', partial:'部分成功', failed:'失败', none:'未导出', open:'待处理', queued:'已入队', cancelled:'已取消', resolved:'已解决', running:'进行中', pending:'待处理' })[s] || s; }
function riskText(s) { return ({ low:'低', medium:'中', high:'高', '高风险':'高风险', '中风险':'中风险', '低风险':'低风险' })[s] || s; }
function riskClass(r) { return String(r).includes('高') || r === 'high' ? 'red' : String(r).includes('中') || r === 'medium' ? 'orange' : 'green'; }
function platformBadge(p) { return `<span class="badge blue">${({wechat:'WeChat',telegram:'Telegram',line:'LINE',whatsapp:'WhatsApp',tiktok:'TikTok'})[p] || p}</span>`; }
function emptyHtml(title, desc) { return `<div class="empty"><div><h3>${title}</h3><p>${desc}</p></div></div>`; }
function settingRows(rows) { return rows.map(r => `<div class="failure-item"><span>${r}</span></div>`).join(''); }
function queryString(obj) { return Object.entries(obj).filter(([,v]) => v !== '' && v !== 'all').map(([k,v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join('&') || 'no_filter=1'; }
function esc(str) { return String(str ?? '').replace(/[&<>'"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[m])); }
function debounce(fn, delay) { let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); }; }
function wait(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
async function withLoading(btn, label, fn) { const old = btn.textContent; btn.disabled = true; btn.textContent = label; try { await fn(); } finally { btn.disabled = false; btn.textContent = old; } }
function toast(type, title, msg) { const el = document.createElement('div'); el.className = `toast ${type}`; el.innerHTML = `<strong>${esc(title)}</strong><p>${esc(msg)}</p>`; $('#toast').appendChild(el); setTimeout(() => el.remove(), 3500); }

function handleIssue(id) { const issue = state.issues.find(i=>i.id===id); if (!issue) return; toast('info','跳转处理', `${issue.p} · ${issue.action}`); go(issue.target || 'issueCenter'); }
function cancelIssue(id) { const issue = state.issues.find(i=>i.id===id); if (issue) { issue.status='cancelled'; toast('success','已取消处理项', issue.title); rerender(); } }
function requeueIssue(id) { const issue = state.issues.find(i=>i.id===id); if (issue) { issue.status='open'; toast('success','已重新加入队列', issue.title); } }
function bulkCancelIssues() { state.issues.filter(i=>i.p==='P2').forEach(i=>i.status='cancelled'); toast('success','已取消低优先级项','P2 已取消，P0/P1 保持待处理。'); renderIssueCenter(); }
function bulkRequeueIssues() { toast('success','已重新加入队列','可见 P0/P1/P2 已写入任务队列。'); }
function handleFailure(id) { const f = state.failures.find(x=>x.id===id); if (f) { toast('info','进入失败处理', `${f.stage} · ${f.reason}`); if (f.target && f.target !== 'failureCenter') go(f.target); } }
function requeueFailure(id) { const f = state.failures.find(x=>x.id===id); if (f) { f.status='queued'; toast('success','已重新加入队列', f.task); rerender(); } }
function cancelFailure(id) { const f = state.failures.find(x=>x.id===id); if (f) { f.status='cancelled'; toast('success','已取消失败任务', f.task); rerender(); } }
function cancelVisibleFailures() { filterFailures().forEach(f=>f.status='cancelled'); toast('success','已取消可见失败任务','状态已更新。'); renderFailureCenter(); }
function requeueVisibleFailures() { filterFailures().forEach(f=>f.status='queued'); toast('success','可见失败任务已重新入队','队列将按优先级执行。'); renderFailureCenter(); }

function selectPack(id) { state.selectedPackId = id; if (state.route === 'library') renderLibrary(); else if (state.route === 'qa') renderQA(); }
function togglePack(id, checked) { checked ? state.selectedRows.add(id) : state.selectedRows.delete(id); renderLibrary(); }
function toggleAllPacks(checked) { getFilteredPacks().forEach(p => checked ? state.selectedRows.add(p.id) : state.selectedRows.delete(p.id)); renderLibrary(); }
function singleExportPack(id) { const p = state.packs.find(x=>x.id===id); toast('success','单个导出已加入队列', p ? p.name : id); go('export'); }
function openPackDrawer(id) { const p = state.packs.find(x=>x.id===id); if (!p) return; const drawer = $('#drawer'); drawer.innerHTML = `<div class="card-title"><div><h2>${p.name}</h2><p>${p.desc}</p></div><button class="icon-button" onclick="closeDrawer()">×</button></div>${memeCard(p)}<br>${inspector(p)}<br><button class="primary-button" style="width:100%" onclick="singleExportPack('${p.id}')">导出本包</button>`; drawer.classList.add('open'); }
function closeDrawer() { $('#drawer').classList.remove('open'); }
function selectExport(id) { state.selectedExportId = id; renderExport(); }
function toggleExport(id, checked) { checked ? state.selectedExportRows.add(id) : state.selectedExportRows.delete(id); renderExport(); }
function toggleExportPage(checked) { pagedExports().forEach(e => checked ? state.selectedExportRows.add(e.id) : state.selectedExportRows.delete(e.id)); renderExport(); }
async function singleExport(id, btn) { const e = state.exports.find(x=>x.id===id); await withLoading(btn, '导出中', async () => { await wait(500); if (e) { e.stage='已完成'; e.progress=100; e.result='通过'; e.download='可下载'; e.status='success'; } toast('success','单条导出完成', e ? e.pack : id); renderExport(); }); }
async function oneClickExportSelected(btn) { if (!state.selectedExportRows.size) return toast('error','未选择任务','请先勾选至少一条导出任务。'); await withLoading(btn, '导出中', async () => { await wait(700); state.exports.forEach(e => { if (state.selectedExportRows.has(e.id)) { e.stage='已完成'; e.progress=100; e.result='通过'; e.download='可下载'; e.status='success'; } }); toast('success','一键导出完成', `已处理 ${state.selectedExportRows.size} 条任务。`); renderExport(); }); }

function generatePrompt(theme, style, platform) {
  const subject = theme || '表情包角色';
  const mood = subject.includes('打工') || subject.includes('职场') ? '疲惫但幽默、带一点自嘲' : subject.includes('夏日') ? '明亮、放松、元气十足' : '夸张、可爱、适合聊天表达';
  return `${subject}，${style}，目标平台 ${platform}。角色需要有明确表情和动作，场景有前景/中景/背景层次，柔和体积光、真实材质、贴纸描边、轻微阴影、高清细节、透明背景友好。画面必须非扁平化，避免 corporate flat vector、简单图标、纯文字贴图。情绪：${mood}。输出应适合 1:1 表情包缩略图，主体居中，移动端小尺寸仍然清晰。`;
}
async function generatePromptByTheme(btn) { await withLoading(btn, '生成中', async () => { await wait(360); const theme=$('#themeInput').value.trim(); $('#promptBox').value = generatePrompt(theme, $('#styleInput').value, $('#genPlatform').value); $('#promptStatus').textContent = 'Prompt 来源：本地主题生成器。'; toast('success','已根据主题生成 Prompt', theme || '默认主题'); }); }
async function optimizePromptLocal(btn) { await withLoading(btn, '优化中', async () => { await wait(320); const val = $('#promptBox').value.trim(); $('#promptBox').value = `${val}\n\n优化补充：增加道具互动、明确视线方向、强化情绪峰值、保留负空间用于短字幕；禁止扁平插画、禁止低质感、禁止无场景白底头像。`; $('#promptStatus').textContent = 'Prompt 来源：本地设计词优化。'; toast('success','设计词已优化','已补充非扁平化、构图和验收约束。'); }); }
async function optimizePromptRemote(btn) { await withLoading(btn, '调用中', async () => { await wait(620); if (!state.promptRemoteEnabled) { $('#promptStatus').textContent = '远程接口未启用，已使用本地回退。'; await optimizePromptLocal(btn); return; } $('#promptBox').value += `\n\n远程优化返回：强化角色连续性、平台尺寸适配、字幕可读性和透明边缘干净度。`; $('#promptStatus').textContent = `Prompt 来源：远程免费优化接口 ${state.promptEndpoint}`; toast('success','远程优化完成','已接入返回的提示词。'); }); }
async function submitGeneration(btn) { await withLoading(btn, '创建中', async () => { await wait(600); toast('success','生成任务已创建','任务已进入实时队列，失败时可取消或重新入队。'); }); }
function saveRemotePromptConfig(btn) { state.promptEndpoint = $('#remoteEndpoint').value.trim(); state.promptRemoteEnabled = true; toast('success','远程接口已启用', state.promptEndpoint); renderGenerationSources(); }
function qaApprove(btn) { toast('success','质检已通过','已写入审核记录并可进入发布导出。'); }
function qaReject(btn) { const reason = $('#rejectReason')?.value.trim(); if (!reason) return toast('error','需要填写不通过原因','质检驳回必须记录原因，不能只显示失败。'); toast('success','已驳回并记录原因', reason); }
function openRuleDrawer(name) { const drawer = $('#drawer'); drawer.innerHTML = `<div class="card-title"><div><h2>${name} 平台规则</h2><p>可编辑规则详情，保存后必须校验。</p></div><button class="icon-button" onclick="closeDrawer()">×</button></div><div class="field"><label>尺寸规则</label><input value="512 x 512 / 平台适配"></div><br><div class="field"><label>格式规则</label><input value="PNG / WEBP / ZIP"></div><br><div class="field"><label>文件体积</label><input value="按平台限制自动校验"></div><br><button class="primary-button" style="width:100%" onclick="toast('success','规则已保存','${name} 规则已保存并通过校验。');closeDrawer();">保存并测试</button>`; drawer.classList.add('open'); }
function confirmDanger(name) { const modal=$('#modal'); modal.innerHTML=`<div class="modal-card"><div class="card-title"><div><h2>${name}</h2><p>危险操作必须二次确认。</p></div></div><p style="color:var(--muted)">此操作会影响后台状态。预览中只展示交互，不会真正删除数据。</p><div class="grid-2"><button class="ghost-button" onclick="closeModal()">取消</button><button class="danger-button" onclick="toast('success','已确认操作','${name} 已执行模拟。');closeModal();">确认执行</button></div></div>`; modal.classList.add('open'); }
function closeModal() { $('#modal').classList.remove('open'); }

init();
