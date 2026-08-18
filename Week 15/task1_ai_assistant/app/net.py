"""
This network blocks outbound IPv6 (packets are silently dropped rather than
rejected), while DNS still returns IPv6 addresses for most external hosts.
Libraries that try IPv6 first hang for a long time before giving up instead
of falling back to IPv4, which breaks huggingface_hub/requests calls (model
downloads) and google-genai's httpx-based transport. Two separate fixes are
needed since they use different HTTP stacks:

  - force_ipv4_dns(): monkeypatches socket.getaddrinfo to only return IPv4
    results. Fixes anything built on stdlib sockets (requests, urllib3 --
    i.e. huggingface_hub / sentence-transformers / transformers).
  - ipv4_httpx_client(): httpx does its own connection handling and doesn't
    go through socket.getaddrinfo, so it needs an httpx.Client bound to the
    IPv4 wildcard local address instead. Used for the google-genai client.

Both are no-ops in cost on a network where IPv6 works fine, so it's safe to
always apply them rather than trying to detect the problem first.
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
