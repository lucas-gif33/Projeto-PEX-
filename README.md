# 🏪 Sistema de Controle de Estoque - Confeitaria

Sistema completo de gerenciamento de estoque com metodologia **FEFO (First Expired, First Out)** desenvolvido em Python e PostgreSQL.

![Python](https://img.shields.io/badge/python-3.x-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)
![Status](https://img.shields.io/badge/status-concluído-success.svg)

---

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

---

## 🚀 Como Executar

### Pré-requisitos

- Python 3.x
- PostgreSQL 15+
- PyCharm (recomendado) ou qualquer IDE Python

### 1. Clonar o Repositório
```bash
git clone https://github.com/seu-usuario/controle-estoque-confeitaria.git
cd controle-estoque-confeitaria
```

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar Banco de Dados

**a) Criar banco no PostgreSQL:**
```sql
CREATE DATABASE estoque_confeitaria WITH ENCODING 'UTF8';
```

**b) Executar scripts SQL (na ordem):**

No pgAdmin, abra o Query Tool no banco `estoque_confeitaria` e execute:

1. `sql/02_create_tables.sql` - Cria tabelas e views
2. `sql/03_insert_sample_data.sql` - Insere dados de exemplo

### 4. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=estoque_confeitaria
DB_USER=postgres
DB_PASSWORD=sua_senha_aqui
```

### 5. Executar o Sistema
```bash
python src/main.py
```

---

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

---

## 🎮 Usando o Sistema

### Menu Principal
```
============================================================
🏪 SISTEMA DE CONTROLE DE ESTOQUE - CONFEITARIA
============================================================

📋 MENU PRINCIPAL:

1. 📥 Entrada de Estoque
2. 📤 Saída de Estoque
3. 🔔 Alertas e Avisos
4. 📊 Relatórios e Análises
5. 📦 Consultar Estoque
6. ❌ Registrar Perda
0. 🚪 Sair
```

### Exemplo de Uso: Saída com FEFO
```python
# O sistema busca automaticamente o lote que vence primeiro
Ingrediente: Farinha de Trigo
Quantidade necessária: 10kg

Sistema verifica lotes:
- Lote A: 15kg (vence dia 10/08) ← Usa este primeiro!
- Lote B: 20kg (vence dia 15/09)
- Lote C: 25kg (vence dia 20/09)

Resultado:
✅ Retirado 10kg do Lote A (FEFO)
   Lote A agora tem: 5kg
```

---

## 📊 Exemplos de Relatórios

### Dashboard de Alertas
```
📊 RESUMO
Total de alertas: 10
  🔴 Vencidos: 0
  🟠 Vence em 3 dias: 3
  🟡 Vence em 7 dias: 4
  🔴 Estoque crítico: 0
  🟡 Estoque baixo: 3
```

### Análise de Consumo
```
TOP 5 Ingredientes Mais Consumidos (30 dias):
1. Farinha de Trigo: 45kg (média: 1.5kg/dia)
2. Açúcar: 30kg (média: 1.0kg/dia)
3. Ovos: 240un (média: 8un/dia)
...
```

---

## 🧪 Testes

O projeto inclui arquivos de teste para cada módulo:
```bash
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

---

## 🚧 Melhorias Futuras

- [ ] Interface web com Flask/Django
- [ ] Dashboard visual com gráficos
- [ ] Exportação de relatórios em PDF/Excel
- [ ] Integração com API de fornecedores
- [ ] Notificações por email/SMS
- [ ] App mobile
- [ ] Sistema de permissões de usuário

---

## 📄 Licença

Este projeto foi desenvolvido para fins educacionais como parte do curso de Tecnólogo em Banco de Dados pela Descomplica - Uniamérica.

---

## 👤 Autor

**Seu Nome**
- Tecnólogo em Banco de Dados - Descomplica/Uniamérica
- 5º Período
- GitHub: [@seu-usuario](https://github.com/seu-usuario)
- LinkedIn: [seu-perfil](https://linkedin.com/in/seu-perfil)
