"""모든 모델을 여기서 import해야 init_db()의 create_all이 테이블을 만든다."""

from app.models.class_member import ClassMember
from app.models.class_payment import ClassPayment
from app.models.class_room import ClassRoom
from app.models.enrollment import Enrollment
from app.models.user import User

__all__ = ["ClassMember", "ClassPayment", "ClassRoom", "Enrollment", "User"]
