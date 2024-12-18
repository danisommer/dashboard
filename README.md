# Aplicação de Painel de Controle do Sistema

## Visão Geral
Este projeto é uma aplicação de painel de controle que exibe métricas do sistema em tempo real. Ele consiste em:
- Uma **interface gráfica em Python** (`dashboard_app.py`) para visualização das métricas do sistema.
- Um **backend em C++** (`getSysInfo.cpp`) para obter informações do sistema.

## Compilação e Execução

### Pré-requisitos
- **g++**: Para compilar o backend em C++.
- **Python 3**: Para executar a aplicação gráfica (matplotlib).

### Passos para Compilar e Executar (Linux)
1. Navegue até o diretório do projeto.
2. Execute o seguinte comando para compilar a biblioteca C++ e iniciar a aplicação Python (OU compile a partir do arquivo Makefile presente):
    ```bash
    g++ -c -fPIC getSysInfo.cpp -o getSysInfo.o
    g++ -shared -Wl,-soname,getSysInfo.so -o libGetSysInfo.so getSysInfo.o
    /bin/python3 main.py
    ```

## Estrutura de Arquivos
- `dashboard_app.py`: Interface gráfica em Python para exibição das métricas.
- `getSysInfo.cpp`: Backend em C++ para informações do sistema.
- `main.py`: Ponto de entrada da aplicação, conectando a interface gráfica ao backend.
