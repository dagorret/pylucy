"""
Backends personalizados de email para Lucy AMS.
"""
from .msgraph import MicrosoftGraphEmailBackend

__all__ = ['MicrosoftGraphEmailBackend']
