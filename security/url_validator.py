"""
URL validation with SSRF protection for OLLAMA host configuration.

This module implements strict validation to prevent Server-Side Request Forgery (SSRF)
attacks when users configure their OLLAMA server URL.
"""

import ipaddress
from urllib.parse import urlparse
import socket
from typing import Tuple


# RFC1918 private networks
RFC1918_NETWORKS = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
]

# Reserved and loopback addresses
RESERVED_NETWORKS = [
    ipaddress.ip_network('127.0.0.0/8'),  # Loopback
    ipaddress.ip_network('0.0.0.0/8'),    # Current network
    ipaddress.ip_network('169.254.0.0/16'),  # Link-local
    ipaddress.ip_network('192.0.0.0/24'),  # IETF Protocol Assignments
    ipaddress.ip_network('192.0.2.0/24'),  # TEST-NET-1
    ipaddress.ip_network('198.51.100.0/24'),  # TEST-NET-2
    ipaddress.ip_network('203.0.113.0/24'),  # TEST-NET-3
    ipaddress.ip_network('224.0.0.0/4'),  # Multicast
    ipaddress.ip_network('240.0.0.0/4'),  # Reserved
]

# Allowed ports (OLLAMA default is 11434)
ALLOWED_PORTS = {11434}


def validate_ollama_host(host_url: str) -> Tuple[bool, str]:
    """
    Validate OLLAMA host URL with SSRF protection.

    Args:
        host_url: URL string to validate

    Returns:
        Tuple of (is_valid, error_message)
        is_valid: True if URL is valid and safe
        error_message: Error message if invalid, None if valid
    """
    if not host_url or not host_url.strip():
        return False, "OLLAMA host URL je povinný"

    host_url = host_url.strip()

    # Step 1: Parse URL
    try:
        parsed = urlparse(host_url)
    except Exception:
        return False, "Neplatný formát URL"

    # Step 2: Validate scheme (only http/https)
    if not parsed.scheme:
        return False, "URL musí začínať http:// alebo https://"
    if parsed.scheme not in ['http', 'https']:
        return False, "URL musí začínať http:// alebo https://"

    # Step 3: Validate host
    if not parsed.netloc:
        return False, "URL musí obsahovať hostname alebo IP adresu"

    # Handle IPv6 addresses with brackets (e.g., http://[fe80::1]:11434)
    if '[' in parsed.netloc and ']' in parsed.netloc:
        hostname = parsed.netloc.split(']')[0][1:]
    else:
        hostname = parsed.hostname or parsed.netloc

    # Step 4: Validate port (before IP check since port is checked first)
    try:
        port = parsed.port
        if port and port not in ALLOWED_PORTS:
            return False, f"Port {port} nie je povolený. Povolené: {sorted(ALLOWED_PORTS)}"
        if port == 0:
            return False, "Port 0 nie je povolený"
    except (ValueError, TypeError):
        # If port cannot be parsed, skip port validation
        pass

    # Step 5: Block RFC1918, loopback, and other unsafe IP ranges
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.version == 4:
            for network in RFC1918_NETWORKS + RESERVED_NETWORKS:
                if ip in network:
                    return False, "Nepovolená IP adresa (localhost, privátna sieť alebo rezervovaná)"
        elif ip.version == 6:
            if ip in ipaddress.ip_network('::1/128'):  # IPv6 loopback
                return False, "Nepovolená IP adresa (localhost)"
            if ip in ipaddress.ip_network('fe80::/10'):  # IPv6 link-local
                return False, "Nepovolená IP adresa (link-local)"
    except ValueError:
        pass  # Not an IP address - continue to DNS resolution check

    # Step 6: DNS resolution protection (prevent DNS rebinding)
    try:
        # Try to resolve hostname to IP
        resolved_ips = socket.getaddrinfo(hostname, parsed.port or 11434, family=socket.AF_INET, type=socket.SOCK_STREAM)
        resolved_ips = [ip[4][0] for ip in resolved_ips]
    except socket.gaierror:
        # Hostname not resolvable - treat as error
        return False, "Nemožno vyriešiť hostname"
    except Exception:
        return False, "Chyba pri overovaní DNS adries"

    # Check resolved IPs against blocked ranges
    for resolved_ip in resolved_ips:
        try:
            ip = ipaddress.ip_address(resolved_ip)
            if ip.version == 4:
                for network in RFC1918_NETWORKS + RESERVED_NETWORKS:
                    if ip in network:
                        return False, "DNS rebind úspešný - adresa smeruje k nepovolenému zdroju"
        except ValueError:
            continue

    return True, None


def is_valid_url_format(host_url: str) -> bool:
    """
    Simple check if URL has valid format (not XSS-safe).
    Use validate_ollama_host() for security checks.

    Args:
        host_url: URL string to check

    Returns:
        True if URL format is valid
    """
    if not host_url or not host_url.strip():
        return False

    try:
        parsed = urlparse(host_url)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False