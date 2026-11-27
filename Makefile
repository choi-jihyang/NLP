# 백엔드(8000)와 프론트엔드(5173)를 한 번에 실행한다. Ctrl+C로 둘 다 종료.
.PHONY: dev
dev:
	@trap 'kill 0' INT TERM; \
	(cd backend && .venv/bin/uvicorn app.main:app --reload) & \
	(cd frontend && npm run dev) & \
	wait
