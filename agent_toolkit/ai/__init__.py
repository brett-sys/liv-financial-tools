"""Illuminate – the LIFI AI coaching suite.

Server-side helpers for calling Claude with forced structured output.
Every tool injects the shared "Operating Principles" config (the single
source of truth, editable in Settings) into its system prompt.

Compliance: these are training, coaching, and admin tools for licensed
agents. They are never client-facing and never decide eligibility or
underwriting.
"""
