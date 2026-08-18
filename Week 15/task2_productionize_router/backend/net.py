"""Same IPv4-forcing workaround as task1_ai_assistant/app/net.py -- see that
file for the full explanation. Duplicated here (rather than imported across
the task1/task2 package boundary) so each task stays independently
deployable, matching the assignment's "two separate deliverables" structure.
"""
import socket

import httpx

_original_getaddrinfo = socket.getaddrinfo


def force_ipv4_dns() -> None:
    def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        return _original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

    socket.getaddrinfo = _ipv4_only_getaddrinfo


def ipv4_httpx_client() -> httpx.Client:
    return httpx.Client(transport=httpx.HTTPTransport(local_address="0.0.0.0"))
