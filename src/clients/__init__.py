"""
API Clients for Brazilian Government Data Sources
"""

from .deputados_client import DeputadosClient
from .tse_client import TSEClient
from .senado_client import SenadoClient
from .portal_transparencia_client import PortalTransparenciaClient
from .tcu_client import TCUClient
from .datajud_client import DataJudClient

__all__ = [
    'DeputadosClient',
    'TSEClient',
    'SenadoClient',
    'PortalTransparenciaClient',
    'TCUClient',
    'DataJudClient'
]