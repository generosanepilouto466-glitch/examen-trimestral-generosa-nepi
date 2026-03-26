from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'microsaas.db')

def get_db(query, params=(), one=False):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, params)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def index():
    projects = get_db('''
        SELECT p.*, u.name as owner_name
        FROM project p
        LEFT JOIN user u ON p.user_id = u.id
    ''')
    users = get_db('SELECT * FROM user')
    total_u = get_db('SELECT COUNT(*) as c FROM user', one=True)['c']
    total_t = get_db('SELECT COUNT(*) as c FROM task', one=True)['c']
    total_s = get_db('SELECT COUNT(*) as c FROM subscription WHERE plan_type != "Free"', one=True)['c']
    stats = {'total_users': total_u, 'total_tasks': total_t, 'active_subs': total_s}
    return render_template('index.html', projects=projects, stats=stats, users=users)

@app.route('/usuarios')
def usuarios():
    usuarios = get_db('''
        SELECT u.id, u.name, u.email, s.plan_type AS suscripcion
        FROM user u
        LEFT JOIN subscription s ON u.id = s.user_id
    ''')
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/add_user', methods=['POST'])
def add_user():
    name = request.form.get('name')
    email = request.form.get('email')
    if name and email:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO user (name, email) VALUES (?, ?)', (name, email))
            user_id = cursor.lastrowid
            cursor.execute('INSERT INTO subscription (plan_type, user_id) VALUES (?, ?)', ('Free', user_id))
            conn.commit()
        finally:
            conn.close()
    return redirect(url_for('usuarios'))

@app.route('/add_project', methods=['POST'])
def add_project():
    title = request.form.get('title')
    u_id = request.form.get('user_id')
    conn = sqlite3.connect(DATABASE)
    conn.execute('INSERT INTO project (title, user_id) VALUES (?, ?)', (title, u_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_project(id):
    conn = sqlite3.connect(DATABASE)
    conn.execute('DELETE FROM project WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/configuracion')
def configuracion():
    usuarios = get_db('''
        SELECT u.id, u.name, s.plan_type AS suscripcion
        FROM user u
        LEFT JOIN subscription s ON u.id = s.user_id
    ''')
    return render_template('configuracion.html', usuarios=usuarios)

@app.route('/actualizar_suscripcion/<int:user_id>', methods=['POST'])
def actualizar_suscripcion(user_id):
    nueva = request.form["suscripcion"]
    conn = sqlite3.connect(DATABASE)
    conn.execute("UPDATE subscription SET plan_type = ? WHERE user_id = ?", (nueva, user_id))
    conn.commit()
    conn.close()
    return redirect("/configuracion")

@app.route('/eliminar_suscripcion/<int:user_id>', methods=['POST'])
def eliminar_suscripcion(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Solo eliminar si existe
    cursor.execute("SELECT * FROM subscription WHERE user_id = ?", (user_id,))
    sub = cursor.fetchone()
    if sub:
        cursor.execute("DELETE FROM subscription WHERE user_id = ?", (user_id,))
        conn.commit()
    conn.close()
    return redirect("/configuracion")

if __name__ == '__main__':
    app.run(debug=True)
