"""
Pipeline completo: base bruta -> base consolidada pronta para o Power BI.

Uso:
    python -m src.main
"""

import logging
import sys

import pandas as pd

from . import classificacao, config, indicadores, ingestao, tratamento

logger = logging.getLogger(__name__)

# Ordem das colunas na base final: identificacao, cadastro, produtos,
# movimentacao, indicadores, classificacao, oportunidades.
COLUNAS_SAIDA = [
    "CHAVE",
    "NOME",
    "AGENCIA",
    "AGENCIA_NOME",
    "CIDADE",
    "DATA_ASSOCIACAO",
    "DATA_VALIDA",
    "RENDA_MENSAL",
    "RENDA_INFORMADA",
    *config.COLUNAS_PRODUTOS,
    *config.COLUNAS_MOVIMENTACAO,
    "QTD_PRODUTOS",
    "TEMPO_RELACIONAMENTO_ANOS",
    "FAIXA_TEMPO",
    "FAIXA_RENDA",
    "INDICE_MOVIMENTACAO",
    "SCORE_PRODUTOS",
    "SCORE_TEMPO",
    "SCORE_MOVIMENTACAO",
    "SCORE_TOTAL",
    "CLASSIFICACAO",
    "OPORT_CROSS_SELL",
    "OPORT_BAIXA_UTILIZACAO",
]


def configurar_log() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )


def exportar(df: pd.DataFrame, resumo: pd.DataFrame) -> None:
    """
    Grava a base consolidada em Excel (com abas de apoio) e em CSV.

    O CSV existe porque diffs de Git em arquivo binario nao dizem nada; com ele
    da para ver no historico o que mudou na base a cada alteracao de regra.
    """
    config.DIR_DADOS_TRATADOS.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(config.ARQUIVO_SAIDA_XLSX, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Base_Consolidada", index=False)
        resumo.to_excel(writer, sheet_name="Resumo_Classificacao", index=False)
        _dicionario().to_excel(writer, sheet_name="Dicionario", index=False)

    df.to_csv(config.ARQUIVO_SAIDA_CSV, index=False, encoding="utf-8-sig")

    logger.info("Base gravada em %s", config.ARQUIVO_SAIDA_XLSX.relative_to(config.RAIZ))
    logger.info("Base gravada em %s", config.ARQUIVO_SAIDA_CSV.relative_to(config.RAIZ))


def _dicionario() -> pd.DataFrame:
    """Dicionario de dados embutido na propria planilha de saida."""
    campos = [
        ("CHAVE", "Identificador unico do associado"),
        ("NOME", "Nome do associado (dado ficticio, sem valor analitico)"),
        ("AGENCIA", "Codigo numerico da agencia"),
        ("AGENCIA_NOME", "Rotulo textual da agencia, para uso no dashboard"),
        ("CIDADE", "Cidade do associado, ja padronizada"),
        ("DATA_ASSOCIACAO", "Data de entrada; nula quando o cadastro era inconsistente"),
        ("DATA_VALIDA", "Falso quando a data original era posterior a data de referencia"),
        ("RENDA_MENSAL", "Renda mensal declarada; nula quando nao informada"),
        ("RENDA_INFORMADA", "Falso quando a renda nao foi informada"),
        ("CONTA_CORRENTE a SEGURO", "Posse do produto (verdadeiro ou falso)"),
        ("SALDO_MEDIO", "Saldo medio mantido pelo associado"),
        ("PIX_MENSAL", "Quantidade de PIX por mes"),
        ("COMPRAS_CARTAO", "Valor de compras no cartao"),
        ("QTD_PRODUTOS", "Total de produtos ativos, de 0 a 6"),
        ("TEMPO_RELACIONAMENTO_ANOS", f"Anos desde a associacao ate {config.DATA_REFERENCIA.date()}"),
        ("FAIXA_TEMPO", "Faixa de tempo de relacionamento"),
        ("FAIXA_RENDA", "Faixa de renda mensal"),
        ("INDICE_MOVIMENTACAO", "Indice 0-100 de movimentacao financeira ponderada"),
        ("SCORE_PRODUTOS", "Pontuacao 0-3 por quantidade de produtos"),
        ("SCORE_TEMPO", "Pontuacao 0-3 por tempo de relacionamento"),
        ("SCORE_MOVIMENTACAO", "Pontuacao 0-3 por quartil de movimentacao"),
        ("SCORE_TOTAL", "Soma das tres pontuacoes, de 0 a 9"),
        ("CLASSIFICACAO", "Estagio: Inicial, Em Desenvolvimento, Maduro ou Engajado"),
        ("OPORT_CROSS_SELL", "Alta renda com poucos produtos"),
        ("OPORT_BAIXA_UTILIZACAO", "Movimentacao no quartil inferior da base"),
    ]
    return pd.DataFrame(campos, columns=["CAMPO", "DESCRICAO"])


def executar() -> pd.DataFrame:
    """Roda o pipeline de ponta a ponta e devolve a base final."""
    logger.info("=" * 70)
    logger.info("PIPELINE BI - RELACIONAMENTO DE ASSOCIADOS")
    logger.info("Data de referencia: %s", config.DATA_REFERENCIA.date())
    logger.info("=" * 70)

    logger.info(">>> ETAPA 1/5 - Ingestao")
    bases = ingestao.carregar_bases()

    logger.info(">>> ETAPA 2/5 - Tratamento e qualidade")
    df = tratamento.tratar(bases)

    logger.info(">>> ETAPA 3/5 - Indicadores")
    df = indicadores.criar_indicadores(df)

    logger.info(">>> ETAPA 4/5 - Classificacao")
    df = classificacao.classificar(df)
    resumo = classificacao.resumo_por_estagio(df)

    logger.info(">>> ETAPA 5/5 - Exportacao")
    df = df[COLUNAS_SAIDA]
    exportar(df, resumo)

    logger.info("=" * 70)
    logger.info("CONCLUIDO - %d associados, %d colunas", len(df), df.shape[1])
    logger.info("=" * 70)

    return df


if __name__ == "__main__":
    configurar_log()
    executar()
