"""
CLI4 Populators Package
Organized populators with comprehensive validators for each data category
"""

from .politician import CLI4PoliticianPopulator, CLI4PoliticianValidator

__all__ = ['CLI4PoliticianPopulator', 'CLI4PoliticianValidator']