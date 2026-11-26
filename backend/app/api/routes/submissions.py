"""학생: 내 제출 · 공개 테스트 실행 · 문항 제출 · 개념 확인 · 최종 제출 (I7 · 결과 공개 전 비공개)."""

from fastapi import APIRouter

from app.api.deps import DbSession, StudentUser
from app.runner import get_code_runner
from app.schemas.submissions import AnswerBody, ConceptReplyBody, RunBody, RunOut, SubmissionOut
from app.services import submission_service as svc

router = APIRouter(tags=["submissions"])


@router.get("/assignments/{assignment_id}/submission")
def get_submission(assignment_id: int, student: StudentUser, db: DbSession) -> SubmissionOut:
    return svc.get_submission(db, student, assignment_id)


@router.post("/assignments/{assignment_id}/questions/{question_id}/run")
async def run_public_tests(
    assignment_id: int, question_id: int, body: RunBody, student: StudentUser, db: DbSession
) -> RunOut:
    return await svc.run_public(db, student, assignment_id, question_id, body.code, get_code_runner())


@router.put("/assignments/{assignment_id}/answers/{question_id}")
async def submit_answer(
    assignment_id: int, question_id: int, body: AnswerBody, student: StudentUser, db: DbSession
) -> SubmissionOut:
    return await svc.submit_answer(db, student, assignment_id, question_id, body.content, get_code_runner())


@router.post("/assignments/{assignment_id}/answers/{question_id}/concept-check")
def answer_concept_check(
    assignment_id: int, question_id: int, body: ConceptReplyBody, student: StudentUser, db: DbSession
) -> SubmissionOut:
    return svc.answer_concept_check(db, student, assignment_id, question_id, body.reply, body.elapsed_ms)


@router.delete("/assignments/{assignment_id}/answers/{question_id}/concept-check")
def cancel_concept_check(assignment_id: int, question_id: int, student: StudentUser, db: DbSession) -> SubmissionOut:
    return svc.cancel_concept_check(db, student, assignment_id, question_id)


@router.post("/assignments/{assignment_id}/submission/finalize")
def finalize_submission(assignment_id: int, student: StudentUser, db: DbSession) -> SubmissionOut:
    return svc.finalize(db, student, assignment_id)
