from exceptions.base import AppException


class BadRequestException(AppException):
    def __init__(self, reason: str = "잘못된 요청입니다."):
        super().__init__(status_code=400, reason=reason)


class NotFoundException(AppException):
    def __init__(self, reason: str = "리소스를 찾을 수 없습니다."):
        super().__init__(status_code=404, reason=reason)


class StorageException(AppException):
    def __init__(self, reason: str = "스토리지 처리 중 오류가 발생했습니다."):
        super().__init__(status_code=500, reason=reason)