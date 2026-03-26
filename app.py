from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

# CONFIGURACIÓN: Aquí pones el nombre EXACTO de tu archivo de DB Browser
DATABASE = 'microsaas.db'

def get_db_connection():
    # Conecta al archivo físico que tú manejas en DB Browser
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # Esto permite acceder por nombre de columna
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    # Cambia "project" por el nombre de tu tabla en DB Browser si es distinto
    projects = conn.execute('SELECT * FROM project').fetchall()
    conn.close()
    return render_template('index.html', projects=projects)

@app.route('/add_project', methods=['POST'])
def add_project():
    title = request.form.get('title')
    user_id = 1 # ID por defecto para pruebas
    if title:
        conn = get_db_connection()
        conn.execute('INSERT INTO project (title, user_id) VALUES (?, ?)', (title, user_id))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_project(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM project WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)