"""
Tratamento e qualidade dos dados.

Cada funcao trata um problema especifico e registra em log o que encontrou,
para que o relatorio de qualidade seja subproduto natural da execucao e nao
uma auditoria manual posterior.
"""

import logging
import unicodedata

import pandas as pd

from . import config

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Duplicidade
# --------------------------------------------------------------------------- #

def remover_duplicados(df: pd.DataFrame, nome: str) -> pd.DataFrame:
    """
    Remove linhas integralmente duplicadas e chaves repetidas.

    A base fornecida nao apresentou duplicidade, mas a verificacao permanece
    no pipeline: e o que garante que uma carga futura suja seja barrada.
    Em caso de CHAVE repetida mantem-se o primeiro registro.
    """
    n_inicial = len(df)

    linhas_dup = int(df.duplicated().sum())
    if linhas_dup:
        df = df.drop_duplicates()
        logger.warning("[%s] %d linhas integralmente duplicadas removidas", nome, linhas_dup)
    else:
        logger.info("[%s] nenhuma linha duplicada encontrada", nome)

    chaves_dup = int(df[config.CHAVE].duplicated().sum())
    if chaves_dup:
        df = df.drop_duplicates(subset=[config.CHAVE], keep="first")
        logger.warning(
            "[%s] %d CHAVEs repetidas - mantido o primeiro registro de cada", nome, chaves_dup
        )
    else:
        logger.info("[%s] nenhuma CHAVE repetida encontrada", nome)

    if len(df) != n_inicial:
        logger.info("[%s] %d -> %d linhas apos deduplicacao", nome, n_inicial, len(df))

    return df.reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Padronizacao de texto
# --------------------------------------------------------------------------- #

def _normalizar(texto: str) -> str:
    """Remove acentos, pontuacao e espacos extras; devolve em caixa alta."""
    if pd.isna(texto):
        return ""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", str(texto)) if not unicodedata.combining(c)
    )
    return " ".join(sem_acento.replace(".", " ").split()).upper()


def padronizar_cidades(df: pd.DataFrame) -> pd.DataFrame:
    """
    Unifica as grafias divergentes de CIDADE.

    Este e o tratamento de maior impacto da base: Pato Branco aparecia como
    'P. Branco', 'Pato Branco' e 'PATO BRANCO'. Sem a unificacao, a cidade se
    fragmenta em tres categorias no dashboard e some do topo do ranking.
    """
    df = df.copy()
    antes = df["CIDADE"].nunique()

    chave_norm = df["CIDADE"].map(_normalizar)
    nao_mapeadas = sorted(set(chave_norm) - set(config.MAPA_CIDADES))
    if nao_mapeadas:
        logger.warning("Cidades sem regra de padronizacao: %s", nao_mapeadas)

    # Cidade desconhecida cai no fallback Title Case em vez de virar nulo.
    df["CIDADE"] = chave_norm.map(config.MAPA_CIDADES).fillna(chave_norm.str.title())

    depois = df["CIDADE"].nunique()
    logger.info("Cidades padronizadas: %d grafias distintas -> %d cidades", antes, depois)
    for cidade, qtd in df["CIDADE"].value_counts().items():
        logger.info("    %-14s %4d associados", cidade, qtd)

    return df


def padronizar_produtos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converte os marcadores S/N em booleanos.

    Aceita variacoes de caixa e espaco. Qualquer valor fora do dominio
    esperado e tratado como ausencia do produto e registrado em log.
    """
    df = df.copy()

    for coluna in config.COLUNAS_PRODUTOS:
        normalizado = df[coluna].map(_normalizar)
        invalidos = ~normalizado.isin({"S", "N"})
        if invalidos.any():
            logger.warning(
                "Coluna %s possui %d valores fora do dominio S/N: %s",
                coluna,
                int(invalidos.sum()),
                sorted(set(normalizado[invalidos]))[:5],
            )
        df[coluna] = normalizado.eq("S")

    logger.info("Colunas de produto convertidas para booleano (%d colunas)", len(config.COLUNAS_PRODUTOS))
    return df


def padronizar_agencia(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cria um rotulo textual para a agencia.

    AGENCIA e um codigo, nao uma quantidade. Mantida como inteiro para
    ordenacao e duplicada em texto para que o Power BI nao a some por engano.
    """
    df = df.copy()
    df["AGENCIA"] = df["AGENCIA"].astype(int)
    df["AGENCIA_NOME"] = "Agencia " + df["AGENCIA"].astype(str)
    logger.info("Rotulo de agencia criado (%d agencias distintas)", df["AGENCIA"].nunique())
    return df


# --------------------------------------------------------------------------- #
# Valores nulos e inconsistentes
# --------------------------------------------------------------------------- #

def tratar_renda(df: pd.DataFrame) -> pd.DataFrame:
    """
    Marca os registros sem renda informada em vez de imputar um valor.

    Decisao deliberada: a renda alimenta a analise de oportunidade comercial
    ('alta renda com poucos produtos'). Imputar pela mediana criaria associados
    de renda mediana que nao existem e poderia inclui-los ou exclui-los da lista
    de prospeccao por um numero inventado. Media e mediana ignoram nulos
    naturalmente, entao os indicadores agregados seguem corretos.
    """
    df = df.copy()

    nulos = int(df["RENDA_MENSAL"].isna().sum())
    df["RENDA_INFORMADA"] = df["RENDA_MENSAL"].notna()

    negativos = int((df["RENDA_MENSAL"] <= 0).sum())
    if negativos:
        logger.warning("%d rendas menores ou iguais a zero convertidas em nulo", negativos)
        df.loc[df["RENDA_MENSAL"] <= 0, "RENDA_MENSAL"] = pd.NA
        df["RENDA_INFORMADA"] = df["RENDA_MENSAL"].notna()

    logger.info(
        "Renda: %d nulos (%.1f%%) preservados e sinalizados em RENDA_INFORMADA",
        nulos,
        100 * nulos / len(df),
    )
    return df


def tratar_datas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Invalida datas de associacao posteriores a data de referencia.

    A base bruta traz associacoes datadas ate dezembro de 2026, o que produziria
    tempo de relacionamento negativo. Sao erros de cadastro: a data e anulada e
    o registro sinalizado, preservando o associado nas demais analises.
    """
    df = df.copy()
    df["DATA_ASSOCIACAO"] = pd.to_datetime(df["DATA_ASSOCIACAO"], errors="coerce")

    ilegiveis = int(df["DATA_ASSOCIACAO"].isna().sum())
    if ilegiveis:
        logger.warning("%d datas de associacao ilegiveis", ilegiveis)

    futuras = df["DATA_ASSOCIACAO"] > config.DATA_REFERENCIA
    n_futuras = int(futuras.sum())
    if n_futuras:
        logger.warning(
            "%d datas de associacao posteriores a %s anuladas (erro de cadastro)",
            n_futuras,
            config.DATA_REFERENCIA.date(),
        )
        df.loc[futuras, "DATA_ASSOCIACAO"] = pd.NaT

    df["DATA_VALIDA"] = df["DATA_ASSOCIACAO"].notna()
    logger.info(
        "Datas: %d validas, %d inconsistentes (%.1f%%)",
        int(df["DATA_VALIDA"].sum()),
        int((~df["DATA_VALIDA"]).sum()),
        100 * int((~df["DATA_VALIDA"]).sum()) / len(df),
    )
    return df


def tratar_movimentacao(df: pd.DataFrame) -> pd.DataFrame:
    """Garante tipo numerico e substitui negativos por nulo nas metricas de uso."""
    df = df.copy()

    for coluna in config.COLUNAS_MOVIMENTACAO:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
        negativos = int((df[coluna] < 0).sum())
        if negativos:
            logger.warning("%s: %d valores negativos convertidos em nulo", coluna, negativos)
            df.loc[df[coluna] < 0, coluna] = pd.NA
        nulos = int(df[coluna].isna().sum())
        if nulos:
            logger.warning("%s: %d valores nulos", coluna, nulos)

    logger.info("Movimentacao validada (%d colunas)", len(config.COLUNAS_MOVIMENTACAO))
    return df


# --------------------------------------------------------------------------- #
# Consolidacao
# --------------------------------------------------------------------------- #

def consolidar(bases: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Junta as tres bases pela CHAVE.

    Usa left join a partir de Associados: o cadastro e a fonte da verdade sobre
    quem existe. Produto ou movimentacao ausentes viram nulo e sao reportados,
    em vez de fazerem o associado desaparecer da base.
    """
    associados = bases["associados"]
    produtos = bases["produtos"]
    movimentacao = bases["movimentacao"]

    chaves_assoc = set(associados[config.CHAVE])
    orfaos_prod = set(produtos[config.CHAVE]) - chaves_assoc
    orfaos_mov = set(movimentacao[config.CHAVE]) - chaves_assoc

    if orfaos_prod:
        logger.warning("%d CHAVEs em Produtos sem cadastro correspondente", len(orfaos_prod))
    if orfaos_mov:
        logger.warning("%d CHAVEs em Movimentacao sem cadastro correspondente", len(orfaos_mov))

    df = associados.merge(produtos, on=config.CHAVE, how="left", validate="one_to_one")
    df = df.merge(movimentacao, on=config.CHAVE, how="left", validate="one_to_one")

    sem_produtos = int(df[config.COLUNAS_PRODUTOS[0]].isna().sum())
    sem_mov = int(df[config.COLUNAS_MOVIMENTACAO[0]].isna().sum())
    if sem_produtos:
        logger.warning("%d associados sem registro em Produtos", sem_produtos)
    if sem_mov:
        logger.warning("%d associados sem registro em Movimentacao", sem_mov)

    logger.info("Base consolidada: %d associados x %d colunas", len(df), df.shape[1])
    return df


def tratar(bases: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Orquestra o tratamento das tres bases e devolve a base consolidada."""
    logger.info("--- Deduplicacao ---")
    bases = {nome: remover_duplicados(df, nome) for nome, df in bases.items()}

    logger.info("--- Padronizacao e nulos ---")
    associados = padronizar_cidades(bases["associados"])
    associados = padronizar_agencia(associados)
    associados = tratar_renda(associados)
    associados = tratar_datas(associados)

    produtos = padronizar_produtos(bases["produtos"])
    movimentacao = tratar_movimentacao(bases["movimentacao"])

    logger.info("--- Consolidacao ---")
    return consolidar(
        {"associados": associados, "produtos": produtos, "movimentacao": movimentacao}
    )
