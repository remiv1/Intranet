from fastapi import FastAPI
from routers import login, logout, page_view, security

log_app = FastAPI()

log_app.include_router(login.router)
log_app.include_router(logout.router)
log_app.include_router(page_view.router)
log_app.include_router(security.router)
