from fastapi import APIRouter

from app.api.deps import DbSession, StudentUser
from app.schemas.enrollments import MyClassOut
from app.services import enrollment_service

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/classes")
def my_classes(student: StudentUser, db: DbSession) -> list[MyClassOut]:
    return [
        MyClassOut(class_id=v.klass.seq, class_name=v.klass.name, student_no=v.enrollment.student_no,
                   enrollment_status=v.enrollment.status)
        for v in enrollment_service.my_classes(db, student)
    ]
