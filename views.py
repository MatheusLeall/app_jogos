from flask import render_template, request, redirect, session, flash, url_for, send_from_directory
from dao import JogoDao, UsuarioDao
from models import Jogo, Usuario
import os, time
from jogoteca import db, app
from helpers import recupera_imagem, deleta_arquivo

jogo_dao = JogoDao(db)
usuario_dao = UsuarioDao(db)

# Rota inicial da aplicação
@app.route('/')
def index():
    lista = jogo_dao.listar()
    return render_template('lista.html', titulo='Jogos', jogos=lista)


# Rota para criar um novo jogo
@app.route('/novo')
def novo():
    if 'usuario_logado' not in session or session['usuario_logado'] == None:
        return redirect(url_for('login', proxima=url_for('novo')))
    return render_template('novo.html', titulo='Novo Jogo')


# Rota pra onde os dados do formulário são enviados e tratados
@app.route('/criar', methods=['POST',])
def criar():
    nome = request.form['nome']
    categoria = request.form['categoria']
    console = request.form['console']
    jogo = Jogo(nome, categoria, console)
    jogo = jogo_dao.salvar(jogo)

    arquivo = request.files['arquivo']
    upload_path = app.config['UPLOAD_PATH']
    timestamp = time.time()
    arquivo.save(f'{upload_path}/capa{jogo.id}-{timestamp}.jpg')
    return redirect(url_for('index'))


# Rota para editar um registro no banco
@app.route('/editar/<int:id>')
def editar(id):
    if 'usuario_logado' not in session or session['usuario_logado'] == None:
        return redirect(url_for('login', proxima=url_for('editar')))
    jogo = jogo_dao.busca_por_id(id)
    nome_imagem = recupera_imagem(id)
    return render_template('editar.html', titulo='Editando Jogo', jogo=jogo
                           , capa_jogo=nome_imagem or 'capa_padrao.jpg')


# Rota para atualizar um registro no banco
@app.route('/atualizar', methods=['POST',])
def atualizar():
    nome = request.form['nome']
    categoria = request.form['categoria']
    console = request.form['console']
    jogo = Jogo(nome, categoria, console, id=request.form['id'])

    # Salva o arquivo de imagem na pasta de arquivos
    arquivo = request.files['arquivo']
    upload_path = app.config['UPLOAD_PATH']
    timestamp = time.time()
    deleta_arquivo(jogo.id)
    # Salva o arquivo com um identificador único para evitar problemas
    # com o cache do navegador
    arquivo.save(f'{upload_path}/capa{jogo.id}-{timestamp}.jpg')
    jogo_dao.salvar(jogo)
    return redirect(url_for('index'))


# Rota para deletar um registro no banco de dados
@app.route('/deletar/<int:id>')
def deletar(id):
    jogo_dao.deletar(id)
    flash('O jogo foi removido com sucesso!')
    return redirect(url_for('index'))


# Rota de login
@app.route('/login')
def login():
    proxima = request.args.get('proxima')
    return render_template('login.html', proxima=proxima)


# Rota de autenticação de usuário
@app.route('/autenticar', methods=['POST', ])
def autenticar():
    usuario = usuario_dao.buscar_por_id(request.form['usuario'])
    if usuario:
        if usuario.senha == request.form['senha']:
            session['usuario_logado'] = usuario.id
            flash('Bem-vindo, '+ usuario.nome)
            proxima_pagina = request.form['proxima']
            return redirect(proxima_pagina)
    else:
        flash('Usuário e/ou senha incorreto!')
        return redirect(url_for('login'))


# Rota de logout
@app.route('/logout')
def logout():
    session['usuario_logado'] = None
    flash('Sessão encerrada!')
    return redirect(url_for('login'))


# Rota para obter uma imagem específica da pasta de arquivos
@app.route('/uploads/<nome_arquivo>')
def imagem(nome_arquivo):
    return send_from_directory('uploads', nome_arquivo)