from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest, UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _response(result: auth_service.AuthResult) -> AuthResponse:
    return AuthResponse(access_token=result.access_token, user=UserOut.model_validate(result.user))


@router.post("/signup", status_code=201)
def signup(body: SignupRequest, db: DbSession) -> AuthResponse:
    return _response(auth_service.signup(db, body.name, body.email, body.password))


@router.post("/login")
def login(body: LoginRequest, db: DbSession) -> AuthResponse:
    return _response(auth_service.login(db, body.email, body.password))
