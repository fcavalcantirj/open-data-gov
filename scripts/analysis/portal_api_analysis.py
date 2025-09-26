#!/usr/bin/env python3
import requests
import json
import sys
sys.path.insert(0, 'src')

# Load API key
api_key = None
try:
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('PORTAL_TRANSPARENCIA_API_KEY='):
                api_key = line.split('=')[1].strip()
                break
except:
    print("Could not load API key")
    exit(1)

base_url = 'https://api.portaldatransparencia.gov.br/api-de-dados/'
headers = {'chave-api-dados': api_key}

# Systematically test all known endpoints and their requirements
endpoints = {
    'ceis': {
        'description': 'Cadastro de Empresas Inidôneas e Suspensas',
        'required_params': [],
        'optional_params': ['cnpjSancionado', 'codigoSancao', 'dataInicioSancao', 'dataFimSancao', 'pagina']
    },
    'cnep': {
        'description': 'Cadastro Nacional de Empresas Punidas',
        'required_params': [],
        'optional_params': ['cpf', 'cnpj', 'codigoSancao', 'dataInicioSancao', 'dataFimSancao', 'pagina']
    },
    'contratos': {
        'description': 'Contratos do Governo Federal',
        'required_params': ['codigoOrgao'],
        'optional_params': ['cnpjContratada', 'dataInicial', 'dataFinal', 'pagina']
    },
    'servidores': {
        'description': 'Servidores Públicos Federais',
        'required_params': ['codigoOrgao'],
        'optional_params': ['nome', 'cpf', 'matricula', 'pagina']
    },
    'cartoes': {
        'description': 'Gastos com Cartão de Pagamento',
        'required_params': ['mesAnoInicio', 'mesAnoFim'],
        'optional_params': ['codigoOrgao', 'cpfPortador', 'pagina']
    },
    'despesas': {
        'description': 'Despesas do Governo Federal',
        'required_params': ['mesAnoInicio', 'mesAnoFim'],
        'optional_params': ['codigoOrgao', 'codigoOrgaoSubordinado', 'pagina']
    },
    'licitacoes': {
        'description': 'Licitações do Governo Federal',
        'required_params': ['codigoOrgao'],
        'optional_params': ['dataInicial', 'dataFinal', 'cnpjParticipante', 'pagina']
    },
    'convenios': {
        'description': 'Convênios do Governo Federal',
        'required_params': [],
        'optional_params': ['convenente', 'codigoOrgao', 'dataInicial', 'dataFinal', 'pagina']
    },
    'transferencias': {
        'description': 'Transferências de Recursos',
        'required_params': [],
        'optional_params': ['mesAnoInicio', 'mesAnoFim', 'codigoIbge', 'pagina']
    },
    'auxilio-emergencial': {
        'description': 'Auxílio Emergencial COVID-19',
        'required_params': [],
        'optional_params': ['mesAno', 'codigoIbge', 'cpf', 'pagina']
    },
    'beneficios-cidadao': {
        'description': 'Benefícios ao Cidadão',
        'required_params': [],
        'optional_params': ['codigoBeneficio', 'mesAno', 'codigoIbge', 'cpf', 'pagina']
    },
    'viagens': {
        'description': 'Viagens a Serviço',
        'required_params': [],
        'optional_params': ['codigoOrgao', 'cpf', 'dataInicial', 'dataFinal', 'pagina']
    }
}

print('# Portal da Transparência API - Complete Route Analysis')
print('=' * 60)
print()
print('Base URL: https://api.portaldatransparencia.gov.br/api-de-dados/')
print('Authentication: API Key via header "chave-api-dados"')
print()

for endpoint, info in endpoints.items():
    print(f'## {endpoint.upper()}')
    print(f'**Description:** {info["description"]}')
    print(f'**Endpoint:** GET /api-de-dados/{endpoint}')

    if info['required_params']:
        req_params = ', '.join(info["required_params"])
        print(f'**Required Parameters:** {req_params}')
    else:
        print('**Required Parameters:** None')

    opt_params = ', '.join(info["optional_params"])
    print(f'**Optional Parameters:** {opt_params}')

    # Test the endpoint
    try:
        params = {'pagina': 1}

        # Add required params with test values
        if 'codigoOrgao' in info['required_params']:
            params['codigoOrgao'] = '20101'
        if 'mesAnoInicio' in info['required_params']:
            params['mesAnoInicio'] = '092024'
            params['mesAnoFim'] = '092024'

        response = requests.get(f'{base_url}{endpoint}', headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and data:
                sample = data[0]
                print('**Status:** ✅ Working')
                print('**Response:** List of records')
                if isinstance(sample, dict):
                    sample_fields = ', '.join(list(sample.keys())[:8])
                    print(f'**Sample Fields:** {sample_fields}...')
            else:
                print('**Status:** ✅ Working (empty result)')
        else:
            error_text = response.text[:100]
            print(f'**Status:** ❌ Error {response.status_code}: {error_text}')

    except Exception as e:
        print(f'**Status:** ❌ Error: {str(e)}')

    print()