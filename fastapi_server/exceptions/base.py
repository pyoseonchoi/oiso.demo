"""
모든 커스텀 예외의 부모
"""


class AppException(Exception):
    def __init__(self, status_code: int, reason: str):
        self.status_code = status_code
        self.reason = reason
        super().__init__(reason)