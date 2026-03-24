# -*- coding: utf-8 -*-
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.database.connection import Database
from src.services.saida_estoque import SaidaEstoque


def test_saida_fefo_simples():
    """Teste 1: Saída simples usando FEFO"""

    print("\n" + "=" * 60)
    print("TESTE 1: Saída FEFO Simples")
    print("=" * 60)

    try:
        db = Database()
        engine = db.connect()
        saida_service = SaidaEstoque(engine)

        # Ver estoque antes
        print("\nEstoque ANTES da saída:")
        result = db.query("""
            SELECT 
                l.id,
                l.quantidade_atual,
                l.data_validade,
                l.numero_lote
            FROM lotes_estoque l
            WHERE l.ingrediente_id = 1  -- Farinha
              AND l.status = 'disponivel'
            ORDER BY l.data_validade
        """)

        for lote in result:
            print(f"  Lote {lote[0]}: {lote[1]}kg (vence {lote[2]}, lote {lote[3]})")

        # Fazer saída de 15kg de farinha
        print("\nRegistrando saída de 15kg de farinha...")
        resultado = saida_service.registrar_saida(
            ingrediente_id=1,  # Farinha
            quantidade_necessaria=15,
            receita_id=1,  # Bolo de Chocolate
            motivo="Producao de 10 bolos",
            usuario="Maria"
        )

        print(f"\nResultado: {resultado['mensagem']}")
        print(f"Lotes utilizados: {len(resultado['lotes_consumidos'])}")

        # Ver estoque depois
        print("\nEstoque DEPOIS da saída:")
        result = db.query("""
            SELECT 
                l.id,
                l.quantidade_atual,
                l.data_validade,
                l.numero_lote,
                l.status
            FROM lotes_estoque l
            WHERE l.ingrediente_id = 1
            ORDER BY l.data_validade
        """)

        for lote in result:
            print(f"  Lote {lote[0]}: {lote[1]}kg (vence {lote[2]}, lote {lote[3]}, status: {lote[4]})")

        print("\nTESTE 1: OK")

    except Exception as e:
        print(f"\nERRO no Teste 1: {str(e)}")
        import traceback
        traceback.print_exc()


def test_saida_multiplos_lotes():
    """Teste 2: Saída que consome múltiplos lotes"""

    print("\n" + "=" * 60)
    print("TESTE 2: Saída Consumindo Múltiplos Lotes")
    print("=" * 60)

    try:
        db = Database()
        engine = db.connect()
        saida_service = SaidaEstoque(engine)

        # Fazer saída GRANDE (vai precisar de vários lotes)
        print("\nRegistrando saída de 40kg de farinha...")
        print("(isso vai consumir múltiplos lotes seguindo FEFO)")

        resultado = saida_service.registrar_saida(
            ingrediente_id=1,
            quantidade_necessaria=40,
            motivo="Producao em lote",
            usuario="Pedro"
        )

        print(f"\n{resultado['mensagem']}")
        print(f"\nDetalhes dos lotes consumidos:")

        for lote in resultado['lotes_consumidos']:
            print(f"  Lote {lote['numero_lote']}: -{lote['quantidade_retirada']}kg "
                  f"(vencia em {lote['data_validade']}, restam {lote['quantidade_restante_lote']}kg)")

        print("\nTESTE 2: OK")

    except Exception as e:
        print(f"\nERRO no Teste 2: {str(e)}")
        import traceback
        traceback.print_exc()


def test_verificar_disponibilidade():
    """Teste 3: Verificar disponibilidade sem fazer saída"""

    print("\n" + "=" * 60)
    print("TESTE 3: Verificar Disponibilidade")
    print("=" * 60)

    try:
        db = Database()
        engine = db.connect()
        saida_service = SaidaEstoque(engine)

        # Verificar se tem estoque suficiente
        print("\nVerificando se tem 50kg de farinha...")
        resultado = saida_service.verificar_disponibilidade(
            ingrediente_id=1,
            quantidade_necessaria=50
        )

        print(f"Ingrediente: {resultado['ingrediente']}")
        print(f"Necessário: {resultado['quantidade_necessaria']}{resultado['unidade']}")
        print(f"Disponível: {resultado['estoque_disponivel']}{resultado['unidade']}")
        print(f"Status: {'OK' if resultado['disponivel'] else 'INSUFICIENTE'}")

        if not resultado['disponivel']:
            print(f"Faltam: {resultado['quantidade_faltante']}{resultado['unidade']}")

        print("\nTESTE 3: OK")

    except Exception as e:
        print(f"\nERRO no Teste 3: {str(e)}")
        import traceback
        traceback.print_exc()


def test_registrar_perda():
    """Teste 4: Registrar perda de produto"""

    print("\n" + "=" * 60)
    print("TESTE 4: Registrar Perda")
    print("=" * 60)

    try:
        db = Database()
        engine = db.connect()
        saida_service = SaidaEstoque(engine)

        # Buscar um lote para registrar perda
        result = db.query("""
            SELECT id, quantidade_atual, numero_lote
            FROM lotes_estoque
            WHERE quantidade_atual > 0
            LIMIT 1
        """)

        if result:
            lote_id, qtd, num_lote = result[0]

            print(f"\nRegistrando perda de 1kg do lote {num_lote}...")

            resultado = saida_service.registrar_perda(
                lote_id=lote_id,
                quantidade=1,
                motivo="Produto contaminado",
                usuario="João"
            )

            print(f"Perda registrada: {resultado['quantidade_perdida']}kg")
            print(f"Motivo: {resultado['motivo']}")

        print("\nTESTE 4: OK")

    except Exception as e:
        print(f"\nERRO no Teste 4: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Iniciando testes de saída de estoque (FEFO)...")
    print("=" * 60)

    test_saida_fefo_simples()
    test_saida_multiplos_lotes()
    test_verificar_disponibilidade()
    test_registrar_perda()

    print("\n" + "=" * 60)
    print("TODOS OS TESTES CONCLUIDOS!")
    print("=" * 60)