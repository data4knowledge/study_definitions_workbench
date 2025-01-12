from app.database.user import User


def test_single_user(db):
    results = User.single_user()
    assert results == {
        "email": "",
        "sub": "SUE|1234567890",
        "nickname": "Single User",
        "roles": [],
    }
