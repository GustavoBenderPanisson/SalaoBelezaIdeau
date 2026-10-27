import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import os
import re
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
            "password": password if password is not None else os.getenv("DB_PASSWORD", "Pedrin#96"),
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
        validar_cliente(nome_completo, telefone, cpf, email, data_nascimento)

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

    def listar_profissionais(self, apenas_ativos: bool = True) -> list[dict[str, Any]]:
        """Retorna os profissionais disponíveis para agendamento."""
        sql = """
            SELECT id_profissional, nome_completo, telefone, email, especialidade, ativo
            FROM profissionais
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


def validar_cliente(
    nome: str, telefone: str, cpf: Optional[str] = None,
    email: Optional[str] = None, data_nascimento: Optional[str] = None,
) -> None:
    """Valida os campos do cliente tanto na interface quanto antes do INSERT."""
    nome = nome.strip()
    if len(nome) < 2 or not any(letra.isalpha() for letra in nome):
        raise ValueError("Informe um nome válido com pelo menos 2 caracteres.")
    if len(nome) > 150:
        raise ValueError("O nome não pode ultrapassar 150 caracteres.")
    telefone = telefone or ""
    digitos_telefone = re.sub(r"[\s()+.-]", "", telefone)
    if not digitos_telefone.isdigit() or not 10 <= len(digitos_telefone) <= 13:
        raise ValueError("Telefone inválido: informe DDD e número (10 ou 11 dígitos; com país, até 13).")
    if cpf:
        if not re.fullmatch(r"[\d.\-\s]+", cpf):
            raise ValueError("CPF inválido: use somente números, pontos e hífen.")
        numeros = re.sub(r"\D", "", cpf)
        if len(numeros) != 11 or len(set(numeros)) == 1:
            raise ValueError("CPF inválido: informe os 11 dígitos.")
        calculado1 = (sum(int(numeros[i]) * (10 - i) for i in range(9)) * 10 % 11) % 10
        calculado2 = (sum(int(numeros[i]) * (11 - i) for i in range(10)) * 10 % 11) % 10
        if numeros[-2:] != f"{calculado1}{calculado2}":
            raise ValueError("CPF inválido: os dígitos verificadores não conferem.")
    if email and (len(email) > 150 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email.strip())):
        raise ValueError("E-mail inválido. Exemplo: nome@dominio.com.")
    if data_nascimento:
        try:
            nascimento = datetime.strptime(data_nascimento, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValueError("Data de nascimento inválida.") from exc
        if nascimento > datetime.now().date():
            raise ValueError("A data de nascimento não pode estar no futuro.")


def imprimir_agendamentos(agendamentos: list[dict[str, Any]]) -> None:
    """Exibe agendamentos no terminal."""
    if not agendamentos:
        print("Nenhum agendamento encontrado.")
        return

    print("\n  CÓD.  DATA/HORA         CLIENTE                  SERVIÇO / PROFISSIONAL")
    print("  " + "─" * 70)
    for item in agendamentos:
        inicio = item["inicio"].strftime("%d/%m/%Y %H:%M")
        fim = item["fim"].strftime("%H:%M")
        print(
            f'  #{item["id_agendamento"]:<4} {inicio}-{fim:<5}  '
            f'{item["cliente"][:23]:<24} {item["servico"][:20]} / {item["profissional"]} [{item["status"]}]'
        )


def _ler_data_hora(mensagem: str) -> datetime:
    valor = input(mensagem).strip()
    try:
        return datetime.strptime(valor, "%d/%m/%Y %H:%M")
    except ValueError as exc:
        raise ValueError("Use o formato DD/MM/AAAA HH:MM (ex.: 25/12/2026 14:30).") from exc


def _selecionar_id(itens: list[dict[str, Any]], chave: str, descricao: str) -> int:
    if not itens:
        raise ValueError(f"Não há {descricao} ativos cadastrados.")
    print(f"\n{descricao.capitalize()} disponíveis:")
    for item in itens:
        nome = item.get("nome_completo") or item.get("nome")
        complemento = item.get("especialidade") or item.get("descricao")
        extra = f" — {complemento}" if complemento else ""
        print(f"  {item[chave]} - {nome}{extra}")
    try:
        selecionado = int(input("Informe o ID desejado: ").strip())
    except ValueError as exc:
        raise ValueError("Informe um ID numérico válido.") from exc
    if not any(item[chave] == selecionado for item in itens):
        raise ValueError("O ID escolhido não está na lista de opções disponíveis.")
    return selecionado


def _titulo(texto: str) -> None:
    largura = 72
    print("\n" + "═" * largura)
    print(f"  {texto}")
    print("═" * largura)


def _campo_validado(rotulo: str, validar, opcional: bool = False) -> str:
    while True:
        valor = input(f"  {rotulo}{' (opcional)' if opcional else ''}: ").strip()
        if opcional and not valor:
            return ""
        try:
            validar(valor)
            return valor
        except ValueError as exc:
            print(f"    ! {exc} Tente novamente.")


def _validar_nome(valor: str) -> None:
    if len(valor) < 2 or not any(ch.isalpha() for ch in valor):
        raise ValueError("Informe um nome com pelo menos 2 caracteres.")
    if len(valor) > 150:
        raise ValueError("Limite de 150 caracteres.")


def _validar_telefone(valor: str) -> None:
    digitos = re.sub(r"[\s()+.-]", "", valor)
    if not digitos.isdigit() or not 10 <= len(digitos) <= 13:
        raise ValueError("Informe DDD e telefone com 10 ou 11 dígitos (até 13 com país).")


def _validar_cpf(valor: str) -> None:
    validar_cliente("Cliente", "11999999999", cpf=valor)


def _validar_email(valor: str) -> None:
    validar_cliente("Cliente", "11999999999", email=valor)


def _validar_data_nascimento(valor: str) -> None:
    try:
        data = datetime.strptime(valor, "%d/%m/%Y").date()
    except ValueError as exc:
        raise ValueError("Use DD/MM/AAAA e informe uma data existente.") from exc
    if data > datetime.now().date():
        raise ValueError("A data não pode estar no futuro.")


def cadastrar_cliente_interativo(banco: SalaoDatabase) -> None:
    """Coleta, valida e apresenta uma prévia antes de inserir o cliente."""
    while True:
        _titulo("NOVO CADASTRO DE CLIENTE")
        print("  Campos opcionais podem ser deixados em branco.\n")
        nome = _campo_validado("Nome completo", _validar_nome)
        telefone = _campo_validado("Telefone com DDD", _validar_telefone)
        cpf = _campo_validado("CPF", _validar_cpf, opcional=True)
        email = _campo_validado("E-mail", _validar_email, opcional=True)
        nascimento = _campo_validado("Nascimento (DD/MM/AAAA)", _validar_data_nascimento, opcional=True)
        observacoes = input("  Observações (opcional): ").strip() or None
        _titulo("CONFIRA OS DADOS")
        print(f"  Nome       : {nome}\n  Telefone   : {telefone}")
        print(f"  CPF        : {cpf or '—'}\n  E-mail     : {email or '—'}")
        print(f"  Nascimento : {nascimento or '—'}\n  Observações: {observacoes or '—'}")
        decisao = input("\n  Confirmar cadastro? [S]im / [R]efazer / [C]ancelar: ").strip().casefold()
        if decisao in ("r", "refazer"):
            continue
        if decisao not in ("s", "sim"):
            print("\n  Cadastro cancelado; nenhum dado foi gravado.\n")
            return
        data_iso = datetime.strptime(nascimento, "%d/%m/%Y").date().isoformat() if nascimento else None
        novo_id = banco.cadastrar_cliente(nome, telefone, cpf or None, email or None, data_iso, observacoes)
        print(f"\n  ✓ Cliente cadastrado com sucesso. Código: {novo_id}\n")
        return


def executar_menu() -> None:
    """Executa o sistema interativo de clientes e agendamentos."""
    banco = SalaoDatabase()
    try:
        banco.conectar()
        while True:
            _titulo("SALÃO DE BELEZA  |  CLIENTES & AGENDAMENTOS")
            print("\n  CLIENTES")
            print("    1   Cadastrar cliente")
            print("    2   Listar clientes")
            print("\n  AGENDA")
            print("    3   Criar agendamento")
            print("    4   Ver agendamentos")
            print("    5   Cancelar agendamento")
            print("\n    0   Sair\n")
            opcao = input("Escolha uma opção: ").strip()
            try:
                if opcao == "1":
                    cadastrar_cliente_interativo(banco)
                elif opcao == "2":
                    _titulo("CLIENTES CADASTRADOS")
                    clientes = banco.listar_clientes()
                    if not clientes:
                        print("\n  Nenhum cliente cadastrado.\n")
                    for cliente in clientes:
                        print(f'\n  #{cliente["id_cliente"]:<5} {cliente["nome_completo"]}\n         {cliente["telefone"]}  ·  {cliente.get("email") or "—"}')
                elif opcao == "3":
                    _titulo("NOVO AGENDAMENTO")
                    id_cliente = _selecionar_id(banco.listar_clientes(), "id_cliente", "clientes")
                    id_profissional = _selecionar_id(banco.listar_profissionais(), "id_profissional", "profissionais")
                    id_servico = _selecionar_id(banco.listar_servicos(), "id_servico", "serviços")
                    inicio = _ler_data_hora("Data e hora (DD/MM/AAAA HH:MM): ")
                    observacoes = input("Observações (opcional): ").strip() or None
                    if input("\nConfirmar criação do agendamento? [S/N]: ").strip().casefold() not in ("s", "sim"):
                        print("Agendamento não foi gravado.")
                        continue
                    novo_id = banco.cadastrar_agendamento(id_cliente, id_profissional, id_servico, inicio, observacoes)
                    print(f"Agendamento criado com sucesso. Código: {novo_id}")
                elif opcao == "4":
                    _titulo("AGENDA DE ATENDIMENTOS")
                    imprimir_agendamentos(banco.listar_agendamentos())
                elif opcao == "5":
                    try:
                        id_agendamento = int(input("Código do agendamento: ").strip())
                    except ValueError as exc:
                        raise ValueError("Informe um código numérico válido.") from exc
                    motivo = input("Motivo do cancelamento: ").strip()
                    banco.cancelar_agendamento(id_agendamento, motivo)
                    print("Agendamento cancelado.")
                elif opcao == "0":
                    print("Até logo!")
                    break
                else:
                    print("Opção inválida. Tente novamente.")
            except (RuntimeError, ValueError) as exc:
                print(f"Não foi possível concluir a operação: {exc}")
    except RuntimeError as exc:
        print(f"Erro de conexão: {exc}")
    finally:
        banco.fechar()


if __name__ == "__main__":
    executar_menu()