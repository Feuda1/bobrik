"""
Модуль утилит для оптимизации производительности
"""

from .cache import SimpleCache, global_cache, cached, memoize_method

__all__ = ['SimpleCache', 'global_cache', 'cached', 'memoize_method']