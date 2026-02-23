from app.core.config import settings
from app.models.schemas import (
    AddressIn, AddressOut, ValidationResult, ValidationStatus, Suggestion
)
from app.services.ruian_client import RuianClient
from app.services.gls_client import GlsApiClient


class AddressValidatorService:
    """
    Validation pipeline:

    1. RUIAN API — authoritative Czech address registry
       ├─ EXACT match       → VALID
       ├─ confidence ≥ 0.85 → CORRECTED (auto)
       └─ confidence < 0.85 → AMBIGUOUS (return suggestions to eshop)
    2. No RUIAN result      → INVALID
    """

    def __init__(self, ruian: RuianClient, gls: GlsApiClient) -> None:
        self.ruian = ruian
        self.gls   = gls

    async def validate(self, address: AddressIn) -> ValidationResult:

        ruian_result = await self.ruian.validate(
            street=address.street,
            house_number=address.house_number,
            city=address.city,
            zip_code=address.zip,
        )

        if ruian_result is None:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                message="Street not found in RUIAN registry. Please verify the address.",
            )

        if ruian_result["status"] == "EXACT":
            return ValidationResult(
                status=ValidationStatus.VALID,
                address=self._to_address_out(address),
            )

        confidence: float = ruian_result["confidence"]

        if confidence >= settings.RUIAN_AUTO_CORRECT_THRESHOLD:
            corrected = AddressOut(
                name=address.name,
                street=ruian_result["street_name"]  or address.street,
                house_number=ruian_result["house_number"] or address.house_number,
                city=ruian_result["municipality"]   or address.city,
                zip=ruian_result["zip"]             or address.zip,
                country=address.country,
            )
            return ValidationResult(
                status=ValidationStatus.CORRECTED,
                address=corrected,
                message=f"Auto-corrected by RUIAN (confidence {round(confidence * 100)}%)",
            )

        # Low confidence → return suggestions
        raw_suggestions = await self.ruian.get_suggestions(address.street, address.city)
        return ValidationResult(
            status=ValidationStatus.AMBIGUOUS,
            address=self._to_address_out(address),
            message="Multiple possible addresses found — please review",
            suggestions=[Suggestion(**s) for s in raw_suggestions],
        )

    @staticmethod
    def _to_address_out(address: AddressIn) -> AddressOut:
        return AddressOut(
            name=address.name,
            street=address.street,
            house_number=address.house_number,
            city=address.city,
            zip=address.zip,
            country=address.country,
        )
