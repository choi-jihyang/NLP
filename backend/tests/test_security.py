from app.core.security import hash_password, verify_password


def test_hash_format():
    stored = hash_password("correct horse")
    algorithm, iterations, salt, digest = stored.split("$")
    assert algorithm == "pbkdf2_sha512"
    assert iterations == "200000"
    assert salt and digest


def test_verify_correct_and_wrong_password():
    stored = hash_password("correct horse")
    assert verify_password("correct horse", stored) is True
    assert verify_password("wrong horse", stored) is False


def test_same_password_gets_different_salt():
    assert hash_password("same") != hash_password("same")


def test_stored_iterations_are_used():
    stored = hash_password("pw", iterations=1000)
    assert stored.split("$")[1] == "1000"
    assert verify_password("pw", stored) is True


def test_malformed_or_unknown_hash_returns_false():
    assert verify_password("pw", "") is False
    assert verify_password("pw", "not-a-hash") is False
    assert verify_password("pw", "pbkdf2_sha512$abc$!!$!!") is False
    assert verify_password("pw", "md5$1$c2FsdA==$aGFzaA==") is False


def test_missing_stored_hash_returns_false():
    # 수업 코드로 입장한 학생은 password_hash가 NULL
    assert verify_password("pw", None) is False


def test_unencodable_password_returns_false():
    # JSON의 "\ud800"(짝 없는 surrogate)은 str로 들어오지만 UTF-8로 인코딩되지 않는다
    stored = hash_password("pw")
    assert verify_password("\ud800", stored) is False
