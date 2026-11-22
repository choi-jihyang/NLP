from functools import lru_cache

from app.core.config import get_settings
from app.leak_guard.base import LeakCheckResult, LeakGuard

__all__ = ["LeakCheckResult", "LeakGuard", "get_leak_guard"]


@lru_cache
def get_leak_guard() -> LeakGuard:
    """LEAK_GUARD_MODULE의 검사 함수를 쓰는 누출 검사기. 끄는 설정은 두지 않는다(항상 검사)."""
    from app.leak_guard.module import ModuleLeakGuard

    return ModuleLeakGuard(get_settings().leak_guard_module)
