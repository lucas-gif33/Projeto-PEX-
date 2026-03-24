from sqlalchemy import text
import logging
from datetime import datetime, date

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EntradaEstoque:
    """
    Classe responsável por registrar entradas de ingredientes no estoque

    O que faz:
    1. Cria um novo lote de estoque
    2. Registra a movimentação no histórico
    3. Valida se os dados estão corretos
    """

    def __init__(self, db_engine):
        """
        Inicializa com a conexão do banco

        Args:
            db_engine: Engine do SQLAlchemy (vem do Database.connect())
        """
        self.engine = db_engine

    def registrar_entrada(self, ingrediente_id, quantidade, data_validade,
                          fornecedor_id=None, numero_lote=None, preco_unitario=None,
                          data_entrada=None, usuario=None):
        """
        Registra uma nova entrada de ingrediente no estoque

        Args:
            ingrediente_id (int): ID do ingrediente (da tabela ingredientes)
            quantidade (float): Quantidade comprada
            data_validade (date): Data de validade do produto
            fornecedor_id (int, opcional): ID do fornecedor
            numero_lote (str, opcional): Número do lote do fornecedor
            preco_unitario (float, opcional): Preço por unidade
            data_entrada (date, opcional): Data da compra (padrão: hoje)
            usuario (str, opcional): Quem registrou a entrada

        Returns:
            int: ID do lote criado

        Exemplo de uso:
            entrada = EntradaEstoque(engine)
            lote_id = entrada.registrar_entrada(
                ingrediente_id=1,      # Farinha
                quantidade=25.5,       # 25.5kg
                data_validade=date(2025, 9, 15),
                fornecedor_id=1,
                numero_lote='FAR-2025-003',
                preco_unitario=4.50,
                usuario='João'
            )
        """

        try:
            # Validações básicas
            if quantidade <= 0:
                raise ValueError("Quantidade deve ser maior que zero")

            if data_validade < (data_entrada or date.today()):
                raise ValueError("Data de validade não pode ser anterior à data de entrada")

            # Usar data de hoje se não informada
            if data_entrada is None:
                data_entrada = date.today()

            # Verificar se o ingrediente existe
            sql_check = """
                SELECT nome, unidade_medida 
                FROM ingredientes 
                WHERE id = :ingrediente_id AND ativo = TRUE
            """

            with self.engine.connect() as conn:
                result = conn.execute(text(sql_check), {"ingrediente_id": ingrediente_id})
                ingrediente = result.fetchone()

                if not ingrediente:
                    raise ValueError(f"Ingrediente ID {ingrediente_id} não encontrado ou inativo")

                ingrediente_nome = ingrediente[0]
                unidade_medida = ingrediente[1]

            logger.info(f"📦 Registrando entrada: {quantidade}{unidade_medida} de {ingrediente_nome}")

            # ============================================
            # PASSO 1: Inserir novo lote na tabela lotes_estoque
            # ============================================
            sql_insert_lote = """
                INSERT INTO lotes_estoque (
                    ingrediente_id,
                    fornecedor_id,
                    quantidade_inicial,
                    quantidade_atual,
                    data_entrada,
                    data_validade,
                    numero_lote,
                    preco_unitario,
                    status
                ) VALUES (
                    :ingrediente_id,
                    :fornecedor_id,
                    :quantidade,
                    :quantidade,  -- No início, quantidade_atual = quantidade_inicial
                    :data_entrada,
                    :data_validade,
                    :numero_lote,
                    :preco_unitario,
                    'disponivel'
                )
                RETURNING id  -- Retorna o ID do lote criado
            """

            params_lote = {
                "ingrediente_id": ingrediente_id,
                "fornecedor_id": fornecedor_id,
                "quantidade": quantidade,
                "data_entrada": data_entrada,
                "data_validade": data_validade,
                "numero_lote": numero_lote,
                "preco_unitario": preco_unitario
            }

            with self.engine.connect() as conn:
                # Inserir lote
                result = conn.execute(text(sql_insert_lote), params_lote)
                lote_id = result.fetchone()[0]  # Pega o ID retornado

                # ============================================
                # PASSO 2: Registrar movimentação no histórico
                # ============================================
                sql_insert_mov = """
                    INSERT INTO movimentacoes (
                        lote_id,
                        tipo_movimentacao,
                        quantidade,
                        motivo,
                        usuario
                    ) VALUES (
                        :lote_id,
                        'entrada',
                        :quantidade,
                        :motivo,
                        :usuario
                    )
                """

                motivo = f"Entrada de estoque - Lote {numero_lote or lote_id}"

                params_mov = {
                    "lote_id": lote_id,
                    "quantidade": quantidade,
                    "motivo": motivo,
                    "usuario": usuario or "Sistema"
                }

                conn.execute(text(sql_insert_mov), params_mov)

                # Confirmar transação
                conn.commit()

            logger.info(f"✅ Entrada registrada com sucesso! Lote ID: {lote_id}")
            logger.info(f"   📅 Validade: {data_validade.strftime('%d/%m/%Y')}")

            # Calcular dias até vencer
            dias_validade = (data_validade - date.today()).days

            if dias_validade <= 7:
                logger.warning(f"⚠️  ATENÇÃO: Este lote vence em {dias_validade} dias!")

            return lote_id

        except Exception as e:
            logger.error(f"❌ Erro ao registrar entrada: {str(e)}")
            raise

    def registrar_multiplas_entradas(self, entradas):
        """
        Registra várias entradas de uma vez (para quando você faz uma compra grande)

        Args:
            entradas (list): Lista de dicionários com dados de cada entrada

        Exemplo:
            entradas = [
                {
                    'ingrediente_id': 1,
                    'quantidade': 25,
                    'data_validade': date(2025, 9, 15),
                    'fornecedor_id': 1,
                    'preco_unitario': 4.50
                },
                {
                    'ingrediente_id': 2,
                    'quantidade': 10,
                    'data_validade': date(2025, 12, 31),
                    'fornecedor_id': 1,
                    'preco_unitario': 3.20
                }
            ]

            entrada_service = EntradaEstoque(engine)
            lotes_criados = entrada_service.registrar_multiplas_entradas(entradas)
        """

        lotes_criados = []

        logger.info(f"📦 Registrando {len(entradas)} entradas...")

        for i, entrada_data in enumerate(entradas, 1):
            try:
                logger.info(f"\n--- Entrada {i}/{len(entradas)} ---")

                lote_id = self.registrar_entrada(**entrada_data)
                lotes_criados.append(lote_id)

            except Exception as e:
                logger.error(f"❌ Erro na entrada {i}: {str(e)}")
                # Continua com as próximas entradas mesmo se uma falhar
                continue

        logger.info(f"\n✅ Total de entradas registradas: {len(lotes_criados)}/{len(entradas)}")

        return lotes_criados

    def consultar_lotes_ingrediente(self, ingrediente_id):
        """
        Lista todos os lotes disponíveis de um ingrediente
        Ordenado por data de validade (FEFO)

        Args:
            ingrediente_id (int): ID do ingrediente

        Returns:
            list: Lista de tuplas com dados dos lotes
        """

        sql = """
            SELECT 
                l.id,
                i.nome as ingrediente,
                l.quantidade_atual,
                i.unidade_medida,
                l.data_validade,
                l.data_validade - CURRENT_DATE as dias_para_vencer,
                l.numero_lote,
                f.nome as fornecedor,
                l.preco_unitario
            FROM lotes_estoque l
            JOIN ingredientes i ON l.ingrediente_id = i.id
            LEFT JOIN fornecedores f ON l.fornecedor_id = f.id
            WHERE l.ingrediente_id = :ingrediente_id
              AND l.status = 'disponivel'
              AND l.quantidade_atual > 0
            ORDER BY l.data_validade ASC  -- FEFO: Primeiro que vence, primeiro listado
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(sql), {"ingrediente_id": ingrediente_id})
            return result.fetchall()