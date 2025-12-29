# dev-start

Um configurador de tecnologias para desenvolvedores.

## Descrição

dev-start é uma ferramenta que automatiza a configuração de ambientes de desenvolvimento. A aplicação:

- **Verifica e instala o Git** se não estiver presente no sistema
- Clona repositórios Git
- Detecta automaticamente a tecnologia usada (Java/SpringBoot, Python, Node.js)
- Instala e configura tudo necessário para o projeto rodar
- Suporta configuração de proxy para ambientes corporativos
- Cria arquivos de ambiente (.env) e configurações

## Tecnologias Suportadas

- **Java/SpringBoot** - Projetos Maven e Gradle
- **Python** - Projetos com requirements.txt, setup.py, pyproject.toml
- **Node.js** - Projetos com package.json

## Instalação

### Pré-requisitos

- Python 3.8 ou superior
- Git (será instalado automaticamente se não estiver presente)

### Instalação de Dependências

```bash
pip install -r requirements.txt
```

## Uso

### Interface Gráfica (GUI)

```bash
# Iniciar interface gráfica
python gui.py
```

**🎨 Interface Moderna e Intuitiva**

A GUI oferece:
- **Design profissional**: Interface limpa e moderna
- **Header customizado**: Identidade visual da aplicação
- **Interface intuitiva** para configuração em português
- **Visualização de logs** em tempo real com código de cores
- **Geração e exportação** de relatórios de instalação
- **Configuração de proxy** visual
- **Indicador de progresso** animado
- **Botões customizados** com cores destacadas

### Linha de Comando

```bash
python -m src.cli <repository-urls>
```

### Exemplos

**Configurar um único repositório:**
```bash
python -m src.cli https://github.com/user/my-project
```

**Configurar múltiplos repositórios:**
```bash
python -m src.cli https://github.com/user/project1 https://github.com/user/project2
```

**Configurar com proxy (ambiente corporativo):**
```bash
python -m src.cli --http-proxy http://proxy.company.com:8080 --https-proxy http://proxy.company.com:8080 https://github.com/user/project
```

## Gerando Executável Windows

Para criar um executável Windows:

```bash
# Opção 1: Usar o script build.bat
build.bat

# Opção 2: Manualmente
pip install -r requirements.txt
pyinstaller dev-start.spec --clean
```

O executável será criado em `dist/dev-start.exe`

### Usando o Executável

```bash
dev-start.exe https://github.com/user/project

# Com proxy
dev-start.exe --http-proxy http://proxy:8080 --https-proxy http://proxy:8080 https://github.com/user/project
```

## Estrutura do Projeto

```
dev-start/
├── src/
│   ├── cli.py              # Interface de linha de comando
│   ├── detector.py         # Detector de tecnologias
│   ├── env_manager.py      # Gerenciador de variáveis de ambiente
│   ├── proxy_manager.py    # Gerenciador de proxy
│   ├── repo_manager.py     # Gerenciador de repositórios
│   └── installers/         # Instaladores por tecnologia
│       ├── base.py
│       ├── java_installer.py
│       ├── python_installer.py
│       └── nodejs_installer.py
├── tests/                  # Testes unitários
├── requirements.txt        # Dependências
└── dev-start.spec         # Configuração PyInstaller
```

## Funcionalidades

### Detecção Automática
- Analisa arquivos do repositório para identificar a tecnologia
- Suporta múltiplos indicadores por tecnologia

### Instalação
- Java: Baixa e configura JDK e Maven
- Python: Cria virtualenv e instala dependências
- Node.js: Baixa Node.js e instala pacotes npm

### Configuração
- Cria arquivos de configuração padrão
- Define variáveis de ambiente
- Configura proxy quando necessário

## Testes

A aplicação possui **76+ testes automatizados** cobrindo todas as funcionalidades:

### Executar todos os testes com pytest
```bash
# Todos os testes com cobertura
pytest tests/ -v --cov=src --cov-report=html

# Apenas testes unitários e integração
pytest tests/ -v -m "not e2e and not performance"

# Apenas testes E2E (com repositórios reais)
pytest tests/test_e2e.py -v -m e2e

# Apenas testes de performance
pytest tests/test_performance.py -v -m performance

# Apenas testes de GUI
pytest tests/test_gui.py -v -m gui
```

### Executar com unittest (legacy)
```bash
# Testar detector de tecnologias
python -m unittest tests.test_detector

# Testar gerenciador de proxy
python -m unittest tests.test_proxy_manager

# Outros módulos...
python -m unittest tests.test_env_manager
python -m unittest tests.test_installers
python -m unittest tests.test_repo_manager
python -m unittest tests.test_integration
```

### Cobertura de Testes

#### Testes Unitários (46 testes)
- **Detector de Tecnologias** - 4 testes
- **Gerenciador de Proxy** - 7 testes
- **Gerenciador de Ambiente** - 7 testes
- **Instaladores (Git, Python, Node.js)** - 14 testes
- **Gerenciador de Repositórios** - 6 testes
- **Testes de Integração** - 8 testes

#### Testes E2E (5 testes)
- Clonagem de repositórios reais do GitHub
- Detecção de tecnologias em projetos reais
- Setup completo de ambiente

#### Testes de Performance (6 testes)
- Velocidade de detecção de tecnologia (<10ms)
- Criação de arquivos .env (<5ms)
- Configuração de proxy (<1ms)
- Criação de diretórios (<2ms)
- Detecção de padrões (<0.5ms)
- Eficiência de memória com arquivos grandes

#### Testes de GUI (24 testes)
- Componentes de relatório
- Redirecionamento de logs
- Widgets e interface
- Integração GUI

**Total: 76+ testes**

### Relatório de Cobertura

```bash
# Gerar relatório HTML de cobertura
pytest tests/ --cov=src --cov-report=html

# Abrir relatório
start htmlcov/index.html  # Windows
```

**Cobertura atual: ~26%** (núcleo testado, CLI e GUI não executados diretamente nos testes)

## Licença

Ver arquivo LICENSE
