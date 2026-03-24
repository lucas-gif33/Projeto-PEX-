# -*- coding: utf-8 -*-
import sys
import io

# Forçar encoding UTF-8 no terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from datetime import date, timedelta
from src.database.connection import Database
from src.services.entrada_estoque import EntradaEstoque


def test_entrada_simples():
    """Teste 1: Registrar uma entrada simples"""

    print("\n" + "=" * 60)
    print("TESTE 1: Entrada Simples")
    print("=" * 60)

    try:
        # Conectar ao banco
        db = Database()
        engine = db.connect()

        # Criar serviço de entrada
        entrada_service = EntradaEstoque(engine)

        # Registrar entrada de farinha
        lote_id = entrada_service.registrar_entrada(
            ingrediente_id=1,  # Farinha de Trigo
            quantidade=30,  # 30kg
            data_validade=date.today() + timedelta(days=180),
            fornecedor_id=1,
            numero_lote="FAR-2025-TESTE-001",
            preco_unitario=4.75,
            usuario="Joao da Silva"
        )

        print(f"\nLote criado com ID: {lote_id}")

        # Consultar lotes de farinha
        print("\nLotes de Farinha disponiveis (ordem FEFO):")
        lotes = entrada_service.consultar_lotes_ingrediente(ingrediente_id=1)

        print(f"\n{'ID':<5} {'Quantidade':<12} {'Validade':<12} {'Dias p/ Vencer':<15} {'Lote':<20}")
        print("-" * 70)

        for lote in lotes:
            lote_id, nome, qtd, unidade, validade, dias, num_lote, fornecedor, preco = lote
            num_lote_str = str(num_lote) if num_lote else 'N/A'
            print(f"{lote_id:<5} {qtd:<12.2f} {validade.strftime('%d/%m/%Y'):<12} {dias:<15} {num_lote_str:<20}")

        print("\nTESTE 1: OK")

    except Exception as e:
        print(f"\nERRO no Teste 1: {str(e)}")
        import traceback
        traceback.print_exc()


def test_entrada_multipla():
    """Teste 2: Registrar várias entradas de uma vez"""

    print("\n" + "=" * 60)
    print("TESTE 2: Entrada Multipla")
    print("=" * 60)

    try:
        db = Database()
        engine = db.connect()
        entrada_service = EntradaEstoque(engine)

        # Simular uma compra com vários itens
        compra = [
            {
                'ingrediente_id': 2,
                'quantidade': 20,
                'data_validade': date.today() + timedelta(days=365),
                'fornecedor_id': 1,
                'numero_lote': 'ACU-2025-005',
                'preco_unitario': 3.40,
                'usuario': 'Maria Santos'
            },
            {
                'ingrediente_id': 3,
                'quantidade': 240,
                'data_validade': date.today() + timedelta(days=21),
                'fornecedor_id': 2,
                'numero_lote': 'OVO-2025-010',
                'preco_unitario': 0.85,
                'usuario': 'Maria Santos'
            },
            {
                'ingrediente_id': 4,
                'quantidade': 30,
                'data_validade': date.today() + timedelta(days=7),
                'fornecedor_id': 2,
                'numero_lote': 'LEI-2025-008',
                'preco_unitario': 4.80,
                'usuario': 'Maria Santos'
            }
        ]

        lotes_criados = entrada_service.registrar_multiplas_entradas(compra)

        print(f"\nTotal de lotes criados: {len(lotes_criados)}")
        print(f"IDs: {lotes_criados}")

        print("\nTESTE 2: OK")

    except Exception as e:
        print(f"\nERRO no Teste 2: {str(e)}")
        import traceback
        traceback.print_exc()


def test_entrada_com_validade_curta():
    """Teste 3: Entrada com validade próxima"""

    print("\n" + "=" * 60)
    print("TESTE 3: Entrada com Validade Proxima")
    print("=" * 60)

    try:
        db = Database()
        engine = db.connect()
        entrada_service = EntradaEstoque(engine)

        # Registrar morangos que vencem em 3 dias
        lote_id = entrada_service.registrar_entrada(
            ingrediente_id=8,
            quantidade=2.5,
            data_validade=date.today() + timedelta(days=3),
            fornecedor_id=3,
            numero_lote="MOR-2025-URGENTE",
            preco_unitario=18.00,
            usuario="Pedro Costa"
        )

        print(f"\nLote de morangos criado: ID {lote_id}")
        print("Sistema deve alertar sobre validade proxima!")

        print("\nTESTE 3: OK")

    except Exception as e:
        print(f"\nERRO no Teste 3: {str(e)}")
        import traceback
        traceback.print_exc()


def test_validacoes():
    """Teste 4: Testar validações"""

    print("\n" + "=" * 60)
    print("TESTE 4: Validacoes")
    print("=" * 60)

    try:
        db = Database()
        engine = db.connect()
        entrada_service = EntradaEstoque(engine)

        # Teste 4.1: Quantidade negativa
        print("\nTeste 4.1: Quantidade negativa (deve dar erro)")
        try:
            entrada_service.registrar_entrada(
                ingrediente_id=1,
                quantidade=-10,
                data_validade=date.today() + timedelta(days=30)
            )
            print("ERRO: Deveria ter rejeitado quantidade negativa!")
        except ValueError as e:
            print(f"Validacao OK: {str(e)}")

        # Teste 4.2: Validade no passado
        print("\nTeste 4.2: Validade no passado (deve dar erro)")
        try:
            entrada_service.registrar_entrada(
                ingrediente_id=1,
                quantidade=10,
                data_validade=date.today() - timedelta(days=30)
            )
            print("ERRO: Deveria ter rejeitado validade passada!")
        except ValueError as e:
            print(f"Validacao OK: {str(e)}")

        # Teste 4.3: Ingrediente inexistente
        print("\nTeste 4.3: Ingrediente inexistente (deve dar erro)")
        try:
            entrada_service.registrar_entrada(
                ingrediente_id=9999,
                quantidade=10,
                data_validade=date.today() + timedelta(days=30)
            )
            print("ERRO: Deveria ter rejeitado ingrediente inexistente!")
        except ValueError as e:
            print(f"Validacao OK: {str(e)}")

        print("\nTESTE 4: OK")

    except Exception as e:
        print(f"\nERRO no Teste 4: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Iniciando testes de entrada de estoque...")
    print("=" * 60)

    test_entrada_simples()
    test_entrada_multipla()
    test_entrada_com_validade_curta()
    test_validacoes()

    print("\n" + "=" * 60)
    print("TODOS OS TESTES CONCLUIDOS!")
    print("=" * 60)