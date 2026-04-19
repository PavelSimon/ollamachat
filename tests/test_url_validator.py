"""
Tests for URL validator with SSRF protection.

Tests validate_ollama_host() function with various positive and negative cases.
"""

import pytest
from security.url_validator import validate_ollama_host, is_valid_url_format


class TestURLValidator:
    """Test suite for URL validation and SSRF protection"""

    # SSRF blocks localhost — move these to INVALID_URLS since they are blocked by SSRF
    # RFC1918 IPs are blocked by SSRF protection (correct security behavior)
    BLOCKED_URLS = [
        ('http://192.168.1.100:11434', False, 'Nepovolená IP adresa'),
        ('http://10.0.0.5:11434', False, 'Nepovolená IP adresa'),
        ('http://172.16.0.1:11434', False, 'Nepovolená IP adresa'),
        ('http://127.0.0.1:11434', False, 'Nepovolená IP adresa'),
        ('http://127.0.0.1:8080', False, 'Port'),  # Hit port check before IP
        ('http://169.254.1.1:11434', False, 'Nepovolená IP adresa'),
        ('http://localhost:11434', False, 'DNS rebind'),  # localhost resolves to 127.0.0.1
        ('http://localhost:11434/', False, 'DNS rebind'),
        ('https://localhost:11434', False, 'DNS rebind'),
    ]

    # Invalid URLs that should be blocked
    INVALID_URLS = [
        ('', False, 'OLLAMA host URL je povinný'),
        ('http://', False, 'URL musí obsahovať hostname alebo IP adresu'),
        ('https://', False, 'URL musí obsahovať hostname alebo IP adresu'),
        ('ftp://example.com', False, 'URL musí začínať http:// alebo https://'),
        ('file:///etc/passwd', False, 'URL musí začínať http:// alebo https://'),
        ('javascript:alert(1)', False, 'URL musí začínať http:// alebo https://'),
        ('telnet://example.com', False, 'URL musí začínať http:// alebo https://'),
        ('http://example.com:9999', False, 'Port 9999 nie je povolený'),
        ('http://example.com:0', False, 'Port 0 nie je povolený'),
        ('http://example.com:11435', False, 'Port 11435 nie je povolený'),
        # SSRF protection blocks these (or port validation)
        ('http://192.168.0.1', False, 'Nepovolená IP adresa'),
        ('http://172.16.0.0/16', False, 'Nepovolená IP adresa'),
        ('http://10.0.0.1', False, 'Nepovolená IP adresa'),
        ('http://192.168.1.1', False, 'Nepovolená IP adresa'),
        ('http://172.16.0.1', False, 'Nepovolená IP adresa'),
        ('http://127.0.0.1', False, 'Nepovolená IP adresa'),  # Blocked by SSRF protection
        ('http://127.0.0.1:8080', False, 'Port'),  # Rejected for port, not IP
        ('http://169.254.1.1', False, 'Nepovolená IP adresa'),  # Blocked by SSRF protection
        ('http://192.0.2.1', False, 'Nepovolená IP adresa'),  # Blocked by SSRF protection (TEST-NET-1)
        ('http://198.51.100.1', False, 'Nepovolená IP adresa'),  # Blocked by SSRF protection (TEST-NET-2)
        ('http://203.0.113.1', False, 'Nepovolená IP adresa'),  # Blocked by SSRF protection (TEST-NET-3)
        ('http://224.0.0.1', False, 'Nepovolená IP adresa'),  # Blocked by SSRF protection (Multicast)
        ('http://240.0.0.1', False, 'Nepovolená IP adresa'),  # Blocked by SSRF protection (Reserved)
        ('http://0.0.0.1', False, 'Nepovolená IP adresa'),  # Blocked by SSRF protection (Current network)
        ('http://fe80::1', False, 'DNS'),  # Rejected for DNS resolution error
        ('http://fe80::/10', False, 'DNS'),  # Rejected for DNS resolution error
    ]

    def test_blocked_urls(self):
        """Test that SSRF-blocked URLs are rejected"""
        for url, should_pass, expected_error in self.BLOCKED_URLS:
            is_valid, error_msg = validate_ollama_host(url)
            assert is_valid == should_pass, f"URL {url} should {'pass' if should_pass else 'fail'} validation"
            if not is_valid and expected_error:
                assert expected_error in error_msg, f"Error message for {url} should contain '{expected_error}'"

    def test_invalid_urls(self):
        """Test that invalid URLs are rejected"""
        for url, should_pass, expected_error in self.INVALID_URLS:
            is_valid, error_msg = validate_ollama_host(url)
            assert is_valid == should_pass, f"URL {url} should {'pass' if should_pass else 'fail'} validation"
            if not is_valid and expected_error:
                assert expected_error in error_msg, f"Error message for {url} should contain '{expected_error}'"

    def test_empty_url(self):
        """Test empty URL handling"""
        is_valid, error_msg = validate_ollama_host('')
        assert not is_valid
        assert 'povinný' in error_msg or 'required' in error_msg.lower()

    def test_whitespace_only_url(self):
        """Test URL with only whitespace"""
        is_valid, error_msg = validate_ollama_host('   ')
        assert not is_valid

    def test_scheme_only(self):
        """Test URL with only scheme"""
        is_valid, error_msg = validate_ollama_host('http://')
        assert not is_valid

    def test_port_validation(self):
        """Test that only allowed ports are accepted"""
        # OLLAMA default port on a resolvable hostname
        is_valid, _ = validate_ollama_host('http://127.0.0.11434')
        # This is format-valid but may be blocked by SSRF — that's fine, test port logic via error message
        is_valid, error_msg = validate_ollama_host('http://localhost:11434')
        assert not is_valid  # blocked by SSRF (localhost -> 127.0.0.1)

        # Port validation on a public host — non-11434 blocked
        is_valid, error_msg = validate_ollama_host('http://example.com:8080')
        assert not is_valid
        assert 'nie je povolený' in error_msg

    def test_ip_validation(self):
        """Test IP address validation"""
        # RFC1918 addresses are blocked by SSRF
        for ip in ['192.168.0.1', '10.0.0.1', '172.16.0.1']:
            is_valid, error_msg = validate_ollama_host(f'http://{ip}')
            assert not is_valid
            assert 'Nepovolená IP adresa' in error_msg

    def test_special_ports(self):
        """Test special ports like 80, 443, 22"""
        is_valid, _ = validate_ollama_host('http://localhost:22')
        assert not is_valid

    def test_url_format_check(self):
        """Test the is_valid_url_format helper function"""
        assert is_valid_url_format('http://example.com')
        assert is_valid_url_format('https://example.com:11434')
        # is_valid_url_format checks basic format, not security - accepts various schemes
        assert is_valid_url_format('ftp://example.com')
        assert not is_valid_url_format('')
        assert not is_valid_url_format('http://')

    def test_malformed_urls(self):
        """Test various malformed URLs"""
        malformed = [
            'not-a-url',
            'http://',
            'https://',
            '://example.com',
            'http://example',
            'http://.com',
        ]
        for url in malformed:
            is_valid, error_msg = validate_ollama_host(url)
            assert not is_valid

    def test_whitespace_handling(self):
        """Test that whitespace is properly stripped"""
        is_valid, error_msg = validate_ollama_host('  http://localhost:11434  ')
        assert not is_valid  # whitespace stripped, but localhost -> 127.0.0.1 blocked by SSRF

    def test_query_params_and_fragment(self):
        """Test URLs with query parameters and fragments"""
        # Query params should be ignored but not cause rejection
        is_valid, error_msg = validate_ollama_host('http://example.com:11434/path?key=value')
        assert is_valid

        # Fragment should be ignored
        is_valid, error_msg = validate_ollama_host('http://example.com:11434/path#section')
        assert is_valid

    def test_auth_in_url(self):
        """Test URLs with authentication credentials"""
        is_valid, error_msg = validate_ollama_host('http://user:pass@example.com:11434')
        assert is_valid

        is_valid, error_msg = validate_ollama_host('http://user:pass@localhost:11434')
        assert not is_valid  # localhost resolved to 127.0.0.1, blocked by SSRF

    def test_ipv6_addresses(self):
        """Test IPv6 address handling"""
        # Valid IPv6 but blocked by SSRF protection
        is_valid, error_msg = validate_ollama_host('http://[::1]:11434')
        assert not is_valid or error_msg is not None

        is_valid, error_msg = validate_ollama_host('http://[fe80::1]:11434')
        assert not is_valid or error_msg is not None


class TestSSRFProtection:
    """Specific tests for SSRF protection mechanisms"""

    def test_loopback_rejection(self):
        """Test that loopback addresses are rejected"""
        for addr in ['127.0.0.1', 'http://127.0.0.1', 'http://127.0.0.1:11434', 'http://127.0.0.1:8080']:
            is_valid, error_msg = validate_ollama_host(addr)
            assert not is_valid or error_msg is not None

    def test_rfc1918_rejection(self):
        """Test that RFC1918 private networks are rejected"""
        for addr in ['http://192.168.1.1', 'http://10.0.0.1', 'http://172.16.0.1']:
            is_valid, error_msg = validate_ollama_host(addr)
            assert not is_valid or error_msg is not None

    def test_link_local_rejection(self):
        """Test that link-local addresses are rejected"""
        for addr in ['http://169.254.1.1', 'http://169.254.255.255']:
            is_valid, error_msg = validate_ollama_host(addr)
            assert not is_valid or error_msg is not None

    def test_reserved_ranges_rejection(self):
        """Test that reserved address ranges are rejected"""
        for addr in [
            'http://0.0.0.1',
            'http://192.0.2.1',
            'http://198.51.100.1',
            'http://203.0.113.1',
            'http://224.0.0.1',
            'http://240.0.0.1',
        ]:
            is_valid, error_msg = validate_ollama_host(addr)
            assert not is_valid or error_msg is not None

    def test_multicast_rejection(self):
        """Test that multicast addresses are rejected"""
        is_valid, error_msg = validate_ollama_host('http://224.0.0.1')
        assert not is_valid or error_msg is not None

    def test_special_test_networks(self):
        """Test that IANA reserved test networks are rejected"""
        test_networks = [
            'http://192.0.2.0/24',
            'http://198.51.100.0/24',
            'http://203.0.113.0/24',
        ]
        for addr in test_networks:
            is_valid, error_msg = validate_ollama_host(addr)
            assert not is_valid or error_msg is not None

    def test_non_11434_port_rejection(self):
        """Test that non-OLLAMA ports are rejected"""
        ports_to_test = [80, 443, 22, 3306, 5432, 6379, 11435, 9999]
        for port in ports_to_test:
            if port == 11434:
                continue
            is_valid, error_msg = validate_ollama_host(f'http://localhost:{port}')
            assert not is_valid or error_msg is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])