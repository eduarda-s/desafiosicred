"""
Classificacao dos associados em estagios de relacionamento.

Metodologia: modelo aditivo de pontuacao em tres dimensoes.

    SCORE_PRODUTOS   0 a 3  (quantos dos seis produtos o associado tem)
    SCORE_TEMPO      0 a 3  (ha quanto tempo e associado)
    SCORE_MOVIMENTO  0 a 3  (quartil do indice de movimentacao)
    ------------------------------------------------------------------
    SCORE_TOTAL      0 a 9  ->  Inicial | Em Desenvolvimento | Maduro | Engajado

Por que pontuacao e nao regra em cascata: os criterios do enunciado se
sobrepoem. Um associado com 5 produtos, 8 meses de casa e alta movimentacao
atende simultaneamente a definicao de 'Maduro' (4+ produtos) e de 'Inicial'
(menos de 2 anos). Numa cascata de if/elif o resultado dele passa a depender da
ordem em que as regras foram escritas, o que e arbitrario e dificil de defender.
O score resolve isso somando evidencias: cada dimensao contribui com o seu peso
e o estagio final reflete o conjunto, nao a primeira regra que casou.
"""

import logging

import pandas as pd

from . import config

logger = logging.getLogger(__name__)


def _pontuar(valor: float, tabela: list[tuple[float, int]], neutro: int) -> int:
    """Aplica a tabela de pontos; devolve pontuacao neutra se o valor for nulo."""
    if pd.isna(valor):
        return neutro
    for limite, pontos in tabela:
        if valor <= limite:
            return pontos
    return tabela[-1][1]


def pontuar_produtos(df: pd.DataFrame) -> pd.Series:
    """0 a 3 pontos conforme a quantidade de produtos ativos."""
    return df["QTD_PRODUTOS"].map(
        lambda v: _pontuar(v, config.PONTOS_PRODUTOS, config.PONTOS_NEUTROS)
    )


def pontuar_tempo(df: pd.DataFrame) -> pd.Series:
    """
    0 a 3 pontos conforme o tempo de relacionamento.

    Data invalida recebe pontuacao neutra: o associado nao e punido por um erro
    de cadastro que nao cometeu, e tambem nao ganha vantagem com ele.
    """
    return df["TEMPO_RELACIONAMENTO_ANOS"].map(
        lambda v: _pontuar(v, config.PONTOS_TEMPO, config.PONTOS_NEUTROS)
    )


def pontuar_movimentacao(df: pd.DataFrame) -> pd.Series:
    """
    0 a 3 pontos conforme o quartil do indice de movimentacao.

    O corte e relativo a propria base: 'alta movimentacao' so faz sentido em
    comparacao com os demais associados, nao contra um valor absoluto que
    envelheceria a cada nova carga.
    """
    cortes = df["INDICE_MOVIMENTACAO"].quantile(config.QUARTIS_MOVIMENTACAO).tolist()

    for i, corte in enumerate(cortes, start=1):
        logger.info("    Q%d do indice de movimentacao: %.1f", i, corte)

    def pontos(valor: float) -> int:
        if pd.isna(valor):
            return config.PONTOS_NEUTROS
        return sum(valor > corte for corte in cortes)

    return df["INDICE_MOVIMENTACAO"].map(pontos)


def classificar_score(score: int) -> str:
    """Traduz o score total (0 a 9) no rotulo do estagio de relacionamento."""
    for limite, estagio in config.CORTES_CLASSIFICACAO:
        if score <= limite:
            return estagio
    return config.CORTES_CLASSIFICACAO[-1][1]


def classificar(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula as tres pontuacoes, o score total e o estagio de cada associado."""
    df = df.copy()

    df["SCORE_PRODUTOS"] = pontuar_produtos(df)
    df["SCORE_TEMPO"] = pontuar_tempo(df)
    df["SCORE_MOVIMENTACAO"] = pontuar_movimentacao(df)

    df["SCORE_TOTAL"] = (
        df["SCORE_PRODUTOS"] + df["SCORE_TEMPO"] + df["SCORE_MOVIMENTACAO"]
    ).astype(int)

    df["CLASSIFICACAO"] = df["SCORE_TOTAL"].map(classificar_score)
    df["CLASSIFICACAO"] = pd.Categorical(
        df["CLASSIFICACAO"], categories=config.ORDEM_CLASSIFICACAO, ordered=True
    )

    logger.info("Distribuicao do score total:")
    for score, n in df["SCORE_TOTAL"].value_counts().sort_index().items():
        logger.info("    score %d: %4d associados", score, n)

    logger.info("Distribuicao da classificacao:")
    for estagio in config.ORDEM_CLASSIFICACAO:
        n = int((df["CLASSIFICACAO"] == estagio).sum())
        logger.info("    %-20s %4d associados (%.1f%%)", estagio, n, 100 * n / len(df))

    return df


def resumo_por_estagio(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perfil medio de cada estagio.

    Serve de validacao da regua: se os estagios nao ficarem monotonicos em
    produtos, tempo e movimentacao, a metodologia esta furada.
    """
    resumo = (
        df.groupby("CLASSIFICACAO", observed=True)
        .agg(
            ASSOCIADOS=("CHAVE", "count"),
            PRODUTOS_MEDIO=("QTD_PRODUTOS", "mean"),
            TEMPO_MEDIO_ANOS=("TEMPO_RELACIONAMENTO_ANOS", "mean"),
            INDICE_MOVIMENTACAO_MEDIO=("INDICE_MOVIMENTACAO", "mean"),
            RENDA_MEDIA=("RENDA_MENSAL", "mean"),
            SALDO_MEDIO=("SALDO_MEDIO", "mean"),
        )
        .round(2)
        .reset_index()
    )
    resumo["PARTICIPACAO_PCT"] = (100 * resumo["ASSOCIADOS"] / len(df)).round(1)
    return resumo
