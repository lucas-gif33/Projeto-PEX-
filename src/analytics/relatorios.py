from sqlalchemy import text
import pandas as pd
import logging
from datetime import date, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Relatorios:
    """
    Gera relatórios e análises do estoque

    Relatórios disponíveis:
    1. Movimentações por período
    2. Consumo por ingrediente
    3. Taxa de desperdício
    4. Giro de estoque
    5. Valor do estoque
    """

    def __init__(self, db_engine):
        """
        Inicializa com a conexão do banco

        Args:
            db_engine: Engine do SQLAlchemy
        """
        self.engine = db_engine

    def relatorio_movimentacoes(self, data_inicio=None, data_fim=None, tipo=None):
        """
        Relatório de movimentações por período

        Args:
            data_inicio (date): Data inicial (padrão: 30 dias atrás)
            data_fim (date): Data final (padrão: hoje)
            tipo (str): Filtrar por tipo (entrada, saida, perda, ajuste)

        Returns:
            DataFrame: Movimentações do período
        """

        if data_inicio is None:
            data_inicio = date.today() - timedelta(days=30)
        if data_fim is None:
            data_fim = date.today()

        logger.info(f"📊 Gerando relatório de movimentações: {data_inicio} a {data_fim}")

        sql = """
            SELECT 
                m.id,
                m.data_movimentacao::date as data,
                m.tipo_movimentacao as tipo,
                i.nome as ingrediente,
                m.quantidade,
                i.unidade_medida as unidade,
                r.nome as receita,
                m.motivo,
                m.usuario,
                l.numero_lote
            FROM movimentacoes m
            JOIN lotes_estoque l ON m.lote_id = l.id
            JOIN ingredientes i ON l.ingrediente_id = i.id
            LEFT JOIN receitas r ON m.receita_id = r.id
            WHERE m.data_movimentacao::date BETWEEN :data_inicio AND :data_fim
        """

        params = {
            "data_inicio": data_inicio,
            "data_fim": data_fim
        }

        if tipo:
            sql += " AND m.tipo_movimentacao = :tipo"
            params["tipo"] = tipo

        sql += " ORDER BY m.data_movimentacao DESC"

        with self.engine.connect() as conn:
            df = pd.read_sql(text(sql), conn, params=params)

        logger.info(f"✅ {len(df)} movimentações encontradas")

        return df

    def relatorio_consumo_por_ingrediente(self, dias=30):
        """
        Análise de consumo por ingrediente

        Args:
            dias (int): Período de análise em dias

        Returns:
            DataFrame: Consumo por ingrediente
        """

        logger.info(f"📊 Analisando consumo dos últimos {dias} dias...")

        sql = """
            SELECT 
                i.id,
                i.nome as ingrediente,
                i.categoria,
                i.unidade_medida as unidade,
                COALESCE(SUM(CASE WHEN m.tipo_movimentacao = 'saida' THEN m.quantidade ELSE 0 END), 0) as consumo_total,
                COALESCE(SUM(CASE WHEN m.tipo_movimentacao = 'perda' THEN m.quantidade ELSE 0 END), 0) as perdas_total,
                COUNT(DISTINCT CASE WHEN m.tipo_movimentacao = 'saida' THEN DATE(m.data_movimentacao) END) as dias_com_uso,
                COALESCE(SUM(CASE WHEN m.tipo_movimentacao = 'saida' THEN m.quantidade ELSE 0 END), 0) / NULLIF(:dias, 0) as consumo_medio_dia
            FROM ingredientes i
            LEFT JOIN lotes_estoque l ON i.id = l.ingrediente_id
            LEFT JOIN movimentacoes m ON l.id = m.lote_id
                AND m.data_movimentacao >= CURRENT_DATE - :dias
                AND m.tipo_movimentacao IN ('saida', 'perda')
            WHERE i.ativo = TRUE
            GROUP BY i.id, i.nome, i.categoria, i.unidade_medida
            HAVING COALESCE(SUM(CASE WHEN m.tipo_movimentacao = 'saida' THEN m.quantidade ELSE 0 END), 0) > 0
            ORDER BY consumo_total DESC
        """

        with self.engine.connect() as conn:
            df = pd.read_sql(text(sql), conn, params={"dias": dias})

        # Calcular métricas adicionais
        if not df.empty:
            df['taxa_desperdicio'] = (df['perdas_total'] / (df['consumo_total'] + df['perdas_total']) * 100).round(2)
            df['consumo_total'] = df['consumo_total'].round(2)
            df['perdas_total'] = df['perdas_total'].round(2)
            df['consumo_medio_dia'] = df['consumo_medio_dia'].round(2)

        logger.info(f"✅ Análise de {len(df)} ingredientes concluída")

        return df

    def relatorio_valor_estoque(self):
        """
        Calcula o valor total do estoque atual

        Returns:
            DataFrame: Valor por ingrediente
        """

        logger.info("💰 Calculando valor do estoque...")

        sql = """
            SELECT 
                i.nome as ingrediente,
                i.categoria,
                SUM(l.quantidade_atual) as quantidade_total,
                i.unidade_medida as unidade,
                AVG(l.preco_unitario) as preco_medio,
                SUM(l.quantidade_atual * l.preco_unitario) as valor_total
            FROM lotes_estoque l
            JOIN ingredientes i ON l.ingrediente_id = i.id
            WHERE l.status = 'disponivel'
              AND l.quantidade_atual > 0
              AND l.preco_unitario IS NOT NULL
            GROUP BY i.id, i.nome, i.categoria, i.unidade_medida
            ORDER BY valor_total DESC
        """

        with self.engine.connect() as conn:
            df = pd.read_sql(text(sql), conn)

        if not df.empty:
            df['quantidade_total'] = df['quantidade_total'].round(2)
            df['preco_medio'] = df['preco_medio'].round(2)
            df['valor_total'] = df['valor_total'].round(2)

            valor_total_estoque = df['valor_total'].sum()
            logger.info(f"✅ Valor total do estoque: R$ {valor_total_estoque:,.2f}")
        else:
            logger.warning("⚠️  Nenhum lote com preço cadastrado")

        return df

    def relatorio_giro_estoque(self, dias=30):
        """
        Analisa o giro de estoque (velocidade de consumo)

        Args:
            dias (int): Período de análise

        Returns:
            DataFrame: Análise de giro
        """

        logger.info(f"🔄 Analisando giro de estoque ({dias} dias)...")

        sql = """
            SELECT 
                i.nome as ingrediente,
                COALESCE(SUM(l.quantidade_atual), 0) as estoque_atual,
                i.unidade_medida as unidade,
                COALESCE(SUM(CASE WHEN m.tipo_movimentacao = 'saida' THEN m.quantidade ELSE 0 END), 0) as consumo_periodo,
                CASE 
                    WHEN COALESCE(SUM(l.quantidade_atual), 0) > 0 AND 
                         COALESCE(SUM(CASE WHEN m.tipo_movimentacao = 'saida' THEN m.quantidade ELSE 0 END), 0) > 0
                    THEN COALESCE(SUM(l.quantidade_atual), 0) / 
                         (COALESCE(SUM(CASE WHEN m.tipo_movimentacao = 'saida' THEN m.quantidade ELSE 0 END), 0) / :dias)
                    ELSE NULL
                END as dias_estoque
            FROM ingredientes i
            LEFT JOIN lotes_estoque l ON i.id = l.ingrediente_id AND l.status = 'disponivel'
            LEFT JOIN movimentacoes m ON l.id = m.lote_id
                AND m.data_movimentacao >= CURRENT_DATE - :dias
            WHERE i.ativo = TRUE
            GROUP BY i.id, i.nome, i.unidade_medida
            HAVING COALESCE(SUM(CASE WHEN m.tipo_movimentacao = 'saida' THEN m.quantidade ELSE 0 END), 0) > 0
            ORDER BY dias_estoque ASC NULLS LAST
        """

        with self.engine.connect() as conn:
            df = pd.read_sql(text(sql), conn, params={"dias": dias})

        if not df.empty:
            df['estoque_atual'] = df['estoque_atual'].round(2)
            df['consumo_periodo'] = df['consumo_periodo'].round(2)
            df['dias_estoque'] = df['dias_estoque'].round(1)

            # Classificar giro
            df['classificacao_giro'] = df['dias_estoque'].apply(
                lambda x: 'RÁPIDO' if pd.notna(x) and x < 15
                else 'MÉDIO' if pd.notna(x) and x < 30
                else 'LENTO' if pd.notna(x)
                else 'SEM DADOS'
            )

        logger.info(f"✅ Análise de giro concluída para {len(df)} ingredientes")

        return df

    def relatorio_top_ingredientes(self, top_n=10, criterio='consumo'):
        """
        Top N ingredientes por critério

        Args:
            top_n (int): Quantidade de itens no ranking
            criterio (str): 'consumo', 'valor' ou 'desperdicio'

        Returns:
            DataFrame: Ranking dos ingredientes
        """

        logger.info(f"🏆 Gerando TOP {top_n} ingredientes por {criterio}...")

        if criterio == 'consumo':
            df = self.relatorio_consumo_por_ingrediente(dias=30)
            df = df.nlargest(top_n, 'consumo_total')

        elif criterio == 'valor':
            df = self.relatorio_valor_estoque()
            df = df.nlargest(top_n, 'valor_total')

        elif criterio == 'desperdicio':
            df = self.relatorio_consumo_por_ingrediente(dias=30)
            df = df.nlargest(top_n, 'perdas_total')

        else:
            raise ValueError(f"Critério inválido: {criterio}")

        logger.info(f"✅ Ranking gerado")

        return df

    def resumo_executivo(self):
        """
        Resumo executivo com principais métricas

        Returns:
            dict: Principais indicadores
        """

        logger.info("📈 Gerando resumo executivo...")

        # Valor do estoque
        df_valor = self.relatorio_valor_estoque()
        valor_total = df_valor['valor_total'].sum() if not df_valor.empty else 0

        # Consumo últimos 30 dias
        df_consumo = self.relatorio_consumo_por_ingrediente(dias=30)
        consumo_total = len(df_consumo)
        perdas_total = df_consumo['perdas_total'].sum() if not df_consumo.empty else 0

        # Movimentações últimos 7 dias
        df_mov = self.relatorio_movimentacoes(
            data_inicio=date.today() - timedelta(days=7),
            data_fim=date.today()
        )

        entradas = len(df_mov[df_mov['tipo'] == 'entrada']) if not df_mov.empty else 0
        saidas = len(df_mov[df_mov['tipo'] == 'saida']) if not df_mov.empty else 0

        resumo = {
            'data_relatorio': date.today(),
            'valor_estoque_total': round(valor_total, 2),
            'ingredientes_com_movimento': consumo_total,
            'perdas_ultimos_30_dias': round(perdas_total, 2),
            'entradas_ultimos_7_dias': entradas,
            'saidas_ultimos_7_dias': saidas,
            'taxa_movimentacao': round((saidas / max(entradas, 1)) * 100, 1)
        }

        logger.info("✅ Resumo executivo gerado")

        return resumo