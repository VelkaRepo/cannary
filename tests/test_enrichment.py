"""
Unit tests for GeoIP enrichment service.
"""

import pytest
from server.enrichment import geoip_service


@pytest.mark.anyio
async def test_geoip_local_ip_lookup():
    """Verify local network IPs return internal metadata without network calls."""
    data_loopback = await geoip_service.lookup_ip("127.0.0.1")
    assert data_loopback["country"] == "Local Network"
    assert data_loopback["country_code"] == "LOCAL"

    data_private = await geoip_service.lookup_ip("192.168.1.50")
    assert data_private["country"] == "Local Network"
