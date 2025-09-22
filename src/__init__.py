"""
Brazilian Political Data Integration Package

Implementation of brazilian-political-data-architecture-v0.md
for comprehensive political network analysis using open government data.
"""

__version__ = "1.0.0"
__author__ = "Brazilian Political Data Team"
__description__ = "Political transparency through data integration"

# Core modules
from .core.discovery_phase import discover_deputy_universe, validate_data_universe
from .core.integrated_discovery import discover_deputy_complete_universe
from .core.temporal_analysis import analyze_temporal_patterns

# Client modules
from .clients.tse_client import TSEClient
from .clients.senado_client import SenadoClient
from .clients.portal_transparencia_client import PortalTransparenciaClient
from .clients.tcu_client import TCUClient
from .clients.datajud_client import DataJudClient

__all__ = [
    # Core functions
    'discover_deputy_universe',
    'validate_data_universe',
    'discover_deputy_complete_universe',
    'analyze_temporal_patterns',

    # API Clients
    'TSEClient',
    'SenadoClient',
    'PortalTransparenciaClient',
    'TCUClient',
    'DataJudClient'
]