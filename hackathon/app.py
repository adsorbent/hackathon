from flask import Flask, request, render_template
import pymongo

app = Flask(__name__)

maxSkills = 3
connStr = 'mongodb://localhost:27017'
preDefSkills = ['один', 'два', 'три']
maxTeams = 3
maxPlayers = 3


@app.route("/reg", methods=['POST', 'GET'])
def reg():
    import time

    if request.method == 'GET':
        return render_template("regTemplate.html", preDefSkills=preDefSkills, len=len(preDefSkills))

    if request.method == 'POST':

        if checkDb('user') >= maxTeams * maxPlayers:
            return 'Достигнуто максимальное возможное количество зарегистрированных пользователей'
        if checkDb('team') == 3:
            return 'Вы не создали ни одной команды'

        # создание переменных для передачи в mongodb
        skills = {}
        fname = request.form.get('fname')
        lname = request.form.get('lname')

        # валидация введенных данных
        if fname == '' or lname == '':
            return 'Поле имя и\или фамилия не может быть пустым полем'
        try:
            age = int(request.form.get('age'))
            if age < 18:
                return 'Ваш возраст меньше 18'
        except:
            return "Возраст должен быть числовым значением"

        counter = 0 #проверка количества выбранных навыков
        for i in range(len(preDefSkills)):
            if request.form.get('skills' + str(i)) != 'NaN':
                skills[request.form.get('skills' + str(i))] = request.form.get('knowledge' + str(i))
            else:
                counter+=1

            if counter == len(preDefSkills):
                return 'Вы не указали ни одного навыка'

        uId = str(round(time.time(), 4))
        teamDist(skills, uId)
        updateUserDb(uId, fname, lname, age, skills)
    return "Вы успешно зарегистрировались"


@app.route("/create", methods=['POST', 'GET'])
def createTeam():
    if request.method == 'GET':
        return '''
            <h1>СОЗДАНИЕ КОМАНДЫ</h1>
            <form method="POST">
                <div><label>Введите название команды: <input type="text" name="teamName"></label></div>
                <input type="submit" value="Submit">
            </form>'''

    if request.method == 'POST':
        name = request.form.get('teamName')
        if checkDb('team', name) == 1:
            return 'Достигнуто максимальное возможное зарегистрированных количество команд'
        if name == '' or name is None:
            return 'Вы использовали пустое название команды'
        if checkDb('team', name) == 2:
            return 'Вы использовали занятое название команды'
        updateTeamDb(name)
        return 'Вы успешно зарегистрировали команду'


@app.route('/date', methods=['GET'])
def showDate():
    import requests, json
    from datetime import datetime
    req = requests.get('https://api.openweathermap.org/data/2.5/onecall?lat=55.7558&lon=37.6173&units=metric&exclude=hourly,minutely&appid=a9e81889724b85e3770cb73b602cc6ce')
    data = json.loads(req.text)
    for i in range(len(data['daily'])):
        # print(data['daily'][i]['temp']['day'])
        if data['daily'][i]['weather'][0]['main'] == 'Clear' and data['daily'][i]['temp']['day'] >= 10:
            tmp =  str( datetime.fromtimestamp( data['daily'][i]['dt'] ))
            return 'Хакатон состоится ' + tmp[0:10]
    return 'Дата проведения хакатона неизвестна, т.к. нет теплых дней'


def updateUserDb(uId, fname, lname, age, skills):
    client = pymongo.MongoClient(connStr)

    db = client['hackathon']
    collection = db.users

    rec1 = {
        '_id':       uId,
        'fname':    fname,
        'lname':    lname,
        'age':      age,
        'skills':   skills
    }
    collection.insert_one(rec1)


def updateTeamDb(name):
    import time
    client = pymongo.MongoClient(connStr)

    db = client['hackathon']
    collection = db.team

    rec1 = {
        'name':     name,
        'time':     round(time.time()),
        'players':  '',
        'score':    0
    }
    collection.insert_one(rec1)


def checkDb(x, name=None):
    client = pymongo.MongoClient(connStr)
    db = client['hackathon']

    if x == 'team':
        if db.command("collstats", "team")['count'] >= maxTeams:
           return 1

        cursor = db.team.find({})
        for document in cursor:
            if name == document['name']:
                return 2

        try:
            list(db.team.find({}))[0]
        except:
            return 3

    if x == 'user':
        return db.command("collstats", "users")['count']


def teamDist(skills, uId):
    client = pymongo.MongoClient(connStr)
    db = client['hackathon']
    counter = 0

    for skill in skills:
        if skills[skill] == 'отлично':
            counter+=2
        if skills[skill] == 'средне':
            counter+=1

    scoreDict = {}
    whereTo = []

    cursor = db.team.find({})
    for document in cursor:
        if len(document['players']) == maxTeams:
            continue
        scoreDict[document['name']] = (document['score'])

    for score in scoreDict:
        whereTo.append(scoreDict[score])
    tmp = dict((v,k) for k,v in scoreDict.items())
    print(whereTo, min(whereTo))
    name = str(tmp[min(whereTo)])

    players = db.team.find_one({'name': name})['players']
    score = db.team.find_one({'name': name})['score'] + counter
    db.team.update_one({'name': name}, {'$set': {'players': str(players) +','+ str(uId)}})
    db.team.update_one({'name': name}, {'$set': {'score': score}})


def configure(maximumSkills, connectionString, predefinedSkills, maximumTeams, maximumPlayers):
    global maxSkills, connStr, preDefSkills, maxTeams, maxPlayers
    maxSkills, connStr, preDefSkills, maxTeams, maxPlayers = maximumSkills, connectionString, predefinedSkills, maximumTeams, maximumPlayers


if __name__ == '__main__':
    print('Задайте строку подключения к mongodb')
    connStr = input()
    print('Задайте максимальное количество игроков')
    maxPlayers = input()
    print('Задайте максимальное количество команд')
    maxTeams = input()
    print('Задайте максимальное количество навыков')
    maxSkills = input()
    print('Задайте теги навыков через запятую')
    preDefSkills = input().split(',')

    app.run(debug=True, port=5000)
