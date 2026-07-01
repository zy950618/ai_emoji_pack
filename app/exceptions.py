class 业务异常(Exception):
    def __init__(self, 消息: str, 错误码: str = "业务错误", 状态码: int = 400) -> None:
        self.消息 = 消息
        self.错误码 = 错误码
        self.状态码 = 状态码
        super().__init__(消息)
