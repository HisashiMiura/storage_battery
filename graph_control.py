import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from datetime import timedelta
from typing import Tuple, List

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()


def draw_graph(y_title: str, ys: List[Tuple[np.ndarray, str]], op: str ='ave', display_date: str = 'year'):
    """1年間の時系列のグラフを描画する。

    Args:
        y_title: Y軸のタイトル
        ys: データと凡例のタプルのリスト
            データは numpy 配列で配列数は8760でないといけない
        op: データの加工方式。以下の文字を指定する。
            ave: 1日ごとに平均化処理をする。データは配列数 365 に加工される。
            itg: 1日ごとに積算処理をする。データは配列数 365 に加工される。
            a3: 1日ごとに最低値・平均値・最大値を計算する。データは配列数 365 ✕ 3 に加工される。
            a5: 1日ごとに最低値・25パーセンタイル値・50パーセンタイル値・75パーセンタイル値・最大値を計算する。
                データは配列数 365 ✕ 5 に加工される。
            raw: 特に加工はしない。データは配列数8760のまま。
        display_date: 1日単位で表示したい場合に日付を指定する。（例："5/14"）
    """

    plt.style.use('seaborn-whitegrid')

    xs = date_xs_range(op)

    fig = plt.figure(figsize=(15, 4))

    ax = fig.add_subplot(1, 1, 1)

    f = {
        'ave': get_average,
        'itg': get_integration,
        'a3': get_three_characteristics,
        'a5': get_five_characteristics,
        'raw': get_raw,
    }[op]

    for y in ys:
        ysds = f(np.array(y[0]), y[1])
        for ysd in ysds:
            ax.plot(xs, ysd[0], label=ysd[1])

    if display_date == 'year':
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    else:
        ax.xaxis.set_major_locator(mdates.HourLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:00'))
    if display_date == 'year':
        ax.set_xlim(datetime.strptime('2018-01-01', '%Y-%m-%d'), datetime.strptime('2019-01-01', '%Y-%m-%d'))
    else:
        start_date = datetime.strptime('2018/' + display_date, '%Y/%m/%d')
        end_date = start_date + timedelta(days=1)
        ax.set_xlim(start_date, end_date)
    ax.set_ylabel(y_title)
    plt.legend()
    plt.show()


def draw_sum_bar_graph(x_title, ys):

    fig = plt.figure(figsize=(15, 4))

    ax = fig.add_subplot(1, 1, 1)

    values = [np.sum(y[0]) for y in ys]
    titles = [y[1] for y in ys]
    xs = np.arange(len(ys))

    ax.barh(xs+0.5, values, tick_label=titles)
    ax.set_yticks(xs + 0.5)
    ax.set_xlabel(x_title)
    plt.show()


def date_xs_range(op):

    start = datetime.strptime('2018-01-01', '%Y-%m-%d')

    if op == 'raw':
        return np.array([start + timedelta(hours=n) for n in range(8760)])
    else:
        return np.array([start + timedelta(n) for n in range(365)])


def get_raw(v, name):
    return [(v, name)]


def get_integration(v, name):
    return [(np.sum(v.reshape(365, 24).T, axis=0), name)]


def get_average(v: np.ndarray, name):
    return [(np.mean(v.reshape(365, 24).T, axis=0), name)]


def get_three_characteristics(v, name):
    return [(np.min(v.reshape(365, 24).T, axis=0), name + '_min'),
            (np.mean(v.reshape(365, 24).T, axis=0), name + '_mean'),
            (np.max(v.reshape(365, 24).T, axis=0), name + '_max')]


def get_five_characteristics(v, name):
    return [
        (np.min(v.reshape(365, 24).T, axis=0), name + '_min'),
        (np.percentile(v.reshape(365, 24).T, 25, axis=0), name + '_25percentile'),
        (np.percentile(v.reshape(365, 24).T, 50, axis=0), name + '_mean'),
        (np.percentile(v.reshape(365, 24).T, 75, axis=0), name + '_75percentile'),
        (np.max(v.reshape(365, 24).T, axis=0), name + '_max')]


