- Análise de Relacionamento de Associados

Projeto desenvolvido para o Desafio Técnico de Assistente de BI.

O objetivo é consolidar e analisar dados cadastrais, produtos contratados e movimentações financeiras de associados, utilizando Python para tratamento dos dados e Power BI para construção do dashboard.

Os dados utilizados no projeto são fictícios e foram disponibilizados exclusivamente para a realização do desafio técnico.

-- Objetivo

O projeto busca transformar as três bases fornecidas em uma base consolidada que permita analisar o perfil e o relacionamento dos associados.

As principais análises realizadas são:

- Distribuição dos associados por agência e cidade;
- Faixa de renda;
- Tempo de relacionamento;
- Quantidade de produtos contratados;
- Movimentação financeira;
- Classificação do nível de relacionamento;
- Identificação de oportunidades de cross-sell;
- Identificação de associados com baixa utilização dos serviços.

-- Tecnologias utilizadas

- Python 3
- Pandas
- OpenPyXL
- Excel
- Power BI Desktop
- Git e GitHub

-- Estrutura do projeto

desafio-bi-associados/

data/
- raw/ - base original disponibilizada para o desafio
- processed/ - bases geradas após o tratamento

src/
- config.py - configurações e parâmetros utilizados nas regras
- ingestao.py - leitura e validação das bases
- tratamento.py - tratamento e padronização dos dados
- indicadores.py - criação dos indicadores
- classificacao.py - classificação dos associados
- main.py - execução do processo completo

docs/
- guia_powerbi.md - documentação utilizada para construção do dashboard

dashboard/
- dashboard_associados.pbix - dashboard final desenvolvido no Power BI

requirements.txt - bibliotecas necessárias para executar o projeto

README.md - documentação do projeto

-- Tratamento dos dados

O tratamento das bases foi realizado em Python.

As três bases foram consolidadas utilizando a CHAVE do associado.

Durante o processo foram realizadas verificações e tratamentos de:

- Registros duplicados;
- Valores nulos;
- Padronização de textos;
- Tipos de dados;
- Datas inconsistentes;
- Integridade entre as três bases;
- Valores numéricos inválidos.

Também foram encontradas diferentes formas de representar a cidade de Pato Branco, como "P. Branco", "Pato Branco" e "PATO BRANCO". Esses valores foram padronizados para evitar que a mesma cidade aparecesse como categorias diferentes nas análises.

Foram identificadas 37 datas de associação posteriores à data de referência utilizada pelo projeto. Essas datas foram consideradas inválidas para o cálculo do tempo de relacionamento.

Também foram encontradas 12 rendas não informadas. Esses valores não foram preenchidos artificialmente. Os registros foram mantidos como "Não informado" para evitar interferência nas análises de renda e nas oportunidades comerciais.

Não foram encontradas CHAVEs duplicadas nas bases fornecidas.

-- Indicadores criados

Foram criados indicadores adicionais para auxiliar as análises no Power BI.

*Quantidade de produtos*

Representa a quantidade de produtos ativos de cada associado, considerando:

- Conta corrente;
- Cartão;
- Crédito;
- Investimento;
- Consórcio;
- Seguro.

O indicador varia de 0 a 6 produtos.

*Tempo de relacionamento*

Calculado a partir da diferença entre a data de associação e a data de referência utilizada no projeto.

Os associados foram separados nas seguintes faixas:

- Menos de 2 anos;
- 2 a 3 anos;
- 3 a 5 anos;
- Mais de 5 anos.

*Faixa de renda*

Os associados foram divididos nas seguintes faixas:

- Até R$ 3.000;
- R$ 3.001 a R$ 8.000;
- R$ 8.001 a R$ 15.000;
- Acima de R$ 15.000;
- Não informado.

*Índice de movimentação*

Foi criado um indicador para representar o nível de movimentação financeira do associado.

O cálculo considera:

- 50% saldo médio;
- 25% quantidade de PIX mensal;
- 25% compras no cartão.

Como esses indicadores possuem escalas diferentes, cada variável é convertida em percentil antes da aplicação dos pesos.

O resultado é um índice entre 0 e 100.

-- Classificação dos associados

Para classificar os associados foi criado um sistema de pontuação baseado em três dimensões:

- Quantidade de produtos;
- Tempo de relacionamento;
- Movimentação financeira.

Cada dimensão pode gerar de 0 a 3 pontos.

*Produtos*

- 0 ou 1 produto: 0 pontos
- 2 ou 3 produtos: 1 ponto
- 4 ou 5 produtos: 2 pontos
- 6 produtos: 3 pontos

*Tempo de relacionamento*

- Menos de 2 anos: 0 pontos
- 2 a 3 anos: 1 ponto
- 3 a 5 anos: 2 pontos
- Mais de 5 anos: 3 pontos

*Movimentação*

A pontuação de movimentação utiliza os quartis do índice de movimentação:

- Primeiro quartil: 0 pontos
- Segundo quartil: 1 ponto
- Terceiro quartil: 2 pontos
- Quarto quartil: 3 pontos

A soma das três dimensões gera o SCORE_TOTAL, que varia de 0 a 9.

A classificação final é:

- 0 a 2 pontos: Inicial
- 3 a 4 pontos: Em Desenvolvimento
- 5 a 6 pontos: Maduro
- 7 a 9 pontos: Engajado

-- Resultado da classificação

A base consolidada possui 1.000 associados.

A classificação obtida foi:

- Inicial: 133 associados (13,3%)
- Em Desenvolvimento: 352 associados (35,2%)
- Maduro: 364 associados (36,4%)
- Engajado: 151 associados (15,1%)

A média do score e a quantidade média de produtos aumentam conforme o nível de relacionamento, o que ajuda a verificar o comportamento da regra de classificação.

-- Oportunidades

Também foram criadas duas regras para identificação de oportunidades.

*Cross-sell*

Associados com renda acima de R$ 15.000 e no máximo 2 produtos contratados.

Foram identificados 177 associados nessa situação.

A flag criada na base é OPORT_CROSS_SELL.

*Baixa utilização*

Associados que estão no quartil inferior do índice de movimentação.

Foram identificados 250 associados nessa situação.

A flag criada na base é OPORT_BAIXA_UTILIZACAO.

Essas flags são disponibilizadas diretamente na base consolidada e utilizadas como filtros no Power BI.

-- Base consolidada

O processo gera o arquivo:

data/processed/base_consolidada.xlsx

O arquivo possui três abas:

- Base_Consolidada - base utilizada no Power BI;
- Resumo_Classificacao - resumo dos indicadores por classificação;
- Dicionario - descrição dos campos da base.

Também é gerada uma versão em CSV.

-- Dashboard

O dashboard foi desenvolvido no Power BI e dividido em quatro páginas.

*Visão Geral*

Apresenta os principais indicadores:

- Total de associados;
- Renda média;
- Produtos por associado;
- Saldo médio;
- Distribuição por classificação;
- Quantidade de produtos;
- Faixa de renda.

*Relacionamento*

Apresenta:

- Associados por agência;
- Associados por cidade;
- Faixa de renda;
- Tempo de relacionamento.

*Classificação*

Apresenta:

- Quantidade de associados em cada classificação;
- Participação percentual;
- Score médio por classificação;
- Média de produtos por classificação.

*Oportunidades*

Apresenta:

- Quantidade de oportunidades de cross-sell;
- Quantidade de associados com baixa utilização;
- Cross-sell por faixa de renda;
- Baixa utilização por classificação;
- Tabela para identificação dos associados e suas oportunidades.

O arquivo está disponível em:

dashboard/dashboard_associados.pbix

-- Como executar

Clone o repositório:

git clone https://github.com/eduarda-s/desafiosicred.git

Entre na pasta do projeto:

cd desafiosicred

Crie o ambiente virtual:

python -m venv .venv

No Windows:

.venv\Scripts\activate

Instale as dependências:

pip install -r requirements.txt

Execute o processamento:

python -m src.main

Após a execução, a base consolidada será gerada na pasta data/processed.

Para visualizar o dashboard, abra dashboard/dashboard_associados.pbix no Power BI Desktop.

Caso a base seja processada novamente, utilize a opção Atualizar no Power BI para carregar os novos dados.
