import traceback
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from exceptions.base import AppException


def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "reason": exc.reason,
        },
    )


def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "reason": exc.detail,
        },
    )


def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "reason": "입력값이 올바르지 않습니다.",
        },
    )


def unexpected_exception_handler(request: Request, exc: Exception):
    # 터미널에 실제 에러 출력 (개발 중 디버깅용)
    print(f"\n[500 ERROR] {request.method} {request.url}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "reason": "서버 내부 오류가 발생했습니다.",
        },
    )