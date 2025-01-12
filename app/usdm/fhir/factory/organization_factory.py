from app.usdm.fhir.factory.base_factory import BaseFactory
from fhir.resources.organization import Organization as FHIROrganization
from usdm_model.organization import Organization as USDMOrganization
from .address_factory import AddressFactory
from uuid import uuid4


class OrganizationFactory(BaseFactory):
    def __init__(self, organization: USDMOrganization):
        try:
            address = AddressFactory(organization.legalAddress)
            name = organization.label if organization.label else organization.name
            self.item = FHIROrganization(
                id=str(uuid4()), name=name, contact=[{"address": address.item}]
            )
        except Exception as e:
            self.item = None
            self.handle_exception(e)
