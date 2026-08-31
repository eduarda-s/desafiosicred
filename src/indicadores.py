"""
Criacao dos indicadores de relacionamento.

Derivam da base consolidada e alimentam tanto a classificacao quanto o
dashboard. Todos os cortes vem do config, nenhum numero e escrito aqui.
"""

import logging

import pandas as pd

from . import config

logger = logging.getLogger(__name__)


def _faixa(valor: float, faixas: list[tuple[float, str]], rotulo_nulo: str) -> str:
    """Devolve o rotulo da primeira faixa cujo limite superior comporta o valor."""
    if pd.isna(valor):
        return rotulo_nulo
    for limite, rotulo in faixas:
        if valor <= limite:
            return rotulo
    return faixas[-1][1]


def calcular_qtd_produtos(df: pd.DataFrame) -> pd.DataFrame:
    """Conta quantos dos seis produtos o associado tem ativos."""
    df = df.copy()
    df["QTD_PRODUTOS"] = df[config.COLUNAS_PRODUTOS].sum(axis=1).astype(int)

    logger.info("Produtos por associado: media %.2f", df["QTD_PRODUTOS"].mean())
    for qtd, n in df["QTD_PRODUTOS"].value_counts().sort_index().items():
        logger.info("    %d produto(s): %4d associados", qtd, n)
    return df


def calcular_tempo_relacionamento(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula o tempo de relacionamento em anos contra a data de referencia.

    Registros com data invalida ficam nulos e recebem faixa 'Nao informado',
    para nao se misturarem com associados legitimamente recentes.
    """
    df = df.copy()

    dias = (config.DATA_REFERENCIA - df["DATA_ASSOCIACAO"]).dt.days
    df["TEMPO_RELACIONAMENTO_ANOS"] = (dias / 365.25).round(2)
    df["FAIXA_TEMPO"] = df["TEMPO_RELACIONAMENTO_ANOS"].map(
        lambda v: _faixa(v, config.FAIXAS_TEMPO, config.ROTULO_TEMPO_INVALIDO)
    )

    validos = df["TEMPO_RELACIONAMENTO_ANOS"].dropna()
    logger.info(
        "Tempo de relacionamento: media %.1f anos, min %.1f, max %.1f (base %s)",
        validos.mean(),
        validos.min(),
        validos.max(),
        config.DATA_REFERENCIA.date(),
    )
    return df


def calcular_faixa_renda(df: pd.DataFrame) -> pd.DataFrame:
    """Enquadra a renda mensal nas quatro faixas do enunciado."""
    df = df.copy()
    df["FAIXA_RENDA"] = df["RENDA_MENSAL"].map(
        lambda v: _faixa(v, config.FAIXAS_RENDA, config.ROTULO_RENDA_NULA)
    )

    for faixa, n in df["FAIXA_RENDA"].value_counts().items():
        logger.info("    %-22s %4d associados", faixa, n)
    return df


def calcular_indice_movimentacao(df: pd.DataFrame) -> pd.DataFrame:
    """
    Constroi um indice unico de movimentacao financeira, de 0 a 100.

    Saldo medio, PIX e compras no cartao estao em escalas muito diferentes
    (centenas de milhares, dezenas, dezenas de milhares). Somar valores brutos
    faria o saldo dominar por acidente de unidade. Cada metrica e convertida no
    seu percentil dentro da base e depois ponderada, de modo que o peso seja uma
    decisao explicita e nao um efeito colateral da escala.
    """
    df = df.copy()

    for coluna, peso in config.PESOS_MOVIMENTACAO.items():
        df[f"PCT_{coluna}"] = df[coluna].rank(pct=True, na_option="keep")
        logger.info("    %-16s peso %.2f", coluna, peso)

    componentes = [df[f"PCT_{c}"] * p for c, p in config.PESOS_MOVIMENTACAO.items()]
    df["INDICE_MOVIMENTACAO"] = (sum(componentes) * 100).round(1)

    df = df.drop(columns=[f"PCT_{c}" for c in config.PESOS_MOVIMENTACAO])

    logger.info(
        "Indice de movimentacao: media %.1f, mediana %.1f",
        df["INDICE_MOVIMENTACAO"].mean(),
        df["INDICE_MOVIMENTACAO"].median(),
    )
    return df


def marcar_oportunidades(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sinaliza os dois grupos de oportunidade comercial da pagina 4 do dashboard.

    Sao flags booleanas para que o Power BI filtre sem precisar de DAX complexo.
    """
    df = df.copy()

    df["OPORT_CROSS_SELL"] = (
        df["RENDA_MENSAL"].ge(config.RENDA_ALTA_OPORTUNIDADE)
        & df["QTD_PRODUTOS"].le(config.MAX_PRODUTOS_OPORTUNIDADE)
    ).fillna(False)

    corte = df["INDICE_MOVIMENTACAO"].quantile(config.LIMITE_BAIXA_UTILIZACAO)
    df["OPORT_BAIXA_UTILIZACAO"] = df["INDICE_MOVIMENTACAO"].le(corte)

    logger.info(
        "Oportunidades: %d de cross-sell (renda >= R$ %s e ate %d produtos), %d de baixa utilizacao",
        int(df["OPORT_CROSS_SELL"].sum()),
        f"{config.RENDA_ALTA_OPORTUNIDADE:,.0f}".replace(",", "."),
        config.MAX_PRODUTOS_OPORTUNIDADE,
        int(df["OPORT_BAIXA_UTILIZACAO"].sum()),
    )
    return df


def criar_indicadores(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica todos os indicadores na ordem de dependencia."""
    logger.info("--- Quantidade de produtos ---")
    df = calcular_qtd_produtos(df)

    logger.info("--- Tempo de relacionamento ---")
    df = calcular_tempo_relacionamento(df)

    logger.info("--- Faixa de renda ---")
    df = calcular_faixa_renda(df)

    logger.info("--- Indice de movimentacao ---")
    df = calcular_indice_movimentacao(df)

    logger.info("--- Oportunidades ---")
    return marcar_oportunidades(df)
