from app.usdm.fhir.factory.iso8601_ucum import ISO8601ToUCUM


def test_convert():
    assert ISO8601ToUCUM.convert("P2D") == {
        "system": "http://unitsofmeasure.org",
        "unit": "d",
        "value": "2",
    }
    assert ISO8601ToUCUM.convert("P12W") == {
        "system": "http://unitsofmeasure.org",
        "unit": "w",
        "value": "12",
    }
    assert ISO8601ToUCUM.convert("P123Y") == {
        "system": "http://unitsofmeasure.org",
        "unit": "y",
        "value": "123",
    }
    assert ISO8601ToUCUM.convert("PT15H") == {
        "system": "http://unitsofmeasure.org",
        "unit": "h",
        "value": "15",
    }


def test_convert_error():
    assert ISO8601ToUCUM.convert("123Y") == {}
    assert ISO8601ToUCUM.convert("P123") == {}
    assert ISO8601ToUCUM.convert("PY") == {}
