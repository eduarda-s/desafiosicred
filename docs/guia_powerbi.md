# Guia de construção do dashboard

Roteiro para montar o dashboard executivo a partir de `data/processed/base_consolidada.xlsx`.

A base já chega com todos os indicadores e a classificação calculados em Python. **Não é necessário nenhum tratamento no Power Query** — a transformação é responsabilidade do pipeline, e o Power BI fica só com a camada de visualização.

---

## 1. Carregar os dados

1. *Obter dados* → *Pasta de trabalho do Excel* → `data/processed/base_consolidada.xlsx`
2. Selecionar apenas a aba **Base_Consolidada** → *Carregar* (não *Transformar*)
3. Conferir os tipos na visão de modelo:

| Campo | Tipo |
|---|---|
| `DATA_ASSOCIACAO` | Data |
| `RENDA_MENSAL`, `SALDO_MEDIO`, `COMPRAS_CARTAO`, `INDICE_MOVIMENTACAO`, `TEMPO_RELACIONAMENTO_ANOS` | Número decimal |
| `QTD_PRODUTOS`, `PIX_MENSAL`, `AGENCIA`, `SCORE_*` | Número inteiro |
| `CIDADE`, `AGENCIA_NOME`, `FAIXA_RENDA`, `FAIXA_TEMPO`, `CLASSIFICACAO` | Texto |
| `OPORT_*`, `DATA_VALIDA`, `RENDA_INFORMADA`, produtos | Verdadeiro/Falso |

### Ordenar as categorias corretamente

Por padrão o Power BI ordena texto em ordem alfabética, o que deixa a classificação como *Em Desenvolvimento → Engajado → Inicial → Maduro*. Sem sentido.

Crie uma coluna de ordenação (*Modelagem* → *Nova coluna*):

```dax
ORDEM_CLASSIFICACAO =
SWITCH(
    Base_Consolidada[CLASSIFICACAO],
    "Inicial", 1,
    "Em Desenvolvimento", 2,
    "Maduro", 3,
    "Engajado", 4,
    99
)
```

Depois selecione a coluna `CLASSIFICACAO` → *Classificar por coluna* → `ORDEM_CLASSIFICACAO`.

Faça o mesmo para as faixas:

```dax
ORDEM_FAIXA_RENDA =
SWITCH(
    Base_Consolidada[FAIXA_RENDA],
    "Até R$ 3.000", 1,
    "R$ 3.001 a R$ 8.000", 2,
    "R$ 8.001 a R$ 15.000", 3,
    "Acima de R$ 15.000", 4,
    99
)
```

```dax
ORDEM_FAIXA_TEMPO =
SWITCH(
    Base_Consolidada[FAIXA_TEMPO],
    "Menos de 2 anos", 1,
    "2 a 3 anos", 2,
    "3 a 5 anos", 3,
    "Mais de 5 anos", 4,
    99
)
```

---

## 2. Medidas

Crie uma tabela vazia chamada `_Medidas` (*Inserir dados* → salvar sem preencher) e coloque todas as medidas nela. Mantém o painel de campos organizado e é o padrão que se espera de um modelo profissional.

### Indicadores principais

```dax
Total de Associados = COUNTROWS(Base_Consolidada)
```

```dax
Renda Média = AVERAGE(Base_Consolidada[RENDA_MENSAL])
```

```dax
Saldo Médio = AVERAGE(Base_Consolidada[SALDO_MEDIO])
```

```dax
Produtos por Associado = AVERAGE(Base_Consolidada[QTD_PRODUTOS])
```

```dax
Tempo Médio de Relacionamento = AVERAGE(Base_Consolidada[TEMPO_RELACIONAMENTO_ANOS])
```

```dax
Índice Médio de Movimentação = AVERAGE(Base_Consolidada[INDICE_MOVIMENTACAO])
```

`AVERAGE` ignora nulos, então as 12 rendas não informadas e as 37 datas inconsistentes não distorcem as médias.

### Participação percentual

```dax
% de Associados =
DIVIDE(
    COUNTROWS(Base_Consolidada),
    CALCULATE(COUNTROWS(Base_Consolidada), REMOVEFILTERS(Base_Consolidada))
)
```

Formate como percentual com uma casa decimal. `REMOVEFILTERS` faz o denominador ser sempre o total da base, então a medida funciona em qualquer visual sem reescrita.

### Oportunidades

```dax
Associados Cross-Sell =
CALCULATE(
    COUNTROWS(Base_Consolidada),
    Base_Consolidada[OPORT_CROSS_SELL] = TRUE()
)
```

```dax
Associados Baixa Utilização =
CALCULATE(
    COUNTROWS(Base_Consolidada),
    Base_Consolidada[OPORT_BAIXA_UTILIZACAO] = TRUE()
)
```

```dax
Receita Potencial Cross-Sell =
CALCULATE(
    SUM(Base_Consolidada[RENDA_MENSAL]),
    Base_Consolidada[OPORT_CROSS_SELL] = TRUE()
)
```

### Qualidade dos dados

Vale expor no dashboard: mostra domínio sobre a base e é exatamente o tipo de cuidado que a avaliação procura.

```dax
Registros com Data Inconsistente =
CALCULATE(
    COUNTROWS(Base_Consolidada),
    Base_Consolidada[DATA_VALIDA] = FALSE()
)
```

```dax
Registros sem Renda Informada =
CALCULATE(
    COUNTROWS(Base_Consolidada),
    Base_Consolidada[RENDA_INFORMADA] = FALSE()
)
```

---

## 3. Páginas

### Página 1 — Visão Geral

Quatro cartões no topo, em linha:

| Cartão | Medida | Formato |
|---|---|---|
| Total de Associados | `Total de Associados` | Inteiro |
| Renda Média | `Renda Média` | R$ com 0 casas |
| Saldo Médio | `Saldo Médio` | R$ com 0 casas |
| Produtos por Associado | `Produtos por Associado` | 2 casas decimais |

Abaixo:

- **Rosca** — `CLASSIFICACAO` na legenda, `Total de Associados` nos valores. Dá o panorama imediato da carteira.
- **Colunas** — `QTD_PRODUTOS` no eixo, `Total de Associados` nos valores. Mostra a concentração em 2–3 produtos.
- **Colunas** — `FAIXA_RENDA` no eixo, `Total de Associados` nos valores.

Segmentações laterais: `AGENCIA_NOME`, `CIDADE`, `CLASSIFICACAO`. Sincronize-as entre as quatro páginas (*Exibir* → *Sincronizar segmentações*) para que o filtro persista na navegação.

### Página 2 — Relacionamento

- **Barras horizontais** — `AGENCIA_NOME` × `Total de Associados`
- **Barras horizontais** — `CIDADE` × `Total de Associados`, ordenado decrescente
- **Colunas** — `FAIXA_RENDA` × `Total de Associados`
- **Colunas** — `FAIXA_TEMPO` × `Total de Associados`
- **Cartão** — `Tempo Médio de Relacionamento`

Pato Branco deve aparecer com 433 associados. Se aparecer fragmentado em três barras, a base carregada é a bruta, não a tratada.

### Página 3 — Classificação

- **Rosca ou barras empilhadas 100%** — `CLASSIFICACAO` com `% de Associados`
- **Tabela** com uma linha por estágio:

| Coluna | Campo |
|---|---|
| Estágio | `CLASSIFICACAO` |
| Associados | `Total de Associados` |
| Participação | `% de Associados` |
| Produtos (média) | `Produtos por Associado` |
| Tempo médio | `Tempo Médio de Relacionamento` |
| Índice de movimentação | `Índice Médio de Movimentação` |
| Saldo médio | `Saldo Médio` |

Essa tabela é a prova visual de que a régua funciona: as colunas crescem de forma monotônica do Inicial ao Engajado.

- **Colunas agrupadas** — `AGENCIA_NOME` no eixo, `CLASSIFICACAO` na legenda. Revela se alguma agência concentra carteira imatura.
- **Cartões** com a contagem de cada estágio.

### Página 4 — Oportunidades

- **Cartões** — `Associados Cross-Sell` (177) e `Associados Baixa Utilização` (250)
- **Tabela de prospecção**, filtrada por `OPORT_CROSS_SELL = Verdadeiro`, ordenada por renda decrescente:

  `CHAVE`, `AGENCIA_NOME`, `CIDADE`, `RENDA_MENSAL`, `QTD_PRODUTOS`, `SALDO_MEDIO`, `CLASSIFICACAO`

- **Dispersão** — `RENDA_MENSAL` no eixo X, `QTD_PRODUTOS` no eixo Y, `CLASSIFICACAO` na legenda, `CHAVE` nos detalhes. O quadrante inferior direito (renda alta, poucos produtos) é a oportunidade, e o gráfico a torna óbvia sem precisar de explicação.
- **Matriz** — `FAIXA_RENDA` nas linhas, `QTD_PRODUTOS` nas colunas, `Total de Associados` nos valores, com formatação condicional. Mostra onde a carteira está subaproveitada.

---

## 4. Acabamento

O enunciado lista qualidade visual como diferencial. O que rende mais em menos tempo:

- **Tema consistente.** *Exibir* → *Temas* → escolher um e não misturar cores fora dele.
- **Títulos que afirmam, não rotulam.** "Pato Branco concentra 43% da carteira" vale mais que "Associados por Cidade".
- **Formatação de número.** Renda e saldo em R$ sem casas decimais; percentuais com uma casa. Número cru com seis dígitos e sem separador é o detalhe que mais denuncia pressa.
- **Alinhamento.** Cartões da mesma altura, gráficos alinhados na grade. *Formatar* → *Alinhar* resolve em segundos.
- **Uma caixa de texto** na página 1 registrando que os dados são fictícios e citando os tratamentos aplicados (433 registros de cidade unificados, 37 datas inconsistentes, 12 rendas não informadas). Transforma o tratamento — que de outro modo fica invisível no dashboard — em evidência de rigor.

---

## 5. Salvar

Salve como `dashboard/dashboard_associados.pbix` dentro do repositório e faça o commit.

O `.pbix` é binário e o Git vai versioná-lo inteiro a cada alteração. Para um projeto deste tamanho não é problema. Evite commitar dez versões seguidas do arquivo enquanto ajusta detalhe visual — deixe para commitar quando a página estiver pronta.
