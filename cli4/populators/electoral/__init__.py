"""
Electoral Records Populator Module
Handles TSE electoral outcome data population following CLI4 architecture
"""

from .populator import ElectoralRecordsPopulator
from .validator import ElectoralRecordsValidator

__all__ = ['ElectoralRecordsPopulator', 'ElectoralRecordsValidator']