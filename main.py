from datetime import datetime
import os
import tkinter as tk
from tkinter import messagebox, ttk

from PIL import Image, ImageTk

from salao_beleza_19 import SalaoDatabase, validar_cliente


class SalaoApp:

  def __init__(self, root):
    self.root = root
    self.root.title("Márcia Gava - Salão de Beleza")
    self.root.geometry("900x720")
    self.root.configure(bg="#000000")  # Fundo totalmente preto

    self.COR_BG = "#000000"  # Preto absoluto
    self.COR_CARD = "#141414"  # Preto suave para elementos
    self.COR_DOURADO = "#c5a059"  # Tom de dourado elegante da logo
    self.COR_TEXTO = "#e6d5b8"  # Champagne / Dourado claro para leitura
    self.COR_BOTAO_BG = "#c5a059"  # Botão dourado
    self.COR_BOTAO_FG = "#000000"  # Texto preto no botão
    self.COR_CINZA_TABELA = "#1c1c1c"  # Cinza escuro para o fundo da tabela
    self.COR_CINZA_CABECALHO = "#2a2a2a"  # Cinza para o cabeçalho da tabela

    self.estilo = ttk.Style()
    self.estilo.theme_use("clam")

    self.estilo.configure("TFrame", background=self.COR_BG)
    self.estilo.configure(
        "TLabel",
        background=self.COR_BG,
        foreground=self.COR_TEXTO,
        font=("Arial", 10),
    )

    self.estilo.configure(
        "TButton",
        background=self.COR_BOTAO_BG,
        foreground=self.COR_BOTAO_FG,
        font=("Arial", 11, "bold"),
        borderwidth=0,
    )
    self.estilo.map(
        "TButton",
        background=[("active", "#dfbe7b")],
        foreground=[("active", "#000000")],
    )

    self.estilo.configure(
        "TCombobox",
        fieldbackground="#1c1c1c",
        background="#1c1c1c",
        foreground="#ffffff",
        darkcolor="#1c1c1c",
        lightcolor="#1c1c1c",
        bordercolor="#c5a059",
        arrowcolor="#c5a059",
    )
    self.estilo.map(
        "TCombobox",
        fieldbackground=[("readonly", "#1c1c1c"), ("active", "#1c1c1c")],
        foreground=[("readonly", "#ffffff"), ("active", "#ffffff")],
    )

    self.estilo.configure(
        "Treeview",
        background=self.COR_CINZA_TABELA,
        foreground=self.COR_TEXTO,
        fieldbackground=self.COR_CINZA_TABELA,
        font=("Arial", 10),
        rowheight=25,
    )
    self.estilo.configure(
        "Treeview.Heading",
        background=self.COR_CINZA_CABECALHO,
        foreground=self.COR_DOURADO,
        font=("Arial", 10, "bold"),
    )
    self.estilo.map(
        "Treeview",
        background=[("selected", self.COR_DOURADO)],
        foreground=[("selected", "#000000")],
    )

    self.db = SalaoDatabase()
    try:
      self.db.conectar()
    except Exception as e:
      messagebox.showerror(
          "Erro de Conexão", f"Não foi possível conectar ao banco de dados: {e}"
      )

    self.logo_img = None
    self.logo_grande = None
    if os.path.exists("logo.png"):
      try:
        img_aberta = Image.open("logo.png")

        fator = 130 / float(img_aberta.size[0])
        img_redimensionada = img_aberta.resize(
            (130, int(float(img_aberta.size[1]) * fator)), Image.Resampling.LANCZOS
        )
        self.logo_img = ImageTk.PhotoImage(img_redimensionada)

        fator_g = 150 / float(img_aberta.size[0])
        img_g_red = img_aberta.resize(
            (150, int(float(img_aberta.size[1]) * fator_g)),
            Image.Resampling.LANCZOS,
        )
        self.logo_grande = ImageTk.PhotoImage(img_g_red)
      except Exception as e:
        print(f"Erro ao carregar logo: {e}")

    self.container = ttk.Frame(self.root)
    self.container.pack(fill="both", expand=True)

    self.frames = {}

    for F in (
        TelaHome,
        TelaCadastrarCliente,
        TelaCadastrarFuncionario,
        TelaCadastrarServico,
        TelaNovoAgendamento,
        TelaAtendimentoPendente,
        TelaConsultarCadastros,
    ):
      nome_classe = F.__name__
      frame = F(parent=self.container, controller=self)
      self.frames[nome_classe] = frame
      frame.grid(row=0, column=0, sticky="nsew")

    self.container.grid_rowconfigure(0, weight=1)
    self.container.grid_columnconfigure(0, weight=1)

    self.mostrar_frame("TelaHome")

  def mostrar_frame(self, nome_classe):
    frame = self.frames[nome_classe]
    if nome_classe == "TelaNovoAgendamento":
      frame.carregar_dados()
    elif nome_classe == "TelaAtendimentoPendente":
      frame.atualizar_lista_pendentes()
    frame.tkraise()


# --- TELA INICIAL (HOME) ---
class TelaHome(ttk.Frame):

  def __init__(self, parent, controller):
    super().__init__(parent)
    self.controller = controller

    center_frame = ttk.Frame(self)
    center_frame.place(relx=0.5, rely=0.5, anchor="center")

    if controller.logo_grande:
      lbl_logo = tk.Label(
          center_frame, image=controller.logo_grande, bg=controller.COR_BG, bd=0
      )
      lbl_logo.pack(pady=3)

    lbl_titulo1 = tk.Label(
        center_frame,
        text="Márcia Gava",
        font=("Arial", 18, "bold"),
        fg=controller.COR_DOURADO,
        bg=controller.COR_BG,
    )
    lbl_titulo1.pack(pady=1)

    lbl_titulo2 = tk.Label(
        center_frame,
        text="Salão de Beleza",
        font=("Arial", 12),
        fg=controller.COR_TEXTO,
        bg=controller.COR_BG,
    )
    lbl_titulo2.pack(pady=2)

    botoes_info = [
        ("Cadastrar Cliente", "TelaCadastrarCliente"),
        ("Cadastrar Funcionário", "TelaCadastrarFuncionario"),
        ("Cadastrar Serviço", "TelaCadastrarServico"),
        ("Novo Agendamento", "TelaNovoAgendamento"),
        ("Atendimento Pendente", "TelaAtendimentoPendente"),
        ("Consultar Cadastros", "TelaConsultarCadastros"),
    ]

    btn_frame = ttk.Frame(center_frame)
    btn_frame.pack(pady=8)

    for texto, destino in botoes_info:
      btn = ttk.Button(
          btn_frame,
          text=texto,
          width=28,
          command=lambda d=destino: controller.mostrar_frame(d),
      )
      btn.pack(pady=4, ipady=2)


# --- CLASSE BASE PARA AS ABAS ---
class BaseTela(ttk.Frame):

  def __init__(self, parent, controller, titulo):
    super().__init__(parent)
    self.controller = controller

    header_frame = ttk.Frame(self)
    header_frame.pack(pady=5)

    if controller.logo_img:
      lbl_logo = tk.Label(
          header_frame, image=controller.logo_img, bg=controller.COR_BG, bd=0
      )
      lbl_logo.pack(pady=2)

    lbl_titulo = tk.Label(
        header_frame,
        text=titulo,
        font=("Arial", 11, "bold"),
        fg=controller.COR_DOURADO,
        bg=controller.COR_BG,
    )
    lbl_titulo.pack(pady=2)

    btn_voltar = ttk.Button(
        self,
        text="⬅ Voltar ao Início",
        command=lambda: controller.mostrar_frame("TelaHome"),
    )
    btn_voltar.pack(anchor="w", padx=15, pady=2)


# --- TELA 1: CADASTRAR CLIENTE ---
class TelaCadastrarCliente(BaseTela):

  def __init__(self, parent, controller):
    super().__init__(parent, controller, "MÁRCIA GAVA — CADASTRO DE CLIENTE")

    form_frame = ttk.Frame(self)
    form_frame.pack(pady=2)

    self.entries_cliente = {}
    campos = [
        ("Nome Completo *", "nome"),
        ("Telefone com DDD *", "telefone"),
        ("CPF", "cpf"),
        ("E-mail", "email"),
        ("Nascimento (DD/MM/AAAA)", "nascimento"),
        ("Observações", "observacoes"),
    ]

    for i, (rotulo, chave) in enumerate(campos):
      lbl = tk.Label(
          form_frame,
          text=rotulo,
          width=25,
          anchor="w",
          fg=controller.COR_TEXTO,
          bg=controller.COR_BG,
          font=("Arial", 9),
      )
      lbl.grid(row=i, column=0, sticky="w", pady=3)
      entry = tk.Entry(
          form_frame,
          width=35,
          bg="#1c1c1c",
          fg="#ffffff",
          insertbackground="white",
          relief="flat",
      )
      entry.grid(row=i, column=1, pady=3, ipady=2)
      self.entries_cliente[chave] = entry

    btn_salvar = ttk.Button(
        self, text="Salvar Cliente", command=self.salvar_cliente
    )
    btn_salvar.pack(pady=10)

  def salvar_cliente(self):
    nome = self.entries_cliente["nome"].get()
    telefone = self.entries_cliente["telefone"].get()
    cpf = self.entries_cliente["cpf"].get() or None
    email = self.entries_cliente["email"].get() or None
    nascimento_input = self.entries_cliente["nascimento"].get().strip()
    obs = self.entries_cliente["observacoes"].get() or None

    nascimento = None
    if nascimento_input:
      try:
        nascimento = datetime.strptime(
            nascimento_input, "%d/%m/%Y"
        ).date().isoformat()
      except ValueError:
        messagebox.showerror(
            "Erro", "Data inválida. Use DD/MM/AAAA (ex: 25/12/2000)."
        )
        return

    try:
      novo_id = self.controller.db.cadastrar_cliente(
          nome, telefone, cpf, email, nascimento, obs
      )
      messagebox.showinfo("Sucesso", f"Cliente cadastrado com ID: {novo_id}")
      for entry in self.entries_cliente.values():
        entry.delete(0, tk.END)
    except Exception as e:
      messagebox.showerror("Erro ao Cadastrar", str(e))


# --- TELA 2: CADASTRAR FUNCIONÁRIO ---
class TelaCadastrarFuncionario(BaseTela):

  def __init__(self, parent, controller):
    super().__init__(parent, controller, "MÁRCIA GAVA — CADASTRO DE FUNCIONÁRIO")

    form_frame = ttk.Frame(self)
    form_frame.pack(pady=2)

    self.entries_profissional = {}
    campos = [
        ("Nome Completo *", "nome"),
        ("Telefone com DDD *", "telefone"),
        ("E-mail", "email"),
        ("Especialidade", "especialidade"),
    ]

    for i, (rotulo, chave) in enumerate(campos):
      lbl = tk.Label(
          form_frame,
          text=rotulo,
          width=25,
          anchor="w",
          fg=controller.COR_TEXTO,
          bg=controller.COR_BG,
          font=("Arial", 9),
      )
      lbl.grid(row=i, column=0, sticky="w", pady=4)
      entry = tk.Entry(
          form_frame,
          width=35,
          bg="#1c1c1c",
          fg="#ffffff",
          insertbackground="white",
          relief="flat",
      )
      entry.grid(row=i, column=1, pady=4, ipady=2)
      self.entries_profissional[chave] = entry

    btn_salvar_prof = ttk.Button(
        self, text="Salvar Funcionário", command=self.salvar_profissional
    )
    btn_salvar_prof.pack(pady=10)

  def salvar_profissional(self):
    nome = self.entries_profissional["nome"].get().strip()
    telefone = self.entries_profissional["telefone"].get().strip()
    email = self.entries_profissional["email"].get().strip() or None
    especialidade = (
        self.entries_profissional["especialidade"].get().strip() or None
    )

    if not nome or not telefone:
      messagebox.showerror(
          "Erro", "Preencha os campos obrigatórios do funcionário (*)."
      )
      return

    try:
      cursor = self.controller.db._cursor()
      sql = """
                INSERT INTO profissionais (nome_completo, telefone, email, especialidade)
                VALUES (%s, %s, %s, %s)
            """
      cursor.execute(sql, (nome, telefone, email, especialidade))
      self.controller.db.connection.commit()
      novo_id = cursor.lastrowid
      cursor.close()

      messagebox.showinfo(
          "Sucesso", f"Funcionário cadastrado com sucesso! ID: {novo_id}"
      )
      for entry in self.entries_profissional.values():
        entry.delete(0, tk.END)
    except Exception as e:
      messagebox.showerror("Erro ao Cadastrar Funcionário", str(e))


# --- TELA 3: CADASTRAR SERVIÇO ---
class TelaCadastrarServico(BaseTela):

  def __init__(self, parent, controller):
    super().__init__(parent, controller, "MÁRCIA GAVA — CADASTRO DE SERVIÇO")

    form_frame = ttk.Frame(self)
    form_frame.pack(pady=5)

    self.entries_servico = {}
    campos = [
        ("Nome do Serviço *", "nome"),
        ("Duração (minutos) *", "duracao"),
        ("Preço (R$) *", "preco"),
    ]

    for i, (rotulo, chave) in enumerate(campos):
      lbl = tk.Label(
          form_frame,
          text=rotulo,
          width=25,
          anchor="w",
          fg=controller.COR_TEXTO,
          bg=controller.COR_BG,
          font=("Arial", 9),
      )
      lbl.grid(row=i, column=0, sticky="w", pady=5)
      entry = tk.Entry(
          form_frame,
          width=35,
          bg="#1c1c1c",
          fg="#ffffff",
          insertbackground="white",
          relief="flat",
      )
      entry.grid(row=i, column=1, pady=5, ipady=2)
      self.entries_servico[chave] = entry

    btn_salvar_serv = ttk.Button(
        self, text="Salvar Serviço", command=self.salvar_servico
    )
    btn_salvar_serv.pack(pady=15)

  def salvar_servico(self):
    nome = self.entries_servico["nome"].get().strip()
    duracao_str = self.entries_servico["duracao"].get().strip()
    preco_str = self.entries_servico["preco"].get().strip()

    if not nome or not duracao_str or not preco_str:
      messagebox.showerror(
          "Erro", "Preencha todos os campos obrigatórios do serviço (*)."
      )
      return

    try:
      duracao_minutos = int(duracao_str)
      preco = float(preco_str.replace(",", "."))
    except ValueError:
      messagebox.showerror(
          "Erro",
          "Duração deve ser um número inteiro e Preço um valor válido (ex: 50.00"
          " ou 50,00).",
      )
      return

    try:
      cursor = self.controller.db._cursor()
      sql = """
                INSERT INTO servicos (nome, duracao_minutos, preco)
                VALUES (%s, %s, %s)
            """
      cursor.execute(sql, (nome, duracao_minutos, preco))
      self.controller.db.connection.commit()
      novo_id = cursor.lastrowid
      cursor.close()

      messagebox.showinfo(
          "Sucesso", f"Serviço cadastrado com sucesso! ID: {novo_id}"
      )
      for entry in self.entries_servico.values():
        entry.delete(0, tk.END)
    except Exception as e:
      messagebox.showerror("Erro ao Cadastrar Serviço", str(e))


# --- TELA 4: NOVO AGENDAMENTO (Com múltiplos procedimentos) ---
class TelaNovoAgendamento(BaseTela):

  def __init__(self, parent, controller):
    super().__init__(parent, controller, "MÁRCIA GAVA — NOVO AGENDAMENTO")

    form_frame = ttk.Frame(self)
    form_frame.pack(pady=2)

    # Cliente
    tk.Label(
        form_frame,
        text="Cliente *",
        width=25,
        anchor="w",
        fg=controller.COR_TEXTO,
        bg=controller.COR_BG,
        font=("Arial", 9),
    ).grid(row=0, column=0, sticky="w", pady=3)
    self.combo_cliente = ttk.Combobox(form_frame, width=38, state="readonly")
    self.combo_cliente.grid(row=0, column=1, pady=3)

    # Profissional
    tk.Label(
        form_frame,
        text="Profissional *",
        width=25,
        anchor="w",
        fg=controller.COR_TEXTO,
        bg=controller.COR_BG,
        font=("Arial", 9),
    ).grid(row=1, column=0, sticky="w", pady=3)
    self.combo_profissional = ttk.Combobox(
        form_frame, width=38, state="readonly"
    )
    self.combo_profissional.grid(row=1, column=1, pady=3)

    # Procedimentos Múltiplos (Checkbuttons)
    tk.Label(
        form_frame,
        text="Serviços / Procedimentos *",
        width=25,
        anchor="w",
        fg=controller.COR_DOURADO,
        bg=controller.COR_BG,
        font=("Arial", 9, "bold"),
    ).grid(row=2, column=0, sticky="nw", pady=3)

    self.servicos_frame = ttk.Frame(form_frame)
    self.servicos_frame.grid(row=2, column=1, sticky="w", pady=3)
    self.servicos_vars = {}

    # Data e Hora
    tk.Label(
        form_frame,
        text="Data e Hora (DD/MM/AAAA HH:MM) *",
        width=28,
        anchor="w",
        fg=controller.COR_TEXTO,
        bg=controller.COR_BG,
        font=("Arial", 9),
    ).grid(row=3, column=0, sticky="w", pady=3)
    self.entry_inicio = tk.Entry(
        form_frame,
        width=40,
        bg="#1c1c1c",
        fg="#ffffff",
        insertbackground="white",
        relief="flat",
    )
    self.entry_inicio.grid(row=3, column=1, pady=3, ipady=2)

    # Observações
    tk.Label(
        form_frame,
        text="Observações",
        width=25,
        anchor="w",
        fg=controller.COR_TEXTO,
        bg=controller.COR_BG,
        font=("Arial", 9),
    ).grid(row=4, column=0, sticky="w", pady=3)
    self.entry_obs_agendamento = tk.Entry(
        form_frame,
        width=40,
        bg="#1c1c1c",
        fg="#ffffff",
        insertbackground="white",
        relief="flat",
    )
    self.entry_obs_agendamento.grid(row=4, column=1, pady=3, ipady=2)

    btn_frame = ttk.Frame(self)
    btn_frame.pack(pady=8)

    ttk.Button(
        btn_frame, text="Atualizar Listas", command=self.carregar_dados
    ).pack(side="left", padx=5)
    ttk.Button(
        btn_frame, text="Criar Agendamento", command=self.salvar_agendamento
    ).pack(side="left", padx=5)

    self.carregar_dados()

  def carregar_dados(self):
    try:
      # Clientes
      clientes = self.controller.db.listar_clientes()
      self.mapa_clientes = {
          f"{c['id_cliente']} - {c['nome_completo']}": c["id_cliente"]
          for c in clientes
      }
      self.combo_cliente["values"] = list(self.mapa_clientes.keys())

      # Profissionais
      profissionais = self.controller.db.listar_profissionais()
      self.mapa_profissionais = {
          f"{p['id_profissional']} - {p['nome_completo']}": p["id_profissional"]
          for p in profissionais
      }
      self.combo_profissional["values"] = list(self.mapa_profissionais.keys())

      # Serviços / Procedimentos
      for widget in self.servicos_frame.winfo_children():
        widget.destroy()

      self.servicos_vars = {}
      servicos = self.controller.db.listar_servicos()
      for s in servicos:
        var = tk.BooleanVar()
        chk = tk.Checkbutton(
            self.servicos_frame,
            text=f"{s['nome']} - R$ {s['preco']:.2f}",
            variable=var,
            bg=self.controller.COR_BG,
            fg=self.controller.COR_TEXTO,
            selectcolor="#1c1c1c",
            activebackground=self.controller.COR_BG,
            activeforeground=self.controller.COR_DOURADO,
            anchor="w",
        )
        chk.pack(anchor="w", pady=1)
        self.servicos_vars[s["id_servico"]] = (
            var,
            s["nome"],
            float(s["preco"]),
        )
    except Exception as e:
      messagebox.showerror(
          "Erro", f"Não foi possível carregar os dados auxiliares: {e}"
      )

  def salvar_agendamento(self):
    try:
      sel_cli = self.combo_cliente.get()
      sel_prof = self.combo_profissional.get()
      inicio_str = self.entry_inicio.get().strip()
      obs = self.entry_obs_agendamento.get() or None

      if not sel_cli or not sel_prof or not inicio_str:
        raise ValueError("Preencha os campos obrigatórios (*).")

      # Recolhe os serviços selecionados
      servicos_selecionados = [
          (sid, dados[1], dados[2])
          for sid, dados in self.servicos_vars.items()
          if dados[0].get()
      ]
      if not servicos_selecionados:
        raise ValueError("Selecione pelo menos um procedimento/serviço.")

      id_cliente = self.mapa_clientes[sel_cli]
      id_profissional = self.mapa_profissionais[sel_prof]

      try:
        inicio = datetime.strptime(inicio_str, "%d/%m/%Y %H:%M")
      except ValueError as exc:
        raise ValueError(
            "Use o formato DD/MM/AAAA HH:MM (ex.: 25/12/2026 14:30)."
        ) from exc

      primeiro_servico_id = servicos_selecionados[0][0]
      novo_id = self.controller.db.cadastrar_agendamento(
          id_cliente,
          id_profissional,
          primeiro_servico_id,
          inicio,
          obs,
      )

      detalhes_str = f"Procedimentos: {', '.join([s[1] for s in servicos_selecionados])} | Total: R$ {sum([s[2] for s in servicos_selecionados]):.2f}"
      if obs:
        obs_completa = f"{obs} | {detalhes_str}"
      else:
        obs_completa = detalhes_str

      cursor = self.controller.db._cursor()
      cursor.execute(
          "UPDATE agendamentos SET observacoes = %s WHERE id_agendamento = %s",
          (obs_completa, novo_id),
      )
      self.controller.db.connection.commit()
      cursor.close()

      messagebox.showinfo(
          "Sucesso",
          f"Agendamento criado com ID: {novo_id}\nValor Total: R$ {sum([s[2] for s in servicos_selecionados]):.2f}",
      )
      self.entry_inicio.delete(0, tk.END)
      self.entry_obs_agendamento.delete(0, tk.END)
      for var, _, _ in self.servicos_vars.values():
        var.set(False)
    except Exception as e:
      messagebox.showerror("Erro ao Agendar", str(e))


# --- TELA 5: ATENDIMENTO PENDENTE ---
class TelaAtendimentoPendente(BaseTela):

  def __init__(self, parent, controller):
    super().__init__(parent, controller, "MÁRCIA GAVA — ATENDIMENTO PENDENTE")

    top_frame = ttk.Frame(self)
    top_frame.pack(pady=5)

    ttk.Button(
        top_frame,
        text="Carregar Pendentes",
        command=self.atualizar_lista_pendentes,
    ).pack(side="left", padx=5)
    ttk.Button(
        top_frame,
        text="Finalizar Atendimento",
        command=self.concluir_agendamento_selecionado,
    ).pack(side="left", padx=5)

    self.tree_pendentes = ttk.Treeview(
        self,
        columns=(
            "ID",
            "Cliente",
            "Profissional",
            "Procedimento(s)",
            "Valor Total",
            "Data/Hora",
            "Status",
        ),
        show="headings",
    )
    for col in (
        "ID",
        "Cliente",
        "Profissional",
        "Procedimento(s)",
        "Valor Total",
        "Data/Hora",
        "Status",
    ):
      self.tree_pendentes.heading(col, text=col)
    self.tree_pendentes.pack(fill="both", expand=True, padx=10, pady=10)

    self.atualizar_lista_pendentes()

  def atualizar_lista_pendentes(self):
    self.tree_pendentes.delete(*self.tree_pendentes.get_children())
    for a in self.controller.db.listar_agendamentos():
      if a["status"] in ("AGENDADO", "CONFIRMADO"):
        obs = a.get("observacoes") or ""
        proc_str = a["servico"]
        valor_str = "R$ —"
        if "Procedimentos:" in obs:
          try:
            partes = obs.split(" | ")
            for p in partes:
              if "Procedimentos:" in p:
                proc_str = p.replace("Procedimentos:", "").strip()
              if "Total:" in p:
                valor_str = p.replace("Total:", "").strip()
          except Exception:
            pass

        self.tree_pendentes.insert(
            "",
            tk.END,
            values=(
                a["id_agendamento"],
                a["cliente"],
                a["profissional"],
                proc_str,
                valor_str,
                a["inicio"].strftime("%d/%m/%Y %H:%M"),
                a["status"],
            ),
        )

  def concluir_agendamento_selecionado(self):
    selecionado = self.tree_pendentes.selection()
    if not selecionado:
      messagebox.showwarning("Aviso", "Selecione um atendimento na tabela.")
      return

    item_dados = self.tree_pendentes.item(selecionado)
    id_agendamento = item_dados["values"][0]

    try:
      cursor = self.controller.db._cursor()
      sql = (
          "UPDATE agendamentos SET status = 'CONCLUIDO' WHERE id_agendamento = %s"
      )
      cursor.execute(sql, (id_agendamento,))
      self.controller.db.connection.commit()
      cursor.close()

      messagebox.showinfo(
          "Sucesso", f"Atendimento #{id_agendamento} finalizado com sucesso!"
      )
      self.atualizar_lista_pendentes()
    except Exception as e:
      messagebox.showerror("Erro", f"Não foi possível finalizar: {e}")


# --- TELA 6: CONSULTAR CADASTROS ---
class TelaConsultarCadastros(BaseTela):

  def __init__(self, parent, controller):
    super().__init__(parent, controller, "MÁRCIA GAVA — CONSULTAR CADASTROS")

    top_frame = ttk.Frame(self)
    top_frame.pack(pady=10)

    ttk.Button(
        top_frame, text="Listar Clientes", command=self.atualizar_lista_clientes
    ).pack(side="left", padx=3)
    ttk.Button(
        top_frame,
        text="Listar Funcionários",
        command=self.atualizar_lista_profissionais,
    ).pack(side="left", padx=3)
    ttk.Button(
        top_frame, text="Listar Serviços", command=self.atualizar_lista_servicos
    ).pack(side="left", padx=3)
    ttk.Button(
        top_frame,
        text="Atendimentos Ativos",
        command=self.atualizar_lista_agendamentos,
    ).pack(side="left", padx=3)
    ttk.Button(
        top_frame, text="Finalizados", command=self.atualizar_lista_finalizados
    ).pack(side="left", padx=3)

    self.tree = ttk.Treeview(self, columns=(1, 2, 3, 4, 5, 6), show="headings")
    self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    self.atualizar_lista_clientes()

  def atualizar_lista_clientes(self):
    self.tree.delete(*self.tree.get_children())
    self.tree.config(columns=("ID", "Nome", "Telefone", "E-mail"), show="headings")
    self.tree.heading("ID", text="ID")
    self.tree.heading("Nome", text="Nome")
    self.tree.heading("Telefone", text="Telefone")
    self.tree.heading("E-mail", text="E-mail")

    for c in self.controller.db.listar_clientes():
      self.tree.insert(
          "",
          tk.END,
          values=(
              c["id_cliente"],
              c["nome_completo"],
              c["telefone"],
              c.get("email") or "—",
          ),
      )

  def atualizar_lista_profissionais(self):
    self.tree.delete(*self.tree.get_children())
    self.tree.config(
        columns=("ID", "Nome", "Telefone", "Especialidade"), show="headings"
    )
    self.tree.heading("ID", text="ID")
    self.tree.heading("Nome", text="Nome")
    self.tree.heading("Telefone", text="Telefone")
    self.tree.heading("Especialidade", text="Especialidade")

    for p in self.controller.db.listar_profissionais():
      self.tree.insert(
          "",
          tk.END,
          values=(
              p["id_profissional"],
              p["nome_completo"],
              p["telefone"],
              p.get("especialidade") or "—",
          ),
      )

  def atualizar_lista_servicos(self):
    self.tree.delete(*self.tree.get_children())
    self.tree.config(
        columns=("ID", "Serviço", "Duração", "Preço"), show="headings"
    )
    self.tree.heading("ID", text="ID")
    self.tree.heading("Serviço", text="Serviço")
    self.tree.heading("Duração", text="Duração (min)")
    self.tree.heading("Preço", text="Preço (R$)")

    for s in self.controller.db.listar_servicos():
      self.tree.insert(
          "",
          tk.END,
          values=(
              s["id_servico"],
              s["nome"],
              s["duracao_minutos"],
              f"R$ {s['preco']:.2f}",
          ),
      )

  def atualizar_lista_agendamentos(self):
    self.tree.delete(*self.tree.get_children())
    self.tree.config(
        columns=(
            "ID",
            "Cliente",
            "Profissional",
            "Procedimento(s)",
            "Valor Total",
            "Data/Hora",
            "Status",
        ),
        show="headings",
    )
    for col in (
        "ID",
        "Cliente",
        "Profissional",
        "Procedimento(s)",
        "Valor Total",
        "Data/Hora",
        "Status",
    ):
      self.tree.heading(col, text=col)

    for a in self.controller.db.listar_agendamentos():
      if a["status"] in ("AGENDADO", "CONFIRMADO"):
        obs = a.get("observacoes") or ""
        proc_str = a["servico"]
        valor_str = "R$ —"
        if "Procedimentos:" in obs:
          try:
            partes = obs.split(" | ")
            for p in partes:
              if "Procedimentos:" in p:
                proc_str = p.replace("Procedimentos:", "").strip()
              if "Total:" in p:
                valor_str = p.replace("Total:", "").strip()
          except Exception:
            pass

        self.tree.insert(
            "",
            tk.END,
            values=(
                a["id_agendamento"],
                a["cliente"],
                a["profissional"],
                proc_str,
                valor_str,
                a["inicio"].strftime("%d/%m/%Y %H:%M"),
                a["status"],
            ),
        )

  def atualizar_lista_finalizados(self):
    self.tree.delete(*self.tree.get_children())
    self.tree.config(
        columns=(
            "ID",
            "Cliente",
            "Profissional",
            "Procedimento(s)",
            "Valor Total",
            "Data/Hora",
            "Status",
        ),
        show="headings",
    )
    for col in (
        "ID",
        "Cliente",
        "Profissional",
        "Procedimento(s)",
        "Valor Total",
        "Data/Hora",
        "Status",
    ):
      self.tree.heading(col, text=col)

    for a in self.controller.db.listar_agendamentos():
      if a["status"] == "CONCLUIDO":
        obs = a.get("observacoes") or ""
        proc_str = a["servico"]
        valor_str = "R$ —"
        if "Procedimentos:" in obs:
          try:
            partes = obs.split(" | ")
            for p in partes:
              if "Procedimentos:" in p:
                proc_str = p.replace("Procedimentos:", "").strip()
              if "Total:" in p:
                valor_str = p.replace("Total:", "").strip()
          except Exception:
            pass

        self.tree.insert(
            "",
            tk.END,
            values=(
                a["id_agendamento"],
                a["cliente"],
                a["profissional"],
                proc_str,
                valor_str,
                a["inicio"].strftime("%d/%m/%Y %H:%M"),
                a["status"],
            ),
        )


if __name__ == "__main__":
  root = tk.Tk()
  app = SalaoApp(root)
  root.protocol(
      "WM_DELETE_WINDOW", lambda: (app.db.fechar(), root.destroy())
  )
  root.mainloop()