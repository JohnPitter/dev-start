# Documentacao de Testes

[Voltar ao README](../README.md)

---

## Visao Geral

A aplicacao possui **329 testes automatizados** com cobertura de **96.54%** de todos os modulos.

---

## Executando os Testes

### Todos os testes com cobertura

```bash
pytest tests/ -v --cov=src --cov-report=html
```

### Por categoria

```bash
# Testes unitarios e integracao
pytest tests/ -v -m "not e2e and not performance"

# Testes E2E (com repositorios reais)
pytest tests/test_e2e.py -v -m e2e

# Testes de performance
pytest tests/test_performance.py -v -m performance

# Testes de GUI
pytest tests/test_gui.py -v -m gui
```

### Com unittest (legacy)

```bash
python -m unittest tests.test_detector
python -m unittest tests.test_proxy_manager
python -m unittest tests.test_env_manager
python -m unittest tests.test_installers
python -m unittest tests.test_repo_manager
python -m unittest tests.test_integration
```

---

## Cobertura de Testes

### Testes Unitarios (234 testes)

| Modulo | Testes | Cobertura |
|--------|--------|-----------|
| Detector de Tecnologias | 19 | 100% |
| Gerenciador de Proxy | 6 | 100% |
| Gerenciador de Ambiente | 14 | 100% |
| Gerenciador de Repositorios | 6 | 100% |
| Testes de Integracao | 7 | - |
| Instaladores Base | 24 | - |
| CLI Basico | 31 | - |
| Git Installer | 26 | - |
| Java Installer | 78 | - |
| Python Installer | 27 | 100% |
| Node.js Installer | 24 | 100% |

### Testes E2E (5 testes)

| Teste | Descricao |
|-------|-----------|
| Clonagem de repositorios | Clona repositorios reais do GitHub |
| Deteccao de tecnologias | Detecta tecnologias em projetos reais |
| Setup completo | Executa setup completo de ambiente |

### Testes de Performance (6 testes)

| Teste | Limite |
|-------|--------|
| Velocidade de deteccao de tecnologia | < 10ms |
| Criacao de arquivos .env | < 5ms |
| Configuracao de proxy | < 1ms |
| Criacao de diretorios | < 2ms |
| Deteccao de padroes | < 0.5ms |
| Eficiencia de memoria | Arquivos grandes |

### Testes de GUI (56 testes)

| Categoria | Testes |
|-----------|--------|
| Componentes de relatorio | 6 |
| Redirecionamento de logs | 3 |
| Widgets e interface | 27 |
| Integracao e instalacao completa | 14 |
| Main e inicializacao | 6 |

---

## Relatorio de Cobertura

```bash
# Gerar relatorio HTML de cobertura
pytest tests/ --cov=src --cov-report=html

# Abrir relatorio (Windows)
start htmlcov/index.html
```

### Modulos com 100% de cobertura

- detector.py
- env_manager.py
- proxy_manager.py
- repo_manager.py
- gui.py (99.74%)
- nodejs_installer.py
- python_installer.py
