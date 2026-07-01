import os
from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse

from app.admin_contracts import admin_error, admin_ok
from app.admin_services import AdminService
from app.admin_store import AdminStore
from app.admin_ui import V7_ADMIN_HTML
from app.audit import 审计服务
from app.analytics import 数据回流服务
from app.asset_validator import 资产校验服务
from app.audience import 受众画像服务
from app.generation import 生成策略服务
from app.hotspot import 热点服务
from app.ip_roles import 原创角色服务
from app.loop_acceptance import LOOP验收服务
from app.platform_packages import 平台包服务
from app.publishing import 发布服务
from app.review import 审核服务
from app.rule_governance import 平台规则治理服务
from app.schemas import (
    创建任务请求,
    创建下一轮策略请求,
    创建发布任务请求,
    创建优化周报请求,
    创建平台规则版本请求,
    创建受众画像请求,
    创建生成策略请求,
    创建原创角色请求,
    创建定时任务请求,
    创建热点请求,
    执行发布请求,
    回滚平台规则版本请求,
    启用平台规则版本请求,
    二审请求,
    LOOP验收请求,
    发布前复核请求,
    第一阶段总门禁请求,
    再执行队列领取请求,
    再执行记录请求,
    再执行完成请求,
    交付包索引请求,
    资产文件校验请求,
    处理规则反馈请求,
    记录表现请求,
    平台规则校验请求,
    平台包下载前检查请求,
    平台包生成请求,
    表情套装验收请求,
    表情包审核请求,
    退回重生成请求,
    执行定时任务请求,
    任务流转请求,
    自动初审请求,
    转正式策略请求,
    标准响应,
)
from app.scheduler import 定时任务服务
from app.security import 操作人, 获取操作人, 要求角色
from app.sticker_acceptance import 表情套装验收服务
from app.task_center import 任务中心
from app.taxonomy import 标签库
from app.validator import 规格校验器


def 创建路由(
    任务服务: 任务中心,
    审计: 审计服务,
    定时任务: 定时任务服务,
    校验器: 规格校验器,
    资产校验: 资产校验服务,
    套装验收: 表情套装验收服务,
    规则治理: 平台规则治理服务,
    受众画像: 受众画像服务,
    热点: 热点服务,
    原创角色: 原创角色服务,
    生成策略: 生成策略服务,
    审核: 审核服务,
    发布: 发布服务,
    平台包: 平台包服务,
    数据回流: 数据回流服务,
    LOOP验收: LOOP验收服务,
) -> APIRouter:
    router = APIRouter()
    admin_asset_root = Path(__file__).resolve().parents[1] / "data" / "generated_assets"
    admin_state_path = Path(
        os.environ.get(
            "AI_EMOJI_ADMIN_STATE_PATH",
            str(Path(__file__).resolve().parents[1] / "data" / "admin_state.json"),
        )
    )
    admin_service = AdminService(AdminStore(admin_state_path))

    @router.get("/admin-assets/{asset_path:path}", summary="读取后台真实本地缩略图")
    def 读取后台真实本地缩略图(asset_path: str) -> FileResponse:
        target = (admin_asset_root / asset_path).resolve()
        if not target.is_file() or admin_asset_root.resolve() not in target.parents:
            raise HTTPException(status_code=404, detail="asset not found")
        return FileResponse(target, media_type="image/png", filename=target.name)

    @router.get("/api/admin/issues", summary="loop3 admin issues")
    def loop3_admin_issues(
        q: str | None = None,
        priority: str | None = None,
        type: str | None = None,
        platform: str | None = None,
        status: str | None = None,
        sort: str = "priority,updated_desc",
    ) -> dict[str, object]:
        data = admin_service.list_issues(
            {"q": q, "priority": priority, "type": type, "platform": platform, "status": status},
            sort,
        )
        return admin_ok(data, dev_mock=False)

    @router.post("/api/admin/issues/{issue_id}/cancel", summary="loop3 cancel issue")
    def loop3_cancel_issue(issue_id: str) -> dict[str, object]:
        try:
            return admin_ok(admin_service.set_issue_status(issue_id, "cancelled"), dev_mock=False)
        except KeyError:
            return admin_error(
                code="issue_not_found",
                message="Issue was not found.",
                stage="issue_cancel",
                recoverable=False,
                actions=["refresh"],
                dev_mock=False,
            )

    @router.post("/api/admin/issues/{issue_id}/requeue", summary="loop3 requeue issue")
    def loop3_requeue_issue(issue_id: str) -> dict[str, object]:
        try:
            return admin_ok(admin_service.set_issue_status(issue_id, "queued"), dev_mock=False)
        except KeyError:
            return admin_error("issue_not_found", "Issue was not found.", "issue_requeue", False, ["refresh"])

    @router.post("/api/admin/issues/{issue_id}/resolve", summary="loop3 resolve issue")
    def loop3_resolve_issue(issue_id: str) -> dict[str, object]:
        try:
            return admin_ok(admin_service.set_issue_status(issue_id, "resolved"), dev_mock=False)
        except KeyError:
            return admin_error("issue_not_found", "Issue was not found.", "issue_resolve", False, ["refresh"])

    @router.get("/api/admin/failures", summary="loop3 admin failures")
    def loop3_admin_failures(
        q: str | None = None,
        stage: str | None = None,
        platform: str | None = None,
        status: str | None = None,
        sort: str = "updated_desc",
    ) -> dict[str, object]:
        data = admin_service.list_failures({"q": q, "stage": stage, "platform": platform, "status": status}, sort)
        return admin_ok(data, dev_mock=False)

    @router.post("/api/admin/failures/{failure_id}/cancel", summary="loop3 cancel failure")
    def loop3_cancel_failure(failure_id: str) -> dict[str, object]:
        try:
            return admin_ok(admin_service.set_failure_status(failure_id, "cancelled"), dev_mock=False)
        except KeyError:
            return admin_error("failure_not_found", "Failure task was not found.", "failure_cancel", False, ["refresh"])

    @router.post("/api/admin/failures/{failure_id}/requeue", summary="loop3 requeue failure")
    def loop3_requeue_failure(failure_id: str) -> dict[str, object]:
        try:
            return admin_ok(admin_service.set_failure_status(failure_id, "queued"), dev_mock=False)
        except KeyError:
            return admin_error("failure_not_found", "Failure task was not found.", "failure_requeue", False, ["refresh"])

    @router.get("/api/admin/sticker-packs", summary="loop3 sticker pack adapter")
    def loop3_sticker_packs(
        q: str | None = None,
        platform: str | None = None,
        status: str | None = None,
        type: str | None = None,
        quality_min: int | None = None,
        quality_max: int | None = None,
        export_status: str | None = None,
        risk: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, object]:
        data = admin_service.list_sticker_packs(
            {
                "q": q,
                "platform": platform,
                "status": status,
                "type": type,
                "quality_min": quality_min,
                "quality_max": quality_max,
                "export_status": export_status,
                "risk": risk,
            },
            page,
            page_size,
        )
        return admin_ok(data, dev_mock=False)

    @router.post("/api/admin/prompt/generate", summary="loop3 generate prompt")
    def loop3_generate_prompt(payload: dict[str, object] = Body(default_factory=dict)) -> dict[str, object]:
        data = admin_service.generate_prompt(
            str(payload.get("theme", "")),
            str(payload.get("style", "")),
            str(payload.get("platform", "")),
        )
        return admin_ok(data, dev_mock=False)

    @router.post("/api/admin/prompt/optimize", summary="loop3 optimize prompt")
    def loop3_optimize_prompt(payload: dict[str, object] = Body(default_factory=dict)) -> dict[str, object]:
        return admin_ok(admin_service.optimize_prompt(str(payload.get("prompt", ""))), dev_mock=False)

    @router.post("/api/admin/prompt/optimize-remote", summary="loop3 remote prompt fallback")
    def loop3_optimize_prompt_remote(payload: dict[str, object] = Body(default_factory=dict)) -> dict[str, object]:
        return admin_ok(admin_service.optimize_prompt_remote(str(payload.get("prompt", ""))), dev_mock=False)

    @router.get("/api/admin/prompt/history", summary="loop3 prompt history")
    def loop3_prompt_history() -> dict[str, object]:
        return admin_ok({"items": admin_service.prompt_history()}, dev_mock=False)

    @router.get("/api/admin/exports", summary="loop3 export list")
    def loop3_exports(page: int = 1, page_size: int = 4, status: str | None = None, platform: str | None = None) -> dict[str, object]:
        return admin_ok(admin_service.list_exports(page, page_size, status, platform), dev_mock=False)

    @router.post("/api/admin/exports/batch", summary="loop3 batch export")
    def loop3_batch_export(payload: dict[str, object] = Body(default_factory=dict)) -> dict[str, object]:
        ids = payload.get("ids") or []
        if not isinstance(ids, list) or not ids:
            return admin_error("empty_export_selection", "No export rows were selected.", "export_batch", True, ["select_rows"])
        return admin_ok(admin_service.batch_export([str(item) for item in ids]), dev_mock=False)

    @router.post("/api/admin/exports/{export_id}/run", summary="loop3 run export")
    def loop3_run_export(export_id: str) -> dict[str, object]:
        try:
            return admin_ok(admin_service.run_export(export_id), dev_mock=False)
        except KeyError:
            return admin_error("export_not_found", "Export task was not found.", "export_run", False, ["refresh"])

    @router.get("/api/admin/exports/{export_id}", summary="loop3 export detail")
    def loop3_export_detail(export_id: str) -> dict[str, object]:
        for row in admin_service.list_exports(1, 1000)["items"]:
            if row["id"] == export_id:
                return admin_ok(row, dev_mock=False)
        return admin_error("export_not_found", "Export task was not found.", "export_detail", False, ["refresh"])

    @router.get("/api/admin/settings/platform-rules", summary="loop3 platform rules")
    def loop3_platform_rules() -> dict[str, object]:
        rules = [
            {
                "platform": name,
                "size": "512x512",
                "formats": ["png", "webp", "zip"],
                "max_file_size": "1MB",
                "transparent_background": True,
                "animated_rule": "within platform limits",
                "naming_rule": "platform-index",
                "validation_enabled": True,
            }
            for name in ["WeChat", "Telegram", "LINE", "WhatsApp"]
        ]
        return admin_ok({"items": rules}, dev_mock=True)

    @router.put("/api/admin/settings/platform-rules/{platform}", summary="loop3 save platform rule")
    def loop3_save_platform_rule(platform: str, payload: dict[str, object] = Body(default_factory=dict)) -> dict[str, object]:
        return admin_ok({"platform": platform, "payload": payload}, dev_mock=True)

    @router.get("/api/admin/settings/generation-sources", summary="loop3 generation sources")
    def loop3_generation_sources() -> dict[str, object]:
        data = {
            "local_prompt_generator": True,
            "remote_prompt_optimizer_url": "",
            "enabled": False,
            "timeout_ms": 1200,
            "fallback_strategy": "local",
            "last_call_status": "fallback_ready",
        }
        return admin_ok(data, dev_mock=True)

    @router.put("/api/admin/settings/generation-sources", summary="loop3 save generation sources")
    def loop3_save_generation_sources(payload: dict[str, object] = Body(default_factory=dict)) -> dict[str, object]:
        return admin_ok({"payload": payload}, dev_mock=True)

    @router.post("/api/admin/settings/generation-sources/test", summary="loop3 test generation source")
    def loop3_test_generation_source() -> dict[str, object]:
        return admin_ok({"remote": "unavailable", "fallback": "local"}, dev_mock=True)

    @router.get("/health", response_model=标准响应, summary="健康检查")
    def 健康检查() -> 标准响应:
        return 标准响应(成功=True, 消息="后台可启动", 数据={"服务状态": "正常"})

    @router.get("/", response_class=HTMLResponse, summary="Owner 后台首页")
    def Owner后台首页() -> HTMLResponse:
        return HTMLResponse(V7_ADMIN_HTML)

    @router.get("/admin", response_class=HTMLResponse, summary="运营管理后台")
    def 运营管理后台() -> HTMLResponse:
        return HTMLResponse(V7_ADMIN_HTML)
        return HTMLResponse(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
              <meta charset="utf-8">
              <meta name="viewport" content="width=device-width, initial-scale=1">
              <link rel="icon" href="data:,">
              <title>表情包运营后台</title>
              <style>
                * { box-sizing: border-box; }
                body { margin: 0; font-family: "Microsoft YaHei", Arial, sans-serif; color: #1f2933; background: #eef2f6; }
                .layout { display: grid; grid-template-columns: 224px 1fr; min-height: 100vh; }
                .sidebar { background: #182331; color: #d7dde6; padding: 18px 14px; }
                .brand { color: #ffffff; font-size: 18px; font-weight: 700; margin: 6px 8px 20px; }
                .nav { display: grid; gap: 6px; }
                .nav a { color: #d7dde6; text-decoration: none; padding: 10px 12px; border-radius: 6px; font-size: 14px; }
                .nav a.active, .nav a:hover { background: #263647; color: #ffffff; }
                .workspace { min-width: 0; padding: 18px 22px 28px; }
                .topbar { display: flex; justify-content: space-between; gap: 16px; align-items: center; margin-bottom: 14px; }
                h1 { margin: 0; font-size: 24px; }
                h2 { font-size: 15px; margin: 0 0 10px; }
                .subtext, .muted { color: #657385; font-size: 13px; }
                .identity { display: flex; gap: 8px; align-items: center; background: #ffffff; border: 1px solid #d7dee8; padding: 10px; border-radius: 8px; }
                input, select { height: 34px; border: 1px solid #b8c4d2; border-radius: 6px; padding: 0 10px; background: #fff; color: #1f2933; }
                button { height: 34px; border: 1px solid #246b8f; border-radius: 6px; background: #246b8f; color: white; padding: 0 12px; cursor: pointer; font-weight: 600; }
                button.secondary { background: #ffffff; color: #246b8f; }
                button:disabled { cursor: wait; opacity: .65; }
                .actionbar { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0 16px; }
                .summary { display: grid; grid-template-columns: repeat(5, minmax(130px, 1fr)); gap: 10px; margin-bottom: 16px; }
                .metric, .panel { background: #ffffff; border: 1px solid #d7dee8; border-radius: 8px; }
                .metric { padding: 14px; min-height: 84px; }
                .metric strong { display: block; font-size: 24px; margin-top: 8px; }
                .board { display: grid; grid-template-columns: 1.35fr .95fr; gap: 14px; align-items: start; }
                .panel { padding: 14px; margin-bottom: 14px; }
                .panel-head { display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 10px; }
                table { width: 100%; border-collapse: collapse; background: #ffffff; table-layout: fixed; }
                th, td { border-bottom: 1px solid #e6ebf2; padding: 9px 8px; text-align: left; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
                th { color: #435269; background: #f4f7fa; font-weight: 700; }
                .empty { padding: 12px; color: #6b7280; background: #f8fafc; border: 1px dashed #cbd5df; border-radius: 6px; }
                .status-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
                .status-item { background: #f8fafc; border: 1px solid #e0e7ef; border-radius: 6px; padding: 10px; font-size: 13px; }
                .asset-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
                .asset-tile { border: 1px solid #d7dee8; border-radius: 8px; padding: 8px; background: #fbfcfe; min-width: 0; }
                .asset-tile img { width: 100%; aspect-ratio: 1 / 1; object-fit: contain; background: linear-gradient(45deg, #f0f3f7 25%, transparent 25%), linear-gradient(-45deg, #f0f3f7 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #f0f3f7 75%), linear-gradient(-45deg, transparent 75%, #f0f3f7 75%); background-size: 16px 16px; background-position: 0 0, 0 8px, 8px -8px, -8px 0; border-radius: 6px; }
                .asset-tile div { margin-top: 6px; font-size: 12px; color: #4b5b70; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
                pre { background: #121826; color: #e5e7eb; border-radius: 8px; padding: 12px; overflow: auto; max-height: 180px; font-size: 12px; }
                @media (max-width: 980px) {
                  .layout { grid-template-columns: 1fr; }
                  .sidebar { position: static; }
                  .board, .summary { grid-template-columns: 1fr; }
                  .topbar, .identity { align-items: stretch; flex-direction: column; }
                  .asset-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
                }
              </style>
            </head>
            <body>
              <div class="layout">
                <aside class="sidebar">
                  <div class="brand">表情包运营后台</div>
                  <nav class="nav" aria-label="后台导航">
                    <a class="active" href="#overview">总览</a>
                    <a href="#generation">生成工作台</a>
                    <a href="#review">审核工作台</a>
                    <a href="#loop">系统设置</a>
                    <a href="#log">操作回执</a>
                  </nav>
                </aside>
                <main class="workspace">
                  <div class="topbar">
                    <div>
                      <h1>总览</h1>
                      <div class="subtext">生产、审核、发布、回流与门禁状态集中处理</div>
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
                  <div class="actionbar" aria-label="主要操作">
                    <button id="demoButton" type="button" onclick="demoGenerate()">一键生成演示套装</button>
                    <button type="button" onclick="runSchedules()">执行定时任务</button>
                    <button type="button" class="secondary" onclick="loadOverview()">刷新总览</button>
                  </div>
                  <section id="overview" class="summary" aria-label="运营总览"></section>
                  <div class="board">
                    <div>
                      <section id="generation" class="panel">
                        <div class="panel-head">
                          <h2>生成工作台</h2>
                          <span class="muted">策略、套装、图片资产</span>
                        </div>
                        <div id="strategyTable" class="empty">等待加载生成策略</div>
                      </section>
                      <section class="panel">
                        <div class="panel-head">
                          <h2>调度执行记录</h2>
                          <span class="muted">后台任务触发与执行结果</span>
                        </div>
                        <div id="scheduleTable" class="empty">等待加载定时任务</div>
                      </section>
                      <section id="review" class="panel">
                        <div class="panel-head">
                          <h2>审核工作台</h2>
                          <span class="muted">复核、发布任务、外网隔离边界</span>
                        </div>
                        <div id="publishTable" class="empty">等待加载发布任务</div>
                      </section>
                    </div>
                    <div>
                      <section class="panel">
                        <div class="panel-head">
                          <h2>资产预览</h2>
                          <span class="muted" id="assetStatus">尚未生成</span>
                        </div>
                          <div id="assetPreview" class="empty">点击“一键生成演示套装”后在这里预览透明图片</div>
                      </section>
                      <section id="loop" class="panel">
                        <div class="panel-head">
                          <h2>系统诊断</h2>
                          <span class="muted">失败项再执行队列</span>
                        </div>
                        <div id="gateTable" class="empty">等待加载门禁与再执行队列</div>
                      </section>
                      <section class="panel">
                        <div class="panel-head">
                          <h2>业务状态</h2>
                          <span class="muted">当前后台可用性</span>
                        </div>
                        <div class="status-list">
                          <div class="status-item">主动生成：<strong id="generateState">待触发</strong></div>
                          <div class="status-item">外网发布：<strong>本地回执</strong></div>
                          <div class="status-item">密钥读取：<strong>生成阶段禁止</strong></div>
                          <div class="status-item">操作日志：<strong id="logState">等待操作</strong></div>
                        </div>
                      </section>
                    </div>
                  </div>
                  <section id="log" class="panel">
                    <div class="panel-head">
                      <h2>操作回执</h2>
                      <span class="muted">仅展示本次操作回执，不展示密钥</span>
                    </div>
                    <pre id="output">等待操作</pre>
                  </section>
                </main>
              </div>
              <script>
                function headerSafeOperatorId() {
                  const value = document.getElementById("operatorId").value.trim();
                  return /^[\\x20-\\x7E]+$/.test(value) ? value : encodeURIComponent(value);
                }
                function headers() {
                  return {"X-Operator-ID": headerSafeOperatorId(), "X-Operator-Role": document.getElementById("operatorRole").value};
                }
                async function callApi(path, options) {
                  const response = await fetch(path, Object.assign({headers: headers()}, options || {}));
                  const text = await response.text();
                  const payload = JSON.parse(text);
                  document.getElementById("output").textContent = `接口回执：${payload.消息}；业务结果：${payload.成功 ? "成功" : "失败"}`;
                  document.getElementById("logState").textContent = response.ok ? "已记录" : "需处理";
                  return payload;
                }
                function renderCards(stats) {
                  document.getElementById("overview").innerHTML = Object.entries(stats).map(([key, value]) => `<div class="metric"><span>${key}</span><strong>${value}</strong></div>`).join("");
                }
                function displayValue(value) {
                  if (value === "Telegram") { return "通用透明图"; }
                  return String(value ?? "").replaceAll("透明PNG", "透明图片").replaceAll("PNG", "透明图片").replaceAll("透明透明图片", "透明图片");
                }
                function renderTable(target, rows, columns) {
                  const node = document.getElementById(target);
                  if (!rows || rows.length === 0) { node.className = "empty"; node.textContent = "暂无记录"; return; }
                  node.className = "";
                  const head = columns.map(column => `<th>${column[0]}</th>`).join("");
                  const body = rows.map(row => `<tr>${columns.map(column => `<td>${displayValue(row[column[1]])}</td>`).join("")}</tr>`).join("");
                  node.innerHTML = `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
                }
                async function loadOverview() {
                  const payload = await callApi("/v1/运营后台/总览");
                  const data = payload.数据;
                  renderCards(data.统计);
                  renderTable("scheduleTable", data.定时任务, [["任务名称", "任务名称"], ["执行周期", "执行周期"], ["状态", "状态"]]);
                  renderTable("strategyTable", data.生成策略, [["生成类型", "生成类型"], ["目标平台", "目标平台"], ["表情数量", "表情数量"]]);
                  renderTable("publishTable", data.发布任务, [["发布平台", "发布平台"], ["发布方式", "发布方式"], ["状态", "状态"]]);
                  renderTable("gateTable", data.再执行队列, [["验收项", "验收项"], ["状态", "状态"], ["失败原因", "失败原因"]]);
                }
                async function fetchAssetObjectUrl(path) {
                  const response = await fetch(path, {headers: headers()});
                  if (!response.ok) { throw new Error(`资产预览下载失败：${response.status}`); }
                  return URL.createObjectURL(await response.blob());
                }
                async function renderAssets(data) {
                  const assets = data.可预览图片 || [];
                  const preview = document.getElementById("assetPreview");
                  document.getElementById("assetStatus").textContent = `${assets.length} 张已生成`;
                  document.getElementById("generateState").textContent = "生成完成";
                  if (assets.length === 0) { preview.className = "empty"; preview.textContent = "本次没有生成可预览图片"; return; }
                  preview.className = "asset-grid";
                  const tiles = await Promise.all(assets.map(async item => {
                    const url = await fetchAssetObjectUrl(item.下载地址);
                    return `<div class="asset-tile"><img src="${url}" alt="${item.文案}"><div title="${item.文案}">${item.序号}. ${item.文案}</div></div>`;
                  }));
                  preview.innerHTML = tiles.join("");
                }
                async function demoGenerate() {
                  const button = document.getElementById("demoButton");
                  button.disabled = true;
                  button.textContent = "正在生成";
                  document.getElementById("generateState").textContent = "生成中";
                  try {
                    const payload = await callApi("/v1/运营后台/演示生成", {method: "POST", headers: Object.assign(headers(), {"Content-Type": "application/json"}), body: "{}"});
                    await renderAssets(payload.数据);
                    await loadOverview();
                    document.getElementById("output").textContent = `接口回执：${payload.消息}；已生成 ${payload.数据.生成数量} 张透明图片`;
                  } finally {
                    button.disabled = false;
                    button.textContent = "一键生成演示套装";
                  }
                }
                async function runSchedules() {
                  await callApi("/v1/定时任务/执行", {method: "POST", headers: Object.assign(headers(), {"Content-Type": "application/json"}), body: "{}"});
                  await loadOverview();
                }
                loadOverview();
              </script>
            </body>
            </html>
            """
        )

    @router.get("/v1/运营后台/总览", response_model=标准响应, summary="查询运营后台总览")
    def 查询运营后台总览(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        定时任务列表 = 定时任务.列表()
        执行记录 = 定时任务.执行记录列表()
        生成策略列表 = 生成策略.策略列表()
        发布任务列表 = 发布.列表()
        再执行队列 = LOOP验收.再执行队列列表()
        return 标准响应(
            成功=True,
            消息="运营后台总览已返回",
            数据={
                "统计": {
                    "定时任务": len(定时任务列表),
                    "调度执行记录": len(执行记录),
                    "生成策略": len(生成策略列表),
                    "发布任务": len(发布任务列表),
                    "待再执行": len([item for item in 再执行队列 if item["状态"] != "已完成"]),
                },
                "定时任务": 定时任务列表[:10],
                "执行记录": 执行记录[:10],
                "生成策略": 生成策略列表[-10:],
                "发布任务": 发布任务列表[-10:],
                "再执行队列": 再执行队列[:10],
                "发布边界": "默认本地开放发布回执，不访问外网",
            },
        )

    @router.post("/v1/运营后台/演示生成", response_model=标准响应, summary="运营后台一键生成演示套装")
    def 运营后台演示生成(
        请求: dict[str, object] | None = Body(default=None),
        当前操作人: 操作人 = Depends(获取操作人),
    ) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        请求 = 请求 or {}
        风格标签 = [str(item) for item in 请求.get("风格标签", []) if str(item).strip()]
        if not 风格标签:
            风格标签 = ["Q萌", "圆润贴纸", "职场聊天"]
        目标平台 = str(请求.get("目标平台") or "Telegram")
        生成类型 = " + ".join(风格标签[:3]) + " 表情套装"
        平台规则 = 规则治理.获取当前规则(目标平台)
        表情数量 = max(6, int(平台规则.最少数量))
        基础情绪 = ["开心", "无语", "加油", "震惊", "感谢", "困惑"]
        基础场景 = ["沟通", "开会", "催办", "确认", "复盘", "交付"]
        情绪标签 = [基础情绪[index % len(基础情绪)] for index in range(表情数量)]
        场景标签 = [基础场景[index % len(基础场景)] for index in range(表情数量)]
        画像名称 = "后台演示受众"
        已有画像 = [item for item in 受众画像.列表() if item["画像名称"] == 画像名称]
        if not 已有画像:
            受众画像.创建(
                当前操作人.编号,
                创建受众画像请求(
                    画像名称=画像名称,
                    年龄段="20-35",
                    兴趣标签=["办公沟通", "项目协作", "轻松表达"],
                    使用场景=["沟通", "开会", "催办", "确认", "复盘", "交付"],
                    风格偏好=["Q萌", "圆润", "职场聊天"],
                    禁用内容=["低俗", "真人肖像", "侵权IP"],
                    风险等级="低",
                ),
            )
        策略结果 = 生成策略.创建(
            当前操作人.编号,
            创建生成策略请求(
                目标平台=目标平台,
                目标受众=画像名称,
                生成类型=生成类型,
                表情数量=表情数量,
                风格标签=风格标签,
                情绪标签=情绪标签,
                场景标签=场景标签,
                风险阈值="低",
            ),
        )
        套装 = 策略结果["套装"]
        资产结果 = 生成策略.生成资产(当前操作人.编号, str(套装["套装编号"]))
        最新套装 = 生成策略.获取套装(str(套装["套装编号"]))
        可预览图片 = [
            {
                "表情编号": item["表情编号"],
                "序号": item["序号"],
                "文案": item["文案"],
                "审美分": item["质量报告"].get("评分", {}).get("审美总分", 0),
                "动势分": item["质量报告"].get("评分", {}).get("静态动势", 0),
                "小图可读性": item["质量报告"].get("评分", {}).get("小图可读性", 0),
                "失败原因": item["失败原因"],
                "下载地址": f"/v1/表情资产/{item['表情编号']}/下载",
            }
            for item in 最新套装["表情列表"]
        ]
        审计.记录(
            当前操作人.编号,
            "运营后台演示生成",
            "套装",
            str(套装["套装编号"]),
            {"生成数量": 资产结果["生成数量"], "风格标签": 风格标签, "外网访问": "否", "真实发布": "否"},
        )
        return 标准响应(
            成功=True,
            消息="运营后台演示套装已生成",
            数据={
                "策略编号": 策略结果["策略编号"],
                "套装编号": 套装["套装编号"],
                "生成数量": 资产结果["生成数量"],
                "封面图": 资产结果["封面图"],
                "缩略图": 资产结果["缩略图"],
                "质量报告": 资产结果["质量报告"],
                "可预览图片": 可预览图片,
            },
        )

    @router.post("/v1/任务", response_model=标准响应, summary="创建后台任务")
    def 创建后台任务(请求: 创建任务请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        任务 = 任务服务.创建任务(当前操作人.编号, 请求.任务名称, 请求.任务类型, 请求.幂等键)
        return 标准响应(成功=True, 消息="任务已创建", 数据=任务)

    @router.post("/v1/任务/{task_id}/status", response_model=标准响应, summary="流转任务状态")
    def 流转后台任务(
        task_id: str,
        请求: 任务流转请求,
        当前操作人: 操作人 = Depends(获取操作人),
    ) -> 标准响应:
        任务 = 任务服务.流转任务(当前操作人.编号, task_id, 请求.目标状态)
        return 标准响应(成功=True, 消息="任务状态已更新", 数据=任务)

    @router.post("/v1/定时任务", response_model=标准响应, summary="创建定时任务")
    def 创建定时任务接口(
        请求: 创建定时任务请求,
        当前操作人: 操作人 = Depends(获取操作人),
    ) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        定时任务结果 = 定时任务.创建(当前操作人.编号, 请求.model_dump())
        return 标准响应(成功=True, 消息="定时任务已创建", 数据=定时任务结果)

    @router.get("/v1/定时任务", response_model=标准响应, summary="查询定时任务")
    def 查询定时任务接口(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="定时任务已返回", 数据=定时任务.列表())

    @router.post("/v1/定时任务/执行", response_model=标准响应, summary="执行定时任务")
    def 执行定时任务接口(请求: 执行定时任务请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        return 标准响应(成功=True, 消息="定时任务执行完成", 数据=定时任务.执行待运行(当前操作人.编号, 请求.定时任务编号))

    @router.get("/v1/定时任务/执行记录", response_model=标准响应, summary="查询定时任务执行记录")
    def 查询定时任务执行记录接口(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="定时任务执行记录已返回", 数据=定时任务.执行记录列表())

    @router.get("/v1/审计日志", response_model=标准响应, summary="查询审计日志")
    def 查询审计日志(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员"})
        return 标准响应(成功=True, 消息="审计日志已返回", 数据=审计.列表())

    @router.get("/v1/平台规则", response_model=标准响应, summary="查询平台规则库")
    def 查询平台规则库(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="平台规则已返回", 数据=规则治理.列出当前规则())

    @router.get("/v1/平台规则/{platform_name}", response_model=标准响应, summary="查询单个平台规则")
    def 查询单个平台规则(platform_name: str, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="平台规则已返回", 数据=规则治理.获取当前规则(platform_name).转字典())

    @router.get("/v1/平台规则/{platform_name}/版本", response_model=标准响应, summary="查询平台规则版本")
    def 查询平台规则版本(platform_name: str, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="平台规则版本已返回", 数据=规则治理.列出版本(platform_name))

    @router.get("/v1/平台规则变更日志", response_model=标准响应, summary="查询平台规则变更日志")
    def 查询平台规则变更日志(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="平台规则变更日志已返回", 数据=规则治理.变更日志())

    @router.post("/v1/平台规则/版本", response_model=标准响应, summary="创建平台规则版本")
    def 创建平台规则版本(请求: 创建平台规则版本请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员"})
        return 标准响应(成功=True, 消息="平台规则版本已创建", 数据=规则治理.创建版本(当前操作人.编号, 请求))

    @router.post("/v1/平台规则/启用", response_model=标准响应, summary="启用平台规则版本")
    def 启用平台规则版本(请求: 启用平台规则版本请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员"})
        return 标准响应(成功=True, 消息="平台规则版本已启用", 数据=规则治理.启用版本(当前操作人.编号, 请求.平台名称, 请求.规则版本, 请求.启用原因))

    @router.post("/v1/平台规则/回滚", response_model=标准响应, summary="回滚平台规则版本")
    def 回滚平台规则版本(请求: 回滚平台规则版本请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员"})
        return 标准响应(成功=True, 消息="平台规则版本已回滚", 数据=规则治理.回滚版本(当前操作人.编号, 请求.平台名称, 请求.目标版本, 请求.回滚原因))

    @router.post("/v1/平台规则/校验", response_model=标准响应, summary="执行平台规则校验")
    def 执行平台规则校验(
        请求: 平台规则校验请求,
        当前操作人: 操作人 = Depends(获取操作人),
    ) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        结果 = 校验器.校验(当前操作人.编号, 请求.平台名称, 请求.套装编号, 请求.表情文件)
        return 标准响应(成功=bool(结果["是否通过"]), 消息="平台规则校验完成", 数据=结果)

    @router.get("/v1/校验报告", response_model=标准响应, summary="查询规格校验报告")
    def 查询校验报告(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="校验报告已返回", 数据=校验器.报告列表())

    @router.post("/v1/资产校验", response_model=标准响应, summary="执行资产文件级校验")
    def 执行资产校验(请求: 资产文件校验请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        结果 = 资产校验.校验(当前操作人.编号, 请求.平台名称, 请求.套装编号, 请求.文件路径)
        return 标准响应(成功=bool(结果["是否通过"]), 消息="资产文件校验完成", 数据=结果)

    @router.get("/v1/资产校验报告", response_model=标准响应, summary="查询资产文件级校验报告")
    def 查询资产校验报告(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="资产校验报告已返回", 数据=资产校验.报告列表())

    @router.post("/v1/表情套装验收", response_model=标准响应, summary="执行表情套装综合验收")
    def 执行表情套装验收(请求: 表情套装验收请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        结果 = 套装验收.验收(当前操作人.编号, 请求.套装编号)
        return 标准响应(成功=bool(结果["是否通过"]), 消息="表情套装综合验收完成", 数据=结果)

    @router.get("/v1/表情套装验收报告", response_model=标准响应, summary="查询表情套装综合验收报告")
    def 查询表情套装验收报告(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="表情套装验收报告已返回", 数据=套装验收.报告列表())

    @router.get("/v1/标签库", response_model=标准响应, summary="查询情绪场景风格标签")
    def 查询标签库(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="标签库已返回", 数据=标签库())

    @router.post("/v1/设计元素/动作", response_model=标准响应, summary="生成动作设计元素")
    def 生成动作设计元素(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        elements = ["点头确认", "摇头拒绝", "跳跃庆祝", "摊手无奈", "打工崩溃", "催办提醒"]
        审计.记录(当前操作人.编号, "生成动作元素", "设计元素", "动作元素", {"元素数量": len(elements)})
        return 标准响应(
            成功=True,
            消息="动作元素已生成",
            数据={
                "元素类型": "动作",
                "推荐元素": elements,
                "应用建议": "用于套装动作差异化，优先覆盖确认、拒绝、庆祝、无奈等高频聊天场景。",
                "下一步": "进入套装编辑器后选择单张表情应用动作元素。",
            },
        )

    @router.post("/v1/设计元素/视觉", response_model=标准响应, summary="生成视觉设计元素")
    def 生成视觉设计元素(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        elements = ["主色板", "描边规则", "纸质纹理", "速度线", "字体风格", "阴影层级"]
        审计.记录(当前操作人.编号, "生成视觉元素", "设计元素", "视觉元素", {"元素数量": len(elements)})
        return 标准响应(
            成功=True,
            消息="视觉元素已生成",
            数据={
                "元素类型": "视觉",
                "推荐元素": elements,
                "应用建议": "用于统一套装视觉语言，优先约束色板、描边、字体和贴纸质感。",
                "下一步": "进入套装编辑器后将视觉元素应用到当前套装。",
            },
        )

    @router.post("/v1/受众画像", response_model=标准响应, summary="创建受众画像")
    def 创建受众画像接口(请求: 创建受众画像请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        return 标准响应(成功=True, 消息="受众画像已创建", 数据=受众画像.创建(当前操作人.编号, 请求))

    @router.get("/v1/受众画像", response_model=标准响应, summary="查询受众画像")
    def 查询受众画像接口(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="受众画像已返回", 数据=受众画像.列表())

    @router.post("/v1/热点", response_model=标准响应, summary="创建热点记录")
    def 创建热点接口(请求: 创建热点请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        return 标准响应(成功=True, 消息="热点已创建", 数据=热点.创建(当前操作人.编号, 请求))

    @router.get("/v1/热点", response_model=标准响应, summary="查询热点记录")
    def 查询热点接口(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="热点已返回", 数据=热点.列表())

    @router.post("/v1/原创角色", response_model=标准响应, summary="创建原创 IP 角色")
    def 创建原创角色接口(请求: 创建原创角色请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        return 标准响应(成功=True, 消息="原创角色已创建", 数据=原创角色.创建(当前操作人.编号, 请求))

    @router.get("/v1/原创角色", response_model=标准响应, summary="查询原创 IP 角色")
    def 查询原创角色接口(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="原创角色已返回", 数据=原创角色.列表())

    @router.post("/v1/生成策略", response_model=标准响应, summary="创建生成策略和套装元数据")
    def 创建生成策略接口(请求: 创建生成策略请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        return 标准响应(成功=True, 消息="生成策略已创建", 数据=生成策略.创建(当前操作人.编号, 请求))

    @router.get("/v1/生成策略", response_model=标准响应, summary="查询生成策略")
    def 查询生成策略接口(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="生成策略已返回", 数据=生成策略.策略列表())

    @router.get("/v1/预览包", response_model=标准响应, summary="查询生成策略预览包")
    def 查询预览包接口(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="预览包已返回", 数据=生成策略.预览包列表())

    @router.get("/v1/预览包文件/{preview_id}", response_model=标准响应, summary="读取生成策略预览包 JSON 文件")
    def 读取预览包文件接口(preview_id: str, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="预览包文件已返回", 数据=生成策略.读取预览包文件(preview_id))

    @router.get("/v1/预览包文件/{preview_id}/下载", summary="下载生成策略预览包 JSON 文件")
    def 下载预览包文件接口(preview_id: str, 当前操作人: 操作人 = Depends(获取操作人)) -> FileResponse:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        package = 生成策略.读取预览包文件(preview_id)
        return FileResponse(package["文件路径"], media_type="application/json", filename=f"{preview_id}.json")

    @router.get("/v1/表情套装/{set_id}", response_model=标准响应, summary="查询表情套装元数据")
    def 查询表情套装接口(set_id: str, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="表情套装已返回", 数据=生成策略.获取套装(set_id))

    @router.post("/v1/表情套装/{set_id}/生成资产", response_model=标准响应, summary="生成表情套装图片资产")
    def 生成表情套装资产接口(set_id: str, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        return 标准响应(成功=True, 消息="表情套装图片资产已生成", 数据=生成策略.生成资产(当前操作人.编号, set_id))

    @router.post("/v1/表情套装/{set_id}/重生成低分项", response_model=标准响应, summary="重生成低质量表情项")
    def 重生成低分项接口(set_id: str, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="低分项已重生成", 数据=生成策略.重生成低分项(当前操作人.编号, set_id))

    @router.get("/v1/表情资产/{item_id}/下载", summary="下载生成后的表情图片")
    def 下载表情资产接口(item_id: str, 当前操作人: 操作人 = Depends(获取操作人)) -> FileResponse:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        asset = 生成策略.读取表情资产(item_id)
        return FileResponse(asset["文件路径"], media_type="image/png", filename=f"{item_id}.png")

    @router.get("/v1/下载中心/套装", response_model=标准响应, summary="查询下载中心套装")
    def 查询下载中心套装接口(
        平台: str | None = Query(default=None, alias="platform"),
        受众: str | None = Query(default=None, alias="audience"),
        状态: str | None = Query(default=None, alias="status"),
        风格标签: list[str] | None = Query(default=None, alias="style"),
        当前操作人: 操作人 = Depends(获取操作人),
    ) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(
            成功=True,
            消息="下载中心套装已返回",
            数据=平台包.套装列表(目标平台=平台, 目标受众=受众, 状态=状态, 风格标签=风格标签),
        )

    @router.post("/v1/下载中心/套装/{set_id}/下载前检查", response_model=标准响应, summary="执行套装下载前检查")
    def 套装下载前检查接口(
        set_id: str,
        请求: 平台包下载前检查请求,
        当前操作人: 操作人 = Depends(获取操作人),
    ) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        结果 = 平台包.下载前检查(当前操作人.编号, set_id, 请求.平台名称)
        return 标准响应(成功=bool(结果["是否通过"]), 消息="下载前检查完成", 数据=结果)

    @router.post("/v1/下载中心/套装/{set_id}/生成平台包", response_model=标准响应, summary="生成套装平台发布包")
    def 下载中心生成平台包接口(
        set_id: str,
        请求: 平台包下载前检查请求,
        当前操作人: 操作人 = Depends(获取操作人),
    ) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        return 标准响应(成功=True, 消息="平台包已生成", 数据=平台包.生成平台包(当前操作人.编号, set_id, 请求.平台名称))

    @router.get("/v1/下载中心/套装/{set_id}/平台包/{platform_name}/下载", summary="下载套装平台发布包")
    def 下载中心下载平台包接口(set_id: str, platform_name: str, 当前操作人: 操作人 = Depends(获取操作人)) -> FileResponse:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        package = 平台包.读取最新平台包文件(当前操作人.编号, set_id, platform_name)
        return FileResponse(package["文件路径"], media_type="application/zip", filename=f"{package['包编号']}-{platform_name}.zip")

    @router.get("/v1/下载中心/表情/{item_id}/下载", summary="下载单张表情")
    def 下载中心单张表情下载接口(item_id: str, 当前操作人: 操作人 = Depends(获取操作人)) -> FileResponse:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        asset = 生成策略.读取表情资产(item_id)
        return FileResponse(asset["文件路径"], media_type="image/png", filename=f"{item_id}.png")

    @router.post("/v1/平台包/生成", response_model=标准响应, summary="生成平台可识别表情包")
    def 生成平台包接口(请求: 平台包生成请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        return 标准响应(成功=True, 消息="平台包已生成", 数据=平台包.生成平台包(当前操作人.编号, 请求.套装编号, 请求.平台名称))

    @router.post("/v1/平台包/下载前检查", response_model=标准响应, summary="执行平台包下载前检查")
    def 平台包下载前检查接口(请求: 平台包生成请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        结果 = 平台包.下载前检查(当前操作人.编号, 请求.套装编号, 请求.平台名称)
        return 标准响应(成功=bool(结果["是否通过"]), 消息="平台包下载前检查完成", 数据=结果)

    @router.get("/v1/平台包/{package_id}", response_model=标准响应, summary="读取平台包索引")
    def 读取平台包接口(package_id: str, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="平台包已返回", 数据=平台包.读取平台包(package_id))

    @router.get("/v1/平台包/{package_id}/下载", summary="下载平台包 ZIP")
    def 下载平台包接口(package_id: str, 当前操作人: 操作人 = Depends(获取操作人)) -> FileResponse:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        package = 平台包.读取平台包文件(package_id)
        return FileResponse(package["文件路径"], media_type="application/zip", filename=f"{package_id}.zip")

    @router.post("/v1/审核/自动初审", response_model=标准响应, summary="自动初审表情包")
    def 自动初审接口(请求: 自动初审请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="自动初审已完成", 数据=审核.自动初审(请求))

    @router.post("/v1/审核", response_model=标准响应, summary="审核表情包")
    def 审核表情包接口(请求: 表情包审核请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "审核员"})
        return 标准响应(成功=True, 消息="审核记录已创建", 数据=审核.审核(当前操作人.编号, 请求))

    @router.post("/v1/审核/二审", response_model=标准响应, summary="二审表情包")
    def 二审表情包接口(请求: 二审请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "审核员"})
        return 标准响应(成功=True, 消息="二审记录已创建", 数据=审核.二审(当前操作人.编号, 请求))

    @router.post("/v1/审核/退回重生成", response_model=标准响应, summary="退回并创建重生成策略")
    def 退回重生成接口(请求: 退回重生成请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "审核员"})
        新策略结果 = 生成策略.创建(当前操作人.编号, 请求.新策略)
        return 标准响应(成功=True, 消息="已退回重生成", 数据=审核.记录退回重生成(当前操作人.编号, 请求.套装编号, 请求.退回原因, 新策略结果))

    @router.get("/v1/审核", response_model=标准响应, summary="查询审核记录")
    def 查询审核记录接口(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="审核记录已返回", 数据=审核.列表())

    @router.post("/v1/发布前复核", response_model=标准响应, summary="发布前复核")
    def 发布前复核接口(请求: 发布前复核请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "审核员"})
        return 标准响应(成功=True, 消息="发布前复核已记录", 数据=发布.发布前复核(当前操作人.编号, 请求.套装编号, 请求.复核结论, 请求.复核意见))

    @router.get("/v1/发布前复核", response_model=标准响应, summary="查询发布前复核")
    def 查询发布前复核接口(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="发布前复核已返回", 数据=发布.复核列表())

    @router.post("/v1/发布任务", response_model=标准响应, summary="创建发布任务")
    def 创建发布任务接口(请求: 创建发布任务请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        return 标准响应(成功=True, 消息="发布任务已创建", 数据=发布.创建任务(当前操作人.编号, 请求))

    @router.post("/v1/发布任务/执行", response_model=标准响应, summary="执行发布任务")
    def 执行发布任务接口(请求: 执行发布请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        return 标准响应(成功=True, 消息="发布任务已执行", 数据=发布.执行(当前操作人.编号, 请求.发布任务编号, 请求.确认真实发布))

    @router.get("/v1/发布任务", response_model=标准响应, summary="查询发布任务")
    def 查询发布任务接口(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="发布任务已返回", 数据=发布.列表())

    @router.get("/v1/发布任务/重试记录", response_model=标准响应, summary="查询发布失败重试记录")
    def 查询发布重试记录接口(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="发布重试记录已返回", 数据=发布.重试记录列表())

    @router.get("/v1/提交包", response_model=标准响应, summary="查询发布 dry-run 提交包")
    def 查询提交包接口(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="提交包已返回", 数据=发布.提交包列表())

    @router.get("/v1/提交包文件/{submit_id}", response_model=标准响应, summary="读取发布 dry-run 提交包 JSON 文件")
    def 读取提交包文件接口(submit_id: str, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="提交包文件已返回", 数据=发布.读取提交包文件(submit_id))

    @router.get("/v1/提交包文件/{submit_id}/下载", summary="下载发布 dry-run 提交包 JSON 文件")
    def 下载提交包文件接口(submit_id: str, 当前操作人: 操作人 = Depends(获取操作人)) -> FileResponse:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        package = 发布.读取提交包文件(submit_id)
        return FileResponse(package["文件路径"], media_type="application/json", filename=f"{submit_id}.json")

    @router.post("/v1/数据回流/表现", response_model=标准响应, summary="记录发布后表现数据")
    def 记录表现接口(请求: 记录表现请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        return 标准响应(成功=True, 消息="表现数据已记录", 数据=数据回流.记录表现(当前操作人.编号, 请求))

    @router.post("/v1/数据回流/周报", response_model=标准响应, summary="生成优化周报")
    def 创建周报接口(请求: 创建优化周报请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        return 标准响应(成功=True, 消息="优化周报已生成", 数据=数据回流.创建周报(当前操作人.编号, 请求))

    @router.get("/v1/数据回流/周报", response_model=标准响应, summary="查询优化周报")
    def 查询周报接口(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="优化周报已返回", 数据=数据回流.周报列表())

    @router.get("/v1/数据回流/规则反馈", response_model=标准响应, summary="查询拒审原因规则反馈")
    def 查询规则反馈接口(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="规则反馈已返回", 数据=数据回流.规则反馈列表())

    @router.post("/v1/数据回流/规则反馈/处理", response_model=标准响应, summary="处理拒审原因规则反馈")
    def 处理规则反馈接口(请求: 处理规则反馈请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        return 标准响应(成功=True, 消息="规则反馈已处理", 数据=数据回流.处理规则反馈(当前操作人.编号, 请求))

    @router.post("/v1/数据回流/下一轮策略", response_model=标准响应, summary="创建下一轮策略草案")
    def 创建下一轮策略接口(请求: 创建下一轮策略请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        return 标准响应(成功=True, 消息="下一轮策略草案已创建", 数据=数据回流.创建下一轮策略(当前操作人.编号, 请求))

    @router.post("/v1/数据回流/下一轮策略/转正式", response_model=标准响应, summary="下一轮策略草案转正式生成策略")
    def 下一轮策略转正式接口(请求: 转正式策略请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        准备结果 = 数据回流.准备草案转正式(请求)
        if 准备结果["是否已转正式"]:
            return 标准响应(成功=True, 消息="下一轮策略草案已转正式", 数据=准备结果)
        策略结果 = 生成策略.创建(当前操作人.编号, 准备结果["生成请求"])
        return 标准响应(成功=True, 消息="下一轮策略草案已转正式", 数据=数据回流.完成草案转正式(当前操作人.编号, 请求.草案编号, 策略结果))

    @router.get("/v1/数据回流/下一轮策略", response_model=标准响应, summary="查询下一轮策略草案")
    def 查询下一轮策略接口(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="下一轮策略草案已返回", 数据=数据回流.下一轮策略列表())

    @router.post("/v1/LOOP验收", response_model=标准响应, summary="执行LOOP总体验收")
    def 执行LOOP验收接口(请求: LOOP验收请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员"})
        结果 = LOOP验收.执行(当前操作人.编号, 请求.验收范围)
        return 标准响应(成功=bool(结果["是否通过"]), 消息="LOOP验收已完成", 数据=结果)

    @router.get("/v1/LOOP验收报告", response_model=标准响应, summary="查询LOOP验收报告")
    def 查询LOOP验收报告接口(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="LOOP验收报告已返回", 数据=LOOP验收.报告列表())

    @router.post("/v1/第一阶段总门禁", response_model=标准响应, summary="执行第一阶段总门禁")
    def 执行第一阶段总门禁接口(请求: 第一阶段总门禁请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员"})
        结果 = LOOP验收.第一阶段总门禁(当前操作人.编号, 请求.LOOP报告编号)
        return 标准响应(成功=bool(结果["是否通过"]), 消息="第一阶段总门禁已完成", 数据=结果)

    @router.get("/v1/第一阶段总门禁报告", response_model=标准响应, summary="查询第一阶段总门禁报告")
    def 查询第一阶段总门禁报告接口(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="第一阶段总门禁报告已返回", 数据=LOOP验收.第一阶段总门禁报告列表())

    @router.get("/v1/再执行队列", response_model=标准响应, summary="查询失败项再执行队列")
    def 查询再执行队列接口(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="再执行队列已返回", 数据=LOOP验收.再执行队列列表())

    @router.post("/v1/再执行队列/领取", response_model=标准响应, summary="领取失败项再执行任务")
    def 领取再执行队列接口(请求: 再执行队列领取请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        return 标准响应(成功=True, 消息="再执行队列项已领取", 数据=LOOP验收.领取再执行项(当前操作人.编号, 请求.队列编号))

    @router.post("/v1/再执行队列/记录", response_model=标准响应, summary="记录失败项再执行过程")
    def 记录再执行队列接口(请求: 再执行记录请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        return 标准响应(成功=True, 消息="再执行记录已写入", 数据=LOOP验收.记录再执行(当前操作人.编号, 请求.队列编号, 请求.执行记录))

    @router.post("/v1/再执行队列/完成", response_model=标准响应, summary="完成失败项再执行任务")
    def 完成再执行队列接口(请求: 再执行完成请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营"})
        return 标准响应(成功=True, 消息="再执行队列项已完成", 数据=LOOP验收.完成再执行项(当前操作人.编号, 请求.队列编号, 请求.完成说明))

    @router.post("/v1/第一阶段交付包索引", response_model=标准响应, summary="创建第一阶段交付包索引")
    def 创建第一阶段交付包索引接口(请求: 交付包索引请求, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员"})
        return 标准响应(成功=True, 消息="第一阶段交付包索引已创建", 数据=LOOP验收.创建交付包索引(当前操作人.编号, 请求.门禁编号))

    @router.get("/v1/第一阶段交付包索引", response_model=标准响应, summary="查询第一阶段交付包索引")
    def 查询第一阶段交付包索引接口(当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="第一阶段交付包索引已返回", 数据=LOOP验收.交付包索引列表())

    @router.get("/v1/第一阶段交付包文件/{package_id}", response_model=标准响应, summary="读取第一阶段交付包 JSON 文件")
    def 读取第一阶段交付包文件接口(package_id: str, 当前操作人: 操作人 = Depends(获取操作人)) -> 标准响应:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        return 标准响应(成功=True, 消息="第一阶段交付包文件已返回", 数据=LOOP验收.读取交付包文件(package_id))

    @router.get("/v1/第一阶段交付包文件/{package_id}/下载", summary="下载第一阶段交付包 JSON 文件")
    def 下载第一阶段交付包文件接口(package_id: str, 当前操作人: 操作人 = Depends(获取操作人)) -> FileResponse:
        要求角色(当前操作人, {"管理员", "运营", "审核员"})
        package = LOOP验收.读取交付包文件(package_id)
        return FileResponse(package["文件路径"], media_type="application/json", filename=f"{package_id}.json")

    return router
