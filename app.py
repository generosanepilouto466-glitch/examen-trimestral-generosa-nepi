rom flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

# Ruta absoluta de la base de datos
DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'microsaas.db')
print("DB path:", os.path.abspath(DATABASE))  # Para verificar que apunta al archivo correcto

# Función para SELECTs
def get_db(query, params=(), one=False):
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query, params)
        rv = cur.fetchall()
        return (rv[0] if rv else None) if one else rv

# --------------------
# Rutas del Dashboard
# --------------------
@app.route('/')
def index():
    projects = get_db('''
        SELECT p.*, u.name AS owner_name
        FROM project p
        LEFT JOIN user u ON p.user_id = u.id
    ''')
    users = get_db('SELECT * FROM user')

    total_u = get_db('SELECT COUNT(*) AS c FROM user', one=True)['c']
    total_t = get_db('SELECT COUNT(*) AS c FROM task', one=True)['c']
    total_s = get_db('SELECT COUNT(*) AS c FROM subscription WHERE plan_type != "Free"', one=True)['c']

    stats = {'total_users': total_u, 'total_tasks': total_t, 'active_subs': total_s}
    return render_template('index.html', projects=projects, stats=stats, users=users)

# --------------------
# Gestión de Usuarios
# --------------------
@app.route('/usuarios')
def usuarios():
    usuarios = get_db('''
        SELECT u.id, u.name AS nombre, u.email, s.plan_type AS suscripcion
        FROM user u
        LEFT JOIN subscription s ON u.id = s.user_id
    ''')
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/add_user', methods=['POST'])
def add_user():
    nombre = request.form.get('name')
    email = request.form.get('email')

    if nombre and email:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            # Insertar usuario
            cursor.execute('INSERT INTO user (name, email) VALUES (?, ?)', (nombre, email))
            user_id = cursor.lastrowid
            # Crear suscripción Free por defecto
            cursor.execute('INSERT INTO subscription (plan_type, user_id) VALUES (?, ?)', ('Free', user_id))
            conn.commit()
    return redirect(url_for('usuarios'))

# --------------------
# Gestión de Proyectos
# --------------------
@app.route('/add_project', methods=['POST'])
def add_project():
    title = request.form.get('title')
    u_id = int(request.form.get('user_id'))  # Convertir a int
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('INSERT INTO project (title, user_id) VALUES (?, ?)', (title, u_id))
        conn.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_project(id):
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('DELETE FROM project WHERE id = ?', (id,))
        conn.commit()
    return redirect(url_for('index'))

# --------------------
# Configuración de Usuarios
# --------------------
@app.route('/configuracion')
def configuracion():
    usuarios = get_db('''
        SELECT u.id, u.name AS nombre, s.plan_type AS suscripcion
        FROM user u
        LEFT JOIN subscription s ON u.id = s.user_id
    ''')
    return render_template('configuracion.html', usuarios=usuarios)

@app.route('/actualizar_suscripcion/<int:user_id>', methods=['POST'])
def actualizar_suscripcion(user_id):
    nueva = request.form["suscripcion"]
    with sqlite3.connect(DATABASE) as conn:
        conn.execute(
            "UPDATE subscription SET plan_type = ? WHERE user_id = ?",
            (nueva, user_id)
        )
        conn.commit()
    return redirect("/configuracion")

@app.route('/eliminar_suscripcion/<int:user_id>', methods=['POST'])
def eliminar_suscripcion(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # Solo eliminar si existe
        cursor.execute("SELECT * FROM subscription WHERE user_id = ?", (user_id,))
        sub = cursor.fetchone()
        if sub:
            cursor.execute("DELETE FROM subscription WHERE user_id = ?", (user_id,))
            conn.commit()
    return redirect("/configuracion")

# --------------------
# Ejecutar la app
# --------------------
if __name__ == '__main__':
    app.run(debug=True)
