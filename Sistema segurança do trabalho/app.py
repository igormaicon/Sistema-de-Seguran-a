from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import sqlite3


app = Flask(__name__)

# Função para conectar ao banco de dados SQLite
def connect_db():
    return sqlite3.connect('empresa.db')

# Criar as tabelas, caso ainda não existam
def init_db():
    with connect_db() as conn:
        # Criar a tabela de colaboradores
        conn.execute('''CREATE TABLE IF NOT EXISTS colaboradores (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nome TEXT NOT NULL,
                            cargo TEXT NOT NULL,
                            setor TEXT NOT NULL,
                            rg TEXT NOT NULL,
                            cpf TEXT NOT NULL,
                            nascimento DATE NOT NULL,
                            admissao DATE NOT NULL,
                            status TEXT NOT NULL,
                            desligamento DATE)''')

        # Criar a tabela de EPIs
        conn.execute('''CREATE TABLE IF NOT EXISTS epis (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nome TEXT NOT NULL,
                            ca TEXT NOT NULL,
                            vencimento DATE NOT NULL,
                            estoque_min INTEGER NOT NULL,
                            estoque_max INTEGER NOT NULL,
                            estoque_atual INTEGER NOT NULL DEFAULT 0,
                            preco REAL NOT NULL,
                            fabricante TEXT)''')

        # Criar a tabela de entradas
        conn.execute('''CREATE TABLE IF NOT EXISTS entradas (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            epi_id INTEGER,
                            quantidade INTEGER,
                            data DATE,
                            nota_fiscal TEXT,
                            fornecedor TEXT,
                            FOREIGN KEY (epi_id) REFERENCES epis (id))''')

        # Criar a tabela de saídas
        conn.execute('''CREATE TABLE IF NOT EXISTS saidas (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            epi_id INTEGER,
                            quantidade INTEGER,
                            colaborador_id INTEGER,
                            data DATE,
                            FOREIGN KEY (epi_id) REFERENCES epis (id),
                            FOREIGN KEY (colaborador_id) REFERENCES colaboradores (id))''')

        conn.execute('''CREATE TABLE IF NOT EXISTS movimentacoes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            epi_id INTEGER,
                            tipo TEXT NOT NULL,
                            quantidade INTEGER,
                            colaborador_id INTEGER,
                            data DATE,
                            FOREIGN KEY (epi_id) REFERENCES epis (id),
                            FOREIGN KEY (colaborador_id) REFERENCES colaboradores (id))''')

# Inicializando o banco de dados
init_db()

# Página inicial
@app.route('/')
def index():
    return render_template('index.html')

# Página de colaboradores com filtro
@app.route('/colaboradores', methods=["GET"])
def colaboradores():
    status_filter = request.args.get('status_filter', 'todos')
    
    query = "SELECT * FROM colaboradores"
    params = []
    
    if status_filter != 'todos':
        query += " WHERE status = ?"
        params.append(status_filter)
    
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        colaboradores_data = cursor.fetchall()
    
    return render_template('colaboradores.html', colaboradores=colaboradores_data, status_filter=status_filter)

@app.route('/editar_colaborador/<int:id>', methods=["GET", "POST"])
def editar_colaborador(id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM colaboradores WHERE id = ?''', (id,))
        colaborador = cursor.fetchone()

    if request.method == "POST":
        # Recebe os dados atualizados do formulário
        nome = request.form["nome"]
        cargo = request.form["cargo"]
        setor = request.form["setor"]
        rg = request.form["rg"]
        cpf = request.form["cpf"]
        nascimento = request.form["nascimento"]
        admissao = request.form["admissao"]
        status = request.form["status"]
        desligamento = request.form.get("desligamento")

        # Atualiza o colaborador no banco de dados
        with connect_db() as conn:
            conn.execute('''UPDATE colaboradores SET nome = ?, cargo = ?, setor = ?, rg = ?, cpf = ?, nascimento = ?, admissao = ?, status = ?, desligamento = ? 
                            WHERE id = ?''',
                         (nome, cargo, setor, rg, cpf, nascimento, admissao, status, desligamento, id))

        return redirect(url_for('colaboradores'))  # Redireciona de volta para a lista de colaboradores

    return render_template('editar_colaborador.html', colaborador=colaborador)

@app.route('/excluir_colaborador/<int:id>', methods=["POST"])
def excluir_colaborador(id):
    with connect_db() as conn:
        conn.execute('''DELETE FROM colaboradores WHERE id = ?''', (id,))
    
    return redirect(url_for('colaboradores'))

@app.route('/add_colaborador', methods=["POST"])
def add_colaborador():
    nome = request.form["nome"]
    cargo = request.form["cargo"]
    setor = request.form["setor"]
    rg = request.form["rg"]
    cpf = request.form["cpf"]
    nascimento = request.form["nascimento"]
    admissao = request.form["admissao"]
    status = request.form["status"]
    desligamento = request.form.get("desligamento")

    with connect_db() as conn:
        conn.execute('''INSERT INTO colaboradores (nome, cargo, setor, rg, cpf, nascimento, admissao, status, desligamento)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                        (nome, cargo, setor, rg, cpf, nascimento, admissao, status, desligamento))
    
    return redirect(url_for('colaboradores'))

# Adicionar EPI
@app.route('/add_epi', methods=["GET", "POST"])
def add_epi():
    if request.method == "POST":
        nome_epi = request.form["nome_epi"]
        fabricante = request.form["fabricante"]
        ca = request.form["ca"]
        vencimento = request.form["vencimento"]
        estoque_min = int(request.form["estoque_min"])
        estoque_max = int(request.form["estoque_max"])
        preco = float(request.form["preco"])

        # Inserir dados no banco de dados
        with connect_db() as conn:
            conn.execute('''INSERT INTO epis (nome, fabricante, ca, vencimento, estoque_min, estoque_max, preco)
                            VALUES (?, ?, ?, ?, ?, ?, ?)''',
                         (nome_epi, fabricante, ca, vencimento, estoque_min, estoque_max, preco))
            conn.commit()
        
        return redirect(url_for('epis'))  # Redireciona para a página de EPIs após cadastro

    return render_template('add_epi.html')


# Página de EPIs
@app.route('/epis')
def epis():
    with connect_db() as conn:
        cursor = conn.cursor()
        # Atualizamos a consulta para incluir a data de vencimento (validade)
        cursor.execute('''SELECT id, nome, fabricante, ca, vencimento, estoque_min, estoque_max, preco FROM epis''')
        epis_data = cursor.fetchall()

    return render_template('epi.html', epis=epis_data)



@app.route('/editar_epi/<int:id>', methods=["GET", "POST"])
def editar_epi(id):
    with connect_db() as conn:
        cursor = conn.cursor()
        # Buscar o EPI existente
        cursor.execute('''SELECT * FROM epis WHERE id = ?''', (id,))
        epi = cursor.fetchone()

    if request.method == "POST":
        # Recebe os dados atualizados do formulário
        nome_epi = request.form["nome_epi"]
        fabricante = request.form["fabricante"]
        ca = request.form["ca"]
        vencimento = request.form["vencimento"]
        estoque_min = int(request.form["estoque_min"])
        estoque_max = int(request.form["estoque_max"])
        preco = float(request.form["preco"])

        # Atualiza o EPI no banco de dados
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''UPDATE epis SET nome = ?, fabricante = ?, ca = ?, vencimento = ?, estoque_min = ?, estoque_max = ?, preco = ?
                              WHERE id = ?''', 
                           (nome_epi, fabricante, ca, vencimento, estoque_min, estoque_max, preco, id))
            conn.commit()

        return redirect(url_for('epis'))  # Redireciona de volta para a página de EPIs

    return render_template('editar_epi.html', epi=epi)


@app.route('/deletar_epi/<int:id>', methods=["GET", "POST"])
def deletar_epi(id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''DELETE FROM epis WHERE id = ?''', (id,))
        conn.commit()
    
    return redirect(url_for('epis'))  # Redireciona para a página de EPIs após a exclusão


# Página de entrada de EPIs
@app.route('/entrada', methods=["GET", "POST"])
def entrada():
    if request.method == "POST":
        epi_id = request.form["epi_id"]  # ID do EPI
        quantidade = request.form["quantidade"]  # Quantidade
        nota_fiscal = request.form["nota_fiscal"]  # Nota Fiscal
        fornecedor = request.form["fornecedor"]  # Fornecedor
        data = request.form["data"]  # Data

        # Verificando se a quantidade e a nota fiscal são numéricas
        if not quantidade.isdigit():
            return "Erro: Quantidade deve ser um número válido."
        if not nota_fiscal.isdigit():
            return "Erro: Nota Fiscal deve ser um número válido."

        # Convertendo para inteiro
        quantidade = int(quantidade)
        nota_fiscal = int(nota_fiscal)

        # Inserindo dados no banco de dados
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO entradas (epi_id, quantidade, data, nota_fiscal, fornecedor)
                              VALUES (?, ?, ?, ?, ?)''', 
                           (epi_id, quantidade, data, nota_fiscal, fornecedor))

            # Atualizando o estoque atual do EPI
            cursor.execute('''UPDATE epis SET estoque_atual = estoque_atual + ? WHERE id = ?''', 
                           (quantidade, epi_id))
            conn.commit()

        return redirect(url_for('entrada'))  # Redireciona de volta para a página de entrada de EPIs

    # Carregar os EPIs para o formulário
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT id, nome FROM epis''')
        epis_data = cursor.fetchall()

    # Carregar o histórico de entradas
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT en.quantidade, e.nome, e.ca, en.data, en.nota_fiscal, en.fornecedor
                          FROM entradas en
                          JOIN epis e ON en.epi_id = e.id
                          ORDER BY en.data DESC''')
        entradas_data = cursor.fetchall()

    return render_template('entrada.html', epis=epis_data, entradas=entradas_data)


@app.route('/add_entrada', methods=["POST"])
def add_entrada():
    try:
        # Captura os dados do formulário
        epi_id = int(request.form["epi_id"])  # ID do EPI
        quantidade = request.form["quantidade"]  # Quantidade
        nota_fiscal = request.form["nota_fiscal"]  # Nota Fiscal
        fornecedor = request.form["fornecedor"]  # Fornecedor
        data = request.form["data"]  # Data

        # Validação para garantir que "quantidade" e "nota fiscal" sejam numéricos
        if not quantidade.isdigit():
            return "A quantidade deve ser um número válido."

        if not nota_fiscal.isdigit():
            return "A nota fiscal deve ser um número válido."

        # Converte para inteiro após a validação
        quantidade = int(quantidade)
        nota_fiscal = int(nota_fiscal)

        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO entradas (epi_id, quantidade, data, nota_fiscal, fornecedor)
                              VALUES (?, ?, ?, ?, ?)''', 
                           (epi_id, quantidade, data, nota_fiscal, fornecedor))
            conn.commit()

        return redirect(url_for('movimentacoes'))  # Redireciona para a página de movimentações

    except ValueError as e:
        return f"Erro ao processar os dados: {e}"

@app.route('/editar_entrada/<int:id>', methods=["GET", "POST"])
def editar_entrada(id):
    with connect_db() as conn:
        cursor = conn.cursor()
        
        # Verifica se o id está correto e imprime para debug
        print(f"Buscando entrada com ID: {id}")
        
        # Consultar a entrada com o ID fornecido
        cursor.execute('''SELECT * FROM entradas WHERE id = ?''', (id,))
        entrada = cursor.fetchone()

    # Se entrada for None, a entrada não foi encontrada
    if entrada is None:
        # Para debug, vamos imprimir a consulta e o erro
        print(f"Entrada com ID {id} não encontrada.")
        return "Entrada não encontrada", 404

    if request.method == "POST":
        # Receber os dados atualizados do formulário
        epi_id = request.form["epi_id"]
        quantidade = request.form["quantidade"]
        nota_fiscal = request.form["nota_fiscal"]
        fornecedor = request.form["fornecedor"]
        data = request.form["data"]

        # Atualizar a entrada no banco de dados
        with connect_db() as conn:
            conn.execute('''UPDATE entradas SET epi_id = ?, quantidade = ?, data = ?, nota_fiscal = ?, fornecedor = ? 
                            WHERE id = ?''',
                         (epi_id, quantidade, data, nota_fiscal, fornecedor, id))
            conn.commit()

        return redirect(url_for('entrada'))  # Redireciona para o histórico de entradas

    # Caso o método seja GET, exibe o formulário com os dados da entrada
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM epis''')
        epis_data = cursor.fetchall()

    return render_template('editar_entrada.html', entrada=entrada, epis=epis_data)



@app.route('/excluir_entrada/<int:id>', methods=["POST"])
def excluir_entrada(id):
    with connect_db() as conn:
        cursor = conn.cursor()
        
        # Excluir a entrada do banco de dados com o ID fornecido
        cursor.execute('''DELETE FROM entradas WHERE id = ?''', (id,))
        conn.commit()

    # Redirecionar de volta para o histórico de entradas
    return redirect(url_for('entrada'))



@app.route('/saida', methods=["GET", "POST"])
def saida():
    if request.method == "POST":
        epi_id = request.form["epi_id"]  # ID do EPI
        quantidade = request.form["quantidade"]  # Quantidade
        colaborador_id = request.form["colaborador_id"]  # ID do colaborador
        data = request.form["data"]  # Data

        # Verificando se a quantidade é numérica
        if not quantidade.isdigit():
            return "Erro: Quantidade deve ser um número válido."

        # Convertendo para inteiro
        quantidade = int(quantidade)

        # Verificando se o estoque é suficiente para a saída
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT estoque_atual FROM epis WHERE id = ?''', (epi_id,))
            estoque_atual = cursor.fetchone()[0]

            if estoque_atual < quantidade:
                return "Erro: Estoque insuficiente para a saída!"

            # Inserindo dados na tabela de saídas
            cursor.execute('''INSERT INTO saidas (epi_id, quantidade, colaborador_id, data)
                              VALUES (?, ?, ?, ?)''', 
                           (epi_id, quantidade, colaborador_id, data))

            # Atualizando o estoque atual do EPI
            cursor.execute('''UPDATE epis SET estoque_atual = estoque_atual - ? WHERE id = ?''', 
                           (quantidade, epi_id))
            conn.commit()

        return redirect(url_for('movimentacoes'))  # Redireciona de volta para a página de movimentações

    # Carregar os EPIs e colaboradores para os formulários
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT id, nome FROM epis''')
        epis_data = cursor.fetchall()

        cursor.execute('''SELECT id, nome FROM colaboradores WHERE status = 'Ativo' ''')
        colaboradores_data = cursor.fetchall()

    return render_template('saida.html', epis=epis_data, colaboradores=colaboradores_data)


@app.route('/add_saida', methods=["POST"])
def add_saida():
    try:
        epi_id = int(request.form["epi_id"])
        quantidade = int(request.form["quantidade"])
        data = request.form["data"]
        colaborador_id = int(request.form["colaborador_id"])

        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT estoque_min FROM epis WHERE id = ?''', (epi_id,))
            estoque_atual = cursor.fetchone()[0]

            if estoque_atual < quantidade:
                return render_template('movimentacoes.html', error="Estoque insuficiente para a saída!")

            cursor.execute('''INSERT INTO saidas (epi_id, quantidade, colaborador_id, data)
                              VALUES (?, ?, ?, ?)''', 
                           (epi_id, quantidade, colaborador_id, data))

        return redirect(url_for('movimentacoes'))
    except Exception as e:
        print(f"Erro na saída: {e}")
        return render_template('movimentacoes.html', error=f"Erro: {e}")

@app.route('/movimentacoes')
def movimentacoes():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT m.id, e.nome, m.tipo, m.quantidade, c.nome, m.data
                          FROM movimentacoes m
                          JOIN epis e ON m.epi_id = e.id
                          LEFT JOIN colaboradores c ON m.colaborador_id = c.id''')
        movimentacoes_data = cursor.fetchall()

        cursor.execute("SELECT id, nome, ca, estoque_min FROM epis")
        epis_data = cursor.fetchall()

        cursor.execute("SELECT id, nome FROM colaboradores WHERE status = 'Ativo'")
        colaboradores_data = cursor.fetchall()

    return render_template('movimentacoes.html', movimentacoes=movimentacoes_data, epis=epis_data, colaboradores=colaboradores_data)


@app.route('/estoque')
def estoque():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.id, e.nome, e.ca, e.estoque_min, e.estoque_atual,
                   COALESCE(SUM(CASE WHEN m.tipo = 'entrada' THEN m.quantidade ELSE 0 END), 0) AS entradas,
                   COALESCE(SUM(CASE WHEN m.tipo = 'saida' THEN m.quantidade ELSE 0 END), 0) AS saidas
            FROM epis e
            LEFT JOIN movimentacoes m ON m.epi_id = e.id
            GROUP BY e.id
        ''')
        epis_data = cursor.fetchall()

    # Calcular o estoque atual com base nas entradas e saídas
    for epi in epis_data:
        estoque_atual = epi[4] + epi[5] - epi[6]  # estoque_atual = estoque_atual + entradas - saídas
        epi = list(epi)  # Convertemos para lista para poder atualizar os valores
        epi[4] = estoque_atual  # Atualiza o estoque_atual

    return render_template('estoque.html', epis=epis_data)


@app.route('/historico_movimentacao')
def historico_movimentacao():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT e.nome, e.ca, en.quantidade, en.data, en.nota_fiscal, en.fornecedor
                          FROM movimentacoes m
                          JOIN epis e ON m.epi_id = e.id
                          LEFT JOIN entradas en ON en.epi_id = m.epi_id  -- Corrigindo a junção com a tabela de entradas
                          ORDER BY en.data DESC''')
        movimentacoes_data = cursor.fetchall()

    return render_template('historico_movimentacao.html', movimentacoes=movimentacoes_data)


# Relatório de movimentações
@app.route('/relatorio_movimentacao', methods=["GET", "POST"])
def relatorio_movimentacao():
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    
    query = '''
        SELECT e.nome, e.ca, m.quantidade, m.data, m.nota_fiscal, m.fornecedor
        FROM movimentacoes m
        JOIN epis e ON m.epi_id = e.id
        WHERE m.data BETWEEN ? AND ? 
    '''
    params = [start_date, end_date]

    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        movimentacoes_data = cursor.fetchall()

    return render_template('relatorio_movimentacao.html', movimentacoes=movimentacoes_data)

@app.route('/aniversariantes', methods=["GET"])
def aniversariantes():
    # Pega o mês selecionado no filtro, se não for selecionado, define o mês atual
    mes_selecionado = request.args.get('mes', datetime.now().month)
    
    # Converte o mês para um valor numérico
    mes_selecionado = int(mes_selecionado)

    with connect_db() as conn:
        cursor = conn.cursor()

        # Consulta SQL para pegar os colaboradores com aniversário no mês selecionado
        cursor.execute('''
            SELECT nome, nascimento FROM colaboradores
            WHERE strftime('%m', nascimento) = ? 
            ORDER BY nascimento
        ''', (f'{mes_selecionado:02d}',))  # Formata o mês para 2 dígitos (01-12)
        
        aniversariantes_data = cursor.fetchall()

    return render_template('aniversariantes.html', aniversariantes=aniversariantes_data, mes_selecionado=mes_selecionado)

# Filtro para formatar o número do mês para o nome do mês
@app.template_filter('format_month')
def format_month(mes):
    meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    return meses[mes-1]  # Subtrai 1 para que o mês 1 corresponda a Janeiro

@app.route('/perfil_colaborador/<int:id>', methods=["GET"])
def perfil_colaborador(id):
    # Buscar os dados do colaborador
    with connect_db() as conn:
        cursor = conn.cursor()

        # Buscar dados principais do colaborador
        cursor.execute('''SELECT * FROM colaboradores WHERE id = ?''', (id,))
        colaborador = cursor.fetchone()

        if colaborador is None:
            return "Colaborador não encontrado", 404

        # Buscar histórico de EPIs retirados pelo colaborador
        cursor.execute('''
            SELECT epi.nome, epi.ca, sa.data, sa.quantidade
            FROM saidas sa
            JOIN epis epi ON sa.epi_id = epi.id
            WHERE sa.colaborador_id = ?
            ORDER BY sa.data DESC
        ''', (id,))
        historico_epis = cursor.fetchall()

    return render_template('perfil_colaborador.html', colaborador=colaborador, historico_epis=historico_epis)

if __name__ == '__main__':
    app.run(debug=True)
