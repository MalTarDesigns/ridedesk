"""Interfaces for every external service, each with a mock that needs no keys.

Core code depends on the Protocols here, never on a provider's SDK, so a real
provider is one new class plus a registry entry.
"""
