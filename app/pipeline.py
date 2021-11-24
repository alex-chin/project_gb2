import numpy as np
import pandas as pd
import dill


class Pipeline:

    def __init__(self, dill_clf_filename):
        self.clf_learn_cols = ['x', 'left_shift_1', 'left_shift_2', 'left_shift_3', 'left_shift_4',
                               'right_shift_1', 'right_shift_2', 'right_shift_3', 'right_shift_4']
        self.dill_clf_filename = dill_clf_filename
        with open(self.dill_clf_filename, 'rb') as f:
            self.clf_model = dill.load(f)
        self.df = None
        self.index = None
        self.threshold = 0.912528

    def clf_transformation(self, X):
        self.df = X.copy()
        self.index = self.df.index
        for idx in range(1, 5):
            left_feat_name = 'left_shift_' + str(idx)
            right_feat_name = 'right_shift_' + str(idx)
            self.df[left_feat_name] = self.df.groupby(self.df.id)['x'].transform(lambda x: x.shift(idx))
            self.df[right_feat_name] = self.df.groupby(self.df.id)['x'].transform(lambda x: x.shift(-idx))
            self.df[left_feat_name].fillna(0, inplace=True)
            self.df[right_feat_name].fillna(0, inplace=True)

    def clf_predict(self):
        y = self.clf_model.predict_proba(self.df[self.clf_learn_cols])[:, 1]
        y = np.where(y >= self.threshold, 1, 0)
        y = pd.Series(y, index=self.index)
        self.df['y2'] = y

    def predict(self, X):
        self.clf_transformation(X)
        self.clf_predict()

        y = np.sum([self.df['y2'].shift(i).fillna(0) for i in range(-5, 5)], axis=0)
        y = pd.Series(np.where(y >= 1, 1, 0), index=self.index)

        # Получаем словарь диагнозов diagnosis_by_id. Ключи - id пациента, значения - диагнозы.
        # True - болен, False - здоров
        diagnosis = self.df.groupby(self.df.id)['y2'].agg(lambda x: True if x.sum() > 0 else False).tolist()
        diagnosis_by_id = dict(zip(self.df.id.unique().tolist(), diagnosis))

        # Получаем словарь кастомной метрики - количество аномалий за 5 минут.
        # Ключи - id пациента, значения - количество аномалий
        tmp_df = self.df.groupby(self.df.id, as_index=False).agg({'x': 'sum', 'y2': 'sum'})
        tmp_df['pattern_per_5minute'] = tmp_df.y2 * 300000 / tmp_df.x
        tmp_df['pattern_per_5minute'] = tmp_df['pattern_per_5minute'].apply(round)
        pattern_per_5minute = dict(zip(tmp_df.id, tmp_df.pattern_per_5minute))

        return y, diagnosis_by_id, pattern_per_5minute
