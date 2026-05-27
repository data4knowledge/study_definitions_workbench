from fastapi import FastAPI, Request, HTTPException, status
from app.database.user import User
from starlette.middleware.sessions import SessionMiddleware
from app.configuration.configuration import application_configuration


def set_middleware_secret(app: FastAPI):
    app.add_middleware(
        SessionMiddleware, secret_key=application_configuration.session_secret
    )


def protect_endpoint(request: Request) -> None:
    if application_configuration.single_user:
        request.session["userinfo"] = User.single_user()
        return None
    # Email-code auth: a logged-in user has 'userinfo' in the session.
    if "userinfo" not in request.session:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            detail="Not authorized",
            headers={"Location": "/login"},
        )
