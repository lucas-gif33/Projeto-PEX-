-- =========================================
-- TABELA 1: INGREDIENTES (Catálogo)
-- =========================================
CREATE TABLE IF NOT EXISTS ingredientes (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    unidade_medida VARCHAR(20) NOT NULL,  -- kg, L, unidade
    categoria VARCHAR(50),                 -- laticínios, farináceos, etc
    estoque_minimo DECIMAL(10, 2) DEFAULT 0,
    estoque_ideal DECIMAL(10, 2) DEFAULT 0,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- COMENTÁRIO: id SERIAL = auto incremento (1, 2, 3...)
-- COMENTÁRIO: UNIQUE = não pode ter dois ingredientes com mesmo nome
-- COMENTÁRIO: estoque_minimo = quando bater esse valor, sistema alerta

-- =========================================
-- TABELA 2: FORNECEDORES
-- =========================================
CREATE TABLE IF NOT EXISTS fornecedores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    contato VARCHAR(100),
    telefone VARCHAR(20),
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================
-- TABELA 3: LOTES_ESTOQUE (Principal!)
-- =========================================
CREATE TABLE IF NOT EXISTS lotes_estoque (
    id SERIAL PRIMARY KEY,
    ingrediente_id INTEGER NOT NULL REFERENCES ingredientes(id),
    fornecedor_id INTEGER REFERENCES fornecedores(id),
    quantidade_inicial DECIMAL(10, 3) NOT NULL,  -- Quanto comprou
    quantidade_atual DECIMAL(10, 3) NOT NULL,    -- Quanto tem agora
    data_entrada DATE NOT NULL DEFAULT CURRENT_DATE,
    data_validade DATE NOT NULL,                 -- CRÍTICO para FEFO!
    numero_lote VARCHAR(50),
    preco_unitario DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'disponivel',     -- disponivel, esgotado, vencido
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Validações
    CONSTRAINT chk_quantidade_positiva CHECK (quantidade_atual >= 0),
    CONSTRAINT chk_validade_futura CHECK (data_validade >= data_entrada)
);

-- COMENTÁRIO: REFERENCES = chave estrangeira (liga com ingredientes)
-- COMENTÁRIO: quantidade_inicial vs atual = ver quanto foi usado
-- COMENTÁRIO: CHECK = validação (não pode ter quantidade negativa)

-- =========================================
-- TABELA 4: RECEITAS
-- =========================================
CREATE TABLE IF NOT EXISTS receitas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    rendimento INTEGER,  -- Quantas unidades produz
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================
-- TABELA 5: MOVIMENTACOES (Histórico)
-- =========================================
CREATE TABLE IF NOT EXISTS movimentacoes (
    id SERIAL PRIMARY KEY,
    lote_id INTEGER NOT NULL REFERENCES lotes_estoque(id),
    tipo_movimentacao VARCHAR(20) NOT NULL,  -- entrada, saida, perda
    quantidade DECIMAL(10, 3) NOT NULL,
    data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    receita_id INTEGER REFERENCES receitas(id),
    motivo TEXT,
    usuario VARCHAR(50),

    CONSTRAINT chk_tipo_valido CHECK (tipo_movimentacao IN ('entrada', 'saida', 'ajuste', 'perda'))
);

-- =========================================
-- ÍNDICES (Aceleram consultas)
-- =========================================
-- Quando buscar por validade, será mais rápido
CREATE INDEX idx_lotes_validade ON lotes_estoque(data_validade);
-- Quando buscar lotes de um ingrediente específico
CREATE INDEX idx_lotes_ingrediente ON lotes_estoque(ingrediente_id);
-- Quando filtrar por status
CREATE INDEX idx_lotes_status ON lotes_estoque(status);

-- COMENTÁRIO: Índices são como índices de livro - facilitam encontrar informação

-- =========================================
-- VIEW 1: Estoque Atual (Consulta pronta)
-- =========================================
CREATE OR REPLACE VIEW v_estoque_atual AS
SELECT
    i.id,
    i.nome,
    i.unidade_medida,
    i.categoria,
    COALESCE(SUM(l.quantidade_atual), 0) as quantidade_total,
    i.estoque_minimo,
    i.estoque_ideal,
    CASE
        WHEN COALESCE(SUM(l.quantidade_atual), 0) < i.estoque_minimo THEN 'CRÍTICO'
        WHEN COALESCE(SUM(l.quantidade_atual), 0) < i.estoque_ideal THEN 'BAIXO'
        ELSE 'OK'
    END as status_estoque
FROM ingredientes i
LEFT JOIN lotes_estoque l ON i.id = l.ingrediente_id AND l.status = 'disponivel'
WHERE i.ativo = TRUE
GROUP BY i.id, i.nome, i.unidade_medida, i.categoria, i.estoque_minimo, i.estoque_ideal;

-- COMENTÁRIO: VIEW = consulta salva, pode usar como tabela
-- COMENTÁRIO: Soma todos os lotes disponíveis de cada ingrediente
-- COMENTÁRIO: COALESCE = se não tiver nada, retorna 0

-- =========================================
-- VIEW 2: Alertas de Validade
-- =========================================
CREATE OR REPLACE VIEW v_alertas_validade AS
SELECT
    l.id as lote_id,
    i.nome as ingrediente,
    l.quantidade_atual,
    i.unidade_medida,
    l.data_validade,
    l.data_validade - CURRENT_DATE as dias_para_vencer,
    f.nome as fornecedor,
    CASE
        WHEN l.data_validade < CURRENT_DATE THEN 'VENCIDO'
        WHEN l.data_validade - CURRENT_DATE <= 3 THEN 'URGENTE'
        WHEN l.data_validade - CURRENT_DATE <= 7 THEN 'ATENÇÃO'
        ELSE 'OK'
    END as nivel_alerta
FROM lotes_estoque l
JOIN ingredientes i ON l.ingrediente_id = i.id
LEFT JOIN fornecedores f ON l.fornecedor_id = f.id
WHERE l.status = 'disponivel'
  AND l.quantidade_atual > 0
ORDER BY l.data_validade;

-- COMENTÁRIO: Mostra quais lotes estão perto de vencer
-- COMENTÁRIO: Ordena pela data de validade (FEFO!)