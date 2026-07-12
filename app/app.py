# ================================================================
#  BANCONOVA Aplicacion Flask
#  Descripcion: Aplicacion bancaria digital
#  Version    : 1.0.0
# ================================================================

from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'banconova-secret-key-2026')

# ── Variables de entorno (para distinguir ambientes) ──
AMBIENTE = os.environ.get('AMBIENTE', 'desarrollo')
VERSION  = os.environ.get('VERSION', '1.0.0')

#  Usuarios válidos 
USUARIOS = {
    'ana.garcia': {'nombre': 'Ana García',    'iniciales': 'AG', 'pass': '12345'},
    'admin':      {'nombre': 'Admin DevOps',  'iniciales': 'AD', 'pass': 'admin'},
}

# ── Datos simulados de la app ─────────────────────────
MOVIMIENTOS = [
    {'id': 1, 'tipo': 'in',  'desc': 'Depósito nómina',          'monto': 18500.00, 'fecha': 'Hoy, 08:00',    'icono': '💼', 'cat': 'Depósitos'},
    {'id': 2, 'tipo': 'out', 'desc': 'Pago CFE',                  'monto': 847.50,   'fecha': 'Hoy, 07:30',    'icono': '⚡', 'cat': 'Servicios'},
    {'id': 3, 'tipo': 'out', 'desc': 'Transferencia a L. Ramos',  'monto': 2000.00,  'fecha': 'Ayer, 18:45',   'icono': '→',  'cat': 'Transferencias'},
    {'id': 4, 'tipo': 'in',  'desc': 'Reembolso OXXO Pay',        'monto': 320.00,   'fecha': 'Ayer, 12:10',   'icono': '↩',  'cat': 'Depósitos'},
    {'id': 5, 'tipo': 'out', 'desc': 'Pago TELMEX',               'monto': 599.00,   'fecha': '24 Jun, 10:00', 'icono': '📡', 'cat': 'Servicios'},
    {'id': 6, 'tipo': 'out', 'desc': 'Transferencia a M. Soto',   'monto': 5000.00,  'fecha': '22 Jun, 15:30', 'icono': '→',  'cat': 'Transferencias'},
    {'id': 7, 'tipo': 'in',  'desc': 'Pago cliente Proyecto BN',  'monto': 12000.00, 'fecha': '20 Jun, 09:00', 'icono': '💰', 'cat': 'Depósitos'},
    {'id': 8, 'tipo': 'out', 'desc': 'Pago IZZI',                 'monto': 449.00,   'fecha': '18 Jun, 11:00', 'icono': '📺', 'cat': 'Servicios'},
]

CONTACTOS = [
    {'nombre': 'Luis R.',   'banco': 'BBVA',      'iniciales': 'LR'},
    {'nombre': 'María S.',  'banco': 'Banamex',   'iniciales': 'MS'},
    {'nombre': 'Pedro G.',  'banco': 'Banorte',   'iniciales': 'PG'},
    {'nombre': 'Ana V.',    'banco': 'HSBC',      'iniciales': 'AV'},
    {'nombre': 'Carlos M.', 'banco': 'Santander', 'iniciales': 'CM'},
    {'nombre': 'Julia T.',  'banco': 'BancoNova', 'iniciales': 'JT'},
]

SERVICIOS = [
    {'nombre': 'CFE',       'emoji': '⚡', 'desc': 'Luz'},
    {'nombre': 'TELMEX',    'emoji': '📞', 'desc': 'Teléfono'},
    {'nombre': 'IZZI',      'emoji': '📺', 'desc': 'Internet'},
    {'nombre': 'TOTALPLAY', 'emoji': '📡', 'desc': 'TV + Net'},
    {'nombre': 'Agua',      'emoji': '💧', 'desc': 'SACMEX'},
    {'nombre': 'Gas',       'emoji': '🔥', 'desc': 'Gas Natural'},
]

# ================================================================
# RUTAS
# ================================================================

# ── Health check (para Kubernetes probes) ────────────
@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'ambiente': AMBIENTE,
        'version': VERSION
    })

# ── Página principal — Login ──────────────────────────
@app.route('/')
def index():
    if 'usuario' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html',
                           ambiente=AMBIENTE,
                           version=VERSION)

# ── Login POST ────────────────────────────────────────
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '').strip()
    usuario  = USUARIOS.get(username)

    if not usuario or usuario['pass'] != password:
        return render_template('index.html',
                               error='Usuario o contraseña incorrectos',
                               ambiente=AMBIENTE,
                               version=VERSION)

    session['usuario']   = username
    session['nombre']    = usuario['nombre']
    session['iniciales'] = usuario['iniciales']
    session['saldo']     = 45820.50
    session['movimientos'] = MOVIMIENTOS.copy()
    return redirect(url_for('dashboard'))

# ── Logout ────────────────────────────────────────────
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ── Dashboard ─────────────────────────────────────────
@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html',
                           nombre=session['nombre'],
                           iniciales=session['iniciales'],
                           saldo=session['saldo'],
                           movimientos=session.get('movimientos', [])[:5],
                           ambiente=AMBIENTE,
                           version=VERSION)

# ── Transferencias ────────────────────────────────────
@app.route('/transferencia')
def transferencia():
    if 'usuario' not in session:
        return redirect(url_for('index'))
    return render_template('transferencia.html',
                           nombre=session['nombre'],
                           iniciales=session['iniciales'],
                           saldo=session['saldo'],
                           contactos=CONTACTOS,
                           ambiente=AMBIENTE,
                           version=VERSION)

@app.route('/transferencia/realizar', methods=['POST'])
def realizar_transferencia():
    if 'usuario' not in session:
        return redirect(url_for('index'))

    monto    = float(request.form.get('monto', 0))
    contacto = request.form.get('contacto', '')
    concepto = request.form.get('concepto', 'Sin concepto')
    error    = None
    exito    = None

    if not contacto:
        error = 'Selecciona un contacto'
    elif monto <= 0:
        error = 'Ingresa un monto válido'
    elif monto > 50000:
        error = 'Monto excede el límite de $50,000'
    elif monto > session['saldo']:
        error = 'Saldo insuficiente'
    else:
        session['saldo'] -= monto
        nuevo = {
            'id': len(session['movimientos']) + 1,
            'tipo': 'out',
            'desc': f'Transferencia a {contacto}',
            'monto': monto,
            'fecha': 'Ahora',
            'icono': '→',
            'cat': 'Transferencias'
        }
        movs = session['movimientos']
        movs.insert(0, nuevo)
        session['movimientos'] = movs
        session.modified = True
        exito = f'Transferencia de ${monto:,.2f} enviada a {contacto}'

    return render_template('transferencia.html',
                           nombre=session['nombre'],
                           iniciales=session['iniciales'],
                           saldo=session['saldo'],
                           contactos=CONTACTOS,
                           error=error,
                           exito=exito,
                           ambiente=AMBIENTE,
                           version=VERSION)

# ── Pagos ─────────────────────────────────────────────
@app.route('/pagos')
def pagos():
    if 'usuario' not in session:
        return redirect(url_for('index'))
    return render_template('pagos.html',
                           nombre=session['nombre'],
                           iniciales=session['iniciales'],
                           saldo=session['saldo'],
                           servicios=SERVICIOS,
                           ambiente=AMBIENTE,
                           version=VERSION)

@app.route('/pagos/realizar', methods=['POST'])
def realizar_pago():
    if 'usuario' not in session:
        return redirect(url_for('index'))

    servicio   = request.form.get('servicio', '')
    referencia = request.form.get('referencia', '').strip()
    monto      = float(request.form.get('monto', 0))
    error      = None
    exito      = None

    if not referencia:
        error = 'Ingresa la referencia del servicio'
    elif monto <= 0:
        error = 'Ingresa un monto válido'
    elif monto > session['saldo']:
        error = 'Saldo insuficiente'
    else:
        session['saldo'] -= monto
        nuevo = {
            'id': len(session['movimientos']) + 1,
            'tipo': 'out',
            'desc': f'Pago {servicio}',
            'monto': monto,
            'fecha': 'Ahora',
            'icono': '⚡',
            'cat': 'Servicios'
        }
        movs = session['movimientos']
        movs.insert(0, nuevo)
        session['movimientos'] = movs
        session.modified = True
        exito = f'Pago de ${monto:,.2f} a {servicio} realizado'

    return render_template('pagos.html',
                           nombre=session['nombre'],
                           iniciales=session['iniciales'],
                           saldo=session['saldo'],
                           servicios=SERVICIOS,
                           error=error,
                           exito=exito,
                           ambiente=AMBIENTE,
                           version=VERSION)

# ── Historial ─────────────────────────────────────────
@app.route('/historial')
def historial():
    if 'usuario' not in session:
        return redirect(url_for('index'))
    filtro = request.args.get('filtro', 'Todos')
    movs   = session.get('movimientos', [])
    if filtro != 'Todos':
        movs = [m for m in movs if m['cat'] == filtro]
    return render_template('historial.html',
                           nombre=session['nombre'],
                           iniciales=session['iniciales'],
                           movimientos=movs,
                           filtro=filtro,
                           ambiente=AMBIENTE,
                           version=VERSION)

# ── Inicio ────────────────────────────────────────────
if __name__ == '__main__':
    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
