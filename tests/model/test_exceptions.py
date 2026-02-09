from app.model.exceptions import FindException


class TestFindException:
    def test_init(self):
        class FakeModel:
            pass

        e = FindException(FakeModel, 42)
        assert e.msg == "Failed to find 'FakeModel' with id '42'."

    def test_str(self):
        class FakeModel:
            pass

        e = FindException(FakeModel, "abc")
        assert str(e) == "Failed to find 'FakeModel' with id 'abc'."

    def test_is_exception(self):
        class FakeModel:
            pass

        e = FindException(FakeModel, 1)
        assert isinstance(e, Exception)
