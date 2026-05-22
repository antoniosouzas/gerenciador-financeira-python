import sqlite3

def inicializar_banco():
    # Conecta (ou cria se não existir) o arquivo do banco de dados
    conn = sqlite3.connect('dashboard_financeiro.db')
    cursor = conn.cursor()

    # 1. Criação da Tabela de Usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Criação da Tabela de Conexões da Pluggy (Relacionamento 1:N com Usuários)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conexoes_bancarias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            pluggy_item_id TEXT UNIQUE NOT NULL,
            nome_instituicao TEXT, 
            data_conexao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()
    print("Banco de dados 'dashboard_financeiro.db' criado e estruturado com sucesso!")

# Executa a função se o arquivo for rodado diretamente
if __name__ == '__main__':
    inicializar_banco()