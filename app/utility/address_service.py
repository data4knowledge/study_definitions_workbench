from d4k_ms_base.service import Service
from app.configuration.configuration import application_configuration


class AddressService(Service):
    def __init__(self):
        super().__init__(application_configuration.address_server)

    def parser(self, address: str) -> dict:
        return super().post("parser", data={"query": address})
