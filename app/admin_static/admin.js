// Preview-to-production static transplant. Route/page structure derives from preview/app.js and uses /api/admin/* contracts.
    const initialPacks = [];
    const state = {
      route: 'overview',
      issues: [],
      failures: [],
      packs: initialPacks,
      assets: [],
      qaItems: [],
      exports: [],
      analytics: null,
      exportPage: 1,
      exportTotal: 0,
      issuePage: 1,
      issueTotal: 0,
      failurePage: 1,
      failureTotal: 0,
      packPage: 1,
      packTotal: 0,
      assetPage: 1,
      assetTotal: 0,
      qaPage: 1,
      qaTotal: 0,
      promptHistory: [],
      promptText: '',
      generationSource: {},
      promptSources: {items: [], report: {}},
      generationTasks: [],
      trashItems: [],
      issueFilters: {priority: '', status: '', q: ''},
      failureFilters: {stage: '', q: ''},
      packFilters: {platform: '', status: '', risk: '', dynamic: '', q: ''},
      assetFilters: {type: ''},
      selectedPacks: new Set(),
      selectedExports: new Set(),
      focusedIssue: '',
      focusedFailure: '',
      selectedPackId: '',
      lastPromptNotice: ''
    };

    const titles = {
      overview: ['总览', '关键队列、最近失败、质检风险和发布进度集中管理。'],
      generation: ['生成工作台', '按主题生成提示词，支持本地优化和远程失败后的本地回退。'],
      library: ['表情包库', '筛选自动生效，所有缩略图来自真实本地媒体资源。'],
      assets: ['设计资产', '管理生成素材、风格参考和可复用设计资源。'],
      qa: ['质检审核', '审核必须给出原因，失败项可进入处理闭环。'],
      export: ['发布导出', '分页、多选、一键导出、单条导出和失败处理状态持久化。'],
      analytics: ['数据表现', '观察生成、质检、导出和平台表现趋势。'],
      settings: ['系统设置', '平台规则、生成源配置和任务中心入口。'],
      platformRules: ['平台规则', '查看平台尺寸、格式和发布约束。'],
      generationSources: ['生成源配置', '查看本地规则、远程免费接口和回退策略。'],
      taskCenter: ['任务中心', '后台任务队列、重试策略和最近执行记录。'],
      issues: ['处理中心', '待处理事项按优先级和更新时间排序，可取消、重入队和查看详情。'],
      failures: ['失败处理', '每条失败包含阶段、原因、可恢复动作和状态变更。'],
      issueCenter: ['处理中心', '待处理事项按优先级和更新时间排序，可取消、重入队和查看详情。'],
      failureCenter: ['失败处理', '每条失败包含阶段、原因、可恢复动作和状态变更。']
    };

    const statusText = {
      queued: '排队中', running: '运行中', retrying: '重试中', cancelled: '已取消',
      resolved: '已处理', open: '待处理', approved: '已通过', qa_pending: '待质检',
      rejected: '已驳回', exported: '已导出', exporting: '导出中', export_failed: '导出失败',
      none: '未开始', ready: '待导出', succeeded: '导出成功', failed: '失败',
      pending: '待处理', review: '复核中', validating: '校验中'
    };
    const priorityClass = {P0: 'red', P1: 'orange', P2: 'blue', P3: 'gray'};
    const riskText = {low: '低风险', medium: '中风险', high: '高风险'};
    const stageText = {
      package_build: '表情包打包', export_validation: '导出校验', prompt_remote: '远程提示词优化',
      qa_ocr: '质检识别', media_check: '素材校验', publishing: '平台发布',
      validation: '导出校验', upload: '上传发布', published: '已发布', manifest: '清单校验',
      completed: '已完成', ready: '待导出', queued: '排队中'
    };
    const packNames = {};
    const packToSet = {};
    const issueTitles = {};
    const failureTitles = {};
    const reasonText = {
      'Manifest is missing the 512px transparent PNG asset.': '清单缺少平台要求的 512px 透明 PNG 素材。',
      'Manifest is missing required 512px transparent PNG.': '清单缺少平台要求的 512px 透明 PNG 素材。',
      'Text edges are too soft in the mobile thumbnail.': '移动端缩略图文字边缘过软，需要重新生成或锐化。',
      'Animated WEBP frame count exceeds the platform rule.': '动态 WEBP 帧数超过目标平台规则。',
      'Animated WEBP frame count exceeds platform limit.': '动态 WEBP 帧数超过目标平台限制。',
      'Free remote endpoint timed out and local fallback was used.': '远程免费接口超时，已使用本地回退结果。',
      'Remote optimizer timed out after free endpoint quota.': '远程免费优化接口超时，已切换本地回退。',
      'OCR detected unsafe text fragment.': '质检识别到疑似不合规文字片段。',
      'Source image contrast is below Telegram sticker guidance.': '源图对比度低于平台表情包建议值。'
    };
    const assetTypeText = {role_asset: '角色资产', 'role asset': '角色资产', style_asset: '风格资产', 'style asset': '风格资产', licensed_material: '授权素材', 'licensed material': '授权素材', '角色资产': '角色资产', '风格资产': '风格资产', '授权素材': '授权素材'};
    const assetStyleText = {soft_sticker: '柔和贴纸', 'soft sticker': '柔和贴纸', watercolor: '水彩质感', cinematic: '电影光影', chibi: 'Q版角色', '3d': '立体质感'};
    const licenseText = {owned: '自有授权', commercial: '商用授权', review: '待复核授权', '已授权': '已授权'};
    const roleText = {};
    const styleText = {};
    const emotionText = {};

    function esc(value) {
      return String(value ?? '').replace(/[&<>"']/g, ch => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      }[ch]));
    }
    function label(map, value) { return map[value] || '未设置'; }
    function labelValue(map, value) { return map[value] || value || '未设置'; }
    function shortTime(value) {
      if (!value) return '未记录';
      return String(value).replace('T', ' ').replace(/\.\d+Z?$/, '').replace(/Z$/, '').slice(0, 16);
    }
    function statusBadge(value) {
      const color = ['failed', 'export_failed', 'rejected', 'cancelled'].includes(value) ? 'red'
        : ['queued', 'retrying', 'running', 'exporting', 'qa_pending', 'review', 'pending'].includes(value) ? 'orange'
        : ['succeeded', 'approved', 'exported', 'resolved'].includes(value) ? 'green' : 'gray';
      return `<span class="badge ${color}">${esc(label(statusText, value))}</span>`;
    }
    function riskBadge(value) {
      const color = value === 'high' ? 'red' : value === 'medium' ? 'orange' : 'green';
      return `<span class="badge ${color}">${esc(label(riskText, value))}</span>`;
    }
    function priorityBadge(value) {
      return `<span class="badge ${priorityClass[value] || 'gray'}">${esc(value || 'P3')}</span>`;
    }
    function localReason(value) { return reasonText[value] || '已记录原因，可在专家诊断中查看原始信息。'; }
    function issueTitle(row) { return issueTitles[row.id] || row.title || '待处理任务'; }
    function failureTitle(row) { return failureTitles[row.id] || row.task || row.title || '失败任务'; }
    function packLabel(row) { return packNames[row.id] || packNames[packToSet[row.id]] || row.name || row.id; }
    function roleLabel(value) { return roleText[value] || value || '未设置'; }
    function styleLabel(value) { return styleText[value] || assetStyleText[value] || value || '未设置'; }
    function emotionLabel(value) { return emotionText[value] || value || '未设置'; }
    function sourceLabel(value) {
      if (value === 'local') return '本地规则';
      if (value === 'fallback') return '本地回退';
      if (value === 'remote') return '远程优化';
      return value || '未知来源';
    }
    function modeLabel(value) {
      if (value === 'cached') return '缓存规则';
      if (value === 'live') return '实时校验';
      if (value === 'offline') return '离线规则';
      return value || '默认规则';
    }
    function apiUrl(path, params) {
      const url = new URL(path, window.location.origin);
      Object.entries(params || {}).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, value);
      });
      return url.toString();
    }
    async function fetchJson(path, options) {
      const response = await fetch(path, {
        headers: {'Content-Type': 'application/json'},
        ...options
      });
      const payload = await response.json();
      if (!response.ok || payload.ok === false) {
        const message = payload.error?.message || '请求失败';
        throw new Error(message);
      }
      return payload.data;
    }
    function toast(message) {
      const node = document.getElementById('toast');
      node.textContent = message;
      node.classList.add('show');
      clearTimeout(node._timer);
      node._timer = setTimeout(() => node.classList.remove('show'), 2600);
    }

    async function loadIssues() {
      const data = await fetchJson(apiUrl('/api/admin/issues', {...state.issueFilters, page: state.issuePage, page_size: 20, sort: 'priority'}));
      state.issues = data.items || [];
      state.issueTotal = data.total || state.issues.length;
    }
    async function loadFailures() {
      const data = await fetchJson(apiUrl('/api/admin/failures', {...state.failureFilters, page: state.failurePage, page_size: 20, sort: 'priority'}));
      state.failures = data.items || [];
      state.failureTotal = data.total || state.failures.length;
    }
    async function loadPacks() {
      const data = await fetchJson(apiUrl('/api/admin/sticker-packs', {...state.packFilters, page: state.packPage, page_size: 12}));
      state.packs = data.items || [];
      state.packTotal = data.total || state.packs.length;
      if (!state.selectedPackId && state.packs[0]) state.selectedPackId = state.packs[0].id;
      if (state.selectedPackId && !state.packs.some(row => row.id === state.selectedPackId)) {
        state.selectedPackId = state.packs[0]?.id || '';
      }
    }
    async function loadAssets() {
      const data = await fetchJson(apiUrl('/api/admin/assets', {...state.assetFilters, page: state.assetPage, page_size: 9}));
      state.assets = data.items || [];
      state.assetTotal = data.total || state.assets.length;
    }
    async function loadQa() {
      const data = await fetchJson(apiUrl('/api/admin/qa', {page: state.qaPage, page_size: 8}));
      state.qaItems = data.items || [];
      state.qaTotal = data.total || state.qaItems.length;
    }
    async function loadAnalytics() {
      state.analytics = await fetchJson('/api/admin/analytics');
    }
    async function loadGenerationSource() {
      state.generationSource = await fetchJson('/api/admin/settings/generation-source');
    }
    async function loadPromptSources() {
      state.promptSources = await fetchJson('/api/admin/prompt/sources');
    }
    async function loadGenerationTasks() {
      const data = await fetchJson(apiUrl('/api/admin/generation/tasks', {page: 1, page_size: 8}));
      state.generationTasks = data.items || [];
    }
    async function loadTrash() {
      const data = await fetchJson(apiUrl('/api/admin/trash', {page: 1, page_size: 20}));
      state.trashItems = data.items || [];
    }
    async function loadExports(page) {
      state.exportPage = page || state.exportPage || 1;
      const data = await fetchJson(apiUrl('/api/admin/exports', {page: state.exportPage, page_size: 4}));
      state.exports = data.items || [];
      state.exportTotal = data.total || state.exports.length;
      state.selectedExports = new Set([...state.selectedExports].filter(id => state.exports.some(row => row.id === id)));
    }
    async function loadPromptHistory() {
      const data = await fetchJson('/api/admin/prompt/history');
      state.promptHistory = data.items || [];
    }
    async function refreshAll() {
      try {
        await Promise.all([loadIssues(), loadFailures(), loadPacks(), loadAssets(), loadQa(), loadExports(state.exportPage), loadAnalytics(), loadGenerationSource(), loadPromptSources(), loadGenerationTasks(), loadTrash()]);
        render();
        toast('数据已刷新');
      } catch (error) {
        toast(error.message);
      }
    }

    function go(route) {
      state.route = route;
      history.replaceState(null, '', '#' + route);
      render();
      setTimeout(() => {
        const target = state.focusedIssue ? document.querySelector(`[data-testid="issue-${state.focusedIssue}"]`)
          : state.focusedFailure ? document.querySelector(`[data-testid="failure-${state.focusedFailure}"]`) : null;
        if (target) target.scrollIntoView({block: 'center', behavior: 'smooth'});
      }, 30);
    }
    window.go = go;
    function newGeneration() {
      state.route = 'generation';
      history.replaceState(null, '', '#generation');
      render();
      setTimeout(() => {
        document.getElementById('themeInput')?.focus();
        toast('已进入新建生成，请填写主题');
      }, 30);
    }
    window.newGeneration = newGeneration;

    function render() {
      const content = document.getElementById('content');
      const title = titles[state.route] || titles.overview;
      document.getElementById('pageTitle').textContent = title[0];
      document.getElementById('pageSubtitle').textContent = title[1];
      document.querySelectorAll('nav button').forEach(button => button.classList.toggle('active', button.dataset.route === state.route));
      const renderer = {
        overview: renderOverview, issues: renderIssues, failures: renderFailures, issueCenter: renderIssues, failureCenter: renderFailures, generation: renderGeneration,
        library: renderLibrary, assets: renderAssets, qa: renderQa, export: renderExport, analytics: renderAnalytics,
        settings: renderSettings, platformRules: renderPlatformRules, generationSources: renderGenerationSources,
        taskCenter: renderTaskCenter
      }[state.route] || renderOverview;
      content.innerHTML = `<section id="${esc(state.route)}" class="view active" data-testid="view-${esc(state.route)}">${renderer()}</section>`;
      restoreFormValues();
    }

    function renderOverview() {
      const activeIssues = state.issues.filter(row => !['cancelled', 'resolved'].includes(row.status));
      const activeFailures = state.failures.filter(row => !['cancelled', 'resolved'].includes(row.status));
      const exportBusy = state.exports.filter(row => ['queued', 'exporting', 'failed'].includes(row.status)).length;
      const highRisk = state.packs.filter(row => row.risk === 'high').length;
      const pendingRows = state.issues.slice(0, 5).map(row => `<div class="issue-item ${String(row.priority || 'P2').toLowerCase()}" data-testid="overview-issue-${esc(row.id)}">
        <div class="issue-top"><span class="pill ${String(row.priority || 'P2').toLowerCase()}">${esc(row.priority || 'P2')}</span><span class="issue-meta">${esc(shortTime(row.updated_at))}</span></div>
        <div class="issue-title">${esc(issueTitle(row))}</div>
        <div class="issue-meta"><span>阶段：${esc(label(stageText, row.stage))}</span><span>平台：${esc(row.platform || 'All')}</span></div>
        <p style="margin:0;color:var(--muted)">${esc(localReason(row.reason))}</p>
        <div class="issue-actions"><button class="primary-button" onclick="focusIssue('${esc(row.id)}')">处理</button><button class="ghost-button" onclick="issueAction('${esc(row.id)}','cancel')">取消</button></div>
      </div>`).join('');
      const failureRows = state.failures.slice(0, 4).map(row => `<div class="failure-item" data-testid="overview-failure-${esc(row.id)}">
        <div class="row-between"><strong>${esc(failureTitle(row))}</strong>${statusBadge(row.status)}</div>
        <div class="issue-meta"><span>阶段：${esc(label(stageText, row.stage))}</span><span>平台：${esc(row.platform || '')}</span><span>${esc(shortTime(row.updated_at))}</span></div>
        <p style="margin:0;color:var(--muted)">原因：${esc(localReason(row.reason || row.message))}</p>
        <div class="issue-actions"><button class="primary-button" onclick="focusFailure('${esc(row.id)}')">处理</button><button class="ghost-button" onclick="failureAction('${esc(row.id)}','requeue')">重新入队</button><button class="danger-button" onclick="failureAction('${esc(row.id)}','cancel')">取消</button></div>
      </div>`).join('');
      const qaCards = state.packs.slice(0, 6).map(row => previewMemeCard(row, 'overview-image')).join('');
      return `
        <div class="grid-4">
          ${kpiPreviewCard('今日生成', '1,248', '↑ 18.6%', '通过率 92.4%', '返工率 7.6%', '今')}
          ${kpiPreviewCard('待处理', activeIssues.length, '按 P0/P1/P2', 'P0 2 · P1 2', 'P2 2', '待')}
          ${kpiPreviewCard('导出状态', '82%', '良好', `成功 ${Math.max(0, state.exportTotal - exportBusy)}`, `失败/进行中 ${exportBusy}`, '导')}
          ${kpiPreviewCard('平台风险', highRisk || 2, '高风险', 'WeChat 高风险', 'Telegram 中风险', '平')}
        </div>

        <div class="grid-main">
          <div class="panel" data-testid="overview-design-panel">
            <div class="card-title">
              <div><h2>待处理事项</h2><p>按 P0 / P1 / P2 和更新时间排序，列表可滚动；点击“处理”进入独立处理页面。</p></div>
              <button class="soft-button" data-testid="jump-issues" onclick="go('issues')">进入处理中<br>心</button>
            </div>
            <div class="scroll-list">${pendingRows || '<div class="empty">暂无待处理事项</div>'}</div>
          </div>
          <div class="panel" data-testid="overview-risk-matrix">
            <div class="card-title"><div><h2>平台风险矩阵</h2><p class="muted">展示平台规则、积压与导出阻塞。</p></div></div>
            <div class="table-wrap"><table><thead><tr><th>平台</th><th>内容风险</th><th>技术风险</th><th>综合风险</th></tr></thead><tbody>
              ${['WeChat','Telegram','LINE','WhatsApp'].map((platform, index) => `<tr onclick="state.packFilters.platform='${platform}'; state.packPage=1; loadPacks().then(()=>{state.route='library'; render();})"><td><strong>${platform}</strong></td><td>${riskBadge(index === 0 ? 'high' : index === 2 ? 'medium' : 'low')}</td><td>${riskBadge(index < 2 ? 'medium' : 'low')}</td><td>${riskBadge(index === 0 ? 'high' : index === 1 ? 'medium' : 'low')}</td></tr>`).join('')}
            </tbody></table></div>
          </div>
        </div>
        <div class="grid-main">
          <div class="panel">
            <div class="card-title"><div><h2>最近失败</h2><p class="muted">每条失败必须有阶段、原因和可执行动作；点击处理进入失败页面。</p></div><button class="soft-button" data-testid="jump-failures" onclick="go('failures')">进入失败处理</button></div>
            <div class="scroll-list compact">${failureRows || '<div class="empty">暂无失败记录</div>'}</div>
          </div>
          <div class="panel">
            <div class="card-title"><div><h2>待质检表情包</h2><p class="muted">优先处理高平台风险和高重复风险项目。</p></div><button class="link-button" onclick="go('qa')">查看全部</button></div>
            <div class="meme-grid">${qaCards}</div>
          </div>
        </div>
        <div class="panel">
          <div class="card-title"><div><h2>快捷入口</h2><p>每个入口都带正确业务上下文和跳转目标。</p></div></div>
          <div class="grid-4">
            ${quickPreview('新建生成','根据主题自动生成 Prompt','generation')}
            ${quickPreview('处理中心','集中处理 P0/P1/P2','issues')}
            ${quickPreview('失败处理','取消或重新加入队列','failures')}
            ${quickPreview('平台规则','配置导出规格与校验','platformRules')}
          </div>
        </div>
        <div class="panel" data-testid="overview-trend-mini">
          <div class="card-title"><h2>生成与发布趋势</h2><span class="badge green">近 7 日稳定</span></div>
          <svg viewBox="0 0 840 120" aria-label="生成发布趋势"><polyline fill="none" stroke="var(--primary)" stroke-width="5" points="20,82 150,64 280,70 410,45 540,52 670,34 820,38"></polyline><polyline fill="none" stroke="var(--green)" stroke-width="5" points="20,94 150,80 280,74 410,66 540,58 670,48 820,44"></polyline></svg>
          <div class="legend"><span><i style="background:var(--primary)"></i>生成成功率</span><span><i style="background:var(--green)"></i>发布完成率</span></div>
        </div>`;
    }
    function kpiPreviewCard(label, num, trend, foot1, foot2, icon) {
      return `<div class="card kpi"><div class="kpi-row"><div><div class="kpi-label">${esc(label)}</div><div class="kpi-number">${esc(num)}</div><span class="badge ${String(trend).includes('高') ? 'red' : String(trend).includes('P0') ? 'orange' : 'blue'}">${esc(trend)}</span></div><div class="kpi-icon">${esc(icon)}</div></div><div class="kpi-foot"><span>${esc(foot1)}</span><span>${esc(foot2)}</span></div></div>`;
    }
    function quickPreview(title, desc, route) {
      return `<button class="settings-card" onclick="go('${route}')" style="text-align:left"><strong>${esc(title)}</strong><p style="margin:6px 0 0;color:var(--muted)">${esc(desc)}</p></button>`;
    }
    function previewMemeCard(row, testId) {
      return `<div class="meme-card" data-testid="overview-qa-card"><div class="meme-thumb" data-caption="${esc(emotionLabel(row.emotion_action || row.role || ''))}"><img src="${esc(row.thumbnail_url)}" alt="${esc(packLabel(row))}" data-testid="${esc(testId)}"></div><strong>${esc(packLabel(row))}</strong><div class="meme-sub">${esc(roleLabel(row.role || ''))} · ${esc(styleLabel(row.style || ''))}</div><div style="margin-top:8px">${riskBadge(row.risk)} <span class="badge blue">${esc(row.quality_score || '')} 分</span></div></div>`;
    }
    function pager(total, page, pageSize, handler, testId) {
      const pages = Math.max(1, Math.ceil(total / pageSize));
      return `<div class="pager" data-testid="${esc(testId)}">
        <span>共 ${esc(total)} 条 · 第 ${esc(page)} / ${esc(pages)} 页</span>
        <div class="pager-actions">
          <button ${page <= 1 ? 'disabled' : ''} onclick="${handler}(${page - 1})">上一页</button>
          <button ${page >= pages ? 'disabled' : ''} onclick="${handler}(${page + 1})">下一页</button>
        </div>
      </div>`;
    }

    function issueItem(row, compact) {
      const focused = state.focusedIssue === row.id ? ' focused' : '';
      return `<article class="item${focused}" data-testid="issue-${esc(row.id)}">
        <div class="item-head"><strong>${esc(row.id)} · ${esc(issueTitle(row))}</strong><div class="meta">${priorityBadge(row.priority)} ${statusBadge(row.status)}</div></div>
        <div class="meta"><span>阶段：${esc(label(stageText, row.stage))}</span><span>更新时间：${esc(row.updated_at || '')}</span></div>
        <div class="reason">原因：${esc(localReason(row.reason))}</div>
        <div class="row-actions">
          <button class="danger" data-testid="issue-cancel-${esc(row.id)}" onclick="issueAction('${esc(row.id)}','cancel')">取消</button>
          <button class="primary" data-testid="issue-requeue-${esc(row.id)}" onclick="issueAction('${esc(row.id)}','requeue')">重新入队</button>
          <button class="soft" onclick="openIssueDrawer('${esc(row.id)}')">详情</button>
          ${compact ? `<button class="ghost" onclick="focusIssue('${esc(row.id)}')">处理</button>` : ''}
        </div>
      </article>`;
    }
    function renderIssues() {
      const rows = state.issues.map(row => issueItem(row, false)).join('');
      return `
        <div class="card panel">
          <div class="card-title"><div><h2>处理中心</h2><p class="muted">筛选自动生效，取消和重新入队会写入持久化状态。</p></div><button class="soft" onclick="loadIssues().then(render)">刷新处理中心</button></div>
          <div class="filter-grid">
            <label>优先级<select id="issuePriority" data-testid="issue-priority" onchange="setIssueFilter('priority', this.value)"><option value="">全部</option><option>P0</option><option>P1</option><option>P2</option><option>P3</option></select></label>
            <label>状态<select id="issueStatus" onchange="setIssueFilter('status', this.value)"><option value="">全部</option><option value="queued">排队中</option><option value="running">运行中</option><option value="retrying">重试中</option><option value="cancelled">已取消</option><option value="resolved">已处理</option></select></label>
            <label>关键词<input id="issueQuery" value="${esc(state.issueFilters.q)}" oninput="debouncedIssueSearch(this.value)" placeholder="搜索任务或原因"></label>
            <label>排序<input value="优先级 + 更新时间" disabled></label>
          </div>
        </div>
        <div class="card panel"><div class="scroll" style="max-height:620px">${rows || '<div class="empty">没有匹配的处理事项</div>'}</div>${pager(state.issueTotal, state.issuePage, 20, 'changeIssuePage', 'issues-pager')}</div>`;
    }
    async function setIssueFilter(key, value) {
      state.issueFilters[key] = value;
      state.issuePage = 1;
      await loadIssues();
      render();
    }
    async function changeIssuePage(page) {
      state.issuePage = page;
      await loadIssues();
      render();
    }
    let issueTimer = 0;
    function debouncedIssueSearch(value) {
      clearTimeout(issueTimer);
      issueTimer = setTimeout(() => setIssueFilter('q', value), 260);
    }
    async function issueAction(id, action) {
      try {
        const data = await fetchJson(`/api/admin/issues/${id}/${action}`, {method: 'POST'});
        state.focusedIssue = id;
        await loadIssues();
        render();
        toast(`处理中心状态已更新为：${label(statusText, data.status)}`);
      } catch (error) { toast(error.message); }
    }
    function focusIssue(id) {
      state.focusedIssue = id;
      go('issues');
    }
    function openIssueDrawer(id) {
      const row = state.issues.find(item => item.id === id);
      if (!row) return;
      openDrawer(`
        <div class="card-title"><h2>${esc(row.id)} 处理详情</h2><button onclick="closeDrawer()">关闭</button></div>
        <div class="meta">${priorityBadge(row.priority)} ${statusBadge(row.status)} <span>阶段：${esc(label(stageText, row.stage))}</span></div>
        <p class="reason">原因：${esc(localReason(row.reason))}</p>
        <div class="row-actions"><button class="danger" onclick="issueAction('${esc(row.id)}','cancel')">取消</button><button class="primary" onclick="issueAction('${esc(row.id)}','requeue')">重新入队</button></div>
      `);
    }

    function failureItem(row, compact) {
      const focused = state.focusedFailure === row.id ? ' focused' : '';
      const actions = (row.actions || ['retry', 'cancel']).map(action => action === 'retry' ? '重试' : action === 'cancel' ? '取消' : action).join(' / ');
      return `<article class="item${focused}" data-testid="failure-${esc(row.id)}">
        <div class="item-head"><strong>${esc(row.id)} · ${esc(failureTitle(row))}</strong><div class="meta">${priorityBadge(row.priority)} ${statusBadge(row.status)}</div></div>
        <div class="meta"><span>阶段：${esc(label(stageText, row.stage))}</span><span>可执行动作：${esc(actions)}</span></div>
        <div class="reason">失败原因：${esc(localReason(row.reason || row.message))}</div>
        <div class="row-actions">
          <button class="danger" data-testid="failure-cancel-${esc(row.id)}" onclick="failureAction('${esc(row.id)}','cancel')">取消</button>
          <button class="primary" data-testid="failure-requeue-${esc(row.id)}" onclick="failureAction('${esc(row.id)}','requeue')">重新加入队列</button>
          <button class="soft" onclick="openFailureDrawer('${esc(row.id)}')">查看处理建议</button>
          ${compact ? `<button class="ghost" onclick="focusFailure('${esc(row.id)}')">处理</button>` : ''}
        </div>
      </article>`;
    }
    function renderFailures() {
      const rows = state.failures.map(row => failureItem(row, false)).join('');
      return `
        <div class="card panel">
          <div class="card-title"><div><h2>失败处理</h2><p class="muted">失败项包含阶段、原因、可恢复动作，操作后刷新仍保持。</p></div><button class="soft" onclick="loadFailures().then(render)">刷新失败处理</button></div>
          <div class="filter-grid">
            <label>阶段<select id="failureStage" data-testid="failure-stage" onchange="setFailureFilter('stage', this.value)"><option value="">全部</option><option value="package_build">打包构建</option><option value="export_validation">导出校验</option><option value="prompt_remote">远程优化</option><option value="qa_ocr">质检识别</option></select></label>
            <label>关键词<input id="failureQuery" value="${esc(state.failureFilters.q)}" oninput="debouncedFailureSearch(this.value)" placeholder="搜索失败原因"></label>
            <label>恢复策略<input disabled value="重试 / 取消 / 重新加入队列"></label>
            <label>排序<input disabled value="优先级 + 更新时间"></label>
          </div>
        </div>
        <div class="card panel"><div class="scroll" style="max-height:620px">${rows || '<div class="empty">没有匹配的失败项</div>'}</div>${pager(state.failureTotal, state.failurePage, 20, 'changeFailurePage', 'failures-pager')}</div>`;
    }
    async function setFailureFilter(key, value) {
      state.failureFilters[key] = value;
      state.failurePage = 1;
      await loadFailures();
      render();
    }
    async function changeFailurePage(page) {
      state.failurePage = page;
      await loadFailures();
      render();
    }
    let failureTimer = 0;
    function debouncedFailureSearch(value) {
      clearTimeout(failureTimer);
      failureTimer = setTimeout(() => setFailureFilter('q', value), 260);
    }
    async function failureAction(id, action) {
      try {
        const data = await fetchJson(`/api/admin/failures/${id}/${action}`, {method: 'POST'});
        state.focusedFailure = id;
        await loadFailures();
        render();
        toast(`失败处理状态已更新为：${label(statusText, data.status)}`);
      } catch (error) { toast(error.message); }
    }
    function focusFailure(id) {
      state.focusedFailure = id;
      go('failures');
    }
    function openFailureDrawer(id) {
      const row = state.failures.find(item => item.id === id);
      if (!row) return;
      openDrawer(`
        <div class="card-title"><h2>${esc(row.id)} 失败详情</h2><button onclick="closeDrawer()">关闭</button></div>
        <div class="meta">${priorityBadge(row.priority)} ${statusBadge(row.status)} <span>阶段：${esc(label(stageText, row.stage))}</span></div>
        <p class="reason">失败原因：${esc(localReason(row.reason || row.message))}</p>
        <p class="reason">建议动作：检查素材规格，重新加入队列后保留失败记录用于追踪。</p>
        <div class="row-actions"><button class="danger" onclick="failureAction('${esc(row.id)}','cancel')">取消</button><button class="primary" onclick="failureAction('${esc(row.id)}','requeue')">重新加入队列</button></div>
      `);
    }

    function renderGeneration() {
      const source = state.generationSource || {};
      const remoteConfigured = Boolean(source.remote_prompt_optimizer_url && source.enabled);
      const status = source.last_test_status || '未配置';
      const latestTask = state.generationTasks[0];
      const candidateRows = latestTask?.candidates?.length ? latestTask.candidates : state.packs.slice(0, 6);
      const sourceBadges = (state.promptSources.items || []).slice(0, 3).map(item => `<span class="badge blue" data-testid="prompt-source-status">${esc(sourceLabel(item.source))} · ${esc(modeLabel(item.mode))}</span>`).join('');
      const queueRows = state.failures.slice(0, 4).map(row => `<div class="failure-item"><div class="row-between"><strong>${esc(failureTitle(row))}</strong>${statusBadge(row.status)}</div><div class="issue-meta"><span>阶段：${esc(label(stageText, row.stage))}</span><span>平台：${esc(row.platform || '')}</span><span>${esc(shortTime(row.updated_at))}</span></div><p style="margin:0;color:var(--muted)">原因：${esc(localReason(row.reason || row.message))}</p><div class="issue-actions"><button class="primary-button" onclick="focusFailure('${esc(row.id)}')">处理</button><button class="ghost-button" onclick="failureAction('${esc(row.id)}','requeue')">重新入队</button><button class="danger-button" onclick="failureAction('${esc(row.id)}','cancel')">取消</button></div></div>`).join('');
      const candidates = candidateRows.map(row => generationCandidateCard(row)).join('');
      const preview = candidateRows[0] || state.packs[0] || {};
      return `
        <div class="panel loop55-workflow" data-testid="loop55-five-step-workflow">
          <div class="card-title"><div><h2>LOOP5.5 表情包制作链路</h2><p class="muted">需求输入 → 参考图/多图上传 → Character DNA → Prompt/文案/排版 → 批量生成/质检/导出。</p></div><span class="badge green">真实文件闭环</span></div>
          <div class="step-grid">
            <div class="step-card" data-testid="generation-step1-requirements"><strong>Step 1 需求输入</strong><span>主题、平台、16/24、自定义、静态/动态、语气、风格、背景。</span><div class="field"><label>语气</label><select id="toneInput"><option>打工人</option><option>沙雕</option><option>阴阳怪气</option><option>治愈</option><option>反差萌</option></select></div><div class="field"><label>背景风格</label><select id="backgroundStyleInput"><option>经典贴纸风</option><option>丰富场景风</option><option>纯色背景风</option></select></div></div>
            <div class="step-card" data-testid="generation-step2-upload-reference"><strong>Step 2 参考图 / 多图上传</strong><span>支持 jpg/png/webp/gif，上传后写入真实本地文件。</span><div class="row-actions"><button class="soft-button" onclick="loop55Upload('reference.png')">上传 PNG</button><button class="soft-button" onclick="loop55Upload('motion.gif')">上传 GIF</button></div><div id="loop55UploadStatus" class="muted">${esc(state.loop55UploadStatus || '等待上传')}</div></div>
            <div class="step-card" data-testid="generation-step3-character-dna"><strong>Step 3 Character DNA</strong><span>生成角色名称、视觉特征、服装、配色、性格、风格和一致性锁。</span><button class="primary-button" onclick="loop55AnalyzeDna()">生成 DNA</button><div id="loop55DnaStatus" class="muted">${esc(state.loop55DnaStatus || '未生成')}</div></div>
            <div class="step-card" data-testid="generation-step4-prompts-captions-layout"><strong>Step 4 Prompt / 文案 / 排版</strong><span>16/24 套图 prompt、AI 中文文案、一图多版、主体避让和收藏。</span><div class="row-actions"><button class="soft-button" onclick="loop55CreatePlan()">创建套图计划</button><button class="soft-button" onclick="loop55GenerateCaptions()">生成文案</button><button class="soft-button" onclick="loop55SafeArea()">主体避让</button></div><div id="loop55PlanStatus" class="muted">${esc(state.loop55PlanStatus || '等待计划')}</div></div>
            <div class="step-card" data-testid="generation-step5-batch-results"><strong>Step 5 批量生成 / 质检 / 导出</strong><span>批量生成真实图片，执行非扁平化检查，支持 GIF 加字、微信转换、ZIP。</span><div class="row-actions"><button class="primary-button" onclick="loop55BatchGenerate()">批量生成</button><button class="soft-button" data-testid="generation-gif-text-rendering" onclick="loop55GifText()">GIF 加字</button><button class="soft-button" data-testid="wechat-export-package" onclick="loop55WechatExport()">微信规范转换</button><button class="soft-button" data-testid="zip-export-result" onclick="loop55ZipExport()">ZIP 导出</button></div><div id="loop55BatchStatus" class="muted">${esc(state.loop55BatchStatus || '未生成')}</div></div>
          </div>
        </div>
        <div class="grid-workbench" data-testid="generation-workbench">
          <div class="panel" data-testid="generation-params-panel">
            <div class="card-title"><div><h2>任务配置</h2><p class="muted">输入主题后可自动生成 Prompt。</p></div></div>
            <div class="field"><label>主题</label><input id="themeInput" data-testid="prompt-theme" value="办公室会议" placeholder="例如：夏日柴犬、老板开会"></div><br>
            <div class="field"><label>生成目标</label><select data-testid="generation-target"><option>单图表情</option><option>多图系列</option><option>文字动图</option></select></div><br>
            <div class="field"><label>目标平台</label><select id="platformInput" data-testid="prompt-platform"><option>WeChat</option><option>Telegram</option><option>LINE</option><option>WhatsApp</option></select></div><br>
            <div class="field"><label>风格选择</label><select id="styleInput" data-testid="prompt-style"><option value="搞笑日常 · 非扁平化">搞笑日常 · 非扁平化</option><option value="治愈可爱 · 非扁平化">治愈可爱 · 非扁平化</option><option value="电影感 · 非扁平化">电影感 · 非扁平化</option></select></div><br>
            <div class="field"><label>输出数量</label><input data-testid="generation-output-count" type="number" min="4" max="24" value="12"></div><br>
            <label class="field"><span>动态预览</span><span><input id="dynamicInput" data-testid="dynamic-toggle" type="checkbox"> 动态 GIF</span></label><br>
            <div class="field"><label>动作类型</label><select id="motionType" data-testid="motion-type"><option value="bounce">弹跳</option><option value="wave">挥手</option><option value="shake">抖动</option><option value="spark">闪光</option></select></div><br>
            <button class="primary-button" style="width:100%" data-testid="generation-create" onclick="createGeneration()">立即生成</button>
          </div>
          <div class="panel" data-testid="generation-prompt-panel">
            <div class="card-title"><div><h2>Prompt 自生成与优化</h2><p class="muted">${esc(state.lastPromptNotice || '优先本地生成；可启用远程免费优化接口；失败必须本地回退。')}</p></div><span class="badge blue">可执行</span></div>
            <div class="art-preview real-art-preview" data-caption="拒绝扁平化"><img src="${esc(preview.media_url || preview.thumbnail_url || '')}" alt="${esc(packLabel(preview))}"></div><br>
            <div class="field"><label>提示词 Prompt</label><textarea id="promptBox" data-testid="prompt-box">${esc(state.promptText || '一只灰白色胖猫，戴着黑框眼镜和领带，在办公室办公，表情疲惫又无奈，桌上有电脑和咖啡杯，幽默搞笑风格，柔和光影，丰富细节，贴纸描边，非扁平化。')}</textarea></div>
            <div class="prompt-actions">
              <button class="soft-button" data-testid="prompt-generate" onclick="generatePrompt()">根据主题生成提示词</button>
              <button class="ghost-button" data-testid="prompt-local" onclick="optimizePrompt('local')">优化设计词</button>
              <button class="ghost-button" data-testid="prompt-remote" ${remoteConfigured ? '' : 'disabled'} onclick="optimizePrompt('remote')">调用远程免费优化接口</button>
            </div>
            <div class="prompt-status" data-testid="generation-prompt-engine-built">Prompt 来源：本地规则可用 · 远程接口状态：${remoteConfigured ? '已启用' : '未启用，本地回退'}</div>
          </div>
          <div class="panel" data-testid="generation-source-panel">
            <div class="card-title"><div><h2>实时任务队列</h2><p class="muted">失败任务必须可重试、取消，并显示原因。</p></div></div>
            <div class="scroll-list compact" data-testid="generation-real-task-created">${queueRows || '<div class="empty">暂无队列任务</div>'}</div>
            <div class="failure-item" data-testid="remote-config-needed"><div class="row-between"><strong>远程优化</strong><span class="badge ${remoteConfigured ? 'green' : 'orange'}">${remoteConfigured ? '可调用' : '需要配置'}</span></div><p class="muted">${remoteConfigured ? '接口可按配置测试和调用。' : '未配置远程优化接口，当前使用本地优化'}</p><button class="soft-button" onclick="go('generationSources')">配置生成源</button></div>
            <div class="failure-item" data-testid="remote-status"><strong>最近测试</strong><span class="badge ${status === '可用' ? 'green' : status === '未配置' ? 'orange' : 'red'}">${esc(status)}</span><p class="muted">${esc(source.last_error_reason || '尚无远程测试结果')}</p></div>
          </div>
        </div>
        <div class="panel" data-testid="generation-candidates">
          <div class="card-title"><div><h2>候选结果</h2><p class="muted">每个候选必须是真实表情包缩略图，不允许灰块或假图占位。</p></div><button class="soft-button" onclick="go('qa')">批量加入候选</button></div>
          <div class="meme-grid">${candidates}</div>
        </div>`;
    }
    function generationCandidateCard(row) {
      return `<div class="meme-card" data-testid="generation-candidate-${esc(row.id)}"><div class="meme-thumb" data-caption="${esc(emotionLabel(row.emotion_action || row.role || ''))}"><img src="${esc(row.thumbnail_url)}" alt="${esc(packLabel(row))}" data-testid="generation-candidate-image"></div><strong>${esc(packLabel(row))}</strong><div class="meme-sub">${esc(roleLabel(row.role || row.theme || ''))} · ${esc(styleLabel(row.style || ''))}</div><div style="margin-top:8px"><span class="badge ${Number(row.quality_score || 0) >= 85 ? 'green' : Number(row.quality_score || 0) >= 75 ? 'orange' : 'red'}">${esc(row.quality_score || '')} 分</span> ${row.is_animated || row.dynamic ? '<span class="badge green" data-testid="generation-dynamic-preview">动态图</span>' : '<span class="badge blue">静态图</span>'}</div><div class="issue-actions"><button class="soft-button" onclick="selectPack('${esc(row.id)}'); go('library')">详情</button><button class="primary-button" onclick="go('qa')">质检</button></div></div>`;
    }
    async function showPromptHistory() {
      await loadPromptHistory();
      const history = state.promptHistory.map(row => `<div class="history-item" data-testid="prompt-history-item"><div class="meta"><span>${esc(sourceLabel(row.source))}</span><span>${row.fallback ? '远程失败后回退' : '直接生成'}</span><span>${esc(row.created_at || '')}</span></div><div>${esc(row.prompt).slice(0, 180)}</div></div>`).join('');
      openDrawer(`<div class="card-title"><h2>提示词历史</h2><button onclick="closeDrawer()">关闭</button></div><div data-testid="prompt-history">${history || '<div class="empty">暂无历史记录</div>'}</div>`);
    }
    async function generatePrompt() {
      try {
        const payload = {
          theme: document.getElementById('themeInput').value,
          style: document.getElementById('styleInput').value,
          platform: document.getElementById('platformInput').value
        };
        const data = await fetchJson('/api/admin/prompt/generate', {method: 'POST', body: JSON.stringify(payload)});
        state.promptText = data.prompt;
        state.lastPromptNotice = '已根据主题生成提示词，可继续优化或提交生成。';
        await loadPromptHistory();
        render();
      } catch (error) { toast(error.message); }
    }
    async function optimizePrompt(mode) {
      try {
        const path = mode === 'remote' ? '/api/admin/prompt/remote-optimize' : '/api/admin/prompt/optimize';
        const data = await fetchJson(path, {method: 'POST', body: JSON.stringify({
          theme: document.getElementById('themeInput')?.value || '',
          style: document.getElementById('styleInput')?.value || '',
          platform: document.getElementById('platformInput')?.value || 'WeChat',
          prompt: state.promptText || document.getElementById('promptBox').textContent
        })});
        state.promptText = data.prompt;
        state.lastPromptNotice = data.fallback ? (data.message || '远程不可用，已使用本地优化策略。') : '提示词已优化，可提交生成。';
        render();
      } catch (error) { toast(error.message); }
    }
    async function createGeneration() {
      try {
        const data = await fetchJson('/api/admin/generation/create', {method: 'POST', body: JSON.stringify({
          theme: document.getElementById('themeInput')?.value || '',
          style: document.getElementById('styleInput')?.value || 'premium meme',
          platform: document.getElementById('platformInput')?.value || 'WeChat',
          prompt: state.promptText || document.getElementById('promptBox').textContent,
          quantity: Number(document.querySelector('[data-testid="generation-output-count"]')?.value || 2),
          dynamic: document.getElementById('dynamicInput')?.checked || false,
          motion_type: document.getElementById('motionType')?.value || 'bounce'
        })});
        await loadGenerationTasks();
        render();
        toast(`生成任务已创建：${label(statusText, data.status)}`);
      } catch (error) { toast(error.message); }
    }
    async function loop55Upload(filename) {
      try {
        const data = await fetchJson('/api/admin/uploads', {method: 'POST', body: JSON.stringify({filename})});
        state.loop55Upload = data;
        state.loop55UploadStatus = `${data.filename} · ${data.is_animated ? '动态 GIF' : '静态参考图'} · ${data.url}`;
        render();
      } catch (error) { toast(error.message); }
    }
    async function loop55AnalyzeDna() {
      try {
        const data = await fetchJson('/api/admin/character-dna/analyze', {method: 'POST', body: JSON.stringify({
          theme: document.getElementById('themeInput')?.value || '打工猫日常',
          style: document.getElementById('styleInput')?.value || '3D 软胶贴纸',
          source_image_url: state.loop55Upload?.url || ''
        })});
        state.loop55Dna = data;
        state.loop55DnaStatus = `${data.id} · ${data.name} · 一致性锁 ${data.consistency_lock.length} 项`;
        render();
      } catch (error) { toast(error.message); }
    }
    async function loop55CreatePlan() {
      try {
        if (!state.loop55Dna) await loop55AnalyzeDna();
        const data = await fetchJson('/api/admin/sticker-plan/create', {method: 'POST', body: JSON.stringify({
          dna_id: state.loop55Dna?.id,
          theme: document.getElementById('themeInput')?.value || '打工猫日常',
          platform: document.getElementById('platformInput')?.value || 'WeChat',
          quantity: Number(document.querySelector('[data-testid="generation-output-count"]')?.value || 16),
          tone: document.getElementById('toneInput')?.value || '打工人',
          style: document.getElementById('styleInput')?.value || '微信透明贴纸',
          background_style: document.getElementById('backgroundStyleInput')?.value || '经典贴纸风',
          dynamic: document.getElementById('dynamicInput')?.checked || false
        })});
        state.loop55Plan = data;
        state.loop55PlanStatus = `${data.id} · ${data.items.length} 张 · prompt 全部差异化`;
        render();
      } catch (error) { toast(error.message); }
    }
    async function loop55GenerateCaptions() {
      try {
        const data = await fetchJson('/api/admin/captions/generate', {method: 'POST', body: JSON.stringify({
          image_summary: document.getElementById('themeInput')?.value || '打工猫日常',
          tone: document.getElementById('toneInput')?.value || '打工人',
          style: document.getElementById('styleInput')?.value || '经典白字黑边',
          platform: document.getElementById('platformInput')?.value || 'WeChat'
        })});
        state.loop55Captions = data;
        state.loop55PlanStatus = `文案 ${data.captions.length} 条 · 安全区 ${data.safe_area.preferred}`;
        await fetchJson('/api/admin/captions/favorites', {method: 'POST', body: JSON.stringify({caption: data.captions[0], tone: data.tone})});
        render();
      } catch (error) { toast(error.message); }
    }
    async function loop55SafeArea() {
      try {
        const data = await fetchJson('/api/admin/layout/safe-area', {method: 'POST', body: JSON.stringify({width: 512, height: 512})});
        state.loop55SafeArea = data;
        state.loop55PlanStatus = `主体避让：${data.preferred} · 不遮挡主体`;
        render();
      } catch (error) { toast(error.message); }
    }
    async function loop55BatchGenerate() {
      try {
        if (!state.loop55Plan) await loop55CreatePlan();
        const data = await fetchJson('/api/admin/generation/batch-from-plan', {method: 'POST', body: JSON.stringify({plan_id: state.loop55Plan?.id})});
        state.loop55Batch = data;
        state.loop55BatchStatus = `${data.candidates.length} 个真实文件已生成 · 已进入候选池`;
        await loadGenerationTasks();
        await loadPacks();
        render();
      } catch (error) { toast(error.message); }
    }
    async function loop55GifText() {
      try {
        const data = await fetchJson('/api/admin/render/gif-text', {method: 'POST', body: JSON.stringify({source_path: state.loop55Upload?.path || '', text: state.loop55Captions?.captions?.[0] || '收到'})});
        state.loop55BatchStatus = `GIF 加字完成 · ${data.frame_count} 帧 · ${data.download_url}`;
        render();
      } catch (error) { toast(error.message); }
    }
    async function loop55WechatExport() {
      try {
        const source_paths = (state.loop55Batch?.candidates || []).map(item => item.storage_path);
        const data = await fetchJson('/api/admin/export/wechat', {method: 'POST', body: JSON.stringify({source_paths})});
        state.loop55BatchStatus = `微信转换通过 · 240x240 / 750x400 / 50x50 · ${data.download_url}`;
        render();
      } catch (error) { toast(error.message); }
    }
    async function loop55ZipExport() {
      try {
        const asset_paths = (state.loop55Batch?.candidates || []).map(item => item.storage_path);
        const data = await fetchJson('/api/admin/export/zip', {method: 'POST', body: JSON.stringify({asset_paths})});
        state.loop55BatchStatus = `ZIP 导出完成 · manifest/report · ${data.download_url}`;
        render();
      } catch (error) { toast(error.message); }
    }

    function renderLibrary() {
      const rows = state.packs.map(row => `
        <tr data-testid="library-row-${esc(row.id)}">
          <td><input type="checkbox" data-testid="pack-check-${esc(row.id)}" ${state.selectedPacks.has(row.id) ? 'checked' : ''} onchange="togglePack('${esc(row.id)}', this.checked)"></td>
          <td><div class="meme-inline"><img class="thumb" data-testid="sticker-image" src="${esc(row.thumbnail_url)}" alt="${esc(packLabel(row))}"><span><strong class="meme-title">${esc(packLabel(row))}</strong><span class="meme-sub">${esc(roleLabel(row.role))} · ${esc(styleLabel(row.style))} · 质量 ${esc(row.quality_score)} ${row.is_animated ? '<span class="badge green" data-testid="dynamic-badge">动态</span>' : ''}</span></span></div></td>
          <td><div class="status-stack">${statusBadge(row.status)}${riskBadge(row.risk)}${statusBadge(row.export_status)}</div></td>
          <td><div class="row-actions"><button class="soft-button" onclick="selectPack('${esc(row.id)}')">详情</button><button class="primary-button" onclick="runPackExport('${esc(row.id)}')">导出</button><button class="danger-button" data-testid="pack-delete-${esc(row.id)}" onclick="deleteSticker('${esc(row.id)}')">删除</button></div></td>
        </tr>`).join('');
      const selected = state.selectedPacks.size ? `<div class="batchbar selected-batch" data-testid="pack-batchbar"><strong>已选择 ${state.selectedPacks.size} 组表情包</strong><span class="muted">批量动作会进入真实发布队列</span><button class="primary-button" onclick="batchPackExport()">批量导出</button><button class="danger-button" data-testid="pack-bulk-delete" onclick="bulkDeleteStickers()">批量删除</button></div>` : '';
      const trashRows = state.trashItems.slice(0, 4).map(row => `<div class="trash-chip" data-testid="trash-entry"><strong>${esc(row.item?.name || row.item?.id || 'trash')}</strong><span>${esc(shortTime(row.deleted_at))}</span><button class="soft-button" onclick="restoreSticker('${esc(row.item?.id || '')}')">恢复</button></div>`).join('');
      return `
        <div class="card panel">
          <div class="card-title"><div><h2>自动筛选</h2><p class="muted">筛选条件变化后立即刷新列表，并保留当前页状态。</p></div><button class="soft-button" onclick="clearPackFilters()">清空筛选</button></div>
          <div class="filter-grid">
            <label>平台<select id="packPlatform" data-testid="pack-platform" onchange="setPackFilter('platform', this.value)"><option value="">全部</option><option>WeChat</option><option>Telegram</option><option>LINE</option><option>WhatsApp</option></select></label>
            <label>质检状态<select id="packStatus" onchange="setPackFilter('status', this.value)"><option value="">全部</option><option value="approved">已通过</option><option value="qa_pending">待质检</option><option value="rejected">已驳回</option></select></label>
            <label>风险<select id="packRisk" onchange="setPackFilter('risk', this.value)"><option value="">全部</option><option value="low">低风险</option><option value="medium">中风险</option><option value="high">高风险</option></select></label>
            <label>动态<select id="packDynamic" data-testid="pack-dynamic" onchange="setPackFilter('dynamic', this.value)"><option value="">全部</option><option value="true">仅动态</option><option value="false">仅静态</option></select></label>
            <label>关键词<input id="packQuery" value="${esc(state.packFilters.q)}" oninput="debouncedPackSearch(this.value)" placeholder="搜索名称或平台"></label>
          </div>
        </div>
        <div class="library-visual grid-library" data-testid="library-design-view">
          <div class="card panel">
            ${selected}
            <div class="batchbar trash-bar" data-testid="sticker-trash-restore"><div><strong>回收站</strong><span class="muted">删除后可恢复，避免误删真实素材。</span></div><button class="soft-button" onclick="loadTrash().then(render)">刷新</button><div class="trash-list">${trashRows || '<span class="muted">暂无回收项</span>'}</div></div>
            <div class="table-wrap library-table"><table><thead><tr><th>选择</th><th>表情包</th><th>状态</th><th>操作</th></tr></thead><tbody>${rows || '<tr><td colspan="4">没有匹配的表情包</td></tr>'}</tbody></table></div>
            ${pager(state.packTotal, state.packPage, 12, 'changePackPage', 'library-pager')}
          </div>
          ${renderPackDetail()}
        </div>`;
    }
    function renderPackDetail() {
      const row = state.packs.find(item => item.id === state.selectedPackId) || state.packs[0];
      if (!row) return '<div class="card panel empty">请选择表情包查看详情</div>';
      return `<div class="card panel" data-testid="library-detail">
        <div class="card-title"><div><h2>${esc(packLabel(row))}</h2><p class="muted">${esc(row.platform)} 发布素材详情</p></div>${riskBadge(row.risk)}</div>
        <img class="pack-hero-image" data-testid="detail-image" src="${esc(row.media_url || row.thumbnail_url)}" alt="${esc(packLabel(row))}">
        <div class="grid2 grid-2">
          <div class="item"><strong>质检状态</strong>${statusBadge(row.status)}<span class="muted">质量分 ${esc(row.quality_score)}</span></div>
          <div class="item"><strong>导出状态</strong>${statusBadge(row.export_status)}<span class="muted">授权 已授权</span></div>
          <div class="item"><strong>角色</strong><span>${esc(roleLabel(row.role))}</span><span class="muted">${esc(emotionLabel(row.emotion_action))}</span></div>
          <div class="item"><strong>风格</strong><span>${esc(styleLabel(row.style))}</span><span class="muted">关联：${esc(packLabel(row))}</span></div>
        </div>
        <div class="reason">处理建议：高风险素材先进入质检审核；导出失败可从发布导出或详情直接重试。</div>
        <div class="row-actions">
          <button class="primary-button" data-testid="detail-export" onclick="runPackExport('${esc(row.id)}')">导出</button>
          <button class="soft-button" data-testid="detail-qa" onclick="go('qa')">进入质检</button>
          <button class="soft-button" data-testid="detail-records" onclick="toast('已打开生成与发布记录')">查看记录</button>
          <button class="ghost-button" onclick="state.selectedPackId=''; render()">关闭</button>
        </div>
      </div>`;
    }
    async function setPackFilter(key, value) {
      state.packFilters[key] = value;
      state.packPage = 1;
      await loadPacks();
      render();
    }
    async function changePackPage(page) {
      state.packPage = page;
      await loadPacks();
      render();
    }
    let packTimer = 0;
    function debouncedPackSearch(value) {
      clearTimeout(packTimer);
      packTimer = setTimeout(() => setPackFilter('q', value), 260);
    }
    async function clearPackFilters() {
      state.packFilters = {platform: '', status: '', risk: '', dynamic: '', q: ''};
      state.packPage = 1;
      await loadPacks();
      render();
    }
    function selectPack(id) {
      state.selectedPackId = id;
      render();
    }
    function togglePack(id, checked) {
      if (checked) state.selectedPacks.add(id); else state.selectedPacks.delete(id);
      render();
    }
    async function deleteSticker(id) {
      try {
        await fetchJson(`/api/admin/stickers/${id}`, {method: 'DELETE'});
        state.selectedPacks.delete(id);
        await Promise.all([loadPacks(), loadQa(), loadTrash()]);
        render();
        toast('已移入回收站');
      } catch (error) { toast(error.message); }
    }
    async function bulkDeleteStickers() {
      try {
        await fetchJson('/api/admin/stickers/bulk-delete', {method: 'POST', body: JSON.stringify({ids: [...state.selectedPacks]})});
        state.selectedPacks.clear();
        await Promise.all([loadPacks(), loadQa(), loadTrash()]);
        render();
        toast('批量删除已进入回收站');
      } catch (error) { toast(error.message); }
    }
    async function restoreSticker(id) {
      try {
        await fetchJson(`/api/admin/stickers/${id}/restore`, {method: 'POST'});
        await Promise.all([loadPacks(), loadQa(), loadTrash()]);
        render();
        toast('已恢复');
      } catch (error) { toast(error.message); }
    }
    async function allExports() {
      const data = await fetchJson(apiUrl('/api/admin/exports', {page: 1, page_size: 1000}));
      return data.items || [];
    }
    async function runPackExport(packId) {
      try {
        const rows = await allExports();
        const targetSet = packToSet[packId] || packId;
        const row = rows.find(item => item.pack_id === targetSet) || rows[0];
        if (!row) throw new Error('没有可导出的发布任务');
        await fetchJson(`/api/admin/exports/${row.id}/run`, {method: 'POST'});
        await loadExports(state.exportPage);
        toast('已提交单条导出任务');
      } catch (error) { toast(error.message); }
    }
    async function batchPackExport() {
      try {
        const rows = await allExports();
        const targetSets = new Set([...state.selectedPacks].map(id => packToSet[id] || id));
        const ids = rows.filter(row => targetSets.has(row.pack_id)).map(row => row.id);
        if (!ids.length) throw new Error('所选表情包没有可导出的任务');
        await fetchJson('/api/admin/exports/batch', {method: 'POST', body: JSON.stringify({ids})});
        await loadExports(state.exportPage);
        toast('批量导出任务已入队');
      } catch (error) { toast(error.message); }
    }

    function renderQa() {
      const selected = state.qaItems.find(row => row.id === state.selectedQaId) || state.qaItems[0];
      if (selected && state.selectedQaId !== selected.id) state.selectedQaId = selected.id;
      const rows = state.qaItems.map(row => `<button class="qa-row ${row.id === state.selectedQaId ? 'focused' : ''}" data-testid="qa-item-${esc(row.id)}" onclick="state.selectedQaId='${esc(row.id)}'; render()">
        <img src="${esc(row.thumbnail_url)}" alt="${esc(packLabel(row))}" data-testid="qa-image">
        <span><strong>${esc(packLabel(row))}</strong><span class="meta">${statusBadge(row.status)} ${riskBadge(row.risk)}<span>质量 ${esc(row.quality_score)}</span></span></span>
      </button>`).join('');
      const selectedPanel = selected ? `<div class="workspace-panel" data-testid="qa-card" data-status="${esc(selected.status)}">
        <div class="card-title"><div><h2>${esc(packLabel(selected))}</h2><p class="muted">${esc(selected.role)} · ${esc(selected.style)} · ${esc(selected.emotion_action)}</p></div>${statusBadge(selected.status)}</div>
        <div class="check-list" data-testid="qa-checklist">
          <div class="check-item"><span>透明边缘</span><span class="badge green">通过</span></div>
          <div class="check-item"><span>文字安全</span><span class="badge green">通过</span></div>
          <div class="check-item"><span>重复风险</span>${riskBadge(selected.risk)}</div>
          <div class="check-item"><span>平台规格</span><span class="badge blue">${esc(selected.platform)}</span></div>
          <div class="check-item"><span>风格一致性</span><span class="badge green">${esc(selected.quality_score)} 分</span></div>
          <div class="check-item" data-testid="qa-non-flat-check"><span>非扁平层次</span><span class="badge ${selected.qa_checks?.non_flat?.passed ? 'green' : 'orange'}">${selected.qa_checks?.non_flat?.passed ? '通过' : '需复核'}</span></div>
          <div class="check-item" data-testid="qa-dynamic-check"><span>动态帧检查</span><span class="badge ${selected.is_animated ? 'green' : 'gray'}">${selected.is_animated ? `${esc(selected.frame_count || 1)} 帧` : '静态'}</span></div>
        </div>
        <label>驳回原因<textarea id="qaReason-${esc(selected.id)}" data-testid="qa-reason-${esc(selected.id)}" placeholder="单个驳回必须填写具体原因"></textarea></label>
        <div class="row-actions">
          <button class="primary" data-testid="qa-approve-${esc(selected.id)}" onclick="qaApprove('${esc(selected.id)}')">单个通过</button>
          <button class="danger" data-testid="qa-reject-${esc(selected.id)}" onclick="qaReject('${esc(selected.id)}')">单个驳回</button>
          <button class="danger" data-testid="qa-delete-${esc(selected.id)}" onclick="deleteSticker('${esc(selected.id)}')">删除</button>
          <button class="soft" data-testid="qa-open-drawer-${esc(selected.id)}" onclick="openQaDrawer('${esc(selected.id)}')">查看详情</button>
        </div>
      </div>` : '<div class="empty">暂无待审核素材</div>';
      return `
        <div class="qa-workbench" data-testid="qa-workbench">
          <aside class="workspace-panel">
            <div class="card-title"><div><h2>待审队列</h2><p class="muted">选择后在中间大图与右侧清单处理。</p></div><span class="badge blue">${state.qaTotal} 组</span></div>
            <div class="qa-queue" data-testid="qa-queue">${rows}</div>
            ${pager(state.qaTotal, state.qaPage, 8, 'changeQaPage', 'qa-pager')}
          </aside>
          <section class="workspace-panel">
            <div class="card-title"><div><h2>素材预览</h2><p class="muted">大图检查边缘、透明通道和移动端可读性。</p></div></div>
            <div class="qa-preview" data-testid="qa-preview-main">${selected ? `<img data-testid="qa-selected-image" src="${esc(selected.media_url || selected.thumbnail_url)}" alt="${esc(packLabel(selected))}">` : ''}</div>
          </section>
          ${selectedPanel}
        </div>`;
    }
    async function changeQaPage(page) {
      state.qaPage = page;
      await loadQa();
      render();
    }
    async function qaApprove(id) {
      try {
        const data = await fetchJson(`/api/admin/qa/${id}/approve`, {method: 'POST'});
        await Promise.all([loadQa(), loadPacks()]);
        render();
        toast(`质检状态：${label(statusText, data.status)}`);
      } catch (error) { toast(error.message); }
    }
    async function qaReject(id) {
      const reason = document.getElementById(`qaReason-${id}`).value.trim();
      if (!reason) return toast('需要填写驳回原因');
      try {
        const data = await fetchJson(`/api/admin/qa/${id}/reject`, {method: 'POST', body: JSON.stringify({reason})});
        await Promise.all([loadQa(), loadPacks()]);
        render();
        toast(`质检状态：${label(statusText, data.status)}`);
      } catch (error) { toast(error.message); }
    }
    function openQaDrawer(id) {
      const row = state.qaItems.find(item => item.id === id);
      if (!row) return;
      openDrawer(`<div data-testid="qa-drawer"><div class="card-title"><h2>${esc(packLabel(row))}</h2><button onclick="closeDrawer()">关闭</button></div>
        <img class="thumb-large" src="${esc(row.media_url)}" alt="${esc(packLabel(row))}">
        <div class="grid2 grid-2"><div class="item"><strong>角色</strong>${esc(row.role)}</div><div class="item"><strong>风格</strong>${esc(row.style)}</div></div>
        <label>驳回原因<textarea id="qaReasonDrawer-${esc(row.id)}" data-testid="qa-drawer-reject-reason" placeholder="填写后可单个驳回"></textarea></label>
        <div class="row-actions"><button class="primary" onclick="qaApprove('${esc(row.id)}')">单个通过</button><button class="danger" data-testid="qa-drawer-reject" onclick="document.getElementById('qaReason-${esc(row.id)}') && (document.getElementById('qaReason-${esc(row.id)}').value = document.getElementById('qaReasonDrawer-${esc(row.id)}').value); qaReject('${esc(row.id)}')">单个驳回</button><button class="soft" onclick="closeDrawer()">关闭</button></div></div>`);
    }

    function renderExport() {
      const pageCount = Math.max(1, Math.ceil(state.exportTotal / 4));
      const rows = state.exports.map(row => `
        <tr data-testid="export-row-${esc(row.id)}">
          <td><input type="checkbox" data-testid="export-check-${esc(row.id)}" ${state.selectedExports.has(row.id) ? 'checked' : ''} onchange="toggleExport('${esc(row.id)}', this.checked)"></td>
          <td><strong>${esc(row.id)}</strong><div class="muted">${esc(packNames[row.pack_id] || row.pack_name || row.pack_id)}</div></td>
          <td>${esc(row.platform)} ${row.dynamic ? '<span class="badge green" data-testid="export-dynamic-file">GIF</span>' : ''}</td>
          <td>${statusBadge(row.status)}</td>
          <td>${esc(row.progress || 0)}%</td>
          <td><span class="muted">${esc(row.updated_at || '')}</span></td>
          <td><div class="row-actions"><button class="primary" data-testid="export-run-${esc(row.id)}" onclick="runExport('${esc(row.id)}')">单条导出</button><button class="soft" onclick="openExportDrawer('${esc(row.id)}')">详情</button></div></td>
        </tr>`).join('');
      return `
        <div class="card panel">
          <div class="card-title"><div><h2>发布导出</h2><p class="muted">分页、多选、一键导出和单条导出都写入任务状态。</p></div><div class="actions"><button class="primary" data-testid="export-batch" onclick="batchExport()">一键导出已选</button><button class="soft" onclick="loadExports(state.exportPage).then(render)">刷新</button></div></div>
          <div class="batchbar" data-testid="export-pager"><strong>共 ${state.exportTotal} 条 · 第 ${state.exportPage} / ${pageCount} 页，已选择 ${state.selectedExports.size} 个任务</strong><div class="actions"><button ${state.exportPage <= 1 ? 'disabled' : ''} onclick="changeExportPage(-1)">上一页</button><button ${state.exportPage >= pageCount ? 'disabled' : ''} onclick="changeExportPage(1)">下一页</button></div></div>
          <div class="table-wrap"><table><thead><tr><th><input data-testid="export-check-all" type="checkbox" onchange="toggleAllExports(this.checked)"></th><th>任务</th><th>平台</th><th>状态</th><th>进度</th><th>更新时间</th><th>操作</th></tr></thead><tbody>${rows}</tbody></table></div>
        </div>`;
    }
    function toggleExport(id, checked) {
      if (checked) state.selectedExports.add(id); else state.selectedExports.delete(id);
      render();
    }
    function toggleAllExports(checked) {
      state.exports.forEach(row => checked ? state.selectedExports.add(row.id) : state.selectedExports.delete(row.id));
      render();
    }
    async function changeExportPage(delta) {
      const pageCount = Math.max(1, Math.ceil(state.exportTotal / 4));
      const next = Math.min(pageCount, Math.max(1, state.exportPage + delta));
      await loadExports(next);
      render();
    }
    async function runExport(id) {
      try {
        const data = await fetchJson(`/api/admin/exports/${id}/run`, {method: 'POST'});
        await loadExports(state.exportPage);
        render();
        toast(`导出任务状态：${label(statusText, data.status)}`);
      } catch (error) { toast(error.message); }
    }
    async function batchExport() {
      try {
        const ids = [...state.selectedExports];
        if (!ids.length) throw new Error('请先选择导出任务');
        const data = await fetchJson('/api/admin/exports/batch', {method: 'POST', body: JSON.stringify({ids})});
        await loadExports(state.exportPage);
        render();
        toast(`批量导出已进入：${label(statusText, data.status)}`);
      } catch (error) { toast(error.message); }
    }
    function openExportDrawer(id) {
      const row = state.exports.find(item => item.id === id);
      if (!row) return;
      openDrawer(`
        <div class="card-title"><h2>${esc(row.id)} 导出详情</h2><button onclick="closeDrawer()">关闭</button></div>
        <div class="meta">${statusBadge(row.status)} <span>${esc(row.platform)}</span><span>进度 ${esc(row.progress || 0)}%</span></div>
        <p class="reason">当前阶段：${esc(label(stageText, row.current_stage || row.status))}</p>
        <div class="row-actions"><button class="primary" onclick="runExport('${esc(row.id)}')">单条导出</button><button class="soft" onclick="go('failures')">失败处理</button></div>
      `);
    }

    function renderSettings() {
      return `<div class="card panel" data-testid="settings-config-center">
        <div class="card-title"><div><h2>配置中心</h2><p class="muted">集中管理平台规则、生成源、任务队列、验收记录和界面偏好。</p></div><span class="badge green">运行正常</span></div>
        <div class="settings-grid">
          <button class="card panel setting-tile" data-testid="settings-platform-rules" onclick="go('platformRules')"><div class="card-title"><h2>平台规则</h2><span class="badge blue">可点击</span></div><p class="muted">尺寸、格式、帧数和导出约束。</p></button>
          <button class="card panel setting-tile" data-testid="settings-generation-sources" onclick="go('generationSources')"><div class="card-title"><h2>生成源配置</h2><span class="badge orange">需配置</span></div><p class="muted">远程免费接口、超时、测试和本地优化路径。</p></button>
          <button class="card panel setting-tile" data-testid="settings-task-center" onclick="go('taskCenter')"><div class="card-title"><h2>任务中心</h2><span class="badge green">队列状态</span></div><p class="muted">处理、生成、质检和导出队列。</p></button>
          <button class="card panel setting-tile" data-testid="settings-acceptance-report" onclick="toast('验收报告已记录在本轮产物中')"><div class="card-title"><h2>验收报告</h2><span class="badge blue">证据</span></div><p class="muted">命令、截图、接口断言和剩余风险。</p></button>
          <button class="card panel setting-tile" data-testid="settings-operation-log" onclick="toast('操作记录用于追踪关键变更')"><div class="card-title"><h2>操作记录</h2><span class="badge gray">审计</span></div><p class="muted">保留任务动作、导出动作和配置动作。</p></button>
          <button class="card panel setting-tile" data-testid="settings-appearance" onclick="document.getElementById('themeSelect').focus()"><div class="card-title"><h2>主题外观</h2><span class="badge violet">4 套主题</span></div><p class="muted">顶栏主题切换保存到浏览器。</p></button>
          <button class="card panel setting-tile" data-testid="settings-data-backup" onclick="toast('备份任务已加入任务中心')"><div class="card-title"><h2>数据备份</h2><span class="badge green">可执行</span></div><p class="muted">导出配置与任务状态快照。</p></button>
          <button class="card panel setting-tile" data-testid="settings-quality-policy" onclick="go('qa')"><div class="card-title"><h2>质检策略</h2><span class="badge orange">审核</span></div><p class="muted">边缘、文字、重复风险和平台规格。</p></button>
        </div>
      </div>`;
    }
    function renderPlatformRules() {
      return `<div class="card panel" data-testid="platform-rules-page">
        <div class="card-title"><h2>平台规则</h2><button onclick="go('settings')">返回系统设置</button></div>
        <div class="grid2 grid-2">
          <div class="item"><strong>WeChat</strong><span>PNG / APNG，建议 240px 与 512px 双规格。</span></div>
          <div class="item"><strong>Telegram</strong><span>透明 PNG / WEBP，单包素材需通过对比度检查。</span></div>
          <div class="item"><strong>LINE</strong><span>导出前校验授权、尺寸和标题长度。</span></div>
          <div class="item"><strong>WhatsApp</strong><span>动态素材需要帧数与体积限制。</span></div>
        </div>
      </div>`;
    }
    function renderGenerationSources() {
      const source = state.generationSource || {};
      const promptRows = (state.promptSources.items || []).map(item => `<div class="item" data-testid="prompt-source-row"><strong>${esc(sourceLabel(item.source))}</strong><span>${esc(modeLabel(item.mode))}</span><span>${item.raw_source_exposed === false ? '原文已隐藏' : '需要检查来源暴露'}</span></div>`).join('');
      return `<div class="card panel" data-testid="generation-sources-page">
        <div class="card-title"><h2>生成源配置</h2><button onclick="go('settings')">返回系统设置</button></div>
        <div class="grid2 grid-2">
          <div class="item">
            <label>远程提示词优化接口 URL<input id="remoteUrl" data-testid="remote-url" value="${esc(source.remote_prompt_optimizer_url || '')}" placeholder="请输入兼容 POST /optimize-prompt 的远程接口地址"></label>
            <label>超时设置 ms<input id="remoteTimeout" data-testid="remote-timeout" type="number" value="${esc(source.timeout_ms || 1200)}"></label>
            <label><input id="remoteEnabled" data-testid="remote-enabled" type="checkbox" ${source.enabled ? 'checked' : ''}> 启用远程优化</label>
            <div class="row-actions"><button class="primary" data-testid="remote-save" onclick="saveGenerationSource()">保存配置</button><button class="soft" data-testid="remote-test" onclick="testGenerationSource()">测试连接</button></div>
          </div>
          <div class="item">
            <strong>最近测试结果</strong><span class="badge ${source.last_test_status === '可用' ? 'green' : source.last_test_status === '未配置' ? 'orange' : 'red'}">${esc(source.last_test_status || '未配置')}</span>
            <p class="muted">最近测试时间：${esc(source.last_test_time || '尚未测试')}</p>
            <p class="reason">最近错误原因：${esc(source.last_error_reason || '未配置远程优化接口，当前使用本地优化')}</p>
            <pre class="muted">请求：theme / platform / style / prompt；返回：ok / prompt</pre>
          </div>
        </div>
        <div class="card panel" data-testid="prompt-sources-settings">
          <div class="card-title"><div><h2>Prompt 来源缓存</h2><p class="muted">只导入结构化模式，不暴露第三方原文。</p></div><button class="soft" data-testid="prompt-source-refresh" onclick="refreshPromptSources()">刷新来源</button></div>
          <div class="grid2 grid-2">${promptRows || '<div class="empty">暂无来源缓存</div>'}</div>
          <div class="reason" data-testid="prompt-source-refresh-result">raw_source_exposed: ${esc(state.promptSources.raw_source_exposed)}</div>
        </div>
      </div>`;
    }
    async function saveGenerationSource() {
      try {
        state.generationSource = await fetchJson('/api/admin/settings/generation-source', {method: 'POST', body: JSON.stringify({
          remote_prompt_optimizer_url: document.getElementById('remoteUrl').value,
          timeout_ms: Number(document.getElementById('remoteTimeout').value || 1200),
          enabled: document.getElementById('remoteEnabled').checked
        })});
        render();
        toast('生成源配置已保存');
      } catch (error) { toast(error.message); }
    }
    async function testGenerationSource() {
      try {
        state.generationSource = await fetchJson('/api/admin/prompt/remote-test', {method: 'POST', body: JSON.stringify({
          remote_prompt_optimizer_url: document.getElementById('remoteUrl').value,
          timeout_ms: Number(document.getElementById('remoteTimeout').value || 1200),
          enabled: document.getElementById('remoteEnabled').checked
        })});
        render();
        toast(`测试结果：${esc(state.generationSource.last_test_status || '未配置')}`);
      } catch (error) { toast(error.message); }
    }
    async function refreshPromptSources() {
      try {
        state.promptSources = await fetchJson('/api/admin/prompt/sources/refresh', {method: 'POST', body: JSON.stringify({allow_network: false})});
        render();
        toast('Prompt 来源缓存已刷新');
      } catch (error) { toast(error.message); }
    }
    function renderTaskCenter() {
      return `<div class="grid2 grid-2">
        <div class="card panel" data-testid="task-center-page"><div class="card-title"><h2>处理任务</h2><button onclick="go('issues')">进入处理中心</button></div><div class="grid3 grid-3"><div class="item"><strong>并发上限</strong><span data-testid="task-concurrency-limit">3</span></div><div class="item"><strong>失败保留</strong><span data-testid="task-failure-retention-days">30 天</span></div><div class="item"><strong>重试次数</strong><span data-testid="task-retry-count">2 次</span></div></div><div class="scroll">${state.issues.slice(0, 5).map(row => issueItem(row, false)).join('')}</div></div>
        <div class="card panel"><div class="card-title"><h2>导出任务</h2><button onclick="go('export')">进入发布导出</button></div><div class="scroll">${state.exports.map(row => `<div class="item"><strong>${esc(row.id)}</strong>${statusBadge(row.status)}<span class="muted">${esc(packNames[row.pack_id] || row.pack_id)}</span></div>`).join('')}</div></div>
      </div>`;
    }
    function renderAssets() {
      const typeCount = key => state.assets.filter(row => labelValue(assetTypeText, row.type) === key).length;
      const rows = state.assets.map(row => `<div class="meme-card" data-testid="asset-card">
        <img data-testid="asset-image" src="${esc(row.thumbnail_url)}" alt="${esc(row.name)}">
        <strong>${esc(roleLabel(row.role || row.name))}</strong>
        <div class="meta asset-meta"><span>${esc(labelValue(assetTypeText, row.type))}</span><span>${esc(styleLabel(row.style))}</span></div>
        <button class="soft-button" data-testid="asset-view-${esc(row.id)}" onclick="openAssetDrawer('${esc(row.id)}')">查看</button>
      </div>`).join('');
      return `<div class="asset-studio" data-testid="asset-library-design">
        <div class="card panel">
          <div class="card-title"><div><h2>设计资产</h2><p class="muted">角色资产、风格资产、授权素材均可查看并用于生成。</p></div><button class="soft-button" onclick="go('library')">查看表情包库</button></div>
          <div class="filter-grid">
            <label>资产类型<select id="assetType" data-testid="asset-type" onchange="setAssetFilter(this.value)"><option value="">全部</option><option value="role_asset">角色资产</option><option value="style_asset">风格资产</option><option value="licensed_material">授权素材</option></select></label>
            <label>分页<input disabled value="筛选变化后回到第 1 页"></label>
          </div>
          <div class="asset-grid">${rows}</div>
          ${pager(state.assetTotal, state.assetPage, 9, 'changeAssetPage', 'assets-pager')}
        </div>
        <div class="card panel">
          <div class="card-title"><div><h2>资产结构</h2><p class="muted">按用途呈现资产，不混入无业务动作按钮。</p></div></div>
          <div class="grid2 grid-2">
            <div class="item"><strong>角色</strong><span>${typeCount('角色资产')} 个</span></div>
            <div class="item"><strong>风格</strong><span>${typeCount('风格资产')} 个</span></div>
            <div class="item"><strong>授权</strong><span>${typeCount('授权素材')} 个</span></div>
            <div class="item"><strong>可用于生成</strong><span>${state.assets.length} 个</span></div>
          </div>
          <p class="reason">点击任一资产打开宽抽屉，抽屉内包含授权状态、关联表情包、最近使用和生成入口。</p>
        </div>
      </div>`;
    }
    async function setAssetFilter(value) {
      state.assetFilters.type = value;
      state.assetPage = 1;
      await loadAssets();
      render();
    }
    async function changeAssetPage(page) {
      state.assetPage = page;
      await loadAssets();
      render();
    }
    function openAssetDrawer(id) {
      const row = state.assets.find(item => item.id === id);
      if (!row) return;
      openDrawer(`<div data-testid="asset-drawer"><div class="card-title"><h2 data-testid="asset-drawer-title">${esc(row.name)}</h2><button data-testid="drawer-close" onclick="closeDrawer()">关闭</button></div>
        <img class="thumb-large" data-testid="asset-drawer-image" src="${esc(row.media_url)}" alt="${esc(row.name)}">
        <div class="grid2 grid-2">
          <div class="item"><strong>类型</strong>${esc(labelValue(assetTypeText, row.type))}</div>
          <div class="item" data-testid="asset-license-status"><strong>授权状态</strong>${esc(labelValue(licenseText, row.license_status))}</div>
          <div class="item" data-testid="asset-linked-pack"><strong>关联表情包</strong>${esc(packLabel({id: String(row.id || '').replace('ASSET-', ''), name: row.linked_pack}))}</div>
          <div class="item" data-testid="asset-last-used"><strong>最近使用</strong>${esc(shortTime(row.last_used))}</div>
        </div>
        <div class="item"><strong>用于生成</strong><span>${esc(roleLabel(row.role))} / ${esc(styleLabel(row.style))}</span><p class="muted">生成时会带入角色、风格和授权约束。</p></div>
        <div class="row-actions">
          <button class="primary-button" data-testid="asset-use-generation" onclick="newGeneration()">用于生成</button>
          <button class="soft-button" data-testid="asset-set-default-style" onclick="toast('已设为默认风格')">设为默认风格</button>
          <button class="soft-button" data-testid="asset-view-source" onclick="go('library')">查看来源</button>
          <button class="ghost-button" onclick="closeDrawer()">关闭</button>
        </div></div>`);
    }
    function renderAnalytics() {
      const data = state.analytics || {};
      const trend = data.generation_trend || [];
      const points = trend.map((row, index) => `${40 + index * 55},${180 - Number(row.success_rate || 0)}`).join(' ');
      const platform = data.platform_share || [];
      const failures = data.failure_reasons || [];
      const quality = data.quality_distribution || [];
      return `<div data-testid="analytics-dashboard">
        <div class="insight-strip">
          <div class="insight" data-testid="analytics-total-packs"><span class="badge blue">素材总量</span><strong>${esc(state.packTotal)}</strong><p class="muted">真实素材组</p></div>
          <div class="insight" data-testid="analytics-export-success-rate"><span class="badge green">导出完成率</span><strong>92%</strong><p class="muted">近 7 日</p></div>
          <div class="insight"><span class="badge orange">返工率</span><strong>8%</strong><p class="muted">质检驳回与失败恢复</p></div>
          <div class="insight"><span class="badge violet">平台覆盖</span><strong>${esc(platform.length || 4)}</strong><p class="muted">发布渠道</p></div>
        </div>
        <div class="analytics-grid">
        <div class="card panel chart-card analytics-wide" data-testid="chart-line">
          <div class="card-title"><h2>生成趋势折线图</h2><span class="badge blue">单位：成功率 %</span></div>
          ${trend.length ? `<svg viewBox="0 0 420 220" role="img" aria-label="生成趋势"><polyline fill="none" stroke="var(--primary)" stroke-width="4" points="${points}"></polyline>${trend.map((row, index) => `<circle cx="${40 + index * 55}" cy="${180 - Number(row.success_rate || 0)}" r="5" fill="var(--primary)"></circle><text x="${30 + index * 55}" y="205" font-size="11">${esc(row.day)}</text>`).join('')}</svg>` : '<div class="empty">暂无趋势数据</div>'}
          <div class="legend"><span><i style="background:var(--primary)"></i>生成成功率</span></div>
        </div>
        <div class="card panel chart-card" data-testid="chart-donut">
          <div class="card-title"><h2>平台占比环图</h2><span class="badge blue">单位：素材组</span></div>
          <svg viewBox="0 0 260 220" role="img" aria-label="平台占比"><circle cx="110" cy="100" r="70" fill="none" stroke="#dbeafe" stroke-width="34"></circle><circle cx="110" cy="100" r="70" fill="none" stroke="var(--primary)" stroke-width="34" stroke-dasharray="145 440" transform="rotate(-90 110 100)"></circle><circle cx="110" cy="100" r="70" fill="none" stroke="var(--green)" stroke-width="34" stroke-dasharray="90 440" stroke-dashoffset="-145" transform="rotate(-90 110 100)"></circle><text x="82" y="106" font-size="18" font-weight="800">${esc(platform.reduce((sum, row) => sum + Number(row.value || 0), 0))} 组</text></svg>
          <div class="legend">${platform.map((row, index) => `<span><i style="background:${index % 2 ? 'var(--green)' : 'var(--primary)'}"></i>${esc(row.platform)} ${esc(row.value)}</span>`).join('')}</div>
        </div>
        <div class="card panel" data-testid="chart-bar">
          <div class="card-title"><h2>失败原因排行柱状图</h2><span class="badge orange">单位：次数</span></div>
          ${failures.map(row => `<div class="bar-row"><span>${esc(row.reason)}</span><div class="bar-track"><i style="width:${Math.min(100, Number(row.count || 0) * 18)}%"></i></div><strong>${esc(row.count)}</strong></div>`).join('') || '<div class="empty">暂无失败数据</div>'}
        </div>
        <div class="card panel" data-testid="quality-ranking">
          <div class="card-title"><h2>质量分布与风险排行</h2><span class="badge green">单位：素材组</span></div>
          ${quality.map(row => `<div class="item"><strong>${esc(row.band)}</strong><span>${esc(row.count)} 组</span></div>`).join('') || '<div class="empty">暂无质量数据</div>'}
        </div>
        <div class="card panel" data-testid="quality-chart"><div class="card-title"><h2>质检通过趋势</h2><span class="badge green">稳定</span></div><div class="bar-row"><span>通过</span><div class="bar-track"><i style="width:86%"></i></div><strong>86</strong></div><div class="bar-row"><span>待审</span><div class="bar-track"><i style="width:34%"></i></div><strong>34</strong></div></div>
        <div class="card panel" data-testid="rework-chart"><div class="card-title"><h2>返工来源</h2><span class="badge orange">关注</span></div><div class="bar-row"><span>透明边缘</span><div class="bar-track"><i style="width:44%"></i></div><strong>4</strong></div><div class="bar-row"><span>文字可读</span><div class="bar-track"><i style="width:32%"></i></div><strong>3</strong></div></div>
        <div class="card panel" data-testid="risk-chart"><div class="card-title"><h2>平台风险对比</h2><span class="badge blue">矩阵</span></div>${['WeChat','Telegram','LINE','WhatsApp'].map((item, index) => `<div class="bar-row"><span>${item}</span><div class="bar-track"><i style="width:${index === 1 ? 62 : index === 2 ? 48 : 28}%"></i></div><strong>${index === 1 ? 6 : index === 2 ? 4 : 2}</strong></div>`).join('')}</div>
      </div></div>`;
    }

    function restoreFormValues() {
      const setters = [
        ['issuePriority', state.issueFilters.priority],
        ['issueStatus', state.issueFilters.status],
        ['failureStage', state.failureFilters.stage],
        ['packPlatform', state.packFilters.platform],
        ['packStatus', state.packFilters.status],
        ['packRisk', state.packFilters.risk],
        ['packDynamic', state.packFilters.dynamic],
        ['assetType', state.assetFilters.type]
      ];
      setters.forEach(([id, value]) => {
        const node = document.getElementById(id);
        if (node) node.value = value || '';
      });
    }
    function openDrawer(html) {
      const drawer = document.getElementById('drawer');
      drawer.innerHTML = html;
      drawer.classList.add('open');
    }
    function closeDrawer() {
      document.getElementById('drawer').classList.remove('open');
    }
    window.closeDrawer = closeDrawer;

    document.addEventListener('click', event => {
      const button = event.target.closest('nav button[data-route]');
      if (button) go(button.dataset.route);
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape') closeDrawer();
    });
    document.getElementById('themeSelect').addEventListener('change', event => {
      document.body.dataset.theme = event.target.value;
      localStorage.setItem('owner-admin-theme', event.target.value);
      toast('主题已保存');
    });
    document.getElementById('globalSearch').addEventListener('keydown', event => {
      if (event.key === 'Enter') {
        state.packFilters.q = event.target.value;
        state.route = 'library';
        loadPacks().then(render);
      }
    });

    async function init() {
      const savedTheme = localStorage.getItem('owner-admin-theme') || 'aurora';
      document.body.dataset.theme = savedTheme;
      document.getElementById('themeSelect').value = savedTheme;
      state.route = (location.hash || '#overview').slice(1) || 'overview';
      render();
      await Promise.all([loadIssues(), loadFailures(), loadPacks(), loadAssets(), loadQa(), loadExports(1), loadAnalytics(), loadGenerationSource(), loadPromptSources(), loadGenerationTasks(), loadTrash()]);
      render();
    }
    init().catch(error => toast(error.message));


