# -*- coding: utf-8 -*-
print("=" * 60)
print("Iniciando testes de alertas...")
print("=" * 60)

try:
    print("\n1. Importando módulos...")
    from src.database.connection import Database
    from src.services.alertas import Alertas

    print("   ✅ Imports OK")

    print("\n2. Conectando ao banco...")
    db = Database()
    engine = db.connect()
    print("   ✅ Conexão OK")

    print("\n3. Criando serviço de alertas...")
    alertas_service = Alertas(engine)
    print("   ✅ Serviço criado")

    print("\n4. Testando alertas de validade...")
    alertas = alertas_service.alertas_validade(dias_antecedencia=30)
    print(f"   ✅ Encontrados {len(alertas)} alertas de validade")

    if alertas:
        print("\n   Detalhes:")
        for i, alerta in enumerate(alertas[:5], 1):  # Mostrar só os 5 primeiros
            print(f"   {i}. {alerta['ingrediente']}: {alerta['quantidade']} {alerta['unidade']} "
                  f"(vence em {alerta['dias_para_vencer']} dias - {alerta['nivel_alerta']})")

    print("\n5. Testando estoque baixo...")
    estoque_baixo = alertas_service.alertas_estoque_baixo()
    print(f"   ✅ Encontrados {len(estoque_baixo)} itens com estoque baixo")

    if estoque_baixo:
        print("\n   Detalhes:")
        for i, item in enumerate(estoque_baixo[:5], 1):
            print(f"   {i}. {item['ingrediente']}: {item['estoque_atual']} {item['unidade']} "
                  f"({item['status']})")

    print("\n6. Testando produtos vencidos...")
    vencidos = alertas_service.produtos_vencidos()
    print(f"   ✅ Encontrados {len(vencidos)} produtos vencidos")

    print("\n7. Testando dashboard...")
    dashboard = alertas_service.dashboard_resumo()
    print(f"   ✅ Dashboard gerado")
    print(f"   📊 Total de alertas: {dashboard['total_alertas']}")

    print("\n" + "=" * 60)
    print("🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
    print("=" * 60)

except Exception as e:
    print(f"\n❌ ERRO: {str(e)}")
    print("\nDetalhes do erro:")
    import traceback

    traceback.print_exc()