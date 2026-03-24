-- =========================================
-- DADOS DE EXEMPLO PARA TESTE
-- =========================================

-- Ingredientes
INSERT INTO ingredientes (nome, unidade_medida, categoria, estoque_minimo, estoque_ideal) VALUES
('Farinha de Trigo', 'kg', 'Farináceos', 10, 25),
('Açúcar Refinado', 'kg', 'Açúcares', 5, 15),
('Ovos', 'unidade', 'Laticínios', 60, 180),
('Leite Integral', 'L', 'Laticínios', 5, 15),
('Manteiga', 'kg', 'Laticínios', 2, 5),
('Chocolate em Pó', 'kg', 'Chocolates', 3, 8),
('Fermento em Pó', 'kg', 'Fermentos', 1, 3),
('Morangos', 'kg', 'Frutas', 1, 3);

-- Fornecedores
INSERT INTO fornecedores (nome, contato, telefone) VALUES
('Distribuidora Pão de Açúcar', 'João Silva', '(31) 3333-4444'),
('Laticínios BH', 'Maria Santos', '(31) 9999-8888'),
('Frutas Frescas', 'Pedro Costa', '(31) 2222-3333');

-- Receitas
INSERT INTO receitas (nome, descricao, rendimento) VALUES
('Bolo de Chocolate', 'Bolo simples de chocolate', 12),
('Brigadeiro', 'Doce de chocolate', 40),
('Torta de Morango', 'Torta com creme e morangos', 8);

-- Lotes de Estoque (IMPORTANTE: Veja as datas!)
INSERT INTO lotes_estoque (ingrediente_id, fornecedor_id, quantidade_inicial, quantidade_atual, data_entrada, data_validade, numero_lote, preco_unitario) VALUES
-- Farinha: Dois lotes com validades diferentes
(1, 1, 25.000, 25.000, '2025-03-10', '2025-08-10', 'FAR-001', 4.50),  -- Vence primeiro
(1, 1, 25.000, 25.000, '2025-03-15', '2025-09-15', 'FAR-002', 4.50),  -- Vence depois

-- Ovos: Validade curta (21 dias)
(3, 2, 180, 180, CURRENT_DATE - 5, CURRENT_DATE + 16, 'OVO-001', 0.80),  -- Vence dia 16
(3, 2, 180, 180, CURRENT_DATE, CURRENT_DATE + 21, 'OVO-002', 0.80),      -- Vence dia 21

-- Leite: Validade muito curta (7 dias)
(4, 2, 20.000, 20.000, CURRENT_DATE - 2, CURRENT_DATE + 5, 'LEI-001', 4.50),  -- URGENTE!
(4, 2, 15.000, 15.000, CURRENT_DATE, CURRENT_DATE + 7, 'LEI-002', 4.50),

-- Morangos: Validade curtíssima (3 dias)
(8, 3, 3.000, 3.000, CURRENT_DATE, CURRENT_DATE + 3, 'MOR-001', 15.00);  -- USAR JÁ!

-- COMENTÁRIO: CURRENT_DATE = data de hoje
-- COMENTÁRIO: CURRENT_DATE + 5 = daqui a 5 dias
-- COMENTÁRIO: Note que temos lotes com validades diferentes propositalmente!