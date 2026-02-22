![image](https://github.com/user-attachments/assets/db39bfc4-df5e-4078-8308-28729568f36e)




# 💻 FredSys v2.0 — Terminal Operating System

> Sistema Operacional de Terminal (TUI) feito em Python puro.  
> Compatível com **Windows**, **Linux** e **Android (Termux)**.  
> Zero dependências externas — funciona com Python 3 puro.

---

## 🚀 Como executar

**Linux / Android (Termux)**
```bash
python3 fredsys_v2.py
```

**Windows (CMD ou PowerShell)**
```cmd
python fredsys_v2.py
```

**Requisito mínimo:** Python 3.6+  
Verifique sua versão com `python --version` ou `python3 --version`

---

## ✨ Funcionalidades

| Módulo | Descrição |
|--------|-----------|
| 🔐 **Autenticação** | Login e criação de conta com senha em hash SHA-256 |
| 🛒 **App Store** | Instale e desinstale apps por usuário |
| 📝 **Notepad** | Bloco de notas com salvar e leitura de arquivos |
| 🔢 **Calculadora** | Expressões matemáticas com histórico de sessão |
| 💻 **SysMonitor** | RAM, disco, IP local, SO e arquitetura |
| 📁 **File Explorer** | Navegar, criar e deletar arquivos e pastas |

---

## 📂 Arquivos gerados localmente

Estes arquivos são criados automaticamente na primeira execução:
```
fredsys_users.json    → Contas de usuário (senhas em SHA-256)
fredsys_config.json   → Apps instalados por usuário
MeusDocumentos/       → Notas salvas pelo Notepad
```

> ⚠️ Esses arquivos estão no `.gitignore` e não são enviados ao GitHub.

---

## 🛠️ Tecnologias

- **Linguagem:** Python 3 puro
- **Bibliotecas:** `os` `sys` `json` `hashlib` `platform` `datetime` `shutil` `socket`
- **Interface:** ANSI Escape Codes (TUI Cyberpunk)

---

## 📄 Licença

MIT License — sinta-se livre para usar, modificar e distribuir.
