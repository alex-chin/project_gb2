import json
import os
import urllib
from io import StringIO
from time import strftime

import dill
from flask import Flask, render_template, jsonify, send_from_directory, flash, redirect, url_for
from flask import request
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np  # для модели dill

from app.pipeline import Pipeline

print(np.__version__)

ALLOWED_EXTENSIONS = {'txt', 'csv'}
model = None

application = Flask(__name__)


def get_flask_file(folder, filename):
    return os.path.join(os.path.dirname(__file__), folder, filename)


# загрузка объекта конвеера обработки и модели предсказания
modelpath = get_flask_file('model', 'dill_clf_model.dill')
model = Pipeline(modelpath)
print(model)

# локальные профили пациентов
patients_profile = ['patient_1_non_anomaly.csv', 'patient_2_anomaly.csv', 'patient_3_anomaly.csv']

'''

Карта маршрутов
 
> application.url_map
Map([<Rule '/series/' (OPTIONS, POST) -> new_series>,
 <Rule '/about' (HEAD, GET, OPTIONS) -> about>,
 <Rule '/' (HEAD, GET, OPTIONS) -> index>,
 <Rule '/' (HEAD, GET, OPTIONS, POST) -> upload_file>,
 <Rule '/test_pat/<id>' (HEAD, GET, OPTIONS) -> test_pat>,
 <Rule '/static/<filename>' (HEAD, GET, OPTIONS) -> static>,
 <Rule '/data/<filename>' (HEAD, GET, OPTIONS) -> files>])
'''

'''
 ======== Маршруты для реализации front-end ============
'''


@application.route('/')
def index():
    # главная страница
    return render_template('index.html', is_home=True)

@application.route('/yandex_dee3385fbef3f620.html')
def verification():
    return render_template('yandex_dee3385fbef3f620.html')


@application.route('/about')
def about():
    # страница о проекте
    return render_template('about_sp.html')


@application.route('/data/<path:filename>')
def files(filename):
    # отдача файлов из специальной директории data
    # - образцы исследований пациентов
    # параметр - имя файла
    return send_from_directory('data', filename)


@application.route('/test_pat/<id>')
def test_pat(id):
    # тестирование модели по малому кругу
    # использование образцов в хранилище
    # параметр - номер образца
    result_pat1 = ''
    result_pat2 = ''
    result_pat3 = ''
    if id == '1':
        preds, diagnosis, pattern_per_5minute = _file_process(get_flask_file('data', patients_profile[0]))
        result_pat1 = _format_predict(preds, diagnosis, pattern_per_5minute)
    elif id == '2':
        preds, diagnosis, pattern_per_5minute = _file_process(get_flask_file('data', patients_profile[1]))
        result_pat2 = _format_predict(preds, diagnosis, pattern_per_5minute)
    elif id == '3':
        preds, diagnosis, pattern_per_5minute = _file_process(get_flask_file('data', patients_profile[2]))
        result_pat3 = _format_predict(preds, diagnosis, pattern_per_5minute)
    return render_template('index.html', result_pat1=result_pat1, result_pat2=result_pat2, result_pat3=result_pat3)


def allowed_file(filename):
    # вспомогательная процедура для проверки расширения файла
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@application.route('/', methods=['GET', 'POST'])
def upload_file():
    # загрузка файла образцов допустима только с главной страницы
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            data_bytes = file.read()
            # преобразования бин -> строка -> csv
            file_stream = StringIO(str(data_bytes, 'utf-8'))
            pred, diagnosis, pattern_per_5minute = _file_process(file_stream)
            result_pat4 = _format_predict(pred, diagnosis, pattern_per_5minute)
            return render_template('index.html', result_pat4=result_pat4)
    return render_template('index.html')
    # return '''
    # <!doctype html>
    # <title>Upload new File</title>
    # <h1>Upload new File</h1>
    # <form method=post enctype=multipart/form-data>
    #   <input type=file name=file>
    #   <input type=submit value=Upload>
    # </form>
    # '''


def _format_predict(preds, diagnosis, pattern_per_5minute):
    num_anomaly = sum(preds)
    result = 'положительный' if diagnosis else 'отрицательный'
    metric = f'Показатель {pattern_per_5minute} A/min'
    buf = f'Результат - {result}, Найдено {num_anomaly} аномалий. {metric if diagnosis else ""}'
    return buf


def _file_process(file):
    df = pd.read_csv(file)
    id = df['id'].tolist()
    x = df['x'].tolist()
    # вызов модельки
    preds, diagnosis, pattern_per_5minute = _get_prediction(id, x)
    return preds, diagnosis, pattern_per_5minute


def _get_prediction(id_, x):
    # вызов API. В данном случае блокирующий запрос к самому серверу
    body = {'id': id_, 'x': x}
    jsondata = json.dumps(body)
    jsondataasbytes = jsondata.encode('utf-8')  # needs to be bytes

    myurl = "http://paydocs.ru/predict"
    # myurl = "http://localhost:5000/predict"
    req = urllib.request.Request(myurl)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    req.add_header('Content-Length', len(jsondataasbytes))

    response = urllib.request.urlopen(req, jsondataasbytes)

    data = json.loads(response.read())

    predictions = data['predictions']
    diagnosis = data['diagnosis']
    pattern_per_5minute = data['pattern_per_5minute']
    return predictions, list(diagnosis.values())[0], list(pattern_per_5minute.values())[0]


'''
 ======== Маршруты для реализации API ============
'''


@application.route("/predict", methods=["POST"])
def predict():
    # initialize the data dictionary that will be returned from the
    # view
    data = {"success": False}
    # dt = strftime("[%Y-%b-%d %H:%M:%S]")
    # ensure an image was properly uploaded to our endpoint
    if request.method == "POST":

        id, x = [], []
        request_json = request.get_json()
        if request_json["id"]:
            id = request_json['id']

        if request_json["x"]:
            x = request_json['x']

        # logger.info(f'{dt} Data: id={id}, x={x}')
        try:
            preds, diagnosis, pattern_per_5minute = model.predict(pd.DataFrame({"id": id, "x": x}))
        except AttributeError as e:
            # logger.warning(f'{dt} Exception: {str(e)}')
            data['predictions'] = str(e)
            data['diagnosis'] = str(e)
            data['pattern_per_5minute'] = str(e)
            data['success'] = False
            return jsonify(data)

        data["predictions"] = list(preds)  # list
        data['diagnosis'] = diagnosis  # dict
        data['pattern_per_5minute'] = pattern_per_5minute  # dict
        # indicate that the request was a success
        data["success"] = True

    # return the data dictionary as a JSON response
    return jsonify(data)


if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0')
    # application.run(host='0.0.0.0')
