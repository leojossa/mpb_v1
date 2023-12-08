from flask import Flask, render_template, redirect
from flask import Flask, jsonify, render_template, url_for, request, session, logging, redirect, flash, Blueprint, make_response, Response
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import datetime, timedelta
from dotenv import load_dotenv
import psycopg2
import os
import requests
from werkzeug.utils import cached_property, secure_filename
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

load_dotenv('.env')
DATABASE_URL = os.getenv('DATABASE_URL')

conn = psycopg2.connect(DATABASE_URL)

#cur = conn.cursor()
cur = conn.cursor()

try:
    cur = conn.cursor()
except psycopg2.InterfaceError as e:
    print('{} - conexão será reiniciada'.format(e))
    # Close old connection 
    if conn:
        if cur:
            cur.close()
        conn.close()
    conn = None
    cursor = None
    
    # Reconnect 
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
'''
cur.execute('CREATE TABLE cadastro (id serial PRIMARY KEY,'
                                 'nome varchar(250),'
                                 'email varchar(550),'
                                 'password varchar(256),'
                                 'endereco varchar(256),'
                                 'complemento varchar(250),'
                                 'cidade varchar(250),'
                                 'estado varchar(50),'
                                 'cep integer,'
                                 'latitude float,'
                                 'longitude float,'
                                 'data_cadastro date DEFAULT CURRENT_TIMESTAMP);'
                                 )

cur.execute('INSERT INTO cadastro (nome, email)'
            'VALUES (%s, %s)',
            ('teste',
             'teste')
            )

conn.commit()

cur.close()
conn.close()
'''

app = Flask(__name__)

URL = 'https://nominatim.openstreetmap.org/search?format=json'

app.config['SESSION_TYPE'] = 'MPB'
app.config['SECRET_KEY'] = 'teste123'

UPLOAD_FOLDER = '/Users/kaleo/MPB2/.venv/static/img'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = set(['png','jpg','jpeg'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/funciona')
def funciona():
    return render_template('funciona.html')

@app.route('/comece')
def comece():
    return render_template('comece.html')

user = []
senha = []
@app.route('/login', methods=['GET', 'POST'])
def login():
    with conn:
        with conn.cursor() as cur:
            if request.method == 'POST':
                email = request.form.get('email')
                password = request.form.get('password')
                print(password)
                senha.clear()
                senha.append(password)
                user.clear()
                user.append(email)
                usernamedata = conn.execute('select email from Cadastro where email=%s', email)
                passworddata = conn.execute('select password from Cadastro where email=%s', email)
                
                if usernamedata is None:
                    flash('digite o usuario', 'danger')
                    return redirect('/login')
                else:
                    for password_data in passworddata:
                        if sha256_crypt.verify(password, password_data):
                            session['log'] = True
                            query = conn.execute('select email, passowrd from Cadastro')
                            flash('Login Efetuado', 'success')
                            return redirect(url_for('login'))
                        return render_template('index.html')
                    else:
                        flash('senha incorreta', 'danger')
                    return redirect(url_for('index.html'))
            return render_template('login.html')

nomeHost = []
@app.route('/host', methods=['GET', 'POST'])
def cadastro():
    with conn:
        with conn.cursor() as cur:
            if request.method == 'POST':
                nome = request.form.get('nome')
                nomeHost.clear()
                nomeHost.append(nome)
                email = request.form.get('email')
                password = request.form.get('password')
                confirmPassword = request.form.get('confirmapassword')
                endereco = request.form.get('endereco')
                complemento = request.form.get('complemento')
                cidade = request.form.get('cidade')
                estado = request.form.get('estado')
                cep = request.form.get('cep')
                hash = sha256_crypt.hash(password)
                nome_Host = nomeHost[0]
                nome_Host_dir = nome_Host
                user_folder = os.path.join(app.config['UPLOAD_FOLDER'], nome_Host_dir)
                os.mkdir(user_folder)
                if cep != '':
                    res = requests.get(f'{URL}&postalcode={cep}')
                    data = res.json()
                    latitude = data[0].get('lat')
                    longitude = data[0].get('lon')
                    cur = conn.cursor()
                    cur.execute('INSERT INTO cadastro (nome, email, password, endereco ,complemento, cidade, estado, cep, latitude, longitude)'
                                'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                                (nome, email, hash, endereco, complemento, cidade, estado, cep, latitude, longitude))
                    conn.commit()
                else:
                    print('Base subiu sem lat ou long')
                flash('Registro Efetuado', 'success')
                return render_template('veiculos.html')
            return render_template('host.html')

#@app.route('/veiculo', methods=['GET', 'POST'])
#def cadVeiculo():
#    return render_template('veiculos.html')

@app.route('/veiculo', methods=['GET', 'POST'])
def upload_file():
    with conn:
        with conn.cursor() as cur:
            if request.method == 'POST':
                PASTA_UPLOAD = '/Users/kaleo/MPB2/.venv/static/img/'+str(nomeHost[0])
                if 'file' not in request.files:
                    flash('No file part')
                    return redirect(request.url)

                files = request.files.getlist('file')
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file.save(os.path.join(PASTA_UPLOAD, filename))

                        cur.execute('INSERT INTO cadastro (imagem) VALUES (%s)',(filename,))
                        conn.commit()

                flash('File(s) successfully uploaded')
            return render_template('veiculos.html')

lista = []
@app.route('/veiculo/consulta', methods=['GET', 'POST'])
def consulta():
    with conn:
        with conn.cursor() as cur:
            if request.method == 'POST':
                cst = request.form.get('consulta')
                lista.clear() # limpa a lista
                lista.append(cst) # faz apende do parametro na lista
                name = lista[0]
                cur.execute("select imagem from cadastro where id in (%s)"% name)
                query = cur.fetchall()
                image = query[0]
                print(image)
                return render_template('veiculos.html', image=image)

            return render_template('veiculos.html')

if __name__ == '__main__':
    app.run(debug=True)
