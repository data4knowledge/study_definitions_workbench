from app.utility.fhir_uuid import extract_uuid


class TestExtractUuid:

    def test_found(self):
        text = "Some text with uuid 12345678-1234-1234-1234-123456789abc in it"
        assert extract_uuid(text) == "12345678-1234-1234-1234-123456789abc"

    def test_not_found(self):
        assert extract_uuid("no uuid here") is None

    def test_empty_string(self):
        assert extract_uuid("") is None

    def test_multiple_returns_first(self):
        text = "first: aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee and second: 11111111-2222-3333-4444-555555555555"
        assert extract_uuid(text) == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
