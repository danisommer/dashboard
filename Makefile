# Nome do compilador e flags
CXX = g++
CXXFLAGS = -c -fPIC
LDFLAGS = -shared -Wl,-soname,getSysInfo.so

# Arquivos
SRC = getSysInfo.cpp
OBJ = getSysInfo.o
SO = libGetSysInfo.so
PYTHON_SCRIPT = /bin/python3 /home/danizs/Programacao/dashboard/main.py

# Alvo padrão
all: $(SO) run

# Compilar o arquivo objeto
$(OBJ): $(SRC)
	$(CXX) $(CXXFLAGS) $(SRC) -o $(OBJ)

# Criar a biblioteca compartilhada
$(SO): $(OBJ)
	$(CXX) $(LDFLAGS) -o $(SO) $(OBJ)

# Executar o script Python
run:
	$(PYTHON_SCRIPT)

# Limpar arquivos gerados
clean:
	rm -f $(OBJ) $(SO)

.PHONY: all run clean
