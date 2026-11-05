"""Priv product context for the growth engine (the default).

Re-exports the canonical ``growth.stats`` surface (Priv's claim registry,
compliance guard and risk block) plus Priv's hook library and page catalog, so
``products.use("priv")`` restores exactly the original behaviour. This module
is the reference for the product-context contract.
"""
from __future__ import annotations

from . import stats as _stats
from . import hooks as _hooks
from . import pages as _pages

# --- stats contract (re-exported verbatim) -----------------------------------
SITE = _stats.SITE
SITE_FULL = _stats.SITE_FULL
DOWNLOADS = _stats.DOWNLOADS
DISCLAIMER = _stats.DISCLAIMER
CATEGORY = _stats.CATEGORY
ONE_LINER = _stats.ONE_LINER
STATS = _stats.STATS
BANNED = _stats.BANNED

get = _stats.get
line = _stats.line
proof = _stats.proof
verified_stats = _stats.verified_stats
guard = _stats.guard
require_clean = _stats.require_clean
risk_block = _stats.risk_block

# --- hook library + page catalog (module attributes the swap rebinds) --------
HOOKS = _hooks.HOOKS
PAGES = _pages.CATALOG
