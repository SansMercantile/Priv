"""Product registry for the growth engine.

The growth package was originally Priv-only: every module read the live site,
claim registry, hooks and page catalog straight off the global ``stats``. To run
a second product (KEV) through the *same* create → launch → scale loop, each
product is now a self-contained context that is installed as the process-global
``stats`` for the duration of a run.

    from growth import products, agent
    with products.use("kev"):
        report = agent.run()

Every product module exposes the full ``stats`` contract (SITE / SITE_FULL /
DOWNLOADS / DISCLAIMER / CATEGORY / ONE_LINER / STATS / BANNED / get / line /
proof / verified_stats / guard / require_clean / risk_block) plus ``HOOKS``
(the hook library) and ``PAGES`` (the programmatic-SEO page catalog). ``use``
rebinds the attributes on the canonical ``growth.stats`` module *and* the
``stats`` reference already imported into every other growth module, so
``pages.py``, ``social.py``, ``paid.py``, ``distribution.py``, ``outreach.py``
and ``hooks.py`` all read the active product with no code changes. ``use`` also
swaps the page catalog / hook library on the page/hook modules and resets the
experiment ledger to a per-product path (``assets/growth/ledger-<id>.json``)
unless ``GROWTH_LEDGER`` is set explicitly.

The default product is ``priv`` — importing the package and running
``agent.run()`` with no ``use`` block behaves exactly as before.
"""
from __future__ import annotations

import importlib
import os
from contextlib import contextmanager

# The canonical ``stats`` module whose attributes every growth module reads.
# We mutate it in place so existing ``from . import stats`` references see the
# swap without a re-import.
from . import stats as _canonical_stats

# Optional stats attributes that one product may set and another may not. These
# are cleared on the canonical module when the active product does not define
# them, so nothing leaks across a swap.
_OPTIONAL_STAT_ATTRS = ("SOCIAL_TAGS",)

_REGISTRY = {
    "priv": "growth.product_priv",
    "kev": "growth.product_kev",
}

_current = None
_saved = None

# Attributes we copy off a product module onto the canonical stats module.
_STAT_ATTRS = (
    "SITE", "SITE_FULL", "DOWNLOADS", "DISCLAIMER", "CATEGORY", "ONE_LINER",
    "STATS", "BANNED", "get", "line", "proof", "verified_stats", "guard",
    "require_clean", "risk_block",
)


def _load(product):
    if product not in _REGISTRY:
        raise ValueError(f"unknown growth product: {product!r} "
                         f"(known: {', '.join(sorted(_REGISTRY))})")
    return importlib.import_module(_REGISTRY[product])


def _swap(product):
    global _current, _saved
    if product == _current:
        return
    if _saved is None:
        # Stash the original (Priv) state so the default run is untouched:
        # the canonical stats attributes, each consumer module's ``stats``
        # reference, the page catalog and the hook library.
        _saved = {
            "attrs": {a: getattr(_canonical_stats, a, None) for a in _STAT_ATTRS},
            "pages_catalog": None,
            "hooks": None,
            "ledger": None,
        }
        try:
            import growth.pages as _p
            _saved["pages_catalog"] = _p.CATALOG
        except Exception:
            pass
        try:
            import growth.hooks as _h
            _saved["hooks"] = _h.HOOKS
        except Exception:
            pass
        _saved["ledger"] = os.environ.get("GROWTH_LEDGER")

    mod = _load(product)

    # 1. Rebind the canonical stats attributes to the product's values. The
    #    consumer modules keep their ``from . import stats`` reference, but the
    #    attributes they read (SITE / STATS / require_clean / ...) now resolve
    #    to the active product.
    for a in _STAT_ATTRS:
        if hasattr(mod, a):
            setattr(_canonical_stats, a, getattr(mod, a))
    # Optional attributes (e.g. SOCIAL_TAGS): copy when present, clear when the
    # active product does not define them so nothing leaks across a swap.
    for a in _OPTIONAL_STAT_ATTRS:
        if hasattr(mod, a):
            setattr(_canonical_stats, a, getattr(mod, a))
        elif hasattr(_canonical_stats, a):
            try:
                delattr(_canonical_stats, a)
            except AttributeError:
                pass

    # 2. Swap the page catalog and hook library on the modules that own them.
    try:
        pages = importlib.import_module("growth.pages")
        if hasattr(mod, "PAGES"):
            pages.CATALOG = mod.PAGES
    except Exception:
        pass
    try:
        hk = importlib.import_module("growth.hooks")
        if hasattr(mod, "HOOKS"):
            hk.HOOKS = mod.HOOKS
    except Exception:
        pass

    _current = product


@contextmanager
def use(product):
    """Install ``product`` as the active stats/hooks/pages context.

    Restores the *original* (Priv) state on exit — canonical stats attributes,
    page catalog, hook library and ledger path — so a ``with`` block can never
    leak KEV state into the next Priv run (the Lambda runs Priv on a schedule;
    KEV runs are explicit).
    """
    _swap(product)
    try:
        yield product
    finally:
        _restore_default()


def _restore_default():
    """Restore the stashed original (Priv) state in place."""
    global _current
    if _saved is None:
        _current = None
        return
    for a, v in _saved["attrs"].items():
        setattr(_canonical_stats, a, v)
    # Clear any optional attributes the outgoing product set (Priv has none).
    for a in _OPTIONAL_STAT_ATTRS:
        if hasattr(_canonical_stats, a):
            try:
                delattr(_canonical_stats, a)
            except AttributeError:
                pass
    try:
        import growth.pages as _p
        if _saved["pages_catalog"] is not None:
            _p.CATALOG = _saved["pages_catalog"]
    except Exception:
        pass
    try:
        import growth.hooks as _h
        if _saved["hooks"] is not None:
            _h.HOOKS = _saved["hooks"]
    except Exception:
        pass
    if _saved["ledger"] is None:
        os.environ.pop("GROWTH_LEDGER", None)
    else:
        os.environ["GROWTH_LEDGER"] = _saved["ledger"]
    _current = None


def current():
    return _current or "priv"
