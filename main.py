from flask import Flask, render_template, request, redirect, make_response
import pymongo
import os
import datetime
import random
import string
import hashlib

app = Flask(__name__)
letters = string.ascii_lowercase
app.jinja_env.globals.update(str=str)

conn = pymongo.MongoClient(f'mongodb://dbUser:{os.getenv("mongokey")}@cluster0-shard-00-00.xoe4b.mongodb.net:27017,cluster0-shard-00-01.xoe4b.mongodb.net:27017,cluster0-shard-00-02.xoe4b.mongodb.net:27017/chill?ssl=true&replicaSet=atlas-rj95f3-shard-0&authSource=admin&retryWrites=true&w=majority')
db = conn.main.main
acc = conn.main.accounts
s = conn.main.sessions

@app.route('/')
def main():
  session_id = request.cookies.get('session_id')
  username = ''
  if session_id:
    session = s.find_one({'session_id': session_id})
    user_id = session['user']
    user = acc.find_one({'id': user_id})
    username = user['username']
  return render_template('index.html', session_id=session_id, username=username)

@app.route('/assignment')
def assignment():
  return render_template('assignment.html')

@app.route('/create-assignment', methods=['POST'])
def createassignment():
  if request.method == 'POST':
    data = request.get_json()
    print(data)
    session_id = request.cookies.get('session_id')
    if session_id:
      session = s.find_one({'session_id': session_id})
      user_id = session['user']
      db.insert_one({
        'assignment_name': data['assignment_name'],
        'subject': data['subject'],
        'work_on': datetime.datetime.strptime(data['work_on'], '%Y-%m-%d'),
        'due': datetime.datetime.strptime(data['due'], '%Y-%m-%d'),
        'id': ''.join(random.choice(letters) for i in range(10)),
        'user': user_id
      })
      return {
        'status': 'success'
      }
    else:
      return {
        'status': 'failed',
        'reason': 'invalid session'
      }

@app.route('/register')
def register():
  return render_template('register.html')

@app.route('/login')
def login():
  return render_template('login.html')

@app.route('/session', methods=['POST'])
def session():
  if request.method == 'POST':
    data = request.form
    print(data)
    username = data['username']
    password = data['password']
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    print(hashed_password)
    user = acc.find_one({
      'username': username,
      'hashword': hashed_password
    })
    resp = make_response(redirect('/', 302))
    session_id = ''.join(random.choice(letters) for i in range(10))
    resp.set_cookie('session_id', session_id)
    s.insert_one({
      'session_id': session_id,
      'user': user['id']
    })
    return resp



@app.route('/create-account', methods=['POST'])
def createaccount():
  if request.method == 'POST':
    data = request.form
    username = data['username']
    password = data['password']
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    print(hashed_password)
    acc.insert_one({
      'username': username,
      'hashword': hashed_password,
      'created': datetime.datetime.now(),
      'id': hash(username)
    })
    return redirect('/login', 302)


@app.route('/delete-assignment', methods=['POST'])
def deleteassignment():
  if request.method == 'POST':
    session_id = request.cookies.get('session_id')
    if session_id:
      session = s.find_one({'session_id': session_id})
      user_id = session['user']
      data = request.get_json()
      db.delete_one({'id': data['id']})
      return {
        'status': 'success'
      }
    else:
      return {
        'status': 'failed',
        'reason': 'invalid session'
      }

@app.route('/tasks')
def tasks():
  assignments = []
  session_id = request.cookies.get('session_id')
  if session_id:
    session = s.find_one({'session_id': session_id})
    user_id = session['user']
    if request.args.get('sort') == 'work':
      sort = 'work'
      for a in db.find({'user': user_id}).sort('work_on', 1):
        assignments.append(a)
    else:
      sort = 'due'
      for a in db.find({'user': user_id}).sort('due', 1):
        assignments.append(a)
    return render_template('tasks.html', assignments=assignments, sort=sort)
  else:
    return 'Error'

@app.route('/calendar')
def calendar():
  assignments = []
  session_id = request.cookies.get('session_id')
  if session_id:
    session = s.find_one({'session_id': session_id})
    user_id = session['user']
    for a in db.find({'user': user_id}).sort('due', 1):
      assignments.append(a)
    return render_template('calendar.html', assignments=assignments)
  else:
    return 'Error'

app.run(host='0.0.0.0', port=8080)