# CardioSpike
Итоговый проект курса "Машинное обучение в бизнесе"

Авторы: Александр Клянчин, Илья Галухин
### Стек:

- ML: catboost, sklearn, pandas, numpy. 
- API: flask. 
- Данные: Цифровой Прорыв, Хакатон "Медицина, здравоохраниение, наука", кейс "Разработка детектора ковидных аномалий в ритме сердца" https://leadersofdigital.ru/event/63008/case/706486#cases

Задача: Разработка детектора COVID-19 аномалий в ритме сердца.

### Разработанный веб-сервис: http://paydocs.ru

Сервис **CardioSpike** по предсказанию COVID-19 аномалий в ритме сердца установлен на стандартный хостинг в
режиме Virtual Private Server (https://en.wikipedia.org/wiki/Virtual_private_server).
В данной конфигурации архитектура не подразумевает разделения на компоненты Front и API Backend.
Однако допустимо например запустить 2 копии сервера, чтобы 1 сервер был в роли Front,
а второй в роли API Backend.

- Адрес сервера: server5.hosting.reg.ru
- IP адрес: 31.31.198.106
- Внешний доступ через домен http://paydocs.ru
- Основной тестируемый API http://paydocs.ru/predict [POST]

### Формат передаваемых данных:
``{'id': [ id0, id1, ... ], 'x': [x0, x1, ...]}``, где
- id - идентификатор пациента
- x - измерения пульса R-R

### Преобразования данных:
- Сериализация в строку JSON - ``json.dumps``
- Кодирование в utf-8 - ``str.encode('utf-8')``

### Основные компоненты системы:
- ``task09.ipynb`` - исходное задание на курсовую работу
- ``EDA_and_learning_model/CardioSpike2.ipynb`` - EDA и создание модели.
- ``requirements_prod.txt`` - необходимые компоненты для установки на сервер 
- ``app/run_server.py`` - запуск сервера на основе Flask
- ``app/model/dill_clf_model.dill`` - реализованная модель
- ``app/data`` - примеры профилей пациентов
  - ``app/data/patient_1_non_anomaly.csv`` - предварительно отрицательный диагноз
  - ``app/data/patient_2_anomaly.csv`` - предварительно положительный диагноз
  - ``app/data/patient_3_anomaly.csv`` - предварительно положительный диагноз
- ``test_api/test_api.ipynb`` - тестирование внешнего API
  - ``test_api/data`` - данные для тестирования

### Авторы: 
- Галухин Илья @i_galukhin Lutiyroker@yandex.ru
- Клянчин Александр @AlexKChin alex.kchin@gmail.com +7(916)587-0140
