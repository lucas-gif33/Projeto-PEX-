# -*- coding: utf-8 -*-
print("Iniciando teste de conexao...")

try:
    from src.database.connection import Database

    print("✅ Import da Database OK")

    db = Database()
    print("✅ Objeto Database criado")

    engine = db.connect()
    print("✅ Conexão estabelecida")

    result = db.query("SELECT COUNT(*) FROM ingredientes")
    print(f"✅ Query executada: {result[0][0]} ingredientes")

    print("\n🎉 Conexão funcionando perfeitamente!")

except Exception as e:
    print(f"\n❌ ERRO: {str(e)}")
    import traceback

    traceback.print_exc()