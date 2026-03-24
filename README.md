# 🏪 Sistema de Controle de Estoque - Confeitaria

Sistema completo de gerenciamento de estoque com metodologia **FEFO (First Expired, First Out)** desenvolvido em Python e PostgreSQL.

## 📋 Sobre o Projeto

Sistema desenvolvido para controle de estoque de confeitaria, com foco em minimizar desperdícios através da metodologia FEFO, que prioriza o uso de produtos próximos ao vencimento.

### 🎯 Funcionalidades Principais

✅ **Entrada de Estoque**
- Registro de compras com data de validade
- Controle de lotes por fornecedor
- Histórico completo de entradas

✅ **Saída de Estoque (FEFO Automático)**
- Sistema usa automaticamente o lote que vence primeiro
- Previne desperdício por vencimento
- Rastreabilidade completa

✅ **Sistema de Alertas**
- Produtos próximos ao vencimento
- Estoque abaixo do mínimo
- Sugestões automáticas de compra

✅ **Relatórios e Análises**
- Consumo por ingrediente
- Valor do estoque
- Giro de estoque
- Taxa de desperdício

---

## 🗄️ Modelo de Dados

### Principais Tabelas

- **ingredientes**: Catálogo de produtos
- **fornecedores**: Cadastro de fornecedores
- **lotes_estoque**: Controle de lotes com validade
- **movimentacoes**: Histórico de entradas/saídas
- **receitas**: Receitas da confeitaria

### Views Analíticas

- `v_estoque_atual`: Visão consolidada do estoque
- `v_alertas_validade`: Produtos próximos ao vencimento

## 📂 Estrutura do Projeto
```
controle-estoque-confeitaria/
├── data/
│   └── exports/              # Relatórios exportados
├── src/
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py     # Conexão com PostgreSQL
│   ├── services/
│   │   ├── __init__.py
│   │   ├── entrada_estoque.py   # Registro de compras
│   │   ├── saida_estoque.py     # Saídas com FEFO
│   │   └── alertas.py           # Sistema de alertas
│   ├── analytics/
│   │   ├── __init__.py
│   │   └── relatorios.py        # Relatórios e análises
│   └── main.py                  # Interface CLI
├── sql/
│   ├── 02_create_tables.sql     # Criação do schema
│   └── 03_insert_sample_data.sql # Dados de exemplo
├── .env                         # Configurações (não versionado)
├── .gitignore
├── requirements.txt
└── README.md
```



## 🧪 Testes

O projeto inclui arquivos de teste para cada módulo:
```
# Testar entrada de estoque
python test_entrada.py

# Testar saída com FEFO
python test_saida.py

# Testar sistema de alertas
python test_alertas.py

# Testar relatórios
python test_relatorios.py
```

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.x**: Linguagem principal
- **PostgreSQL**: Banco de dados relacional
- **SQLAlchemy**: ORM para Python
- **Pandas**: Análise de dados
- **python-dotenv**: Gerenciamento de variáveis de ambiente

### Dependências
```txt
pandas==2.0.3
psycopg2-binary==2.9.6
python-dotenv==1.0.0
sqlalchemy==2.0.19
tabulate==0.9.0
```

---

## 📈 Conceitos Aplicados

### FEFO (First Expired, First Out)

Metodologia que prioriza o uso de produtos com data de validade mais próxima, minimizando perdas por vencimento.

**Como funciona:**

1. Sistema ordena lotes pela data de validade
2. Ao fazer uma saída, consome automaticamente do lote que vence primeiro
3. Registra todo o histórico de movimentações
4. Gera alertas preventivos

### Modelagem de Dados

- Normalização 3FN
- Índices para otimização de queries FEFO
- Views materializadas para relatórios
- Constraints para integridade referencial

---

## 🎓 Aprendizados do Projeto

Este projeto consolidou conhecimentos em:

- ✅ Modelagem de banco de dados relacional
- ✅ Programação orientada a objetos em Python
- ✅ Algoritmos de ordenação e priorização (FEFO)
- ✅ Geração de relatórios e análises
- ✅ Boas práticas de versionamento (Git)
- ✅ Segurança (variáveis de ambiente)


## 👤 Autor

**Seu Nome**
- Graduando em Banco de Dados - Descomplica/Uniamérica
- 5º Período
- GitHub: [@lucas.http](https://github.com/lucas-gif33)
- LinkedIn: [Lucas Soares Pinto](https://www.linkedin.com/in/lucas-soarespinto/)
