from fastapi import Depends

from app.services.ruian_client import RuianClient
from app.services.gls_client import GlsApiClient
from app.services.validator import AddressValidatorService

# Singletons — created once, reused across requests
_ruian = RuianClient()
_gls   = GlsApiClient()


def get_ruian() -> RuianClient:
    return _ruian


def get_gls() -> GlsApiClient:
    return _gls


def get_validator(
    ruian: RuianClient  = Depends(get_ruian),
    gls:   GlsApiClient = Depends(get_gls),
) -> AddressValidatorService:
    return AddressValidatorService(ruian=ruian, gls=gls)
