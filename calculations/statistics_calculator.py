from scipy.stats import describe, sem, t
from math import sqrt


class StatisticsSet:
    def __init__(self, dataset, conf=0.95):
        dataset = list(map(float, dataset))
        d = describe(dataset)
        self.N = d.nobs
        self.min = d.minmax[0]
        self.max = d.minmax[1]
        self.mean = d.mean
        self.std = sem(dataset) * sqrt(self.N)
        self.conf_int = sem(dataset) * t.ppf((conf + 1) / 2.0, self.N - 1)

    def descr(self, prec=None, form=('', '')):
        descr_dict = {}
        for attr, value in self.__dict__.items():
            descr_dict.update(
                {attr: f'{form[0]}{value:0.{prec}f}{form[1]}'} if prec else {attr: f'{form[0]}{value:g}{form[1]}'}
            )
        return descr_dict
