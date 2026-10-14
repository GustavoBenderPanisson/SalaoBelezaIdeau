import os
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

import mysql.connector
from mysql.connector import Error


class SalaoDatabase:
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ) -> None:
        self.config = {
            "host": host or os.getenv("DB_HOST", "localhost"),
            "port": port or int(os.getenv("DB_PORT", "3306")),
            "user": user or os.getenv("DB_USER", "root"),
            "password": password if password is not None else os.getenv("DB_PASSWORD", "Mude este texto para a senha do MYSQL"),
            "database": database or os.getenv("DB_NAME", "salao_beleza"),
        }
        self.connection: Optional[mysql.connector.MySQLConnection] = None

    def conectar(self) -> None:
        """Abre a conexão com o MySQL."""
        if self.connection and self.connection.is_connected():
            return

        try:
            self.connection = mysql.connector.connect(**self.config)
            print("Conexão com o banco realizada com sucesso.")
        except Error as exc:
            raise RuntimeError(f"Não foi possível conectar ao MySQL: {exc}") from exc

    def fechar(self) -> None:
        """Fecha a conexão com o banco."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Conexão encerrada.")

    def _cursor(self):
        self.conectar()
        return self.connection.cursor(dictionary=True)

    def cadastrar_cliente(
        self,
        nome_completo: str,
        telefone: str,
        cpf: Optional[str] = None,
        email: Optional[str] = None,
        data_nascimento: Optional[str] = None,
        observacoes: Optional[str] = None,
    ) -> int:
        """Cadastra um cliente e retorna o ID criado."""
        if not nome_completo.strip() or not telefone.strip():
            raise ValueError("Nome e telefone são obrigatórios.")

        sql = """
            INSERT INTO clientes
                (nome_completo, cpf, telefone, email, data_nascimento, observacoes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        valores = (
            nome_completo.strip(),
            cpf or None,
            telefone.strip(),
            email or None,
            data_nascimento or None,
            observacoes or None,
        )

        cursor = self._cursor()
        try:
            cursor.execute(sql, valores)
            self.connection.commit()
            return cursor.lastrowid
        except Error as exc:
            self.connection.rollback()
            raise RuntimeError(f"Erro ao cadastrar cliente: {exc}") from exc
        finally:
            cursor.close()

    def listar_clientes(self, apenas_ativos: bool = True) -> list[dict[str, Any]]:
        """Retorna os clientes cadastrados."""
        sql = """
            SELECT id_cliente, nome_completo, cpf, telefone, email,
                   data_nascimento, observacoes, ativo
            FROM clientes
        """
        if apenas_ativos:
            sql += " WHERE ativo = TRUE"
        sql += " ORDER BY nome_completo"

        cursor = self._cursor()
        try:
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def cadastrar_agendamento(
        self,
        id_cliente: int,
        id_profissional: int,
        id_servico: int,
        inicio: str | datetime,
        observacoes: Optional[str] = None,
    ) -> int:
        """Cadastra um agendamento. O campo fim é calculado pelo trigger do banco."""
        if isinstance(inicio, str):
            try:
                inicio = datetime.fromisoformat(inicio)
            except ValueError as exc:
                raise ValueError(
                    "O início deve estar no formato YYYY-MM-DD HH:MM:SS."
                ) from exc

        sql = """
            INSERT INTO agendamentos
                (id_cliente, id_profissional, id_servico, inicio, observacoes)
            VALUES (%s, %s, %s, %s, %s)
        """
        valores = (id_cliente, id_profissional, id_servico, inicio, observacoes or None)

        cursor = self._cursor()
        try:
            cursor.execute(sql, valores)
            self.connection.commit()
            return cursor.lastrowid
        except Error as exc:
            self.connection.rollback()
            raise RuntimeError(f"Erro ao cadastrar agendamento: {exc}") from exc
        finally:
            cursor.close()

    def listar_agendamentos(
        self,
        a_partir_de: Optional[str | datetime] = None,
        somente_ativos: bool = False,
    ) -> list[dict[str, Any]]:
        """Lista agendamentos com os nomes relacionados."""
        sql = """
            SELECT
                a.id_agendamento,
                c.nome_completo AS cliente,
                c.telefone AS telefone_cliente,
                p.nome_completo AS profissional,
                s.nome AS servico,
                a.inicio,
                a.fim,
                a.status,
                a.motivo_cancelamento,
                a.observacoes
            FROM agendamentos a
            JOIN clientes c ON c.id_cliente = a.id_cliente
            JOIN profissionais p ON p.id_profissional = a.id_profissional
            JOIN servicos s ON s.id_servico = a.id_servico
        """
        filtros = []
        parametros: list[Any] = []

        if a_partir_de is not None:
            if isinstance(a_partir_de, str):
                a_partir_de = datetime.fromisoformat(a_partir_de)
            filtros.append("a.inicio >= %s")
            parametros.append(a_partir_de)

        if somente_ativos:
            filtros.append("a.status IN ('AGENDADO', 'CONFIRMADO')")

        if filtros:
            sql += " WHERE " + " AND ".join(filtros)
        sql += " ORDER BY a.inicio"

        cursor = self._cursor()
        try:
            cursor.execute(sql, parametros)
            return cursor.fetchall()
        finally:
            cursor.close()

    def cancelar_agendamento(self, id_agendamento: int, motivo: str) -> None:
        """Cancela um agendamento por meio da procedure do banco."""
        cursor = self._cursor()
        try:
            cursor.callproc("cancelar_agendamento", (id_agendamento, motivo))
            self.connection.commit()
        except Error as exc:
            self.connection.rollback()
            raise RuntimeError(f"Erro ao cancelar agendamento: {exc}") from exc
        finally:
            cursor.close()

    def listar_servicos(self, apenas_ativos: bool = True) -> list[dict[str, Any]]:
        """Retorna os serviços disponíveis."""
        sql = """
            SELECT id_servico, nome, descricao, duracao_minutos, preco, ativo
            FROM servicos
        """
        if apenas_ativos:
            sql += " WHERE ativo = TRUE"
        sql += " ORDER BY nome"

        cursor = self._cursor()
        try:
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()


def imprimir_agendamentos(agendamentos: list[dict[str, Any]]) -> None:
    """Exibe agendamentos no terminal."""
    if not agendamentos:
        print("Nenhum agendamento encontrado.")
        return

    for item in agendamentos:
        inicio = item["inicio"].strftime("%d/%m/%Y %H:%M")
        fim = item["fim"].strftime("%H:%M")
        print(
            f'#{item["id_agendamento"]} | {inicio}-{fim} | '
            f'{item["cliente"]} | {item["servico"]} | '
            f'{item["profissional"]} | {item["status"]}'
        )


def exemplo_de_uso() -> None:
    """Exemplo mínimo de uso da classe."""
    banco = SalaoDatabase()
    try:
        banco.conectar()

        print("\nClientes:")
        for cliente in banco.listar_clientes():
            print(f'#{cliente["id_cliente"]} - {cliente["nome_completo"]} - {cliente["telefone"]}')

        print("\nServiços:")
        for servico in banco.listar_servicos():
            preco = Decimal(servico["preco"])
            print(f'#{servico["id_servico"]} - {servico["nome"]} - R$ {preco:.2f}')

        print("\nAgendamentos:")
        imprimir_agendamentos(banco.listar_agendamentos(somente_ativos=True))
    except (RuntimeError, ValueError) as exc:
        print(f"Erro: {exc}")
    finally:
        banco.fechar()


if __name__ == "__main__":
    exemplo_de_uso()
