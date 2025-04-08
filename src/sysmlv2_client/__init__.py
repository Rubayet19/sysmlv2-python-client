# src/sysmlv2_client/__init__.py

"""
SysML v2 Python Client Package
"""

from .client import SysMLV2Client
from .exceptions import SysMLV2Error, SysMLV2AuthError, SysMLV2APIError, SysMLV2NotFoundError

__version__ = "0.1.0"

__all__ = [
    "SysMLV2Client",
    "SysMLV2Error",
    "SysMLV2AuthError",
    "SysMLV2APIError",
    "SysMLV2NotFoundError",
]