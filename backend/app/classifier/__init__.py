from functools import lru_cache

from app.classifier.base import ClassificationResult, Classifier
from app.core.config import get_settings

__all__ = ["Classifier", "ClassificationResult", "get_classifier"]


@lru_cache
def get_classifier() -> Classifier:
    """CLASSIFIER 환경변수에 맞는 분류기를 돌려준다."""
    s = get_settings()
    if s.classifier == "module":
        from app.classifier.module import ModuleClassifier

        return ModuleClassifier(s.classifier_module)
    if s.classifier == "http":
        from app.classifier.http import HttpClassifier

        return HttpClassifier(s.classifier_url)
    from app.classifier.keyword_stub import KeywordStubClassifier

    return KeywordStubClassifier()
