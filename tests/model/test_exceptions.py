from app.model.exceptions import FindException, USDMLoadException


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


class TestUSDMLoadException:
    def test_problems_and_str(self):
        e = USDMLoadException(["study.id: bad", "study.name: missing"])
        assert e.problems == ["study.id: bad", "study.name: missing"]
        assert str(e) == "study.id: bad; study.name: missing"

    def test_is_exception(self):
        assert isinstance(USDMLoadException([]), Exception)
