"""Shared error handling utilities for user-safe fallbacks."""
import logging
import streamlit as st

logger = logging.getLogger(__name__)


def show_user_error(message: str):
    st.error(message)


def log_exception(context: str, exc: Exception):
    logger.exception("%s: %s", context, exc)
