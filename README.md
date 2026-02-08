<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-GPL--3.0-blue?style=for-the-badge)
![Tests](https://img.shields.io/badge/Tests-329-success?style=for-the-badge)

**Configurador de Tecnologias para Desenvolvedores**

*Automatize a configuracao de ambientes de desenvolvimento*

[Overview](#overview) •
[Funcionalidades](#funcionalidades) •
[Instalacao](#instalacao) •
[Uso](#uso) •
[Tecnologias](#tecnologias-suportadas) •
[Testes](#testes) •
[Documentacao](#documentacao)

</div>

---

## Overview

dev-start e uma ferramenta que automatiza a configuracao de ambientes de desenvolvimento. A aplicacao verifica e instala dependencias, clona repositorios Git, detecta automaticamente a tecnologia usada e configura tudo o necessario para o projeto funcionar.

**O que voce obtem:**
- Deteccao automatica de tecnologia (Java, Python, Node.js)
- Instalacao e configuracao completa do ambiente
- Interface grafica moderna e intuitiva
- Suporte a proxy para ambientes corporativos
- Criacao automatica de arquivos de ambiente (.env)
- Verificacao e instalacao automatica do Git

---

## Funcionalidades

| Funcionalidade | Descricao |
|----------------|-----------|
| **Deteccao Automatica** | Analisa arquivos do repositorio para identificar a tecnologia |
| **Instalacao Completa** | Baixa e configura JDK, Maven, virtualenv, Node.js |
| **Configuracao de Proxy** | Suporte a ambientes corporativos com proxy HTTP/HTTPS |
| **Interface Grafica** | GUI moderna com visualizacao de logs em tempo real |
| **Linha de Comando** | CLI para automacao e uso em scripts |
| **Multiplos Repositorios** | Configure varios projetos de uma vez |
| **Relatorios** | Geracao e exportacao de relatorios de instalacao |
| **Arquivos .env** | Criacao automatica de arquivos de ambiente |

---

## Instalacao

### Requisitos

| Requisito | Versao |
|-----------|--------|
| Python | 3.8+ |
| Git | Qualquer (instalado automaticamente se ausente) |

### Inicio Rapido

```bash
# Clone o repositorio
git clone https://github.com/JohnPitter/dev-start.git
cd dev-start

# Instale as dependencias
pip install -r requirements.txt
```

---

## Uso

### Interface Grafica (GUI)

```bash
python gui.py
```

A GUI oferece:
- Design profissional com identidade visual da aplicacao
- Interface intuitiva para configuracao em portugues
- Visualizacao de logs em tempo real com codigo de cores
- Geracao e exportacao de relatorios de instalacao
- Configuracao de proxy visual
- Indicador de progresso animado

### Linha de Comando (CLI)

```bash
# Configurar um unico repositorio
python -m src.cli https://github.com/user/my-project

# Configurar multiplos repositorios
python -m src.cli https://github.com/user/project1 https://github.com/user/project2

# Configurar com proxy (ambiente corporativo)
python -m src.cli --http-proxy http://proxy.company.com:8080 --https-proxy http://proxy.company.com:8080 https://github.com/user/project
```

Para exemplos detalhados, consulte [docs/USAGE.md](docs/USAGE.md).

---

## Tecnologias Suportadas

| Tecnologia | Deteccao | Instalacao |
|------------|----------|------------|
| **Java/SpringBoot** | Maven (pom.xml), Gradle (build.gradle) | JDK + Maven/Gradle |
| **Python** | requirements.txt, setup.py, pyproject.toml | virtualenv + dependencias |
| **Node.js** | package.json | Node.js + npm install |

---

## Testes

A aplicacao possui **329 testes automatizados** com cobertura de **96.54%**.

| Categoria | Quantidade | Descricao |
|-----------|------------|-----------|
| **Unitarios** | 234 | Detector, Proxy, Ambiente, Repositorios, Instaladores, CLI |
| **E2E** | 5 | Clonagem real, deteccao em projetos reais, setup completo |
| **Performance** | 6 | Velocidade de deteccao, criacao de arquivos, eficiencia de memoria |
| **GUI** | 56 | Componentes, widgets, integracao, inicializacao |
| **Instaladores** | 28 | Git Installer, instaladores base |

```bash
# Todos os testes com cobertura
pytest tests/ -v --cov=src --cov-report=html

# Apenas testes unitarios e integracao
pytest tests/ -v -m "not e2e and not performance"

# Apenas testes E2E
pytest tests/test_e2e.py -v -m e2e

# Apenas testes de performance
pytest tests/test_performance.py -v -m performance

# Apenas testes de GUI
pytest tests/test_gui.py -v -m gui
```

Para documentacao completa de testes, consulte [docs/TESTING.md](docs/TESTING.md).

---

## Gerando Executavel

```bash
# Opcao 1: Usar o script build.bat
build.bat

# Opcao 2: Manualmente
pip install -r requirements.txt
pyinstaller dev-start.spec --clean
```

O executavel sera criado em `dist/dev-start.exe`.

```bash
# Uso do executavel
dev-start.exe https://github.com/user/project

# Com proxy
dev-start.exe --http-proxy http://proxy:8080 --https-proxy http://proxy:8080 https://github.com/user/project
```

---

## Documentacao

| Documento | Descricao |
|-----------|-----------|
| [docs/USAGE.md](docs/USAGE.md) | Guia detalhado de uso (GUI + CLI) |
| [docs/TESTING.md](docs/TESTING.md) | Documentacao de testes |
| [CHANGELOG.md](CHANGELOG.md) | Historico de alteracoes |

---

## Licenca

Este projeto esta licenciado sob a [GPL-3.0 License](LICENSE).

---

## Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudancas (`git commit -m 'feat: adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

---

## Suporte

- Abra uma [issue](https://github.com/JohnPitter/dev-start/issues) para reportar bugs
- Use [discussions](https://github.com/JohnPitter/dev-start/discussions) para perguntas

---

<div align="center">

**[Voltar ao topo](#dev-start)**

</div>
