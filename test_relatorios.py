# -*- coding: utf-8 -*-
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.database.connection import Database
from src.analytics.relatorios import Relatorios
from datetime import date, timedelta


def test_movimentacoes():
    """Teste 1: Relatório de movimentações"""

    print("\n" + "=" * 60)
    print("TESTE 1: Relatório de Movimentações")
    print("=" * 60)

    try:
        db = Database()
        engine = db.connect()
        relatorios = Relatorios(engine)

        # Últimos 7 dias
        df = relatorios.relatorio_movimentacoes(
            data_inicio=date.today() - timedelta(days=7),
            data_fim=date.today()
        )

        print(f"\nTotal de movimentações (7 dias): {len(df)}")

        if not df.empty:
            print(f"\nPor tipo:")
            print(df['tipo'].value_counts())

            print(f"\nÚltimas 5 movimentações:")
            print(df[['data', 'tipo', 'ingrediente', 'quantidade', 'unidade']].head())

        print("\nTESTE 1: OK")

    except Exception as e:
        print(f"\nERRO: {str(e)}")
        import traceback
        traceback.print_exc()


def test_consumo():
    """Teste 2: Análise de consumo"""

    print("\n" + "=" * 60)
    print("TESTE 2: Análise de Consumo")
    print("=" * 60)

    try:
        db = Database()
        engine = db.connect()
        relatorios = Relatorios(engine)

        df = relatorios.relatorio_consumo_por_ingrediente(dias=30)

        print(f"\nIngredientes com consumo (30 dias): {len(df)}")

        if not df.empty:
            print(f"\nTOP 5 mais consumidos:")
            top5 = df.nlargest(5, 'consumo_total')
            for idx, row in top5.iterrows():
                print(f"  {row['ingrediente']}: {row['consumo_total']}{row['unidade']} "
                      f"(média: {row['consumo_medio_dia']}{row['unidade']}/dia)")

        print("\nTESTE 2: OK")

    except Exception as e:
        print(f"\nERRO: {str(e)}")
        import traceback
        traceback.print_exc()


def test_valor_estoque():
    """Teste 3: Valor do estoque"""

    print("\n" + "=" * 60)
    print("TESTE 3: Valor do Estoque")
    print("=" * 60)

    try:
        db = Database()
        engine = db.connect()
        relatorios = Relatorios(engine)

        df = relatorios.relatorio_valor_estoque()

        if not df.empty:
            valor_total = df['valor_total'].sum()
            print(f"\n💰 Valor total do estoque: R$ {valor_total:,.2f}")

            print(f"\nTOP 5 itens mais valiosos:")
            for idx, row in df.head().iterrows():
                print(f"  {row['ingrediente']}: R$ {row['valor_total']:,.2f} "
                      f"({row['quantidade_total']}{row['unidade']})")
        else:
            print("\nNenhum item com preço cadastrado")

        print("\nTESTE 3: OK")

    except Exception as e:
        print(f"\nERRO: {str(e)}")
        import traceback
        traceback.print_exc()


def test_giro_estoque():
    """Teste 4: Giro de estoque"""

    print("\n" + "=" * 60)
    print("TESTE 4: Giro de Estoque")
    print("=" * 60)

    try:
        db = Database()
        engine = db.connect()
        relatorios = Relatorios(engine)

        df = relatorios.relatorio_giro_estoque(dias=30)

        print(f"\nIngredientes analisados: {len(df)}")

        if not df.empty:
            print(f"\nClassificação do giro:")
            print(df['classificacao_giro'].value_counts())

            print(f"\nGiro mais rápido (estoque dura menos):")
            for idx, row in df.head(3).iterrows():
                if pd.notna(row['dias_estoque']):
                    print(f"  {row['ingrediente']}: {row['dias_estoque']:.1f} dias de estoque")

        print("\nTESTE 4: OK")

    except Exception as e:
        print(f"\nERRO: {str(e)}")
        import traceback
        traceback.print_exc()


def test_resumo_executivo():
    """Teste 5: Resumo executivo"""

    print("\n" + "=" * 60)
    print("TESTE 5: Resumo Executivo")
    print("=" * 60)

    try:
        db = Database()
        engine = db.connect()
        relatorios = Relatorios(engine)

        resumo = relatorios.resumo_executivo()

        print(f"\n📊 RESUMO EXECUTIVO - {resumo['data_relatorio'].strftime('%d/%m/%Y')}")
        print("=" * 60)
        print(f"💰 Valor do estoque: R$ {resumo['valor_estoque_total']:,.2f}")
        print(f"📦 Ingredientes ativos: {resumo['ingredientes_com_movimento']}")
        print(f"🗑️  Perdas (30 dias): {resumo['perdas_ultimos_30_dias']}")
        print(f"📥 Entradas (7 dias): {resumo['entradas_ultimos_7_dias']}")
        print(f"📤 Saídas (7 dias): {resumo['saidas_ultimos_7_dias']}")
        print(f"📈 Taxa de movimentação: {resumo['taxa_movimentacao']}%")

        print("\nTESTE 5: OK")

    except Exception as e:
        print(f"\nERRO: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Iniciando testes de relatórios...")
    print("=" * 60)

    import pandas as pd

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)

    test_movimentacoes()
    test_consumo()
    test_valor_estoque()
    test_giro_estoque()
    test_resumo_executivo()

    print("\n" + "=" * 60)
    print("🎉 TODOS OS TESTES DE RELATÓRIOS CONCLUÍDOS!")
    print("=" * 60)