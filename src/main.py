# -*- coding: utf-8 -*-
import sys
import os
from datetime import date, timedelta

# Adicionar pasta raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import Database
from src.services.entrada_estoque import EntradaEstoque
from src.services.saida_estoque import SaidaEstoque
from src.services.alertas import Alertas
from src.analytics.relatorios import Relatorios


class SistemaEstoque:
    """Sistema de Controle de Estoque - Interface CLI"""

    def __init__(self):
        """Inicializa conexão com banco"""
        print("🔧 Iniciando sistema...")
        self.db = Database()
        self.engine = self.db.connect()

        # Inicializar serviços
        self.entrada_service = EntradaEstoque(self.engine)
        self.saida_service = SaidaEstoque(self.engine)
        self.alertas_service = Alertas(self.engine)
        self.relatorios_service = Relatorios(self.engine)

        print("✅ Sistema pronto!\n")

    def limpar_tela(self):
        """Limpa a tela do terminal"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def pausar(self):
        """Pausa para o usuário ler"""
        input("\nPressione ENTER para continuar...")

    def menu_principal(self):
        """Exibe menu principal"""
        while True:
            self.limpar_tela()
            print("=" * 60)
            print("🏪 SISTEMA DE CONTROLE DE ESTOQUE - CONFEITARIA")
            print("=" * 60)
            print("\n📋 MENU PRINCIPAL:\n")
            print("1. 📥 Entrada de Estoque")
            print("2. 📤 Saída de Estoque")
            print("3. 🔔 Alertas e Avisos")
            print("4. 📊 Relatórios e Análises")
            print("5. 📦 Consultar Estoque")
            print("6. ❌ Registrar Perda")
            print("0. 🚪 Sair")
            print("\n" + "=" * 60)

            opcao = input("\nEscolha uma opção: ").strip()

            if opcao == '1':
                self.menu_entrada()
            elif opcao == '2':
                self.menu_saida()
            elif opcao == '3':
                self.menu_alertas()
            elif opcao == '4':
                self.menu_relatorios()
            elif opcao == '5':
                self.consultar_estoque()
            elif opcao == '6':
                self.registrar_perda()
            elif opcao == '0':
                print("\n👋 Até logo!")
                break
            else:
                print("\n❌ Opção inválida!")
                self.pausar()

    def menu_entrada(self):
        """Menu de entrada de estoque"""
        self.limpar_tela()
        print("=" * 60)
        print("📥 ENTRADA DE ESTOQUE")
        print("=" * 60)

        try:
            # Listar ingredientes
            result = self.db.query("SELECT id, nome, unidade_medida FROM ingredientes WHERE ativo = TRUE ORDER BY nome")

            print("\n📋 Ingredientes disponíveis:\n")
            for ing in result:
                print(f"  {ing[0]:2d}. {ing[1]} ({ing[2]})")

            print("\n" + "-" * 60)

            # Coletar dados
            ing_id = int(input("\nID do ingrediente: "))
            quantidade = float(input("Quantidade: "))

            print("\nData de validade:")
            try:
                dia = int(input("  Dia: "))
                mes = int(input("  Mes: "))
                ano = int(input("  Ano: "))
                data_validade = date(ano, mes, dia)
            except ValueError as e:
                print(f"\n Data inválida! Use apenas números.")
                self.pausar()
                return

            numero_lote = input("Número do lote (Enter para pular): ").strip() or None

            preco = input("Preço unitário (Enter para pular): ").strip()
            preco_unitario = float(preco) if preco else None

            # Fornecedores
            fornecedores = self.db.query("SELECT id, nome FROM fornecedores WHERE ativo = TRUE")

            if fornecedores:
                print("\nFornecedores:")
                for forn in fornecedores:
                    print(f"  {forn[0]}. {forn[1]}")

                forn_id = input("\nID do fornecedor (Enter para pular): ").strip()
                fornecedor_id = int(forn_id) if forn_id else None
            else:
                fornecedor_id = None

            usuario = input("Seu nome: ").strip() or "Sistema"

            # Registrar entrada
            print("\n⏳ Registrando entrada...")
            lote_id = self.entrada_service.registrar_entrada(
                ingrediente_id=ing_id,
                quantidade=quantidade,
                data_validade=data_validade,
                fornecedor_id=fornecedor_id,
                numero_lote=numero_lote,
                preco_unitario=preco_unitario,
                usuario=usuario
            )

            print(f"\n✅ Entrada registrada! Lote ID: {lote_id}")

        except Exception as e:
            print(f"\n❌ Erro: {str(e)}")

        self.pausar()

    def menu_saida(self):
        """Menu de saída de estoque"""
        self.limpar_tela()
        print("=" * 60)
        print("📤 SAÍDA DE ESTOQUE (FEFO)")
        print("=" * 60)

        try:
            # Listar ingredientes com estoque
            result = self.db.query("""
                SELECT DISTINCT i.id, i.nome, i.unidade_medida
                FROM ingredientes i
                JOIN lotes_estoque l ON i.id = l.ingrediente_id
                WHERE l.status = 'disponivel' AND l.quantidade_atual > 0
                ORDER BY i.nome
            """)

            print("\n📋 Ingredientes com estoque:\n")
            for ing in result:
                print(f"  {ing[0]:2d}. {ing[1]} ({ing[2]})")

            print("\n" + "-" * 60)

            # Coletar dados
            ing_id = int(input("\nID do ingrediente: "))
            quantidade = float(input("Quantidade a retirar: "))

            # Verificar disponibilidade
            print("\n🔍 Verificando disponibilidade...")
            disp = self.saida_service.verificar_disponibilidade(ing_id, quantidade)

            print(f"\nDisponível: {disp['estoque_disponivel']}{disp['unidade']}")

            if not disp['disponivel']:
                print(f" Estoque insuficiente! Faltam: {disp['quantidade_faltante']}{disp['unidade']}")
                self.pausar()
                return

            # Receitas (opcional)
            receitas = self.db.query("SELECT id, nome FROM receitas WHERE ativo = TRUE")

            if receitas:
                print("\nReceitas:")
                for rec in receitas:
                    print(f"  {rec[0]}. {rec[1]}")

                rec_id = input("\nID da receita (Enter para pular): ").strip()
                receita_id = int(rec_id) if rec_id else None
            else:
                receita_id = None

            motivo = input("Motivo da saída: ").strip() or "Saída de estoque"
            usuario = input("Seu nome: ").strip() or "Sistema"

            # Confirmar
            confirma = input(f"\n  Confirma saída de {quantidade}{disp['unidade']}? (s/n): ")

            if confirma.lower() == 's':
                print("\n⏳ Registrando saída (FEFO)...")
                resultado = self.saida_service.registrar_saida(
                    ingrediente_id=ing_id,
                    quantidade_necessaria=quantidade,
                    receita_id=receita_id,
                    motivo=motivo,
                    usuario=usuario
                )

                print(f"\n✅ {resultado['mensagem']}")
                print(f"   Lotes utilizados: {len(resultado['lotes_consumidos'])}")
            else:
                print("\n Saída cancelada")

        except Exception as e:
            print(f"\n Erro: {str(e)}")

        self.pausar()

    def menu_alertas(self):
        """Menu de alertas"""
        self.limpar_tela()
        print("=" * 60)
        print(" ALERTAS E AVISOS")
        print("=" * 60)

        try:
            # Dashboard resumo
            dashboard = self.alertas_service.dashboard_resumo()

            print(f"\n📊 RESUMO - {dashboard['data_atualizacao'].strftime('%d/%m/%Y')}")
            print("-" * 60)
            print(f"Total de alertas: {dashboard['total_alertas']}")
            print(f"   Vencidos: {dashboard['alertas']['vencidos']}")
            print(f"   Vence em 3 dias: {dashboard['alertas']['vence_em_3_dias']}")
            print(f"   Vence em 7 dias: {dashboard['alertas']['vence_em_7_dias']}")
            print(f"   Estoque crítico: {dashboard['alertas']['estoque_critico']}")
            print(f"   Estoque baixo: {dashboard['alertas']['estoque_baixo']}")

            print("\n" + "=" * 60)
            print("\n1. Ver alertas de validade")
            print("2. Ver estoque baixo")
            print("3. Ver produtos vencidos")
            print("4. Sugestão de compras")
            print("0. Voltar")

            opcao = input("\nEscolha: ").strip()

            if opcao == '1':
                self.ver_alertas_validade()
            elif opcao == '2':
                self.ver_estoque_baixo()
            elif opcao == '3':
                self.ver_produtos_vencidos()
            elif opcao == '4':
                self.ver_sugestao_compras()

        except Exception as e:
            print(f"\n❌ Erro: {str(e)}")

        self.pausar()

    def ver_alertas_validade(self):
        """Mostra alertas de validade"""
        print("\n" + "=" * 60)
        print("⏰ ALERTAS DE VALIDADE")
        print("=" * 60)

        alertas = self.alertas_service.alertas_validade(dias_antecedencia=30)

        if alertas:
            print(f"\n{'Ingrediente':<20} {'Qtd':<10} {'Vence em':<12} {'Status':<10}")
            print("-" * 60)

            for alerta in alertas:
                print(f"{alerta['ingrediente']:<20} "
                      f"{alerta['quantidade']:<10.2f} "
                      f"{alerta['dias_para_vencer']} dias{'':<7} "
                      f"{alerta['nivel_alerta']:<10}")
        else:
            print("\n✅ Nenhum alerta de validade!")

    def ver_estoque_baixo(self):
        """Mostra estoque baixo"""
        print("\n" + "=" * 60)
        print("📉 ESTOQUE BAIXO")
        print("=" * 60)

        alertas = self.alertas_service.alertas_estoque_baixo()

        if alertas:
            print(f"\n{'Ingrediente':<20} {'Atual':<10} {'Mínimo':<10} {'Status':<12}")
            print("-" * 60)

            for alerta in alertas:
                print(f"{alerta['ingrediente']:<20} "
                      f"{alerta['estoque_atual']:<10.2f} "
                      f"{alerta['estoque_minimo']:<10.2f} "
                      f"{alerta['status']:<12}")
        else:
            print("\n✅ Todos os estoques OK!")

    def ver_produtos_vencidos(self):
        """Mostra produtos vencidos"""
        print("\n" + "=" * 60)
        print("🗑️  PRODUTOS VENCIDOS")
        print("=" * 60)

        vencidos = self.alertas_service.produtos_vencidos()

        if vencidos:
            print(f"\n{'Ingrediente':<20} {'Qtd':<10} {'Venceu há':<15}")
            print("-" * 50)

            for item in vencidos:
                print(f"{item['ingrediente']:<20} "
                      f"{item['quantidade']:<10.2f} "
                      f"{item['dias_vencido']} dias")
        else:
            print("\n✅ Nenhum produto vencido!")

    def ver_sugestao_compras(self):
        """Mostra sugestão de compras"""
        print("\n" + "=" * 60)
        print("🛒 SUGESTÃO DE COMPRAS")
        print("=" * 60)

        sugestoes = self.alertas_service.sugestao_compras()

        if sugestoes:
            print(f"\n{'Ingrediente':<20} {'Comprar':<12} {'Prioridade':<15}")
            print("-" * 50)

            for sug in sugestoes:
                print(f"{sug['ingrediente']:<20} "
                      f"{sug['quantidade_sugerida']:<12.2f} "
                      f"{sug['prioridade']:<15}")
        else:
            print("\n✅ Estoque completo!")

    def menu_relatorios(self):
        """Menu de relatórios"""
        self.limpar_tela()
        print("=" * 60)
        print("📊 RELATÓRIOS E ANÁLISES")
        print("=" * 60)

        print("\n1. Resumo executivo")
        print("2. Movimentações recentes")
        print("3. Consumo por ingrediente")
        print("4. Valor do estoque")
        print("5. Giro de estoque")
        print("0. Voltar")

        opcao = input("\nEscolha: ").strip()

        try:
            if opcao == '1':
                self.resumo_executivo()
            elif opcao == '2':
                self.movimentacoes_recentes()
            elif opcao == '3':
                self.consumo_ingredientes()
            elif opcao == '4':
                self.valor_estoque()
            elif opcao == '5':
                self.giro_estoque()
        except Exception as e:
            print(f"\n❌ Erro: {str(e)}")

        self.pausar()

    def resumo_executivo(self):
        """Mostra resumo executivo"""
        print("\n" + "=" * 60)
        print("📈 RESUMO EXECUTIVO")
        print("=" * 60)

        resumo = self.relatorios_service.resumo_executivo()

        print(f"\nData: {resumo['data_relatorio'].strftime('%d/%m/%Y')}")
        print(f"💰 Valor do estoque: R$ {resumo['valor_estoque_total']:,.2f}")
        print(f"📦 Ingredientes com movimento: {resumo['ingredientes_com_movimento']}")
        print(f"🗑️  Perdas (30 dias): {resumo['perdas_ultimos_30_dias']}")
        print(f"📥 Entradas (7 dias): {resumo['entradas_ultimos_7_dias']}")
        print(f"📤 Saídas (7 dias): {resumo['saidas_ultimos_7_dias']}")

    def movimentacoes_recentes(self):
        """Mostra movimentações recentes"""
        print("\n" + "=" * 60)
        print("📋 MOVIMENTAÇÕES RECENTES (7 dias)")
        print("=" * 60)

        df = self.relatorios_service.relatorio_movimentacoes(
            data_inicio=date.today() - timedelta(days=7),
            data_fim=date.today()
        )

        print(f"\nTotal: {len(df)} movimentações")

        if not df.empty:
            print("\nÚltimas 10:")
            print(df[['data', 'tipo', 'ingrediente', 'quantidade', 'usuario']].head(10).to_string(index=False))

    def consumo_ingredientes(self):
        """Mostra consumo por ingrediente"""
        print("\n" + "=" * 60)
        print("📊 CONSUMO POR INGREDIENTE (30 dias)")
        print("=" * 60)

        df = self.relatorios_service.relatorio_consumo_por_ingrediente(dias=30)

        if not df.empty:
            print(f"\nTOP 10 mais consumidos:")
            print(df[['ingrediente', 'consumo_total', 'unidade', 'consumo_medio_dia']].head(10).to_string(index=False))

    def valor_estoque(self):
        """Mostra valor do estoque"""
        print("\n" + "=" * 60)
        print("💰 VALOR DO ESTOQUE")
        print("=" * 60)

        df = self.relatorios_service.relatorio_valor_estoque()

        if not df.empty:
            total = df['valor_total'].sum()
            print(f"\n💰 Valor total: R$ {total:,.2f}")
            print(f"\nTOP 10 itens mais valiosos:")
            print(df[['ingrediente', 'quantidade_total', 'valor_total']].head(10).to_string(index=False))

    def giro_estoque(self):
        """Mostra giro de estoque"""
        print("\n" + "=" * 60)
        print("🔄 GIRO DE ESTOQUE")
        print("=" * 60)

        df = self.relatorios_service.relatorio_giro_estoque(dias=30)

        if not df.empty:
            print(f"\nIngredientes com giro mais rápido:")
            print(df[['ingrediente', 'dias_estoque', 'classificacao_giro']].head(10).to_string(index=False))

    def consultar_estoque(self):
        """Consulta estoque atual"""
        self.limpar_tela()
        print("=" * 60)
        print("📦 ESTOQUE ATUAL")
        print("=" * 60)

        result = self.db.query("SELECT * FROM v_estoque_atual ORDER BY nome")

        print(f"\n{'Ingrediente':<20} {'Qtd Atual':<12} {'Mínimo':<10} {'Ideal':<10} {'Status':<10}")
        print("-" * 70)

        for row in result:
            nome, unidade, categoria, qtd, minimo, ideal, status = row[1], row[2], row[3], row[4], row[5], row[6], row[
                7]
            print(f"{nome:<20} {qtd:<12.2f} {minimo:<10.2f} {ideal:<10.2f} {status:<10}")

        self.pausar()

    def registrar_perda(self):
        """Registra perda de produto"""
        self.limpar_tela()
        print("=" * 60)
        print("❌ REGISTRAR PERDA")
        print("=" * 60)

        try:
            # Listar lotes disponíveis
            result = self.db.query("""
                SELECT l.id, i.nome, l.quantidade_atual, i.unidade_medida, l.numero_lote
                FROM lotes_estoque l
                JOIN ingredientes i ON l.ingrediente_id = i.id
                WHERE l.status = 'disponivel' AND l.quantidade_atual > 0
                ORDER BY i.nome, l.data_validade
            """)

            print("\n📋 Lotes disponíveis:\n")
            for lote in result[:20]:  # Mostrar primeiros 20
                print(f"  {lote[0]:3d}. {lote[1]:<20} - {lote[2]:.2f}{lote[3]} (Lote: {lote[4] or 'N/A'})")

            print("\n" + "-" * 60)

            lote_id = int(input("\nID do lote: "))
            quantidade = float(input("Quantidade perdida: "))
            motivo = input("Motivo da perda: ").strip()
            usuario = input("Seu nome: ").strip() or "Sistema"

            # Confirmar
            confirma = input(f"\n⚠️  Confirma perda de {quantidade}? (s/n): ")

            if confirma.lower() == 's':
                print("\n⏳ Registrando perda...")
                self.saida_service.registrar_perda(
                    lote_id=lote_id,
                    quantidade=quantidade,
                    motivo=motivo,
                    usuario=usuario
                )
                print("\n✅ Perda registrada!")
            else:
                print("\n❌ Cancelado")

        except Exception as e:
            print(f"\n❌ Erro: {str(e)}")

        self.pausar()


def main():
    """Função principal"""
    try:
        sistema = SistemaEstoque()
        sistema.menu_principal()
    except KeyboardInterrupt:
        print("\n\n👋 Sistema encerrado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()