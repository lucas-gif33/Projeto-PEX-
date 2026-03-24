import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO, encoding='utf-8')
logger = logging.getLogger(__name__)


class Database:
    """Gerencia conexão com PostgreSQL com encoding UTF-8"""

    def __init__(self):
        self.host = os.getenv('DB_HOST')
        self.port = os.getenv('DB_PORT')
        self.database = os.getenv('DB_NAME')
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.engine = None

    def connect(self):
        """Cria conexão com banco forçando UTF-8"""
        try:
            # String de conexão
            conn_string = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

            # Criar engine COM encoding UTF-8 forçado
            self.engine = create_engine(
                conn_string,
                poolclass=NullPool,
                connect_args={
                    'client_encoding': 'utf8',
                    'options': '-c client_encoding=UTF8'
                },
                echo=False
            )

            # Testar conexão
            with self.engine.connect() as conn:
                conn.execute(text("SET CLIENT_ENCODING TO 'UTF8';"))
                conn.execute(text("SELECT 1"))
                conn.commit()

            logger.info("✅ Conectado ao banco de dados com sucesso!")
            return self.engine

        except Exception as e:
            logger.error(f"❌ Erro ao conectar: {str(e)}")
            raise

    def execute_sql_file(self, filepath):
        """Executa arquivo SQL com encoding UTF-8"""
        try:
            # Ler arquivo forçando UTF-8
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                sql = file.read()

            with self.engine.connect() as conn:
                # Garantir UTF-8
                conn.execute(text("SET CLIENT_ENCODING TO 'UTF8';"))

                for statement in sql.split(';'):
                    if statement.strip():
                        conn.execute(text(statement))
                conn.commit()

            logger.info(f"✅ SQL executado: {filepath}")

        except Exception as e:
            logger.error(f"❌ Erro ao executar SQL: {str(e)}")
            raise

    def query(self, sql, params=None):
        """Executa consulta e retorna resultados"""
        try:
            with self.engine.connect() as conn:
                # Garantir UTF-8
                conn.execute(text("SET CLIENT_ENCODING TO 'UTF8';"))
                result = conn.execute(text(sql), params or {})
                return result.fetchall()
        except Exception as e:
            logger.error(f"❌ Erro na consulta: {str(e)}")
            raise

    def execute(self, sql, params=None):
        """Executa comando SQL (INSERT, UPDATE, DELETE)"""
        try:
            with self.engine.connect() as conn:
                # Garantir UTF-8
                conn.execute(text("SET CLIENT_ENCODING TO 'UTF8';"))
                conn.execute(text(sql), params or {})
                conn.commit()
            logger.info("✅ Comando executado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao executar comando: {str(e)}")
            raise