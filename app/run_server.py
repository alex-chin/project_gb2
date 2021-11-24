import json
import os
from time import strftime

import dill
from flask import Flask, render_template, jsonify, send_from_directory, flash, redirect, url_for
from flask import request
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np  # для модели dill

print(np.__version__)

ALLOWED_EXTENSIONS = {'txt', 'csv'}
model = None

application = Flask(__name__)


def load_model(model_path):
    # load the pre-trained model
    global model
    # with application.open_instance_resource(model_path, 'rb') as f:
    #     model = dill.load(f)
    with open(model_path, 'rb') as f:
        model = dill.load(f)
    print(model)


# modelpath = os.path.join(os.path.dirname(__file__), 'model', 'init_finall_model.dill')
modelpath = os.path.join(os.path.dirname(__file__), 'model', 'numpy_finall_model.dill')
load_model(modelpath)

preds, diagnosis, pattern_per_5minute = model.predict(pd.DataFrame(
    {"id": [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
     "x": [760, 784, 772, 760, 768, 776, 852, 728, 800, 832, 808, 800, 840, 808, 792, 828, 808, 788, 816, 796]}))

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
        result_pat1 = ' Результат - положительный, Найдено 10 аномалий. '
    elif id == '2':
        result_pat2 = ' Результат - положительный, Найдено 3 аномалий. '
    elif id == '3':
        result_pat3 = ' Результат - отрицательный, Найдено 0 аномалий. '
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
            file_txt = file.read()
            # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            result_pat4 = ' Результат - отрицательный, Найдено 0 аномалий. '
            # return redirect(url_for('index', file_txt=file_txt, result_pat4=result_pat4))
            return render_template('index.html', file_txt=file_txt, result_pat4=result_pat4)
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''


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


@application.route('/series/', methods=['POST'])
def new_series():
    series = request.json
    return '<h1>Waiting for results</h1>' + json.dumps(series)


if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0')
    # application.run(host='0.0.0.0')
