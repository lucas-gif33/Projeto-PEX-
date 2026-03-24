from sqlalchemy import text
import logging
from datetime import date, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Alertas:
    """
    Sistema de alertas para gestão de estoque

    Funcionalidades:
    1. Alertas de validade (produtos vencendo)
    2. Alertas de estoque baixo
    3. Produtos já vencidos
    4. Sugestões de compra
    """

    def __init__(self, db_engine):
        """
        Inicializa com a conexão do banco

        Args:
            db_engine: Engine do SQLAlchemy
        """
        self.engine = db_engine

    def alertas_validade(self, dias_antecedencia=7):
        """
        Retorna produtos que vencem nos próximos X dias

        Args:
            dias_antecedencia (int): Alertar produtos que vencem em até X dias

        Returns:
            list: Lista de alertas ordenados por urgência

        Exemplo:
            alertas_service = Alertas(engine)
            # Ver produtos que vencem nos próximos 7 dias
            alertas = alertas_service.alertas_validade(dias_antecedencia=7)
        """

        logger.info(f"🔍 Verificando produtos que vencem em até {dias_antecedencia} dias...")

        sql = """
            SELECT 
                l.id as lote_id,
                i.nome as ingrediente,
                l.quantidade_atual,
                i.unidade_medida,
                l.data_validade,
                l.data_validade - CURRENT_DATE as dias_para_vencer,
                l.numero_lote,
                f.nome as fornecedor,
                l.preco_unitario,
                CASE 
                    WHEN l.data_validade < CURRENT_DATE THEN 'VENCIDO'
                    WHEN l.data_validade - CURRENT_DATE <= 3 THEN 'URGENTE'
                    WHEN l.data_validade - CURRENT_DATE <= 7 THEN 'ATENCAO'
                    ELSE 'OK'
                END as nivel_alerta
            FROM lotes_estoque l
            JOIN ingredientes i ON l.ingrediente_id = i.id
            LEFT JOIN fornecedores f ON l.fornecedor_id = f.id
            WHERE l.status = 'disponivel' 
              AND l.quantidade_atual > 0
              AND l.data_validade <= CURRENT_DATE + :dias_antecedencia
            ORDER BY l.data_validade ASC
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(sql), {"dias_antecedencia": dias_antecedencia})
            alertas = result.fetchall()

        # Processar alertas
        alertas_processados = []

        for alerta in alertas:
            (lote_id, ingrediente, qtd, unidade, data_val, dias,
             num_lote, fornecedor, preco, nivel) = alerta

            alertas_processados.append({
                'lote_id': lote_id,
                'ingrediente': ingrediente,
                'quantidade': qtd,
                'unidade': unidade,
                'data_validade': data_val,
                'dias_para_vencer': dias,
                'numero_lote': num_lote,
                'fornecedor': fornecedor,
                'nivel_alerta': nivel,
                'valor_estimado': round(qtd * preco, 2) if preco else None
            })

        # Log resumo
        vencidos = sum(1 for a in alertas_processados if a['nivel_alerta'] == 'VENCIDO')
        urgentes = sum(1 for a in alertas_processados if a['nivel_alerta'] == 'URGENTE')
        atencao = sum(1 for a in alertas_processados if a['nivel_alerta'] == 'ATENCAO')

        logger.info(f"📋 Encontrados {len(alertas_processados)} alertas:")
        if vencidos > 0:
            logger.warning(f"   🔴 VENCIDOS: {vencidos}")
        if urgentes > 0:
            logger.warning(f"   🟠 URGENTES (≤3 dias): {urgentes}")
        if atencao > 0:
            logger.info(f"   🟡 ATENÇÃO (≤7 dias): {atencao}")

        return alertas_processados

    def alertas_estoque_baixo(self):
        """
        Retorna ingredientes com estoque abaixo do mínimo

        Returns:
            list: Ingredientes que precisam ser repostos
        """

        logger.info("🔍 Verificando estoque baixo...")

        sql = """
            SELECT 
                i.id,
                i.nome,
                i.unidade_medida,
                COALESCE(SUM(l.quantidade_atual), 0) as estoque_atual,
                i.estoque_minimo,
                i.estoque_ideal,
                i.estoque_ideal - COALESCE(SUM(l.quantidade_atual), 0) as quantidade_sugerida,
                CASE 
                    WHEN COALESCE(SUM(l.quantidade_atual), 0) = 0 THEN 'SEM_ESTOQUE'
                    WHEN COALESCE(SUM(l.quantidade_atual), 0) < i.estoque_minimo THEN 'CRITICO'
                    WHEN COALESCE(SUM(l.quantidade_atual), 0) < i.estoque_ideal THEN 'BAIXO'
                    ELSE 'OK'
                END as status
            FROM ingredientes i
            LEFT JOIN lotes_estoque l ON i.id = l.ingrediente_id 
                AND l.status = 'disponivel'
            WHERE i.ativo = TRUE
            GROUP BY i.id, i.nome, i.unidade_medida, i.estoque_minimo, i.estoque_ideal
            HAVING COALESCE(SUM(l.quantidade_atual), 0) < i.estoque_ideal
            ORDER BY 
                CASE 
                    WHEN COALESCE(SUM(l.quantidade_atual), 0) = 0 THEN 1
                    WHEN COALESCE(SUM(l.quantidade_atual), 0) < i.estoque_minimo THEN 2
                    ELSE 3
                END,
                i.nome
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            alertas = result.fetchall()

        alertas_processados = []

        for alerta in alertas:
            (ing_id, nome, unidade, estoque_atual, est_min,
             est_ideal, qtd_sugerida, status) = alerta

            alertas_processados.append({
                'ingrediente_id': ing_id,
                'ingrediente': nome,
                'unidade': unidade,
                'estoque_atual': estoque_atual,
                'estoque_minimo': est_min,
                'estoque_ideal': est_ideal,
                'quantidade_sugerida_compra': max(0, qtd_sugerida),
                'status': status
            })

        # Log resumo
        sem_estoque = sum(1 for a in alertas_processados if a['status'] == 'SEM_ESTOQUE')
        critico = sum(1 for a in alertas_processados if a['status'] == 'CRITICO')
        baixo = sum(1 for a in alertas_processados if a['status'] == 'BAIXO')

        logger.info(f"📋 Encontrados {len(alertas_processados)} ingredientes com estoque baixo:")
        if sem_estoque > 0:
            logger.error(f"   🔴 SEM ESTOQUE: {sem_estoque}")
        if critico > 0:
            logger.warning(f"   🟠 CRÍTICO (< mínimo): {critico}")
        if baixo > 0:
            logger.info(f"   🟡 BAIXO (< ideal): {baixo}")

        return alertas_processados

    def produtos_vencidos(self):
        """
        Lista produtos já vencidos que ainda estão no sistema

        Returns:
            list: Produtos vencidos
        """

        logger.info("🔍 Verificando produtos vencidos...")

        sql = """
            SELECT 
                l.id as lote_id,
                i.nome as ingrediente,
                l.quantidade_atual,
                i.unidade_medida,
                l.data_validade,
                CURRENT_DATE - l.data_validade as dias_vencido,
                l.numero_lote,
                l.preco_unitario
            FROM lotes_estoque l
            JOIN ingredientes i ON l.ingrediente_id = i.id
            WHERE l.data_validade < CURRENT_DATE
              AND l.status = 'disponivel'
              AND l.quantidade_atual > 0
            ORDER BY l.data_validade ASC
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            vencidos = result.fetchall()

        vencidos_processados = []
        valor_total_perdido = 0

        for item in vencidos:
            (lote_id, ingrediente, qtd, unidade, data_val,
             dias_venc, num_lote, preco) = item

            valor_perdido = round(qtd * preco, 2) if preco else 0
            valor_total_perdido += valor_perdido

            vencidos_processados.append({
                'lote_id': lote_id,
                'ingrediente': ingrediente,
                'quantidade': qtd,
                'unidade': unidade,
                'data_validade': data_val,
                'dias_vencido': dias_venc,
                'numero_lote': num_lote,
                'valor_perdido': valor_perdido
            })

        if vencidos_processados:
            logger.warning(f"⚠️  Encontrados {len(vencidos_processados)} produtos VENCIDOS!")
            logger.warning(f"   💰 Valor estimado perdido: R$ {valor_total_perdido:.2f}")
        else:
            logger.info("✅ Nenhum produto vencido encontrado")

        return vencidos_processados

    def sugestao_compras(self):
        """
        Gera lista de compras sugerida baseada em:
        - Estoque atual
        - Estoque mínimo/ideal
        - Consumo médio

        Returns:
            list: Sugestões de compra
        """

        logger.info("📝 Gerando sugestões de compra...")

        # Buscar ingredientes com estoque baixo
        estoque_baixo = self.alertas_estoque_baixo()

        # Buscar consumo médio dos últimos 30 dias
        sql_consumo = """
            SELECT 
                i.id,
                i.nome,
                COALESCE(SUM(m.quantidade), 0) as consumo_30_dias
            FROM ingredientes i
            LEFT JOIN lotes_estoque l ON i.id = l.ingrediente_id
            LEFT JOIN movimentacoes m ON l.id = m.lote_id
                AND m.tipo_movimentacao = 'saida'
                AND m.data_movimentacao >= CURRENT_DATE - 30
            WHERE i.ativo = TRUE
            GROUP BY i.id, i.nome
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(sql_consumo))
            consumo_data = {row[0]: row[2] for row in result.fetchall()}

        sugestoes = []

        for item in estoque_baixo:
            ing_id = item['ingrediente_id']
            consumo_mensal = consumo_data.get(ing_id, 0)

            # Calcular quanto comprar
            # Leva em conta: estoque ideal + 1 mês de consumo
            qtd_sugerida = item['quantidade_sugerida_compra'] + consumo_mensal

            sugestoes.append({
                'ingrediente': item['ingrediente'],
                'unidade': item['unidade'],
                'estoque_atual': item['estoque_atual'],
                'estoque_ideal': item['estoque_ideal'],
                'consumo_mensal_medio': consumo_mensal,
                'quantidade_sugerida': round(qtd_sugerida, 2),
                'prioridade': item['status'],
                'motivo': self._gerar_motivo_compra(item, consumo_mensal)
            })

        # Ordenar por prioridade
        ordem_prioridade = {'SEM_ESTOQUE': 1, 'CRITICO': 2, 'BAIXO': 3}
        sugestoes.sort(key=lambda x: ordem_prioridade.get(x['prioridade'], 4))

        logger.info(f"📋 {len(sugestoes)} sugestões de compra geradas")

        return sugestoes

    def _gerar_motivo_compra(self, item, consumo_mensal):
        """Gera descrição do motivo da compra"""

        if item['status'] == 'SEM_ESTOQUE':
            return f"SEM ESTOQUE! Consumo médio: {consumo_mensal:.1f}{item['unidade']}/mês"
        elif item['status'] == 'CRITICO':
            return f"Estoque crítico ({item['estoque_atual']:.1f} < {item['estoque_minimo']:.1f})"
        else:
            return f"Estoque baixo. Reabastecer para nível ideal"

    def dashboard_resumo(self):
        """
        Retorna resumo geral para dashboard

        Returns:
            dict: Métricas gerais do estoque
        """

        logger.info("📊 Gerando dashboard...")

        # Produtos vencendo em diferentes períodos
        hoje = date.today()

        sql_metricas = """
            SELECT 
                COUNT(DISTINCT i.id) as total_ingredientes,
                COUNT(DISTINCT CASE WHEN l.quantidade_atual > 0 THEN l.id END) as total_lotes_ativos,
                COUNT(DISTINCT CASE WHEN l.data_validade < CURRENT_DATE THEN l.id END) as lotes_vencidos,
                COUNT(DISTINCT CASE WHEN l.data_validade BETWEEN CURRENT_DATE AND CURRENT_DATE + 3 THEN l.id END) as vence_3_dias,
                COUNT(DISTINCT CASE WHEN l.data_validade BETWEEN CURRENT_DATE + 4 AND CURRENT_DATE + 7 THEN l.id END) as vence_7_dias,
                COUNT(DISTINCT CASE WHEN est.status_estoque = 'CRÍTICO' THEN i.id END) as estoque_critico,
                COUNT(DISTINCT CASE WHEN est.status_estoque = 'BAIXO' THEN i.id END) as estoque_baixo
            FROM ingredientes i
            LEFT JOIN lotes_estoque l ON i.id = l.ingrediente_id AND l.status = 'disponivel'
            LEFT JOIN v_estoque_atual est ON i.id = est.id
            WHERE i.ativo = TRUE
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(sql_metricas))
            metricas = result.fetchone()

        dashboard = {
            'total_ingredientes': metricas[0],
            'total_lotes_ativos': metricas[1],
            'alertas': {
                'vencidos': metricas[2],
                'vence_em_3_dias': metricas[3],
                'vence_em_7_dias': metricas[4],
                'estoque_critico': metricas[5],
                'estoque_baixo': metricas[6]
            },
            'total_alertas': metricas[2] + metricas[3] + metricas[4] + metricas[5] + metricas[6],
            'data_atualizacao': hoje
        }

        logger.info("✅ Dashboard gerado com sucesso")

        return dashboard