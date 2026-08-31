"""
Configuracoes centrais do projeto.

Todos os parametros de negocio (faixas, pesos, cortes de classificacao) ficam
aqui para que a metodologia seja auditavel e ajustavel sem tocar na logica.
"""

from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------- #
# Caminhos
# --------------------------------------------------------------------------- #

RAIZ = Path(__file__).resolve().parents[1]

DIR_DADOS_BRUTOS = RAIZ / "data" / "raw"
DIR_DADOS_TRATADOS = RAIZ / "data" / "processed"

ARQUIVO_ENTRADA = DIR_DADOS_BRUTOS / "teste_bi_base_crua.xlsx"
ARQUIVO_SAIDA_XLSX = DIR_DADOS_TRATADOS / "base_consolidada.xlsx"
ARQUIVO_SAIDA_CSV = DIR_DADOS_TRATADOS / "base_consolidada.csv"

ABAS = {
    "associados": "Associados",
    "produtos": "Produtos",
    "movimentacao": "Movimentacao",
}

CHAVE = "CHAVE"

# --------------------------------------------------------------------------- #
# Data de referencia
# --------------------------------------------------------------------------- #
# O tempo de relacionamento e calculado contra uma data fixa, e nao contra
# datetime.today(), para que a base consolidada seja reproduzivel: rodar o
# pipeline amanha deve gerar exatamente o mesmo arquivo de hoje.

DATA_REFERENCIA = pd.Timestamp("2026-08-30")

# --------------------------------------------------------------------------- #
# Tratamento
# --------------------------------------------------------------------------- #

# Cidades gravadas com grafias divergentes na base bruta.
# A chave e a forma normalizada (sem acento, caixa alta, sem pontuacao);
# o valor e a grafia oficial de saida.
MAPA_CIDADES = {
    "PATO BRANCO": "Pato Branco",
    "P BRANCO": "Pato Branco",
    "CASCAVEL": "Cascavel",
    "CHAPECO": "Chapeco",
    "TOLEDO": "Toledo",
    "MARINGA": "Maringa",
}

COLUNAS_PRODUTOS = [
    "CONTA_CORRENTE",
    "CARTAO",
    "CREDITO",
    "INVESTIMENTO",
    "CONSORCIO",
    "SEGURO",
]

COLUNAS_MOVIMENTACAO = ["SALDO_MEDIO", "PIX_MENSAL", "COMPRAS_CARTAO"]

# --------------------------------------------------------------------------- #
# Indicadores
# --------------------------------------------------------------------------- #

# Faixas de renda conforme enunciado do desafio.
# (limite_superior, rotulo) - o ultimo limite e infinito.
FAIXAS_RENDA = [
    (3000.0, "Ate R$ 3.000"),
    (8000.0, "R$ 3.001 a R$ 8.000"),
    (15000.0, "R$ 8.001 a R$ 15.000"),
    (float("inf"), "Acima de R$ 15.000"),
]

ROTULO_RENDA_NULA = "Nao informado"

FAIXAS_TEMPO = [
    (2.0, "Menos de 2 anos"),
    (3.0, "2 a 3 anos"),
    (5.0, "3 a 5 anos"),
    (float("inf"), "Mais de 5 anos"),
]

ROTULO_TEMPO_INVALIDO = "Nao informado"

# Pesos do indice de movimentacao. Somam 1,0.
# Saldo medio pesa mais por ser o indicador de relacionamento financeiro
# mais estavel; PIX e compras no cartao medem intensidade de uso corrente.
PESOS_MOVIMENTACAO = {
    "SALDO_MEDIO": 0.50,
    "PIX_MENSAL": 0.25,
    "COMPRAS_CARTAO": 0.25,
}

# --------------------------------------------------------------------------- #
# Classificacao
# --------------------------------------------------------------------------- #
# Modelo de pontuacao em tres dimensoes, cada uma valendo de 0 a 3 pontos.
# Score final vai de 0 a 9 e e traduzido em quatro estagios de relacionamento.

# Pontos por quantidade de produtos ativos: (limite_superior_inclusivo, pontos)
PONTOS_PRODUTOS = [(1, 0), (3, 1), (5, 2), (6, 3)]

# Pontos por tempo de relacionamento em anos: (limite_superior_exclusivo, pontos)
PONTOS_TEMPO = [(2.0, 0), (3.0, 1), (5.0, 2), (float("inf"), 3)]

# Pontos por quartil do indice de movimentacao.
# Q1 = 0 pontos, Q2 = 1, Q3 = 2, Q4 = 3.
QUARTIS_MOVIMENTACAO = [0.25, 0.50, 0.75]

# Pontuacao neutra atribuida quando a dimensao nao pode ser avaliada
# (data de associacao inconsistente). Evita punir o associado por um erro
# de cadastro, empurrando-o artificialmente para o estagio Inicial.
PONTOS_NEUTROS = 1

# Cortes do score total (0 a 9): (limite_superior_inclusivo, estagio)
CORTES_CLASSIFICACAO = [
    (2, "Inicial"),
    (4, "Em Desenvolvimento"),
    (6, "Maduro"),
    (9, "Engajado"),
]

ORDEM_CLASSIFICACAO = ["Inicial", "Em Desenvolvimento", "Maduro", "Engajado"]

# --------------------------------------------------------------------------- #
# Oportunidades comerciais
# --------------------------------------------------------------------------- #

# Alta renda com poucos produtos: potencial de venda cruzada.
RENDA_ALTA_OPORTUNIDADE = 15000.0
MAX_PRODUTOS_OPORTUNIDADE = 2

# Baixa utilizacao: indice de movimentacao no quartil inferior.
LIMITE_BAIXA_UTILIZACAO = 0.25
