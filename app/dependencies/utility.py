from fastapi import Request
from app.database.user import User


def user_details(request: Request, db):
    user_info = request.session["userinfo"]
    user, present_in_db = User.check(user_info, db)
    return user, present_in_db


def admin_role_enabled(request: Request):
    user_info = request.session["userinfo"]
    role = next((x for x in user_info["roles"] if x["name"] == "Admin"), None)
    return True if role else False


def transmit_role_enabled(request: Request):
    user_info = request.session["userinfo"]
    role = next((x for x in user_info["roles"] if x["name"] == "Transmit"), None)
    return True if role else False
