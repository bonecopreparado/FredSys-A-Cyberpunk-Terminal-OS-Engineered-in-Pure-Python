#!/usr/bin/env python3
# =============================================================================
#
#   ███████╗██████╗ ███████╗██████╗ ███████╗██╗   ██╗███████╗  ██╗   ██╗██████╗ 
#   ██╔════╝██╔══██╗██╔════╝██╔══██╗██╔════╝╚██╗ ██╔╝██╔════╝  ██║   ██║╚════██╗
#   █████╗  ██████╔╝█████╗  ██║  ██║███████╗ ╚████╔╝ ███████╗  ██║   ██║ █████╔╝
#   ██╔══╝  ██╔══██╗██╔══╝  ██║  ██║╚════██║  ╚██╔╝  ╚════██║  ╚██╗ ██╔╝██╔═══╝ 
#   ██║     ██║  ██║███████╗██████╔╝███████║   ██║   ███████║   ╚████╔╝ ███████╗
#   ╚═╝     ╚═╝  ╚═╝╚══════╝╚═════╝ ╚══════╝   ╚═╝   ╚══════╝    ╚═══╝  ╚══════╝
#
#   FredSys v2.0 — Terminal Operating System (TUI Avançado)
#   ─────────────────────────────────────────────────────────
#   Compatível  : Windows (CMD/PowerShell) · Linux · Android (Termux)
#   Dependências: ZERO — apenas bibliotecas embutidas do Python 3
#   Bibliotecas : os · sys · json · hashlib · platform · datetime · shutil · socket
#
# =============================================================================

import os
import sys
import json
import hashlib
import platform
import datetime
import shutil
import socket
import subprocess

# ═════════════════════════════════════════════════════════════════════════════
#  SEÇÃO 1 ─ CONSTANTES GLOBAIS E CONFIGURAÇÃO DO AMBIENTE
# ═════════════════════════════════════════════════════════════════════════════

# Detecta o SO uma única vez para usar em todo o programa
WINDOWS = os.name == "nt"

# Caminhos dos arquivos de dados persistentes (ficam na mesma pasta do script)
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_USERS   = os.path.join(BASE_DIR, "fredsys_users.json")
ARQUIVO_CONFIG  = os.path.join(BASE_DIR, "fredsys_config.json")
PASTA_DOCS      = os.path.join(BASE_DIR, "MeusDocumentos")

# Variável global que guarda o usuário que fez login nesta sessão
USUARIO_LOGADO  = None

# ─────────────────────────────────────────────────────────────────────────────
#  CATÁLOGO DE APLICATIVOS
#  Cada app tem: id (chave), nome, descrição e a função Python que o executa.
#  "installed" é gerenciado pelo fredsys_config.json, não aqui.
# ─────────────────────────────────────────────────────────────────────────────
CATALOGO_APPS = {
    "notepad": {
        "nome":    "📝 Notepad",
        "desc":    "Bloco de notas com múltiplas linhas. Salva e lê arquivos .txt.",
        "funcao":  "app_notepad",
    },
    "calc": {
        "nome":    "🔢 Calculadora Avançada",
        "desc":    "Resolve expressões matemáticas com detecção de erros.",
        "funcao":  "app_calculadora",
    },
    "sysmon": {
        "nome":    "💻 SysMonitor",
        "desc":    "RAM, SO, hostname, IP local e informações do disco.",
        "funcao":  "app_sysmonitor",
    },
    "explorer": {
        "nome":    "📁 File Explorer",
        "desc":    "Navega entre pastas, lista, cria e deleta arquivos/diretórios.",
        "funcao":  "app_file_explorer",
    },
}

# ═════════════════════════════════════════════════════════════════════════════
#  SEÇÃO 2 ─ CORES E INTERFACE (TUI ENGINE)
# ═════════════════════════════════════════════════════════════════════════════

def _habilitar_ansi_windows():
    """
    No Windows 10+, o suporte a ANSI precisa ser ativado via API do kernel.
    Esta função usa ctypes para habilitar ENABLE_VIRTUAL_TERMINAL_PROCESSING.
    Em versões antigas do Windows, as cores simplesmente não aparecem (sem crash).
    """
    if WINDOWS:
        try:
            import ctypes
            k32 = ctypes.windll.kernel32
            k32.SetConsoleMode(k32.GetStdHandle(-11), 7)
        except Exception:
            pass

_habilitar_ansi_windows()

# Paleta de cores cyberpunk — cada entrada é uma sequência de escape ANSI
COR = {
    "reset"   : "\033[0m",
    "bold"    : "\033[1m",
    "dim"     : "\033[2m",
    "under"   : "\033[4m",
    # Cores principais
    "ciano"   : "\033[96m",
    "verde"   : "\033[92m",
    "vermelho": "\033[91m",
    "amarelo" : "\033[93m",
    "magenta" : "\033[95m",
    "azul"    : "\033[94m",
    "branco"  : "\033[97m",
    "cinza"   : "\033[90m",
    # Fundos para destaques especiais
    "bg_ciano": "\033[46m",
    "bg_verde": "\033[42m",
}

def c(texto, cor="branco", negrito=False, dim=False):
    """
    Função utilitária para colorir texto com ANSI.
    Uso: print(c("Olá!", "verde", negrito=True))
    """
    estilos = ""
    if negrito:
        estilos += COR["bold"]
    if dim:
        estilos += COR["dim"]
    return f"{estilos}{COR.get(cor, '')}{texto}{COR['reset']}"

def limpar():
    """Limpa o terminal de forma multiplataforma."""
    os.system("cls" if WINDOWS else "clear")

def pausar(msg="Pressione ENTER para continuar..."):
    """Pausa a execução até o usuário pressionar ENTER."""
    try:
        input(c(f"\n  {msg}", "cinza", dim=True))
    except (KeyboardInterrupt, EOFError):
        pass

def linha_h(char="─", tamanho=65, cor_nome="azul"):
    """Imprime uma linha horizontal decorativa."""
    print(c(char * tamanho, cor_nome))

def cabecalho(titulo_texto):
    """Exibe um cabeçalho de seção formatado."""
    print()
    linha_h("╔" + "═" * 63 + "╗", tamanho=1, cor_nome="ciano")
    padding = (63 - len(titulo_texto)) // 2
    print(c(f"║{' ' * padding}{titulo_texto}{' ' * (63 - padding - len(titulo_texto))}║", "ciano", negrito=True))
    linha_h("╚" + "═" * 63 + "╝", tamanho=1, cor_nome="ciano")
    print()

def msg_ok(texto):
    print(c(f"\n  ✔  {texto}", "verde"))

def msg_erro(texto):
    print(c(f"\n  ✘  ERRO: {texto}", "vermelho"))

def msg_aviso(texto):
    print(c(f"\n  ⚠  {texto}", "amarelo"))

def msg_info(texto):
    print(c(f"     {texto}", "branco"))

def linha_item(label, valor, cor_valor="verde"):
    """Imprime uma linha formatada de informação 'label: valor'."""
    print(c(f"  │  {label:<28}", "cinza") + c(f"{valor}", cor_valor))

# ═════════════════════════════════════════════════════════════════════════════
#  SEÇÃO 3 ─ BANNER ASCII ART
# ═════════════════════════════════════════════════════════════════════════════

BANNER_ARTE = r"""
  ███████╗██████╗ ███████╗██████╗ ███████╗██╗   ██╗███████╗  ██╗   ██╗██████╗
  ██╔════╝██╔══██╗██╔════╝██╔══██╗██╔════╝╚██╗ ██╔╝██╔════╝  ██║   ██║╚════██╗
  █████╗  ██████╔╝█████╗  ██║  ██║███████╗ ╚████╔╝ ███████╗  ██║   ██║ █████╔╝
  ██╔══╝  ██╔══██╗██╔══╝  ██║  ██║╚════██║  ╚██╔╝  ╚════██║  ╚██╗ ██╔╝██╔═══╝
  ██║     ██║  ██║███████╗██████╔╝███████║   ██║   ███████║   ╚████╔╝ ███████╗
  ╚═╝     ╚═╝  ╚═╝╚══════╝╚═════╝ ╚══════╝   ╚═╝   ╚══════╝    ╚═══╝  ╚══════╝
"""

def exibir_banner(subtitulo="Terminal Operating System"):
    """
    Limpa a tela e exibe o banner completo do FredSys.
    O subtítulo muda conforme o contexto (login, menu, etc.).
    """
    limpar()
    print(c(BANNER_ARTE, "ciano", negrito=True))

    # Linha de status com informações contextuais
    agora     = datetime.datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
    so_info   = f"{platform.system()} {platform.release()}"
    usuario   = f"Usuário: {c(USUARIO_LOGADO, 'verde')}" if USUARIO_LOGADO else c("[ Não autenticado ]", "vermelho")

    print(c("  ╔" + "═" * 63 + "╗", "azul"))
    print(
        c("  ║ ", "azul") +
        c(f"  {subtitulo:<30}", "amarelo", negrito=True) +
        c(f"{agora:>22}   ", "cinza") +
        c("║", "azul")
    )
    print(
        c("  ║ ", "azul") +
        c(f"  SO: {so_info:<25}", "cinza") +
        f"  {usuario:<30}" +
        c("║", "azul")
    )
    print(c("  ╚" + "═" * 63 + "╝", "azul"))
    print()

# ═════════════════════════════════════════════════════════════════════════════
#  SEÇÃO 4 ─ PERSISTÊNCIA (JSON: usuários e configurações)
# ═════════════════════════════════════════════════════════════════════════════

def carregar_json(caminho, padrao=None):
    """
    Carrega um arquivo JSON do disco.
    Se o arquivo não existir, retorna o valor 'padrao' e não lança erro.
    """
    if padrao is None:
        padrao = {}
    if not os.path.exists(caminho):
        return padrao
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return padrao

def salvar_json(caminho, dados):
    """
    Salva um dicionário Python como arquivo JSON formatado no disco.
    indent=2 deixa o arquivo legível por humanos.
    """
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        msg_erro(f"Não foi possível salvar '{caminho}': {e}")
        return False

def hash_senha(senha):
    """
    Gera o hash SHA-256 da senha em formato hexadecimal.
    NUNCA salvamos a senha em texto puro — apenas o hash.
    Mesmo que o arquivo vaze, a senha original é irrecuperável.
    """
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

# ─────────────────────────────────────────────────────────────────────────────
#  Funções de alto nível para usuários
# ─────────────────────────────────────────────────────────────────────────────

def listar_usuarios():
    """Retorna o dicionário completo de usuários do arquivo JSON."""
    return carregar_json(ARQUIVO_USERS, padrao={})

def usuario_existe(nome):
    """Verifica se um nome de usuário já está cadastrado."""
    return nome in listar_usuarios()

def criar_usuario(nome, senha):
    """
    Cria um novo usuário e salva no arquivo JSON.
    Retorna True em caso de sucesso, False se o usuário já existir.
    """
    usuarios = listar_usuarios()
    if nome in usuarios:
        return False  # Usuário já existe
    usuarios[nome] = {
        "senha_hash": hash_senha(senha),
        "criado_em" : datetime.datetime.now().isoformat(),
    }
    return salvar_json(ARQUIVO_USERS, usuarios)

def verificar_login(nome, senha):
    """
    Compara o hash da senha fornecida com o hash armazenado.
    Retorna True se coincidir, False caso contrário.
    """
    usuarios = listar_usuarios()
    if nome not in usuarios:
        return False
    return usuarios[nome]["senha_hash"] == hash_senha(senha)

# ─────────────────────────────────────────────────────────────────────────────
#  Funções de configuração (apps instalados por usuário)
# ─────────────────────────────────────────────────────────────────────────────

def carregar_config():
    """Carrega o arquivo de configuração geral do sistema."""
    return carregar_json(ARQUIVO_CONFIG, padrao={"usuarios_apps": {}})

def salvar_config(config):
    """Persiste o objeto de configuração no disco."""
    return salvar_json(ARQUIVO_CONFIG, config)

def apps_instalados(usuario):
    """
    Retorna uma lista com os IDs dos apps instalados pelo usuário.
    Ex: ["notepad", "calc"]
    """
    config = carregar_config()
    return config.get("usuarios_apps", {}).get(usuario, [])

def instalar_app(usuario, app_id):
    """Marca um app como instalado para o usuário."""
    config = carregar_config()
    if "usuarios_apps" not in config:
        config["usuarios_apps"] = {}
    if usuario not in config["usuarios_apps"]:
        config["usuarios_apps"][usuario] = []
    if app_id not in config["usuarios_apps"][usuario]:
        config["usuarios_apps"][usuario].append(app_id)
    salvar_config(config)

def desinstalar_app(usuario, app_id):
    """Remove um app da lista de instalados do usuário."""
    config = carregar_config()
    lista  = config.get("usuarios_apps", {}).get(usuario, [])
    if app_id in lista:
        lista.remove(app_id)
        config["usuarios_apps"][usuario] = lista
        salvar_config(config)

# ═════════════════════════════════════════════════════════════════════════════
#  SEÇÃO 5 ─ TELAS DE AUTENTICAÇÃO
# ═════════════════════════════════════════════════════════════════════════════

def tela_criar_conta():
    """
    Fluxo de criação de nova conta:
    1. Pede nome de usuário
    2. Verifica se já existe
    3. Pede senha e confirmação
    4. Salva com hash SHA-256
    """
    global USUARIO_LOGADO

    exibir_banner("Criar Nova Conta")
    cabecalho("CADASTRO DE USUÁRIO")

    # ── Validação do nome de usuário ─────────────────────────────────────────
    while True:
        nome = input(c("  Nome de usuário: ", "ciano")).strip()
        if len(nome) < 3:
            msg_erro("O nome precisa ter ao menos 3 caracteres.")
            continue
        if usuario_existe(nome):
            msg_erro(f"O usuário '{nome}' já existe. Escolha outro nome.")
            continue
        # Só permite letras, números e underscore
        if not all(ch.isalnum() or ch == "_" for ch in nome):
            msg_erro("Use apenas letras, números e underscore (_).")
            continue
        break

    # ── Validação da senha ───────────────────────────────────────────────────
    while True:
        try:
            import getpass
            senha  = getpass.getpass(c("  Senha (min. 4 chars): ", "ciano"))
            senha2 = getpass.getpass(c("  Confirme a senha: ",    "ciano"))
        except Exception:
            # Fallback sem ocultação (ex: alguns terminais do Termux)
            senha  = input(c("  Senha (min. 4 chars): ", "ciano"))
            senha2 = input(c("  Confirme a senha: ",    "ciano"))

        if len(senha) < 4:
            msg_erro("A senha deve ter no mínimo 4 caracteres.")
            continue
        if senha != senha2:
            msg_erro("As senhas não coincidem. Tente novamente.")
            continue
        break

    # ── Criação ──────────────────────────────────────────────────────────────
    if criar_usuario(nome, senha):
        msg_ok(f"Conta '{nome}' criada com sucesso!")
        msg_info("Você pode fazer login agora.")
        USUARIO_LOGADO = nome
    else:
        msg_erro("Falha ao criar conta. Tente novamente.")

    pausar()

def tela_login():
    """
    Tela de login: pede credenciais e valida contra o arquivo JSON.
    Permite 3 tentativas antes de bloquear temporariamente.
    """
    global USUARIO_LOGADO

    exibir_banner("Tela de Login")
    cabecalho("ACESSO AO SISTEMA")

    tentativas = 3
    while tentativas > 0:
        nome = input(c("  Usuário: ", "ciano")).strip()

        try:
            import getpass
            senha = getpass.getpass(c("  Senha:   ", "ciano"))
        except Exception:
            senha = input(c("  Senha:   ", "ciano"))

        if verificar_login(nome, senha):
            USUARIO_LOGADO = nome
            msg_ok(f"Bem-vindo de volta, {nome}!")
            pausar("Pressione ENTER para acessar o sistema...")
            return True
        else:
            tentativas -= 1
            if tentativas > 0:
                msg_erro(f"Credenciais inválidas. Tentativas restantes: {tentativas}")
            else:
                msg_erro("Número máximo de tentativas atingido!")
                pausar()
                return False

    return False

def tela_autenticacao():
    """
    Tela inicial de autenticação: oferece Login ou Criar Conta.
    Fica em loop até que o usuário se autentique com sucesso.
    """
    global USUARIO_LOGADO

    while not USUARIO_LOGADO:
        exibir_banner("Sistema de Autenticação")
        cabecalho("BEM-VINDO AO FREDSYS v2.0")

        print(c("  ┌─────────────────────────────────┐", "azul"))
        print(c("  │", "azul") + c("  [1]  Fazer Login          ", "branco") + c("│", "azul"))
        print(c("  │", "azul") + c("  [2]  Criar Nova Conta     ", "branco") + c("│", "azul"))
        print(c("  │", "azul") + c("  [0]  Sair                 ", "branco") + c("│", "azul"))
        print(c("  └─────────────────────────────────┘", "azul"))
        print()

        op = input(c("  FredSys Auth ➤ ", "amarelo", negrito=True)).strip()

        if op == "1":
            tela_login()
        elif op == "2":
            tela_criar_conta()
        elif op == "0":
            print(c("\n  Encerrando FredSys. Até logo!\n", "cinza"))
            sys.exit(0)
        else:
            msg_erro("Opção inválida. Digite 1, 2 ou 0.")
            pausar()

# ═════════════════════════════════════════════════════════════════════════════
#  SEÇÃO 6 ─ GERENCIADOR DE APLICATIVOS (APP STORE)
# ═════════════════════════════════════════════════════════════════════════════

def tela_app_store():
    """
    Módulo de App Store do FredSys.
    Permite ao usuário logado visualizar, instalar e desinstalar aplicativos.
    O estado (instalado/não-instalado) é salvo em fredsys_config.json.
    """
    while True:
        exibir_banner("App Store")
        cabecalho("GERENCIADOR DE APLICATIVOS")

        instalados = apps_instalados(USUARIO_LOGADO)

        print(c("  APLICATIVOS DISPONÍVEIS NO FREDSYS\n", "amarelo", negrito=True))
        print(c(f"  {'#':<4}{'ID':<12}{'NOME':<22}{'STATUS':<14}DESCRIÇÃO", "cinza"))
        linha_h(tamanho=65)

        # Exibe cada app do catálogo com seu status atual
        itens_menu = list(CATALOGO_APPS.items())
        for i, (app_id, app_info) in enumerate(itens_menu, start=1):
            status = c(" INSTALADO ", "verde", negrito=True) if app_id in instalados \
                     else c("disponível", "cinza")
            print(
                c(f"  [{i}]", "ciano") +
                c(f" {app_id:<12}", "branco") +
                c(f"{app_info['nome']:<22}", "amarelo") +
                f"{status:<14}" +
                c(f"  {app_info['desc'][:28]}...", "cinza", dim=True)
            )

        print()
        linha_h(tamanho=65)
        print(c("  [I] Instalar app   [D] Desinstalar app   [0] Voltar", "cinza"))
        print()

        cmd = input(c("  App Store ➤ ", "ciano", negrito=True)).strip().upper()

        # ── Instalar ─────────────────────────────────────────────────────────
        if cmd == "I":
            exibir_banner("App Store · Instalar")
            num = input(c("  Número do app para instalar: ", "ciano")).strip()
            if num.isdigit() and 1 <= int(num) <= len(itens_menu):
                app_id, app_info = itens_menu[int(num) - 1]
                if app_id in instalados:
                    msg_aviso(f"'{app_info['nome']}' já está instalado.")
                else:
                    msg_info(f"Instalando {app_info['nome']}...")
                    # Simula um progresso de instalação
                    for passo in ["Verificando dependências", "Baixando pacotes", "Configurando", "Concluído"]:
                        print(c(f"     ► {passo}...", "ciano"))
                    instalar_app(USUARIO_LOGADO, app_id)
                    msg_ok(f"'{app_info['nome']}' instalado com sucesso!")
            else:
                msg_erro("Número inválido.")
            pausar()

        # ── Desinstalar ───────────────────────────────────────────────────────
        elif cmd == "D":
            exibir_banner("App Store · Desinstalar")
            num = input(c("  Número do app para desinstalar: ", "ciano")).strip()
            if num.isdigit() and 1 <= int(num) <= len(itens_menu):
                app_id, app_info = itens_menu[int(num) - 1]
                if app_id not in instalados:
                    msg_aviso(f"'{app_info['nome']}' não está instalado.")
                else:
                    conf = input(c(f"  Desinstalar '{app_info['nome']}'? (s/N): ", "amarelo")).strip().lower()
                    if conf == "s":
                        desinstalar_app(USUARIO_LOGADO, app_id)
                        msg_ok(f"'{app_info['nome']}' foi desinstalado.")
                    else:
                        msg_aviso("Operação cancelada.")
            else:
                msg_erro("Número inválido.")
            pausar()

        elif cmd == "0":
            break
        else:
            msg_erro("Comando inválido.")
            pausar()

# ═════════════════════════════════════════════════════════════════════════════
#  SEÇÃO 7 ─ APLICATIVOS (MÓDULOS INSTALÁVEIS)
# ═════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
#  APP 1 ─ NOTEPAD (Bloco de Notas)
# ─────────────────────────────────────────────────────────────────────────────

def app_notepad():
    """
    Bloco de notas textual com TUI.
    Funcionalidades:
      • Criar notas multilinha e salvar como .txt em MeusDocumentos/
      • Listar e ler notas existentes
      • Deletar notas
    """
    # Garante que a pasta de documentos existe
    os.makedirs(PASTA_DOCS, exist_ok=True)

    while True:
        exibir_banner("Notepad")
        cabecalho("📝 BLOCO DE NOTAS")

        print(c("  [1]", "ciano") + "  Nova nota")
        print(c("  [2]", "ciano") + "  Ler nota existente")
        print(c("  [3]", "ciano") + "  Listar todas as notas")
        print(c("  [4]", "ciano") + "  Deletar nota")
        print(c("  [0]", "vermelho") + "  Fechar Notepad")
        print()

        op = input(c("  Notepad ➤ ", "ciano")).strip()

        # ── Nova nota ────────────────────────────────────────────────────────
        if op == "1":
            exibir_banner("Notepad · Nova Nota")
            cabecalho("EDITOR DE TEXTO")

            nome = input(c("  Título da nota (sem extensão): ", "ciano")).strip()
            if not nome:
                msg_erro("Título não pode ser vazio.")
                pausar()
                continue

            # Sanitiza o nome do arquivo
            for ch in r'\/:*?"<>|':
                nome = nome.replace(ch, "_")

            print(c("\n  Digite o texto abaixo.", "amarelo"))
            print(c("  Use '/salvar' para salvar ou '/cancelar' para descartar.\n", "cinza", dim=True))

            linhas = []
            contador = 1
            while True:
                try:
                    entrada = input(c(f"  {contador:>3} │ ", "cinza"))
                except (KeyboardInterrupt, EOFError):
                    break

                if entrada.strip().lower() == "/salvar":
                    break
                if entrada.strip().lower() == "/cancelar":
                    linhas = None
                    break
                linhas.append(entrada)
                contador += 1

            if linhas is None:
                msg_aviso("Nota descartada.")
            elif not linhas:
                msg_aviso("Nota vazia, nada foi salvo.")
            else:
                # Cria o arquivo com cabeçalho informativo
                caminho = os.path.join(PASTA_DOCS, f"{nome}.txt")
                agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                conteudo = (
                    f"═══ {nome} ═══\n"
                    f"Criado em: {agora}  |  Autor: {USUARIO_LOGADO}\n"
                    f"{'─' * 50}\n\n"
                    + "\n".join(linhas)
                    + "\n"
                )
                try:
                    with open(caminho, "w", encoding="utf-8") as f:
                        f.write(conteudo)
                    msg_ok(f"Nota salva em: {caminho}")
                except IOError as e:
                    msg_erro(f"Falha ao salvar: {e}")
            pausar()

        # ── Ler nota ─────────────────────────────────────────────────────────
        elif op == "2":
            notas = [f for f in os.listdir(PASTA_DOCS) if f.endswith(".txt")]
            if not notas:
                msg_aviso("Nenhuma nota encontrada em MeusDocumentos/.")
                pausar()
                continue

            exibir_banner("Notepad · Ler Nota")
            for i, nota in enumerate(sorted(notas), 1):
                print(c(f"  [{i}]", "ciano") + f"  {nota}")
            print()

            num = input(c("  Número da nota: ", "ciano")).strip()
            if num.isdigit() and 1 <= int(num) <= len(notas):
                caminho = os.path.join(PASTA_DOCS, sorted(notas)[int(num) - 1])
                exibir_banner("Notepad · Leitura")
                try:
                    with open(caminho, "r", encoding="utf-8") as f:
                        texto = f.read()
                    print(c("  " + "─" * 63, "azul"))
                    for linha_nota in texto.splitlines():
                        print(c(f"  {linha_nota}", "branco"))
                    print(c("  " + "─" * 63, "azul"))
                except IOError as e:
                    msg_erro(f"Não foi possível ler o arquivo: {e}")
            else:
                msg_erro("Número inválido.")
            pausar()

        # ── Listar notas ─────────────────────────────────────────────────────
        elif op == "3":
            exibir_banner("Notepad · Notas Salvas")
            cabecalho("ARQUIVOS EM MeusDocumentos/")

            try:
                notas = [f for f in os.listdir(PASTA_DOCS) if f.endswith(".txt")]
                if not notas:
                    msg_aviso("Nenhuma nota encontrada.")
                else:
                    for nota in sorted(notas):
                        caminho = os.path.join(PASTA_DOCS, nota)
                        sz = os.path.getsize(caminho)
                        mtime = datetime.datetime.fromtimestamp(
                            os.path.getmtime(caminho)
                        ).strftime("%d/%m/%Y %H:%M")
                        print(
                            c(f"  📄  {nota:<35}", "branco") +
                            c(f"{sz:>6} B", "cinza") +
                            c(f"   {mtime}", "cinza", dim=True)
                        )
                    print()
                    msg_info(f"Total: {len(notas)} nota(s) | Pasta: {PASTA_DOCS}")
            except Exception as e:
                msg_erro(str(e))
            pausar()

        # ── Deletar nota ─────────────────────────────────────────────────────
        elif op == "4":
            notas = [f for f in os.listdir(PASTA_DOCS) if f.endswith(".txt")]
            if not notas:
                msg_aviso("Nenhuma nota para deletar.")
                pausar()
                continue

            exibir_banner("Notepad · Deletar Nota")
            for i, nota in enumerate(sorted(notas), 1):
                print(c(f"  [{i}]", "ciano") + f"  {nota}")
            print()

            num = input(c("  Número da nota: ", "ciano")).strip()
            if num.isdigit() and 1 <= int(num) <= len(notas):
                alvo = sorted(notas)[int(num) - 1]
                conf = input(c(f"  Deletar '{alvo}'? (s/N): ", "amarelo")).strip().lower()
                if conf == "s":
                    try:
                        os.remove(os.path.join(PASTA_DOCS, alvo))
                        msg_ok(f"'{alvo}' deletada.")
                    except Exception as e:
                        msg_erro(str(e))
                else:
                    msg_aviso("Cancelado.")
            else:
                msg_erro("Número inválido.")
            pausar()

        elif op == "0":
            break
        else:
            msg_erro("Opção inválida.")
            pausar()

# ─────────────────────────────────────────────────────────────────────────────
#  APP 2 ─ CALCULADORA AVANÇADA
# ─────────────────────────────────────────────────────────────────────────────

# Conjunto de caracteres considerados seguros para eval()
_CHARS_CALC_SEGUROS = set("0123456789+-*/().% \t")
# Funções matemáticas adicionais permitidas
_FUNCOES_MATEMATICAS = {
    "abs": abs, "round": round, "pow": pow, "max": max, "min": min,
}

def app_calculadora():
    """
    Calculadora de terminal em loop contínuo.
    Suporta:
      • Operações básicas: + - * / // % **
      • Funções: abs(), round(), pow(), max(), min()
      • Detecção de: divisão por zero, sintaxe inválida, caracteres perigosos
    """
    exibir_banner("Calculadora Avançada")
    cabecalho("🔢 CALCULADORA")

    print(c("  Operadores : + - * / // % **", "cinza"))
    print(c("  Funções    : abs() round() pow() max() min()", "cinza"))
    print(c("  Comandos   : /historico · /limpar · /sair", "cinza"))
    print(c("  Exemplos   : 2**10  |  abs(-42)  |  (3+4)*2", "cinza"))
    print()

    historico = []  # Guarda os últimos cálculos desta sessão

    while True:
        try:
            expr = input(c("  calc ➤ ", "amarelo", negrito=True)).strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not expr:
            continue

        # Comandos especiais
        if expr.lower() in ("/sair", "exit", "quit", "0"):
            break

        if expr.lower() == "/historico":
            if not historico:
                msg_aviso("Histórico vazio.")
            else:
                print(c("\n  ─── Histórico desta sessão ───", "ciano"))
                for h in historico[-10:]:  # Exibe os últimos 10
                    print(c(f"     {h}", "branco"))
                print()
            continue

        if expr.lower() == "/limpar":
            historico.clear()
            msg_ok("Histórico limpo.")
            continue

        # Validação de segurança: só permite caracteres da whitelist
        # Isso impede execução de código arbitrário via eval()
        chars_usados = set(expr.replace(" ", ""))
        funcs_texto = set("abcdefghijklmnopqrstuvwxyz_()")
        if not chars_usados.issubset(_CHARS_CALC_SEGUROS | funcs_texto):
            msg_erro("Expressão contém caracteres não permitidos.")
            continue

        # Verifica se as funções usadas são apenas as permitidas
        import re
        funcs_usadas = re.findall(r"[a-z_]+", expr)
        funcs_invalidas = [f for f in funcs_usadas if f not in _FUNCOES_MATEMATICAS]
        if funcs_invalidas:
            msg_erro(f"Função(ões) não permitida(s): {', '.join(set(funcs_invalidas))}")
            continue

        # Avaliação segura da expressão
        try:
            # Fornecemos apenas as funções da whitelist como namespace
            resultado = eval(expr, {"__builtins__": {}}, _FUNCOES_MATEMATICAS)
            entrada_fmt = f"{expr} = {resultado}"
            print(c(f"\n      ➤  {resultado}", "verde", negrito=True))
            print()
            historico.append(entrada_fmt)
        except ZeroDivisionError:
            msg_erro("Divisão por zero! O universo agradece sua contenção.")
        except SyntaxError:
            msg_erro("Sintaxe inválida. Verifique a expressão e tente novamente.")
        except Exception as e:
            msg_erro(f"Erro ao calcular: {e}")

# ─────────────────────────────────────────────────────────────────────────────
#  APP 3 ─ SYSMONITOR
# ─────────────────────────────────────────────────────────────────────────────

def _obter_ram():
    """
    Obtém informações de RAM de forma multiplataforma.
    Linux/Android : lê /proc/meminfo (disponível no Termux)
    Windows       : usa ctypes para chamar GlobalMemoryStatusEx()
    Retorna       : (total_bytes, usado_bytes, livre_bytes) ou (None, None, None)
    """
    if not WINDOWS:
        # ── Linux / Android (Termux) ─────────────────────────────────────────
        try:
            dados = {}
            with open("/proc/meminfo", "r") as f:
                for linha_m in f:
                    partes = linha_m.split()
                    if len(partes) >= 2:
                        dados[partes[0].rstrip(":")] = int(partes[1]) * 1024
            total = dados.get("MemTotal", 0)
            livre = dados.get("MemAvailable") or dados.get("MemFree", 0)
            return total, total - livre, livre
        except Exception:
            return None, None, None
    else:
        # ── Windows ──────────────────────────────────────────────────────────
        try:
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength",                ctypes.c_ulong),
                    ("dwMemoryLoad",            ctypes.c_ulong),
                    ("ullTotalPhys",            ctypes.c_ulonglong),
                    ("ullAvailPhys",            ctypes.c_ulonglong),
                    ("ullTotalPageFile",        ctypes.c_ulonglong),
                    ("ullAvailPageFile",        ctypes.c_ulonglong),
                    ("ullTotalVirtual",         ctypes.c_ulonglong),
                    ("ullAvailVirtual",         ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            ms = MEMORYSTATUSEX()
            ms.dwLength = ctypes.sizeof(ms)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
            t = ms.ullTotalPhys
            l = ms.ullAvailPhys
            return t, t - l, l
        except Exception:
            return None, None, None

def _bytes_para_legivel(b):
    """Converte bytes em string legível (KB / MB / GB)."""
    if b is None:
        return "N/D"
    for unidade in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024:
            return f"{b:.1f} {unidade}"
        b /= 1024
    return f"{b:.1f} PB"

def _barra_progresso(pct, tamanho=30):
    """
    Gera uma barra de progresso colorida baseada na porcentagem.
    Vermelho se > 80%, Amarelo se > 60%, Verde caso contrário.
    """
    preenchido = int(tamanho * pct / 100)
    cor_barra  = "vermelho" if pct > 80 else ("amarelo" if pct > 60 else "verde")
    barra = c("█" * preenchido, cor_barra) + c("░" * (tamanho - preenchido), "cinza", dim=True)
    return f"[{barra}] {c(f'{pct:.1f}%', cor_barra)}"

def _ip_local():
    """Obtém o IP local tentando conectar a um servidor externo (sem enviar dados)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "Indisponível"

def app_sysmonitor():
    """
    Monitor do sistema: exibe informações de hardware e software em tempo real.
    Pressionar ENTER atualiza as métricas.
    """
    while True:
        exibir_banner("SysMonitor")
        cabecalho("💻 MONITOR DO SISTEMA")

        agora = datetime.datetime.now()

        # ── Sistema Operacional ───────────────────────────────────────────────
        print(c("  ┌─── Sistema Operacional ─────────────────────────────┐", "azul"))
        linha_item("SO",              f"{platform.system()} {platform.release()}")
        linha_item("Versão",          platform.version()[:50])
        linha_item("Plataforma",      platform.machine())
        linha_item("Arquitetura",     " | ".join(platform.architecture()))
        linha_item("Python",          f"{platform.python_version()} ({platform.python_implementation()})")
        linha_item("Hostname",        platform.node())
        linha_item("IP Local",        _ip_local(), cor_valor="amarelo")
        linha_item("Data & Hora",     agora.strftime("%d/%m/%Y  %H:%M:%S"), cor_valor="ciano")
        print(c("  └─────────────────────────────────────────────────────┘", "azul"))
        print()

        # ── Memória RAM ───────────────────────────────────────────────────────
        print(c("  ┌─── Memória RAM ──────────────────────────────────────┐", "azul"))
        total, usado, livre = _obter_ram()
        if total:
            pct_ram = (usado / total * 100) if usado else 0
            linha_item("Total",   _bytes_para_legivel(total))
            linha_item("Em uso",  _bytes_para_legivel(usado))
            linha_item("Livre",   _bytes_para_legivel(livre))
            print(c("  │  Uso da RAM         : ", "cinza") + _barra_progresso(pct_ram))
        else:
            msg_aviso("Não foi possível obter dados de RAM neste sistema.")
        print(c("  └─────────────────────────────────────────────────────┘", "azul"))
        print()

        # ── Armazenamento ─────────────────────────────────────────────────────
        print(c("  ┌─── Armazenamento (Disco Atual) ──────────────────────┐", "azul"))
        try:
            disco = shutil.disk_usage(BASE_DIR)
            pct_disco = disco.used / disco.total * 100
            linha_item("Total",  _bytes_para_legivel(disco.total))
            linha_item("Usado",  _bytes_para_legivel(disco.used))
            linha_item("Livre",  _bytes_para_legivel(disco.free))
            print(c("  │  Uso do Disco       : ", "cinza") + _barra_progresso(pct_disco))
            linha_item("Caminho", BASE_DIR, cor_valor="cinza")
        except Exception as e:
            msg_aviso(f"Não foi possível ler disco: {e}")
        print(c("  └─────────────────────────────────────────────────────┘", "azul"))
        print()

        print(c("  [R] Atualizar   [0] Fechar SysMonitor", "cinza"))
        print()
        op = input(c("  SysMonitor ➤ ", "ciano")).strip().upper()
        if op not in ("R", ""):
            break

# ─────────────────────────────────────────────────────────────────────────────
#  APP 4 ─ FILE EXPLORER (Explorador de Arquivos)
# ─────────────────────────────────────────────────────────────────────────────

def app_file_explorer():
    """
    Explorador de arquivos TUI.
    Funcionalidades:
      • Listar arquivos e pastas com tamanho e data de modificação
      • Navegar entre diretórios (cd, ..)
      • Criar novos diretórios
      • Deletar arquivos ou pastas (com confirmação)
    """
    diretorio_atual = os.getcwd()

    while True:
        exibir_banner("File Explorer")

        print(c(f"\n  📂 {diretorio_atual}", "amarelo", negrito=True))
        linha_h(tamanho=65)

        # ── Lista os itens do diretório atual ─────────────────────────────────
        try:
            itens = sorted(os.listdir(diretorio_atual))
        except PermissionError:
            msg_erro("Sem permissão para acessar este diretório.")
            diretorio_atual = os.path.dirname(diretorio_atual)
            pausar()
            continue

        pastas   = [i for i in itens if os.path.isdir(os.path.join(diretorio_atual, i))]
        arquivos = [i for i in itens if os.path.isfile(os.path.join(diretorio_atual, i))]

        print(c(f"\n  {'NOME':<38} {'TIPO':<10} {'TAMANHO':>10}  MODIFICADO", "cinza"))
        linha_h(char="·", tamanho=65, cor_nome="cinza")

        # Pastas primeiro
        for pasta in pastas:
            caminho_p = os.path.join(diretorio_atual, pasta)
            try:
                mtime = datetime.datetime.fromtimestamp(
                    os.path.getmtime(caminho_p)
                ).strftime("%d/%m/%y %H:%M")
            except Exception:
                mtime = "?"
            print(
                c(f"  📁 {pasta:<37}", "azul") +
                c(f"{'DIR':<10}", "cinza") +
                c(f"{'—':>10}", "cinza") +
                c(f"  {mtime}", "cinza", dim=True)
            )

        # Depois os arquivos
        for arquivo in arquivos:
            caminho_a = os.path.join(diretorio_atual, arquivo)
            try:
                sz    = os.path.getsize(caminho_a)
                mtime = datetime.datetime.fromtimestamp(
                    os.path.getmtime(caminho_a)
                ).strftime("%d/%m/%y %H:%M")
                ext   = os.path.splitext(arquivo)[1].upper() or "FILE"
            except Exception:
                sz, mtime, ext = 0, "?", "?"

            # Colorização por extensão
            cor_arq = "verde" if ext in (".PY", ".SH", ".BAT") else \
                      "amarelo" if ext in (".TXT", ".MD", ".JSON") else "branco"
            print(
                c(f"  📄 {arquivo:<37}", cor_arq) +
                c(f"{ext[1:]:<10}", "cinza") +
                c(f"{_bytes_para_legivel(sz):>10}", "cinza") +
                c(f"  {mtime}", "cinza", dim=True)
            )

        if not itens:
            msg_aviso("Diretório vazio.")

        print()
        linha_h(tamanho=65)
        print(c("  [N] Navegar   [C] Criar pasta   [D] Deletar   [0] Sair", "cinza"))
        print()

        cmd = input(c("  Explorer ➤ ", "ciano", negrito=True)).strip().upper()

        # ── Navegar ───────────────────────────────────────────────────────────
        if cmd == "N":
            destino = input(c("  Destino (nome da pasta ou caminho): ", "ciano")).strip()
            if destino == "..":
                novo = os.path.dirname(diretorio_atual)
            else:
                novo = os.path.abspath(os.path.join(diretorio_atual, destino))
            if os.path.isdir(novo):
                diretorio_atual = novo
            else:
                msg_erro(f"Diretório não encontrado: {novo}")
                pausar()

        # ── Criar pasta ───────────────────────────────────────────────────────
        elif cmd == "C":
            nome_pasta = input(c("  Nome da nova pasta: ", "ciano")).strip()
            if nome_pasta:
                novo_caminho = os.path.join(diretorio_atual, nome_pasta)
                try:
                    os.makedirs(novo_caminho, exist_ok=False)
                    msg_ok(f"Pasta '{nome_pasta}' criada!")
                except FileExistsError:
                    msg_erro(f"'{nome_pasta}' já existe.")
                except Exception as e:
                    msg_erro(str(e))
            else:
                msg_erro("Nome não pode ser vazio.")
            pausar()

        # ── Deletar ───────────────────────────────────────────────────────────
        elif cmd == "D":
            alvo_nome = input(c("  Nome do arquivo/pasta a deletar: ", "ciano")).strip()
            alvo_path = os.path.join(diretorio_atual, alvo_nome)
            if not os.path.exists(alvo_path):
                msg_erro(f"'{alvo_nome}' não encontrado.")
            else:
                tipo = "pasta" if os.path.isdir(alvo_path) else "arquivo"
                conf = input(
                    c(f"  ⚠  Confirma deletar {tipo} '{alvo_nome}'? (s/N): ", "amarelo")
                ).strip().lower()
                if conf == "s":
                    try:
                        if os.path.isdir(alvo_path):
                            shutil.rmtree(alvo_path)
                        else:
                            os.remove(alvo_path)
                        msg_ok(f"'{alvo_nome}' removido com sucesso.")
                    except Exception as e:
                        msg_erro(str(e))
                else:
                    msg_aviso("Operação cancelada.")
            pausar()

        elif cmd == "0":
            break
        else:
            msg_erro("Comando inválido.")
            pausar()

# ═════════════════════════════════════════════════════════════════════════════
#  SEÇÃO 8 ─ MENU PRINCIPAL
# ═════════════════════════════════════════════════════════════════════════════

# Mapa de funções: conecta o nome de função (string no catálogo) à função real
MAPA_FUNCOES = {
    "app_notepad"       : app_notepad,
    "app_calculadora"   : app_calculadora,
    "app_sysmonitor"    : app_sysmonitor,
    "app_file_explorer" : app_file_explorer,
}

def menu_principal():
    """
    Menu principal dinâmico do FredSys.
    Exibe APENAS os apps instalados pelo usuário logado + opções fixas do sistema.
    """
    global USUARIO_LOGADO
    while True:
        exibir_banner("Menu Principal")

        instalados = apps_instalados(USUARIO_LOGADO)

        print(c(f"  Olá, {USUARIO_LOGADO}! Seus apps instalados:\n", "amarelo"))

        # ── Itens dinâmicos (apps instalados) ────────────────────────────────
        if not instalados:
            msg_aviso("Você não tem apps instalados ainda.")
            msg_info("Acesse a App Store para instalar aplicativos.")
        else:
            for i, app_id in enumerate(instalados, start=1):
                if app_id in CATALOGO_APPS:
                    app_info = CATALOGO_APPS[app_id]
                    print(
                        c(f"  [{i}]", "ciano", negrito=True) +
                        c(f"  {app_info['nome']}", "branco")
                    )

        # ── Itens fixos do sistema ────────────────────────────────────────────
        print()
        linha_h(char="·", tamanho=40, cor_nome="azul")
        print(c("  [A]", "magenta") + c("  App Store (Gerenciar Apps)", "branco"))
        print(c("  [S]", "amarelo") + c("  Sair da Conta", "branco"))
        print(c("  [0]", "vermelho") + c("  Desligar FredSys", "branco"))
        print()

        op = input(c(f"  {USUARIO_LOGADO}@FredSys ➤ ", "ciano", negrito=True)).strip()

        # ── App Store ─────────────────────────────────────────────────────────
        if op.upper() == "A":
            tela_app_store()

        # ── Sair da conta ─────────────────────────────────────────────────────
        elif op.upper() == "S":
            nome_saindo = USUARIO_LOGADO
            USUARIO_LOGADO = None
            msg_info(f"Sessão de '{nome_saindo}' encerrada.")
            pausar()
            # Volta para a tela de autenticação
            tela_autenticacao()

        # ── Desligar ──────────────────────────────────────────────────────────
        elif op == "0":
            exibir_banner("Encerrando")
            print(c("\n  FredSys v2.0 encerrado com segurança.", "amarelo"))
            print(c(f"  Até logo, {USUARIO_LOGADO}!\n", "ciano", negrito=True))
            sys.exit(0)

        # ── App instalado selecionado ─────────────────────────────────────────
        elif op.isdigit():
            idx = int(op) - 1
            if 0 <= idx < len(instalados):
                app_id     = instalados[idx]
                nome_funcao = CATALOGO_APPS[app_id]["funcao"]
                funcao     = MAPA_FUNCOES.get(nome_funcao)
                if funcao:
                    try:
                        funcao()  # Executa o app selecionado
                    except KeyboardInterrupt:
                        msg_aviso("App interrompido pelo usuário.")
                        pausar()
                else:
                    msg_erro(f"Função '{nome_funcao}' não registrada no sistema.")
                    pausar()
            else:
                msg_erro("Número de app inválido.")
                pausar()
        else:
            msg_erro("Opção inválida.")
            pausar()

# ═════════════════════════════════════════════════════════════════════════════
#  SEÇÃO 9 ─ PONTO DE ENTRADA DO PROGRAMA
# ═════════════════════════════════════════════════════════════════════════════

def inicializar_sistema():
    """
    Verifica e cria a estrutura de arquivos necessária para o FredSys.
    Executado uma única vez na inicialização.
    """
    # Cria a pasta MeusDocumentos se não existir
    os.makedirs(PASTA_DOCS, exist_ok=True)

    # Garante que os arquivos JSON existam (evita erros na primeira execução)
    if not os.path.exists(ARQUIVO_USERS):
        salvar_json(ARQUIVO_USERS, {})

    if not os.path.exists(ARQUIVO_CONFIG):
        salvar_json(ARQUIVO_CONFIG, {"usuarios_apps": {}})


if __name__ == "__main__":
    try:
        # 1. Configura o ambiente
        inicializar_sistema()

        # 2. Tela de autenticação (fica em loop até login válido)
        tela_autenticacao()

        # 3. Menu principal (loop infinito até desligar)
        menu_principal()

    except KeyboardInterrupt:
        # Ctrl+C em qualquer ponto do programa
        print(c("\n\n  FredSys interrompido. Até logo!\n", "amarelo"))
        sys.exit(0)
    except Exception as e:
        # Captura erros inesperados para não travar sem mensagem
        print(c(f"\n  ERRO CRÍTICO DO SISTEMA: {e}", "vermelho", negrito=True))
        print(c("  Reinicie o FredSys. Se o erro persistir, verifique os arquivos .json.\n", "cinza"))
        sys.exit(1)
