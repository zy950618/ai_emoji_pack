from dataclasses import dataclass

from fastapi import Header

from app.exceptions import 业务异常


@dataclass(frozen=True)
class 操作人:
    编号: str
    角色: str


角色映射 = {
    "admin": "管理员",
    "operator": "运营",
    "reviewer": "审核员",
}


def 获取操作人(
    x_operator_id: str | None = Header(default=None, alias="X-Operator-ID"),
    x_operator_role: str | None = Header(default=None, alias="X-Operator-Role"),
) -> 操作人:
    if not x_operator_id or not x_operator_role:
        raise 业务异常("缺少操作人身份或角色", "无权限", 403)
    角色 = 角色映射.get(x_operator_role, x_operator_role)
    return 操作人(编号=x_operator_id, 角色=角色)


def 要求角色(操作人实例: 操作人, 允许角色: set[str]) -> None:
    if 操作人实例.角色 not in 允许角色:
        raise 业务异常("当前角色无权执行该操作", "无权限", 403)
