"""
Leitura das bases brutas.

Responsabilidade unica: trazer as tres abas do Excel para memoria e validar
que a estrutura esperada esta presente. Nenhuma transformacao acontece aqui.
"""

import logging
from pathlib import Path

import pandas as pd

from . import config

logger = logging.getLogger(__name__)

COLUNAS_ESPERADAS = {
    "associados": ["CHAVE", "NOME", "AGENCIA", "CIDADE", "DATA_ASSOCIACAO", "RENDA_MENSAL"],
    "produtos": ["CHAVE"] + config.COLUNAS_PRODUTOS,
    "movimentacao": ["CHAVE"] + config.COLUNAS_MOVIMENTACAO,
}


def _validar_colunas(df: pd.DataFrame, nome: str) -> None:
    """Falha cedo se a base nao tiver as colunas que o pipeline espera."""
    esperadas = set(COLUNAS_ESPERADAS[nome])
    encontradas = set(df.columns)
    faltantes = esperadas - encontradas

    if faltantes:
        raise ValueError(
            f"Base '{nome}' esta sem as colunas obrigatorias: {sorted(faltantes)}"
        )

    extras = encontradas - esperadas
    if extras:
        logger.warning("Base '%s' possui colunas nao previstas: %s", nome, sorted(extras))


def carregar_bases(caminho: Path | None = None) -> dict[str, pd.DataFrame]:
    """
    Le as tres abas do arquivo Excel de entrada.

    Args:
        caminho: caminho do .xlsx. Usa o padrao do config se omitido.

    Returns:
        Dicionario com as chaves 'associados', 'produtos' e 'movimentacao'.
    """
    caminho = caminho or config.ARQUIVO_ENTRADA

    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo de entrada nao encontrado em {caminho}. "
            "Coloque a base bruta em data/raw/ antes de rodar o pipeline."
        )

    logger.info("Lendo base bruta: %s", caminho.name)

    bases: dict[str, pd.DataFrame] = {}
    with pd.ExcelFile(caminho) as excel:
        for nome, aba in config.ABAS.items():
            if aba not in excel.sheet_names:
                raise ValueError(
                    f"Aba '{aba}' nao encontrada. Abas disponiveis: {excel.sheet_names}"
                )
            df = pd.read_excel(excel, sheet_name=aba)
            _validar_colunas(df, nome)
            bases[nome] = df
            logger.info("  %-14s %5d linhas x %d colunas", aba, len(df), df.shape[1])

    return bases
