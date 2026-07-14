"""Resolve markets from property codes."""

from __future__ import annotations

import logging
import re

from .errors import MarketInferenceError

MARKET_PROPERTY_CODES = {
    "Chicagoland": {"AEC", "HCA", "HCJ"},
    "St. Louis": {"HSL", "RSL"},
    "Baton Rouge": {"LBR"},
    "Dayton": {"HDR"},
    "Toledo": {"HTO"},
}

MARKET_NAME_ALIASES = {
    "chicagoland": "Chicagoland",
    "stlouis": "St. Louis",
    "saintlouis": "St. Louis",
    "batonrouge": "Baton Rouge",
    "batonrogue": "Baton Rouge",
    "lbr": "Baton Rouge",
    "dayton": "Dayton",
    "hdr": "Dayton",
    "toledo": "Toledo",
    "hto": "Toledo",
}

MARKET_SHEET_ALIASES = {
    "St. Louis": ["St. Louis", "St Louis"],
    "Baton Rouge": ["Baton Rouge", "Baton Rogue", "LBR"],
}

logger = logging.getLogger(__name__)


def infer_market_from_rows(rows: list[dict[str, object]]) -> str:
    """Infer the hosted-player market from Property ID values."""

    property_codes = {
        str(row.get("Property ID") or "").strip().upper() for row in rows if str(row.get("Property ID") or "").strip()
    }
    if not property_codes:
        raise MarketInferenceError("Could not infer market because Property ID is blank.")

    matching_markets = [market for market, codes in MARKET_PROPERTY_CODES.items() if property_codes.issubset(codes)]
    if len(matching_markets) == 1:
        logger.info(
            "market_inference_result operation=market_inference result=resolved market=%s property_code_count=%s",
            matching_markets[0],
            len(property_codes),
        )
        return matching_markets[0]

    if matching_markets:
        raise MarketInferenceError("Property IDs match more than one market: " + ", ".join(matching_markets))

    known_codes = {code for codes in MARKET_PROPERTY_CODES.values() for code in codes}
    unknown_codes = sorted(property_codes - known_codes)
    if unknown_codes:
        raise MarketInferenceError(
            "Unknown Property ID value(s): "
            + ", ".join(unknown_codes)
            + ". Add them to MARKET_PROPERTY_CODES before running."
        )

    raise MarketInferenceError("Property IDs span multiple markets: " + ", ".join(sorted(property_codes)))


def normalize_market_name(market: str) -> str:
    """Return a canonical market name for user-entered aliases."""

    text = market.strip()
    key = re.sub(r"[^a-z0-9]+", "", text.lower())
    if key in MARKET_NAME_ALIASES:
        return MARKET_NAME_ALIASES[key]
    supported = ", ".join(sorted(set(MARKET_NAME_ALIASES.values())))
    raise MarketInferenceError(f"Unsupported market name: {text}. Supported markets are: {supported}.")


def sheet_candidates_for_market(market: str) -> list[str]:
    """Return possible last-week workbook sheet names for the inferred market."""

    original = market.strip()
    market = normalize_market_name(original)
    aliases = MARKET_SHEET_ALIASES.get(market, [])
    candidates = [market, original, *aliases]
    deduped: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in deduped:
            deduped.append(candidate)
    return deduped
