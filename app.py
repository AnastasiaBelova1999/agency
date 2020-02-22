import mysql
from flask import Flask, render_template, request, abort, redirect, flash, url_for
from flask_login import login_required
from collections import namedtuple

from mysql_db import MySQL
import mysql.connector
import flask_login
import hashlib

app = Flask(__name__)
app.secret_key = 'asjdfbajSLDFBhjasbfd'
app.config.from_pyfile('config.py')
db = MySQL(app)
login_manager = flask_login.LoginManager()
login_manager.init_app(app)


class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(login):
    cursor = db.db.cursor(named_tuple=True)
    cursor.execute('select id, login from users where id = %s', (login,))
    user_db = cursor.fetchone()
    if user_db:
        user = User()
        user.id = user_db.id
        user.login = user_db.login
        return user
    return None

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template("index.html", authorization=False, login="anonimus", login_false=False)

@app.route('/', methods=['POST', 'GET'])
def hello_world():
    if request.method == 'GET':
        login: str
        if flask_login.current_user.is_anonymous:
            login = "anonymus"
        else:
            login = flask_login.current_user.login
        return render_template("index.html", authorization=not flask_login.current_user.is_anonymous, login=login)
    elif request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        password_hash = hashlib.sha224(password.encode()).hexdigest()
        if username and password:
            cursor = db.db.cursor(named_tuple=True, buffered=True)
            try:
                cursor.execute(
                    "SELECT id,login FROM users WHERE `login` = '%s' and `password_hash` = '%s'" % (
                        username, password_hash))
                user = cursor.fetchone()
            except Exception:
                cursor.close()
                return render_template("index.html", authorization=False,
                                       login="anonimus", login_false=True)
            cursor.close()
            if user is not None:
                flask_user = User()
                flask_user.id = user.id
                flask_user.login = user.login
                flask_login.login_user(flask_user, remember=True)
                return render_template("index.html", authorization=not flask_login.current_user.is_anonymous,
                                       login=user.login, login_false=False)
            else:
                flash("Не правильный логин или пароль")
                return render_template("index.html", authorization=False,
                                       login="anonimus", login_false=True)
        else:
            flash("Не правильный логин или пароль")
            return render_template("index.html", authorization=False,
                                   login="anonimus", login_false=True)


@app.route('/logout', methods=['GET'])
def logout():
    flask_login.logout_user()
    return render_template("index.html", authorization=not flask_login.current_user.is_anonymous, login="anonimus",
                           login_false=False)

@app.route('/req', methods=['GET'])
@login_required
def req():
    requests = db.select(None, "requests")
    sities = dict(db.select(["id","title"], "sities"))
    status = dict(db.select(["id","title"], "status"))
    return render_template("req.html", requests=requests, sities=sities, status=status)

@app.route('/req/delete', methods=['POST'])
@login_required
def list_delete():
    id = request.form.get("id")
    cursor = db.db.cursor()
    cursor.execute("DELETE FROM `requests` WHERE `requests`.`id` = '%s'" % id)
    db.db.commit()
    cursor.close()
    return redirect("/req")

@app.route('/req/new', methods=['POST', 'GET'])
@login_required
def sub_new():
    if request.method == 'GET':
        sities = db.select(["id", "title"], "sities")
        status = db.select(["id", "title"], "status")
        return render_template("new.html",  status=status, sities=sities)
    elif request.method == 'POST':
        wife = request.form.get("wife")
        husband = request.form.get("husband")
        sities = request.form.get("sities_id")
        id_status = request.form.get("id_status")
        if wife and husband and sities and id_status:
            cursor = db.db.cursor(named_tuple=True)
            try:
                cursor.execute(
                    "INSERT INTO `requests` (`wife`, `husband`, `id_sity`, `id_status`) VALUES ('%s','%s','%s','%s')" % (
                        wife, husband, sities, id_status))
                db.db.commit()
                cursor.close()
                return redirect("/req")
            except Exception:
                sities = db.select(["id", "title"], "sities")
                status = db.select(["id", "title"], "status")
                return render_template("new.html", insert_false=True, sities=sities,
                                       status=status)
        else:
            sities = db.select(["id", "title"], "sities")
            status = db.select(["id", "title"], "status")
            return render_template("new.html", insert_false=True, sities =sities,
                                   status=status)

@app.route('/req/edit', methods=['POST'])
@login_required
def list_edit():
    try:
        list_id = request.form.get("list_id")
        wife = request.form.get("wife")
        husband = request.form.get("husband")
        sity_id = request.form.get("sity_id")
        status_id = request.form.get("status_id")
        statuss = db.select(None, "status")
        sities = db.select(None, "sities")
        sub = {
            'list_id': list_id,
            'wife': wife,
            'husband': husband,
            'sity_id': sity_id,
            'status_id': status_id
        }
        return render_template("req_edit.html", sub=sub, sities=sities, statuss=statuss,
                               login=flask_login.current_user.login, user_id=flask_login.current_user.id
                               , user_role=1, list_id=list_id)

    except Exception:
        return redirect(url_for("req"))


@app.route('/req/edit/submit', methods=['POST'])
@login_required
def sub_edit_submit():
    request_id = request.form.get("id")
    wife = request.form.get("wife")
    husband = request.form.get("husband")
    sity_id = request.form.get("sity_id")
    status_id = request.form.get("status_id")

    if wife and husband and status_id and sity_id:
        cursor = db.db.cursor(named_tuple=True)
        try:
            cursor.execute(
                "UPDATE `requests` SET  `wife` = '%s', `husband` = '%s', `id_sity` = '%s', `id_status` = '%s'  WHERE `requests`.`id` = '%s'" % (
                    wife, husband, sity_id, status_id, request_id))
            db.db.commit()
            cursor.close()
            return redirect("/req")
        except Exception:
            return redirect("/req")
    else:
        return redirect("/req")



if __name__ == '__main__':
    app.run()
