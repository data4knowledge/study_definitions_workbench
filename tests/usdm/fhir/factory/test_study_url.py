import pytest
from app.usdm.fhir.factory.study_url import StudyUrl
from usdm_model.study import Study

@pytest.fixture
def study():
    params = {
        "name": "study_pilot  15",
        "description": "pilot",
        "label": "pilot",
        "versions": [],
        "documentedBy": [],
        "instanceType": "Study",
    }
    return Study(**params)

def test_generate(study):
    assert StudyUrl.generate(study) == "http://d4k.dk/fhir/vulcan-soa/study-pilot-15"
