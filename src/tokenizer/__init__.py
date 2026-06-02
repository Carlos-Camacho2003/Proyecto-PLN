"""Fase 1 — Tokenización léxica basada en un Autómata Finito Determinista (DFA)."""

from .dfa import DFA
from .tokenizer import Token, Tokenizador, tokenizar

__all__ = ["DFA", "Token", "Tokenizador", "tokenizar"]
