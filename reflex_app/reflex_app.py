"""Reflex entry module.

This module re-exports the `app` instance so Reflex can discover it via
`app_name='reflex_app'` in `rxconfig.py`.
"""

from .tft_app import app  # noqa: F401

