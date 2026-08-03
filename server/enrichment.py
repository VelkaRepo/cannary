"""
GeoIP Telemetry Enrichment Service for CanaryFile Engine.
Uses free ip-api.com API to resolve IP address location, ISP, and ASN metadata.
"""

import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("canaryfile.enrichment")


class GeoIPService:
    """Free GeoIP lookup service with in-memory caching."""

    def __init__(self, timeout: float = 3.0):
        self.timeout = timeout
        self._cache: Dict[str, Dict[str, Any]] = {}

    async def lookup_ip(self, ip_address: str) -> Dict[str, Any]:
        """
        Lookup IP geolocation details.
        Returns dictionary with country, country_code, city, isp, asn, and is_proxy.
        """
        # Skip local/private IP addresses
        if not ip_address or ip_address in ("127.0.0.1", "localhost", "::1") or ip_address.startswith(("10.", "172.16.", "192.168.")):
            return {
                "country": "Local Network",
                "country_code": "LOCAL",
                "city": "Internal",
                "isp": "Private LAN",
                "asn": "N/A",
                "is_proxy": False
            }

        # Return cached result if available
        if ip_address in self._cache:
            return self._cache[ip_address]

        url = f"http://ip-api.com/json/{ip_address}?fields=status,message,country,countryCode,city,isp,as,proxy"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        result = {
                            "country": data.get("country", "Unknown"),
                            "country_code": data.get("countryCode", "XX"),
                            "city": data.get("city", "Unknown"),
                            "isp": data.get("isp", "Unknown"),
                            "asn": data.get("as", "Unknown"),
                            "is_proxy": data.get("proxy", False)
                        }
                        self._cache[ip_address] = result
                        return result
        except Exception as e:
            logger.warning(f"GeoIP lookup failed for IP {ip_address}: {e}")

        fallback = {
            "country": "Unknown",
            "country_code": "XX",
            "city": "Unknown",
            "isp": "Unknown",
            "asn": "Unknown",
            "is_proxy": False
        }
        return fallback


# Singleton instance
geoip_service = GeoIPService()
