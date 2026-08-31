# Análise de Relacionamento de Associados

Solução de BI que consolida três bases cadastrais, trata inconsistências, deriva indicadores de relacionamento e classifica cada associado em um estágio de maturidade, entregando o resultado em um dashboard executivo no Power BI.

> Os dados utilizados são fictícios e foram criados exclusivamente para fins de avaliação técnica. Não há qualquer relação com associados, clientes, colaboradores ou informações reais de pessoas físicas ou jurídicas.

---

## Objetivo

Transformar três planilhas desconectadas — cadastro, produtos contratados e movimentação financeira — em uma visão única e confiável do relacionamento de cada associado, capaz de responder três perguntas de negócio:

1. **Quem são nossos associados?** Distribuição por agência, cidade, faixa de renda e tempo de casa.
2. **Em que estágio de relacionamento cada um está?** Classificação em Inicial, Em Desenvolvimento, Maduro ou Engajado.
3. **Onde estão as oportunidades?** Associados com alta renda e poucos produtos, e associados com baixa utilização dos serviços.

## Tecnologias

| Ferramenta | Uso |
|---|---|
| Python 3.11 | Tratamento, consolidação e regras de negócio |
| pandas | Manipulação das bases |
| openpyxl | Leitura e escrita de Excel |
| Power BI Desktop | Dashboard executivo |
| Git | Versionamento |

## Estrutura do projeto

```
desafio-bi-associados/
├── data/
│   ├── raw/                      Base bruta, nunca alterada
│   │   └── teste_bi_base_crua.xlsx
│   └── processed/                Saída do pipeline
│       ├── base_consolidada.xlsx
│       └── base_consolidada.csv
├── src/
│   ├── config.py                 Parâmetros de negócio centralizados
│   ├── ingestao.py               Leitura e validação de estrutura
│   ├── tratamento.py             Qualidade, padronização e consolidação
│   ├── indicadores.py            Indicadores derivados
│   ├── classificacao.py          Régua de classificação
│   └── main.py                   Orquestração do pipeline
├── docs/
│   └── guia_powerbi.md           Medidas DAX e construção do dashboard
├── dashboard/
│   └── dashboard_associados.pbix
├── requirements.txt
└── README.md
```

A separação por responsabilidade é proposital: cada módulo faz uma coisa, e **nenhum número de negócio está escrito dentro da lógica**. Faixas de renda, pesos, cortes de score e limites de oportunidade vivem todos em `config.py`, então revisar a metodologia é ler um arquivo, e mudá-la não exige tocar no código.

---

## Como executar

```bash
git clone <url-do-repositorio>
cd desafio-bi-associados

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
python -m src.main
```

O pipeline lê `data/raw/teste_bi_base_crua.xlsx`, escreve `data/processed/base_consolidada.xlsx` e `.csv`, e imprime o relatório de qualidade no console. Leva poucos segundos.

Para o dashboard, abra `dashboard/dashboard_associados.pbix` no Power BI Desktop. Se a base tiver sido reprocessada, use *Atualizar* para recarregar.

---

## Tratamento dos dados

O relatório de qualidade é subproduto da execução: cada tratamento registra em log o que encontrou. O que a base bruta apresentou:

### Cidades gravadas em três grafias

`P. Branco` (165), `Pato Branco` (136) e `PATO BRANCO` (132) são a mesma cidade. Somadas representam **433 associados, 43% da base**.

Este é o tratamento de maior impacto do projeto. Sem ele, Pato Branco se fragmenta em três categorias e Cascavel (150) aparece como a maior cidade do dashboard — uma conclusão errada apresentada com confiança. A padronização remove acentos e pontuação, normaliza a caixa e mapeia contra uma tabela de grafias oficiais; qualquer cidade fora do mapa é registrada em log em vez de virar nulo silenciosamente.

### 37 datas de associação no futuro

A base traz associações datadas até dezembro de 2026, posteriores à data de referência. Produziriam tempo de relacionamento negativo e empurrariam esses associados artificialmente para o estágio Inicial.

São erros de cadastro. A data é anulada, o registro recebe `DATA_VALIDA = falso` e o associado permanece na base com pontuação neutra na dimensão tempo — não é punido por um erro que não cometeu, e também não ganha vantagem com ele.

### 12 rendas não informadas

Optou-se por **não imputar**. A renda alimenta diretamente a análise de oportunidade comercial ("alta renda com poucos produtos"); preencher pela mediana criaria associados de renda mediana que não existem e poderia incluí-los ou excluí-los de uma lista de prospecção por um número inventado. Os registros são sinalizados em `RENDA_INFORMADA` e recebem a faixa "Não informado". Média e mediana ignoram nulos naturalmente, então os indicadores agregados seguem corretos.

### Duplicidade: nenhuma encontrada

Verificaram-se linhas integralmente duplicadas e CHAVEs repetidas nas três bases. **Nenhuma ocorrência.** A verificação permanece no pipeline mesmo assim — é o que barra uma carga futura suja, e o log documenta que a checagem foi feita.

### Demais padronizações

- Produtos convertidos de `S`/`N` para booleano, com tolerância a variação de caixa e espaço; valor fora do domínio é registrado em log.
- `AGENCIA` mantida como código inteiro e duplicada em `AGENCIA_NOME` ("Agência 1"), para que o Power BI não a some por engano.
- Métricas de movimentação validadas como numéricas; negativos seriam anulados (não houve).
- Integridade referencial conferida nos dois sentidos: as três bases têm 1.000 registros e casam integralmente pela CHAVE, sem órfãos.

---

## Indicadores

| Indicador | Definição |
|---|---|
| `QTD_PRODUTOS` | Soma dos seis produtos ativos, de 0 a 6 |
| `TEMPO_RELACIONAMENTO_ANOS` | Anos entre a data de associação e a data de referência |
| `FAIXA_RENDA` | Até R$ 3.000 / R$ 3.001 a R$ 8.000 / R$ 8.001 a R$ 15.000 / Acima de R$ 15.000 |
| `FAIXA_TEMPO` | Menos de 2 anos / 2 a 3 / 3 a 5 / Mais de 5 |
| `INDICE_MOVIMENTACAO` | Índice 0–100 de movimentação financeira ponderada |

### Data de referência

O tempo de relacionamento é calculado contra uma data fixa (`2026-08-30`, em `config.py`) e não contra `datetime.today()`. Isso torna a base **reproduzível**: rodar o pipeline em outro dia gera exatamente o mesmo arquivo, e o Git mostra mudanças de regra em vez de ruído de calendário.

### Índice de movimentação

Saldo médio, PIX mensal e compras no cartão estão em escalas muito diferentes — centenas de milhares, dezenas e dezenas de milhares. Somar valores brutos faria o saldo dominar o índice **por acidente de unidade**, não por decisão.

Cada métrica é convertida no seu percentil dentro da base e depois ponderada:

```
INDICE_MOVIMENTACAO = (0,50 × pct(saldo médio)
                     + 0,25 × pct(PIX mensal)
                     + 0,25 × pct(compras cartão)) × 100
```

O saldo médio pesa mais por ser o indicador mais estável de relacionamento financeiro; PIX e cartão medem intensidade de uso corrente. Os pesos estão em `config.py` e são o ponto natural de discussão com a área de negócio.

---

## Regras de classificação

Modelo aditivo de pontuação em três dimensões, cada uma valendo de 0 a 3 pontos.

### Por que pontuação e não regra em cascata

Os critérios do enunciado se sobrepõem. Um associado com 5 produtos, 8 meses de casa e alta movimentação atende ao mesmo tempo à definição de **Maduro** (4+ produtos) e à de **Inicial** (menos de 2 anos). Numa cascata de `if/elif`, o estágio dele passa a depender da ordem em que as regras foram escritas — arbitrário e difícil de defender numa reunião.

O score resolve isso somando evidências: cada dimensão contribui com seu peso e o estágio final reflete o conjunto, não a primeira regra que casou.

### Dimensões

**Produtos** — quantos dos seis o associado tem

| Produtos ativos | Pontos |
|---|---|
| 0 a 1 | 0 |
| 2 a 3 | 1 |
| 4 a 5 | 2 |
| 6 | 3 |

**Tempo de relacionamento**

| Tempo | Pontos |
|---|---|
| Menos de 2 anos | 0 |
| 2 a 3 anos | 1 |
| 3 a 5 anos | 2 |
| Mais de 5 anos | 3 |

**Movimentação** — quartil do índice dentro da base

| Quartil | Pontos |
|---|---|
| Q1 (25% menores) | 0 |
| Q2 | 1 |
| Q3 | 2 |
| Q4 (25% maiores) | 3 |

O corte é relativo à própria base: "alta movimentação" só faz sentido em comparação com os demais associados, não contra um valor absoluto que envelheceria a cada nova carga.

Dimensão que não pode ser avaliada (data de associação inconsistente) recebe **1 ponto**, valor neutro.

### Estágios

| Score total | Estágio |
|---|---|
| 0 a 2 | Inicial |
| 3 a 4 | Em Desenvolvimento |
| 5 a 6 | Maduro |
| 7 a 9 | Engajado |

### Resultado

| Estágio | Associados | Participação | Produtos | Tempo | Índice mov. | Saldo médio |
|---|---:|---:|---:|---:|---:|---:|
| Inicial | 133 | 13,3% | 2,27 | 1,3 anos | 34,8 | R$ 67.715 |
| Em Desenvolvimento | 352 | 35,2% | 2,78 | 3,4 anos | 43,5 | R$ 100.113 |
| Maduro | 364 | 36,4% | 3,19 | 5,3 anos | 54,0 | R$ 140.146 |
| Engajado | 151 | 15,1% | 3,66 | 6,4 anos | 69,3 | R$ 186.131 |

**Validação da régua:** as três dimensões crescem de forma monotônica do Inicial ao Engajado, e o saldo médio — que não entra no score em valor absoluto, apenas via percentil — acompanha, quase triplicando entre as pontas. A distribuição concentra a maioria nos estágios intermediários e afunila nos extremos, comportamento esperado de um modelo aditivo bem calibrado.

A renda média, por outro lado, é praticamente estável entre os estágios (R$ 15,4 mil a R$ 16,1 mil). Isso é **intencional e desejável**: renda não entra na classificação. É justamente essa independência que dá sentido à análise de oportunidade — se renda alta já implicasse estágio avançado, "alta renda com poucos produtos" seria um grupo vazio.

---

## Oportunidades comerciais

| Flag | Critério | Associados |
|---|---|---:|
| `OPORT_CROSS_SELL` | Renda acima de R$ 15.000 e no máximo 2 produtos | 177 |
| `OPORT_BAIXA_UTILIZACAO` | Índice de movimentação no quartil inferior | 250 |

São colunas booleanas na base consolidada, para que o dashboard filtre sem depender de DAX complexo.

---

## Saída

`data/processed/base_consolidada.xlsx` com três abas:

- **Base_Consolidada** — 1.000 associados, 30 colunas, pronta para o Power BI sem passar por Power Query.
- **Resumo_Classificacao** — perfil médio de cada estágio.
- **Dicionario** — descrição de cada campo.

O mesmo conteúdo é gravado em CSV. O motivo é prático: diff de Git em arquivo binário não diz nada, e com o CSV dá para ver no histórico exatamente o que mudou na base a cada ajuste de regra.

---

## Dashboard

Quatro páginas, detalhadas em [`docs/guia_powerbi.md`](docs/guia_powerbi.md):

1. **Visão Geral** — total de associados, renda média, saldo médio, produtos por associado.
2. **Relacionamento** — distribuição por agência, cidade, faixa de renda e tempo de casa.
3. **Classificação** — os quatro estágios com participação percentual e quantitativa.
4. **Oportunidades** — alta renda com poucos produtos, baixa utilização e potencial de crescimento.
