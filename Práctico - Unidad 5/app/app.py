from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy, query
from sqlalchemy.sql import text
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib

app = Flask(__name__)
app.config.from_pyfile('config.py')

from models import db
from models import Preceptor, Curso, Estudiante, Asistencia, Padre
    
@app.route('/')
def inicio():
	return render_template('inicio.html')

@app.route('/login', methods = ['GET','POST'])
def login():
    if request.method == 'POST':
        if  not request.form['email'] or not request.form['password'] or not request.form['user_type']:
            return render_template('error.html', error="Por favor ingrese los datos requeridos")
        else:
            if request.form['user_type'] == 'Preceptor':
                user= Preceptor.query.filter_by(correo = request.form['email']).first()
            elif request.form['user_type'] == 'Padre':
                user= Padre.query.filter_by(correo= request.form['email']).first()

            if user is None:
                return render_template('error.html', error="El correo no está registrado")
            else:
                c = request.form['password']
                result = hashlib.md5(c.encode()).hexdigest()
                if result == user.clave:
                    verificacion = True
                elif result != user.clave:
                    verificacion = False
                if verificacion and request.form['user_type'] == 'Preceptor':
                    session['user_id'] = user.id
                    session['name']=request.form['email']
                    session['user_type'] = request.form['user_type']
                    return render_template('preceptor_home.html', hora=datetime.now().hour, usuario = user)
                elif verificacion and request.form['user_type'] == 'Padre':
                    return render_template('inicio_padre.html', hora=datetime.now().hour, usuario = user)
                else:
                    return render_template('error.html', error="La contraseña no es válida")
    else:
        return render_template('login.html')


@app.route('/preceptor_home')
def preceptor_home():
    return render_template('preceptor_home.html', usuario = Preceptor.query.filter_by(id = session['user_id']).first())

@app.route('/registrar_asistencia', methods=['GET','POST'])
def registrar_asistencia():
    if request.method == 'POST':
        if not  session['curso']:
            curso_actual=request.form['curso']
            session['curso']=curso_actual
            curso_obtenido=Curso.query.filter_by(id=curso_actual).first()
            estudiantes_obtenidos=Estudiante.query.filter_by(idcurso=curso_obtenido.id).order_by(text('apellido, nombre')).all()
            return render_template('cargar_asistencias.html',estudiantes=estudiantes_obtenidos)
        else:
            if request.form['fecha']:
                fecha=request.form['fecha']
                clase=int(request.form['claseAula'])
                curso_obtenido=Curso.query.filter_by(id=session['curso']).first()
                estudiantes_obtenidos=Estudiante.query.filter_by(idcurso=curso_obtenido.id).order_by(text('apellido, nombre')).all()
                for estudiante in estudiantes_obtenidos:
                    asistencia=request.form.get(f'asistio_{estudiante.id}')
                    justificacion=request.form.get(f'justificacion_{estudiante.id}','')
                    nueva_asistencia=Asistencia(idestudiante=estudiante.id,fecha=datetime.strptime(fecha, "%Y-%m-%d").date(),codigoclase=clase,asistio=asistencia,justificacion=justificacion if asistencia == 'n' else '')
                    db.session.add(nueva_asistencia)
                    db.session.commit()
                return render_template('registro_exitoso.html',mensaje='Asistencia guardada con éxito')
    else:
        session['curso']=None
        return render_template('registrar_asistencia.html',preceptor=Preceptor.query.filter_by(correo=session['name']).first())
        
@app.route('/cargar_asistencia')
def cargar_asistencia():
    if request.method == 'POST':
        print('xd')
        if not request.form['fecha']:
            return render_template('error_preceptor.html',error='No se han seleccionado correctamente los datos')
        else:
            clase_actual=int(request.form['clase'])
            fecha_actual=request.form['fecha']
            
            return render_template('registro_exitoso.html', mensaje='Registro exitoso!')
    else:
        curso_actual=request.form['curso']
        curso_obtenido=Curso.query.filter_by(id=curso_actual).first()
        estudiantes_obtenidos=Estudiante.query.filter_by(idcurso=curso_obtenido.id).order_by(text('apellido, nombre')).all()
        return render_template('cargar_asistencias.html',estudiantes=estudiantes_obtenidos)

@app.route('/mostrar_informe', methods=['GET','POST'])
def mostrar_informe():
    if request.method == 'POST':
        curso_actual=request.form['curso']
        curso_obtenido=Curso.query.filter_by(id=curso_actual).first()
        estudiantes_obtenidos=Estudiante.query.filter_by(idcurso=curso_obtenido.id).order_by(text('apellido, nombre')).all()
        lista_asistencias=[]
        for estudiante in estudiantes_obtenidos:
            contadores=['%s %s'%(estudiante.apellido, estudiante.nombre),0,0,0,0,0,0,0.0]
            asistencias_obtenidas=estudiante.asistencias
            for asistencia in asistencias_obtenidas:
                if asistencia.codigoclase==1:
                    if asistencia.asistio=='s':
                        contadores[1]+=1
                    elif asistencia.asistio=='n':
                        if asistencia.justificacion=='':
                            contadores[2]+=1
                        else:
                            contadores[3]+=1
                elif asistencia.codigoclase==2:
                    if asistencia.asistio=='s':
                        contadores[4]+=1
                    elif asistencia.asistio=='n':
                        if asistencia.justificacion=='':
                            contadores[5]+=1
                        else:
                            contadores[6]+=1
            contadores[7]=float(contadores[2]+contadores[3])+contadores[5]/2+contadores[6]/2
            lista_asistencias.append(contadores)
                
        return render_template('listado_asistencias.html',lista=lista_asistencias)
    else:
        return render_template('obtener_informe.html',preceptor=Preceptor.query.filter_by(correo=session['name']).first())

@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.pop('username', None)
    return redirect('/')
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug = True, port=5000)
    session.pop('username', None)