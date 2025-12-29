# Changelog - dev-start

## [2.5.0] - 28/12/2025

### Added - Variáveis de Ambiente Permanentes

#### Configuração Permanente do Sistema
- **Variáveis de ambiente persistentes**: Todas as tecnologias agora são instaladas com variáveis de ambiente permanentes
- **PATH do usuário atualizado**: Tecnologias adicionadas ao PATH permanente do Windows
- **Funciona em qualquer terminal**: Comandos como `javac`, `node`, `python`, `git`, `mvn` funcionam em qualquer CMD/PowerShell
- **Disponível para todos os projetos**: Tecnologias instaladas uma vez, utilizáveis em qualquer projeto

**Variáveis configuradas permanentemente:**
- Java: `JAVA_HOME` + `PATH`
- Maven: `MAVEN_HOME` + `PATH`
- Node.js: `NODE_HOME` + `PATH`
- Git: `GIT_HOME` + `PATH`

**Como testar:**
1. Após instalar uma tecnologia com a aplicação
2. Feche a aplicação completamente
3. Abra um novo CMD ou PowerShell
4. Execute comandos:
   ```cmd
   javac --help        # Se instalou Java
   mvn --version       # Se instalou Maven
   node --version      # Se instalou Node.js
   git --version       # Se instalou Git
   python --version    # Se instalou Python
   ```

**Observação importante:** Após a instalação, é necessário **reiniciar o terminal/IDE** para que as novas variáveis de ambiente sejam carregadas.

**Implementação técnica:**
- Usa PowerShell `[Environment]::SetEnvironmentVariable()` para configurar PATH permanente
- Usa comando `setx` para criar variáveis de ambiente permanentes
- Atualiza variáveis no escopo do usuário (não requer privilégios de administrador)

## [2.4.1] - 28/12/2025

### Improved - Formatação de Logs

#### Melhor Legibilidade dos Logs
- **Quebras de linha adicionadas**: Todos os logs agora têm espaçamento adequado
- **Separação visual**: Mensagens importantes têm linha em branco antes
- **Agrupamento lógico**: Seções relacionadas ficam claramente separadas
- **Consistência**: Mesmo padrão em todos os installers (Java, Node.js, Python)

**Exemplo antes:**
```
Configuring Java project...Maven not found. Installing Maven...✓ Maven installed successfully✓ Maven directory created/verified
```

**Exemplo depois:**
```
Configuring Java project...

Maven not found. Installing Maven...

✓ Maven environment variables configured
  MAVEN_HOME: C:\Users\user\.dev-start\tools\maven
  PATH: C:\Users\user\.dev-start\tools\maven\bin (added)

✓ Maven installed successfully

✓ Maven directory created/verified: C:\Users\user\.m2
```

#### Arquivos Modificados
- `src/installers/java_installer.py`: Quebras de linha em instalação, configuração e build
- `src/installers/nodejs_installer.py`: Quebras de linha em configuração e npm install
- `src/installers/python_installer.py`: Quebras de linha em configuração e pip install

### Improved - Debug Information

#### Informações Detalhadas Durante Instalação
- Exibe estrutura de diretórios do Maven após extração
- Lista arquivos no diretório `bin/`
- Mostra caminho completo do executável Maven usado
- Mensagens de debug para troubleshooting

---

## [2.4.0] - 28/12/2025

### Added - Validação de Build e Variáveis de Ambiente

#### Validação de Build Automática
- **Validação de artifacts**: Verifica se JARs foram criados após o build
- **Informações detalhadas**: Mostra nome e tamanho dos JARs gerados
- **Instruções de execução**: Comando completo para executar a aplicação
- **Suporte Maven e Gradle**: Valida tanto `target/` quanto `build/libs/`

**Exemplo de Output:**
```
============================================================
Build Validation
============================================================
✓ Build artifacts found:
  - desafio-cast-0.0.1-SNAPSHOT.jar (45.32 MB)

✓ Application is ready to run!
  To run: cd C:\...\desafio-cast && java -jar target/desafio-cast-0.0.1-SNAPSHOT.jar
============================================================
```

#### Variáveis de Ambiente no Processo Atual
- **Atualização imediata**: Variáveis de ambiente atualizadas no processo atual
- **Disponibilidade imediata**: Ferramentas disponíveis sem reiniciar
- **Feedback detalhado**: Mostra exatamente quais variáveis foram configuradas

**Aplicado para:**
- **Java**: `JAVA_HOME` e `PATH` (java/bin)
- **Maven**: `MAVEN_HOME` e `PATH` (maven/bin)
- **Node.js**: `NODE_HOME` e `PATH` (nodejs)
- **Git**: `GIT_HOME` e `PATH` (git/bin ou git/cmd)

**Exemplo de Output:**
```
✓ Maven environment variables configured
  MAVEN_HOME: C:\Users\user\.dev-start\tools\maven
  PATH: C:\Users\user\.dev-start\tools\maven\bin (added)
```

#### Busca Inteligente de Executáveis
- **Método `_find_maven_executable()`**: Procura Maven no PATH e no diretório de instalação
- **Fallback robusto**: Tenta `mvn`, `mvn.cmd`, `mvn.bat` em múltiplos locais
- **Uso de caminho completo**: Executa com caminho completo se não estiver no PATH

#### Arquivos Modificados
- `src/installers/java_installer.py`:
  - `_validate_build()`: Novo método para validar artifacts
  - `_find_maven_executable()`: Busca inteligente do executável Maven
  - Atualização de `os.environ` em `_install_maven()` e `install()`
  - Mensagens detalhadas de configuração de ambiente
- `src/installers/nodejs_installer.py`:
  - Atualização de `os.environ` em `install()`
- `src/installers/git_installer.py`:
  - Atualização de `os.environ` em `_add_to_path()`

### Improved - Output Detalhado
- Mensagens claras sobre cada etapa da configuração
- Feedback sobre variáveis de ambiente configuradas
- Instruções práticas para executar a aplicação

---

## [2.3.1] - 28/12/2025

### Fixed - Maven Download

#### Correção de URL do Maven
- **Problema**: URL do Maven 3.9.6 retornando erro 404
- **Solução**: Atualizado para Maven 3.9.9 com múltiplos mirrors de fallback
- **URLs de fallback**:
  1. `dlcdn.apache.org` (mirror oficial)
  2. `archive.apache.org` (arquivo oficial)
  3. `mirrors.estointernet.in` (mirror alternativo)
- **Lógica de retry**: Tenta cada URL até encontrar uma que funcione
- **Validação**: Não executa `mvn clean install` se Maven não estiver disponível

#### Melhorias no Output
- Mensagens mais detalhadas sobre tentativas de download
- Feedback claro sobre sucesso/falha de cada mirror
- Instruções para instalação manual se todos os mirrors falhar

#### Arquivos Modificados
- `src/installers/java_installer.py`:
  - Atualizado `MAVEN_URL` para `MAVEN_URLS` (lista de URLs)
  - Modificado `_install_maven()` para tentar múltiplos mirrors
  - Adicionado controle de `maven_available` no `configure()`
  - Skip de `mvn clean install` se Maven não estiver disponível

---

## [2.3.0] - 28/12/2025

### Added - Verificação e Configuração Automática de Ferramentas

#### Verificação de Ferramentas de Build
- **Maven**: Verifica se Maven está instalado antes de usar em projetos Java
  - Instalação automática se não estiver presente
  - Criação de pasta `.m2` e `settings.xml`
  - Configuração de repositório local
- **pip**: Verifica se pip está instalado para projetos Python
  - Instalação automática via `python -m ensurepip`
  - Criação de pasta `pip` e arquivo `pip.ini`
  - Configuração de timeout padrão (60s)
- **npm**: Verifica se npm está instalado para projetos Node.js
  - Criação de arquivo `.npmrc` na home do usuário
  - Configuração de registry e cache
  - Configuração de timeout (60000ms)

#### Configuração Automática do Git
- **Diálogo de configuração**: Ao instalar Git, pergunta ao usuário:
  - Nome completo (user.name)
  - Email (user.email)
  - Verificação SSL (http.sslVerify)
- **GUI**: Diálogos interativos usando tkinter.simpledialog
- **CLI**: Prompts interativos usando click.prompt
- **Verificação inteligente**: Detecta se Git já está configurado
- **Configuração global**: Todas as configurações são salvas globalmente

#### Arquivos Modificados
- `src/installers/java_installer.py`:
  - `is_maven_installed()`: Verifica instalação do Maven
  - `_ensure_maven_directories()`: Cria `.m2` e `settings.xml`
  - Modificado `configure()` para instalar Maven se necessário
- `src/installers/python_installer.py`:
  - `is_pip_installed()`: Verifica instalação do pip
  - `_ensure_pip_directories()`: Cria pasta `pip` e `pip.ini`
  - Modificado `configure()` para instalar pip se necessário
- `src/installers/nodejs_installer.py`:
  - `is_npm_installed()`: Verifica instalação do npm
  - `_ensure_npm_config()`: Cria arquivo `.npmrc`
  - Modificado `configure()` para verificar npm
- `src/installers/git_installer.py`:
  - `configure()`: Aceita parâmetros user_name, user_email, ssl_verify
  - `_is_git_configured()`: Verifica se Git já está configurado
  - Configuração global de user.name, user.email, http.sslVerify
- `src/gui.py`:
  - `_prompt_git_config()`: Diálogo para configuração do Git
  - Integrado verificação de Git no fluxo de instalação
- `src/cli.py`:
  - `_configure_git()`: Prompts para configuração do Git
  - Integrado verificação de Git no `ensure_git_installed()`

### Improved - Mensagens e Feedback

#### Output Detalhado
- Mensagens de sucesso/falha para cada ferramenta verificada
- Feedback sobre criação de diretórios e arquivos de configuração
- Mensagens coloridas (CLI) para melhor visibilidade

---

## [2.2.0] - 28/12/2025

### Added - Instalação Automática de Dependências

#### Execução Automática de Builds
- **Maven clean install**: Projetos Java/SpringBoot agora executam `mvn clean install -DskipTests`
- **Gradle build**: Projetos Gradle executam `gradle build -x test` (ou `gradlew.bat`)
- **npm install**: Projetos Node.js executam `npm install`
- **pip install**: Projetos Python executam `pip install -r requirements.txt` (ou `pip install -e .`)

#### Melhorias na Instalação
- **Timeout de 10 minutos**: Cada build tem timeout de 600 segundos
- **Output detalhado**: Mensagens claras sobre o progresso da instalação
- **Erro não-bloqueante**: Se a instalação falhar, o processo continua com warning
- **Detecção de erros**: Captura e exibe primeiros 500 caracteres do erro
- **Suporte a múltiplos formatos**:
  - Java: Maven (pom.xml) e Gradle (build.gradle, gradlew.bat)
  - Python: requirements.txt, setup.py, pyproject.toml
  - Node.js: package.json

#### Arquivos Modificados
- `src/installers/java_installer.py`: Adicionados `_run_maven_install()` e `_run_gradle_build()`
- `src/installers/nodejs_installer.py`: Adicionado `_run_npm_install()`
- `src/installers/python_installer.py`: Adicionado `_run_pip_install()`

### Improved - Interface

#### Banner Simplificado
- **Removido "dev-start"**: Banner agora mostra apenas "BRADESCO Technology Configurator"
- **Identidade mais limpa**: Foco na marca Bradesco
- **Arquivo**: `src/gui.py` - Linha 277

---

## [2.1.1] - 28/12/2025

### Improved - UX e Estabilidade

#### Interface de Proxy Otimizada
- **Configuração de proxy oculta por default**: Proxy fields agora ficam escondidos para simplificar a interface
- **Botão "⚙ Configurar Proxy"**: Toggle button para mostrar/ocultar configurações de proxy
- **UX melhorada**: Interface mais limpa para usuários que não precisam de proxy
- **Arquivo**: `src/gui.py` - Adicionado método `toggle_proxy()`

#### Correção de Erro de Permissão ao Deletar Repositórios
- **Problema**: `[WinError 5] Acesso negado` ao tentar deletar repositórios existentes
- **Solução**: Implementado sistema robusto de deleção com retry logic
- **Funcionalidades**:
  - Retry automático (3 tentativas) para diretórios locked
  - Handler para arquivos read-only (`.git` files)
  - Intervalo de 1 segundo entre tentativas
  - Mensagens de erro claras e instruções para o usuário
  - Suporte para arquivos em uso por outros programas
- **Arquivos modificados**:
  - `src/gui.py`: Adicionados métodos `safe_rmtree()` e `remove_readonly()`
  - `src/cli.py`: Adicionados mesmos métodos para consistência

#### Melhorias Técnicas
- Imports otimizados: `os`, `stat`, `time`, `shutil`
- Error handling robusto para operações de I/O
- Mensagens de feedback detalhadas durante deleção
- Compatibilidade com Windows file locking

---

## [2.1.0] - 28/12/2025

### Added - Tema Bradesco na GUI ⭐ DESTAQUE

#### Interface Gráfica com Design Bradesco
- **Cores Institucionais**: Implementado paleta completa do Bradesco
  - Vermelho principal: #CC092F
  - Vermelho escuro: #A00724 (hover states)
  - Cinza claro: #F5F5F5 (background)
  - Cinza escuro: #333333 (status bar)

- **Header Personalizado**:
  - Logo "BRADESCO" em destaque (24pt bold)
  - Subtítulo "dev-start Technology Configurator"
  - Background vermelho Bradesco (#CC092F)
  - Altura fixa de 80px

- **Botões Customizados**:
  - Botão principal: Vermelho Bradesco com hover escuro
  - Botões secundários: Cinza claro
  - Padding e fontes otimizadas
  - Estilos: `Bradesco.TButton`, `Secondary.TButton`

- **Componentes Temáticos**:
  - Log de instalação com cores Bradesco
  - Barra de progresso vermelha
  - Status bar em cinza escuro
  - Labels e frames com tema consistente

- **Interface em Português**:
  - "Configuração"
  - "URLs de Repositórios (uma por linha)"
  - "Iniciar Instalação"
  - "Limpar Log"
  - "Exibir Relatório"
  - "Log de Instalação"
  - "Pronto"

#### Arquivos Modificados
- `src/gui.py`: Adicionado `BradescoTheme` class e `setup_styles()` method
- Tamanho da janela aumentado para 1000x750px
- Fontes atualizadas para Segoe UI (interface) e Consolas (log)

#### Documentação
- `BRADESCO_THEME.md`: Documentação completa do tema
  - Paleta de cores
  - Layout detalhado
  - Componentes visuais
  - Guia de estilo

### Fixed

#### Bug #1 - Missing subprocess import
- **Arquivo**: `src/installers/java_installer.py`
- **Problema**: `NameError: name 'subprocess' is not defined`
- **Solução**: Adicionado `import subprocess`
- **Impacto**: Projetos Java/SpringBoot agora funcionam corretamente

---

## [2.0.0] - 28/12/2025

### Added - Funcionalidades Avançadas

#### 1. Interface Gráfica (GUI) Original
- Interface tkinter completa
- Logs em tempo real
- Exportação de relatórios
- Configuração de proxy visual
- **Arquivo**: `src/gui.py` (482 linhas iniciais)

#### 2. Geração de Relatórios
- Relatórios detalhados com timestamps
- Estatísticas de sucesso/falha
- Tecnologias detectadas
- Duração de execução
- Exportação para arquivo .txt

#### 3. Cobertura de Código (pytest-cov)
- `pytest.ini`: Configuração pytest
- `.coveragerc`: Configuração coverage
- Relatórios HTML, XML e terminal
- Cobertura atual: ~26%

#### 4. Testes E2E
- **Arquivo**: `tests/test_e2e.py` (5 testes)
- Repositórios reais do GitHub
- Flask, Click, Calculator, Gitignore
- Clonagem e detecção real

#### 5. Testes de Performance
- **Arquivo**: `tests/test_performance.py` (6 testes)
- Métricas de tempo detalhadas
- Validação de eficiência
- Todas operações <10ms

#### 6. Testes de UI/GUI
- **Arquivo**: `tests/test_gui.py` (24 testes)
- InstallationReport (6 testes)
- LogRedirector (3 testes)
- DevStartGUI (15 testes)

#### Dependências
- `pytest >= 7.4.0`
- `pytest-cov >= 4.1.0`

---

## [1.0.0] - 28/12/2025

### Added - Release Inicial

#### Funcionalidades Core

1. **Verificação e Instalação Automática do Git**
   - Detecção de instalação
   - Instalação MinGit para Windows
   - Configuração de PATH
   - **Arquivo**: `src/installers/git_installer.py`

2. **Detecção Automática de Tecnologias**
   - Java/SpringBoot (Maven, Gradle)
   - Python (requirements.txt, setup.py)
   - Node.js (package.json)
   - **Arquivo**: `src/detector.py`

3. **Instaladores Automáticos**
   - JavaInstaller (JDK, Maven)
   - PythonInstaller (virtualenv, pip)
   - NodeJSInstaller (npm)
   - BaseInstaller (funcionalidade comum)

4. **Gerenciadores**
   - ProxyManager (HTTP/HTTPS)
   - RepositoryManager (Git operations)
   - EnvironmentManager (.env, configs)

5. **Interface CLI**
   - Click framework
   - Colorama para cores
   - Suporte a múltiplos repositórios
   - Configuração de proxy

#### Testes (46 testes iniciais)
- test_detector.py (4 testes)
- test_proxy_manager.py (7 testes)
- test_env_manager.py (7 testes)
- test_installers.py (14 testes)
- test_repo_manager.py (6 testes)
- test_integration.py (8 testes)

#### Build
- PyInstaller configurado
- `build.bat` para Windows
- `dev-start.spec`

#### Documentação
- README.md
- CLAUDE.md (guia para desenvolvedores)
- IMPLEMENTATION_SUMMARY.md
- example_usage.md

---

## Estatísticas por Versão

### v2.4.1 (Atual)
- **Testes**: 76+
- **Cobertura**: ~26%
- **Linhas de Código**: ~3.750
- **Arquivos Python**: 26
- **Arquivos .md**: 9
- **Status**: ✅ PRODUÇÃO READY

### v2.4.0
- **Testes**: 76+
- **Cobertura**: ~26%
- **Linhas de Código**: ~3.700
- **Arquivos Python**: 26
- **Arquivos .md**: 9
- **Status**: ✅ PRODUÇÃO READY

### v2.3.1
- **Testes**: 76+
- **Cobertura**: ~26%
- **Linhas de Código**: ~3.500
- **Arquivos Python**: 26
- **Arquivos .md**: 9
- **Status**: ✅ PRODUÇÃO READY

### v2.3.0
- **Testes**: 76+
- **Cobertura**: ~26%
- **Linhas de Código**: ~3.500
- **Arquivos Python**: 26
- **Arquivos .md**: 9
- **Status**: ✅ PRODUÇÃO READY

### v2.2.0
- **Testes**: 76+
- **Cobertura**: ~26%
- **Linhas de Código**: ~3.200
- **Arquivos Python**: 26
- **Arquivos .md**: 9
- **Status**: ✅ PRODUÇÃO READY

### v2.1.1
- **Testes**: 76+
- **Cobertura**: ~26%
- **Linhas de Código**: ~3.000
- **Arquivos Python**: 26
- **Arquivos .md**: 9
- **Status**: ✅ PRODUÇÃO READY

### v2.1.0
- **Testes**: 76+
- **Cobertura**: ~26%
- **Linhas de Código**: ~2.900
- **Arquivos Python**: 26
- **Arquivos .md**: 9
- **Status**: ✅ PRODUÇÃO READY

### v2.0.0
- **Testes**: 76 (46 + 30 novos)
- **Cobertura**: ~26%
- **Linhas de Código**: ~2.800
- **Novos arquivos**: 5 (3 testes + 2 config)

### v1.0.0
- **Testes**: 46
- **Cobertura**: ~26%
- **Linhas de Código**: ~1.700
- **Arquivos Python**: 20

---

## Roadmap Futuro

### v3.0.0 (Planejado)
- [ ] Suporte a mais tecnologias (Go, Rust, Ruby, PHP)
- [ ] Docker integration
- [ ] CI/CD com GitHub Actions
- [ ] Auto-update
- [ ] Temas adicionais (dark mode)
- [ ] Multi-idioma (EN, PT, ES)
- [ ] Histórico de instalações
- [ ] Configurações persistentes

### Melhorias Contínuas
- [ ] Aumentar cobertura para 80%+
- [ ] Testes E2E automatizados em CI
- [ ] Performance benchmarks
- [ ] Publicação no PyPI
- [ ] Geração de binários para Linux/Mac

---

## Licença

Ver arquivo LICENSE

---

**Última Atualização**: 28 de Dezembro de 2025
**Versão Atual**: 2.4.1
**Status**: ✅ PRODUÇÃO READY
