from sqlalchemy import text
import logging
from datetime import date

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SaidaEstoque:
    """
    Classe responsável por registrar saídas de estoque usando FEFO

    FEFO = First Expired, First Out
    Sempre usa o lote que vence primeiro!
    """

    def __init__(self, db_engine):
        """
        Inicializa com a conexão do banco

        Args:
            db_engine: Engine do SQLAlchemy
        """
        self.engine = db_engine

    def registrar_saida(self, ingrediente_id, quantidade_necessaria,
                        receita_id=None, motivo=None, usuario=None):
        """
        Registra saída de ingrediente usando algoritmo FEFO
        """

        try:
            # Validação básica
            if quantidade_necessaria <= 0:
                raise ValueError("Quantidade deve ser maior que zero")

            # Buscar informações do ingrediente
            sql_ingrediente = """
                SELECT nome, unidade_medida 
                FROM ingredientes 
                WHERE id = :ingrediente_id AND ativo = TRUE
            """

            with self.engine.connect() as conn:
                result = conn.execute(text(sql_ingrediente), {"ingrediente_id": ingrediente_id})
                ingrediente = result.fetchone()

                if not ingrediente:
                    raise ValueError(f"Ingrediente ID {ingrediente_id} não encontrado")

                ingrediente_nome = ingrediente[0]
                unidade_medida = ingrediente[1]

            logger.info(f"📤 Saída: {quantidade_necessaria}{unidade_medida} de {ingrediente_nome}")

            # ALGORITMO FEFO - BUSCAR LOTES ORDENADOS
            sql_lotes = """
                SELECT 
                    id,
                    quantidade_atual,
                    data_validade,
                    numero_lote
                FROM lotes_estoque
                WHERE ingrediente_id = :ingrediente_id
                  AND status = 'disponivel'
                  AND quantidade_atual > 0
                ORDER BY data_validade ASC
            """

            with self.engine.connect() as conn:
                result = conn.execute(text(sql_lotes), {"ingrediente_id": ingrediente_id})
                lotes_disponiveis = result.fetchall()

            if not lotes_disponiveis:
                raise ValueError(f"Sem estoque disponível de {ingrediente_nome}")

            # Verificar se tem estoque suficiente - CONVERTER PARA FLOAT
            estoque_total = sum(float(lote[1]) for lote in lotes_disponiveis)

            if estoque_total < quantidade_necessaria:
                raise ValueError(
                    f"Estoque insuficiente! "
                    f"Necessário: {quantidade_necessaria}{unidade_medida}, "
                    f"Disponível: {estoque_total}{unidade_medida}"
                )

            # CONSUMIR LOTES SEGUINDO FEFO
            quantidade_restante = quantidade_necessaria
            lotes_consumidos = []

            for lote in lotes_disponiveis:
                lote_id, qtd_disponivel_raw, data_validade, num_lote = lote

                # CONVERTER DECIMAL PARA FLOAT
                qtd_disponivel = float(qtd_disponivel_raw)

                if quantidade_restante <= 0:
                    break

                # Quanto vamos pegar deste lote?
                qtd_a_retirar = min(quantidade_restante, qtd_disponivel)

                # Atualizar quantidade do lote
                nova_quantidade = qtd_disponivel - qtd_a_retirar

                # Atualizar status se o lote acabar
                novo_status = 'esgotado' if nova_quantidade == 0 else 'disponivel'

                sql_update = """
                    UPDATE lotes_estoque
                    SET quantidade_atual = :nova_quantidade,
                        status = :novo_status
                    WHERE id = :lote_id
                """

                with self.engine.connect() as conn:
                    conn.execute(text(sql_update), {
                        "nova_quantidade": nova_quantidade,
                        "novo_status": novo_status,
                        "lote_id": lote_id
                    })
                    conn.commit()

                # Registrar movimentação
                sql_mov = """
                    INSERT INTO movimentacoes (
                        lote_id,
                        tipo_movimentacao,
                        quantidade,
                        receita_id,
                        motivo,
                        usuario
                    ) VALUES (
                        :lote_id,
                        'saida',
                        :quantidade,
                        :receita_id,
                        :motivo,
                        :usuario
                    )
                """

                motivo_final = motivo or f"Saída de estoque - {ingrediente_nome}"

                with self.engine.connect() as conn:
                    conn.execute(text(sql_mov), {
                        "lote_id": lote_id,
                        "quantidade": qtd_a_retirar,
                        "receita_id": receita_id,
                        "motivo": motivo_final,
                        "usuario": usuario or "Sistema"
                    })
                    conn.commit()

                # Guardar informações do lote consumido
                lotes_consumidos.append({
                    'lote_id': lote_id,
                    'numero_lote': num_lote,
                    'quantidade_retirada': qtd_a_retirar,
                    'data_validade': data_validade,
                    'quantidade_restante_lote': nova_quantidade
                })

                # Calcular quanto ainda falta
                quantidade_restante -= qtd_a_retirar

                # Log detalhado
                dias_validade = (data_validade - date.today()).days
                logger.info(
                    f"   Lote {num_lote or lote_id}: "
                    f"-{qtd_a_retirar}{unidade_medida} "
                    f"(vence em {dias_validade} dias, "
                    f"restam {nova_quantidade}{unidade_medida})"
                )

            logger.info(f"✅ Saída registrada com sucesso!")
            logger.info(f"   Total retirado: {quantidade_necessaria}{unidade_medida}")
            logger.info(f"   Lotes utilizados: {len(lotes_consumidos)}")

            # Retornar resultado
            return {
                'sucesso': True,
                'ingrediente': ingrediente_nome,
                'quantidade_total': quantidade_necessaria,
                'unidade': unidade_medida,
                'lotes_consumidos': lotes_consumidos,
                'mensagem': f"Saída de {quantidade_necessaria}{unidade_medida} de {ingrediente_nome} registrada"
            }

        except Exception as e:
            logger.error(f"❌ Erro ao registrar saída: {str(e)}")
            raise

    def registrar_perda(self, lote_id, quantidade, motivo, usuario=None):
        """
        Registra perda/desperdício de um lote específico
        """

        try:
            if not motivo:
                raise ValueError("Motivo da perda é obrigatório!")

            # Buscar informações do lote
            sql_lote = """
                SELECT 
                    l.quantidade_atual,
                    i.nome,
                    i.unidade_medida,
                    l.numero_lote
                FROM lotes_estoque l
                JOIN ingredientes i ON l.ingrediente_id = i.id
                WHERE l.id = :lote_id
            """

            with self.engine.connect() as conn:
                result = conn.execute(text(sql_lote), {"lote_id": lote_id})
                lote = result.fetchone()

                if not lote:
                    raise ValueError(f"Lote ID {lote_id} não encontrado")

                qtd_atual_raw, nome, unidade, num_lote = lote
                qtd_atual = float(qtd_atual_raw)  # CONVERTER DECIMAL PARA FLOAT

            if quantidade > qtd_atual:
                raise ValueError(
                    f"Quantidade de perda ({quantidade}) maior que disponível ({qtd_atual})"
                )

            logger.info(f"🗑️  Registrando perda: {quantidade}{unidade} de {nome}")
            logger.info(f"   Motivo: {motivo}")

            # Atualizar lote
            nova_quantidade = qtd_atual - quantidade
            novo_status = 'esgotado' if nova_quantidade == 0 else 'disponivel'

            sql_update = """
                UPDATE lotes_estoque
                SET quantidade_atual = :nova_quantidade,
                    status = :novo_status
                WHERE id = :lote_id
            """

            with self.engine.connect() as conn:
                conn.execute(text(sql_update), {
                    "nova_quantidade": nova_quantidade,
                    "novo_status": novo_status,
                    "lote_id": lote_id
                })
                conn.commit()

            # Registrar movimentação como perda
            sql_mov = """
                INSERT INTO movimentacoes (
                    lote_id,
                    tipo_movimentacao,
                    quantidade,
                    motivo,
                    usuario
                ) VALUES (
                    :lote_id,
                    'perda',
                    :quantidade,
                    :motivo,
                    :usuario
                )
            """

            with self.engine.connect() as conn:
                conn.execute(text(sql_mov), {
                    "lote_id": lote_id,
                    "quantidade": quantidade,
                    "motivo": motivo,
                    "usuario": usuario or "Sistema"
                })
                conn.commit()

            logger.info(f"✅ Perda registrada com sucesso!")

            return {
                'sucesso': True,
                'lote_id': lote_id,
                'quantidade_perdida': quantidade,
                'motivo': motivo
            }

        except Exception as e:
            logger.error(f"❌ Erro ao registrar perda: {str(e)}")
            raise

    def verificar_disponibilidade(self, ingrediente_id, quantidade_necessaria):
        """
        Verifica se há estoque suficiente SEM fazer a saída
        """

        sql = """
            SELECT 
                i.nome,
                i.unidade_medida,
                COALESCE(SUM(l.quantidade_atual), 0) as estoque_total
            FROM ingredientes i
            LEFT JOIN lotes_estoque l ON i.id = l.ingrediente_id 
                AND l.status = 'disponivel'
            WHERE i.id = :ingrediente_id
            GROUP BY i.id, i.nome, i.unidade_medida
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(sql), {"ingrediente_id": ingrediente_id})
            dados = result.fetchone()

        if not dados:
            raise ValueError(f"Ingrediente ID {ingrediente_id} não encontrado")

        nome, unidade, estoque_total_raw = dados
        estoque_total = float(estoque_total_raw)  # CONVERTER DECIMAL PARA FLOAT

        disponivel = estoque_total >= quantidade_necessaria
        faltante = max(0, quantidade_necessaria - estoque_total)

        return {
            'ingrediente': nome,
            'quantidade_necessaria': quantidade_necessaria,
            'estoque_disponivel': estoque_total,
            'unidade': unidade,
            'disponivel': disponivel,
            'quantidade_faltante': faltante
        }