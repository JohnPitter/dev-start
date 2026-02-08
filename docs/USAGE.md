# Guia de Uso

[Voltar ao README](../README.md)

---

## Interface Grafica (GUI)

### Iniciando a GUI

```bash
python gui.py
```

### Funcionalidades da GUI

A interface grafica oferece uma experiencia completa para configuracao de ambientes:

**Configuracao de Repositorios**
1. Insira a URL do repositorio Git no campo de texto
2. Opcionalmente, configure o proxy HTTP/HTTPS
3. Clique em "Configurar" para iniciar o processo
4. Acompanhe o progresso na area de logs em tempo real

**Configuracao de Proxy**
1. Acesse a secao de proxy na interface
2. Preencha os campos HTTP Proxy e HTTPS Proxy
3. As configuracoes serao aplicadas automaticamente ao clonar repositorios

**Relatorios de Instalacao**
1. Apos a configuracao, clique em "Gerar Relatorio"
2. O relatorio pode ser exportado para arquivo
3. Inclui detalhes de todas as etapas executadas

**Recursos Visuais**
- Logs em tempo real com codigo de cores (sucesso, erro, info)
- Indicador de progresso animado durante a configuracao
- Botoes customizados com cores destacadas
- Header com identidade visual da aplicacao

---

## Linha de Comando (CLI)

### Sintaxe

```bash
python -m src.cli [opcoes] <repository-urls>
```

### Opcoes

| Opcao | Descricao |
|-------|-----------|
| `--http-proxy <url>` | Configura proxy HTTP |
| `--https-proxy <url>` | Configura proxy HTTPS |

### Exemplos

**Configurar um unico repositorio:**

```bash
python -m src.cli https://github.com/user/my-project
```

**Configurar multiplos repositorios:**

```bash
python -m src.cli https://github.com/user/project1 https://github.com/user/project2
```

**Configurar com proxy (ambiente corporativo):**

```bash
python -m src.cli \
  --http-proxy http://proxy.company.com:8080 \
  --https-proxy http://proxy.company.com:8080 \
  https://github.com/user/project
```

---

## Usando o Executavel

Apos gerar o executavel com `build.bat` ou `pyinstaller`:

```bash
# Uso basico
dev-start.exe https://github.com/user/project

# Com proxy
dev-start.exe \
  --http-proxy http://proxy:8080 \
  --https-proxy http://proxy:8080 \
  https://github.com/user/project
```

---

## Fluxo de Configuracao

O dev-start executa as seguintes etapas automaticamente:

1. **Verificacao do Git** - Verifica se o Git esta instalado; instala automaticamente se necessario
2. **Clonagem** - Clona o repositorio para o diretorio local
3. **Deteccao** - Analisa os arquivos do repositorio para identificar a tecnologia
4. **Instalacao** - Baixa e configura as dependencias necessarias
5. **Configuracao** - Cria arquivos de ambiente (.env) e configuracoes
6. **Relatorio** - Gera relatorio com o resultado da configuracao
