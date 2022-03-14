from typing import Dict

from pyhees import section3_1, section3_2

def run(spec: Dict):
    """エネルギー消費量を計算する。

    Args:
        spec (Dict): 仕様（入力値）
    """

    # 熱損失係数, W/(m2K)
    # 暖房期の日射取得係数, (W/m2)/(W/m2)
    # 冷房期の日射取得係数, (W/m2)/(W/m2)
    # 外皮の面積の合計, m2
    Q, mu_H, mu_C, A_env = get_envelope(dict_env=spec["ENV"])

    return Q, mu_H, mu_C, A_env


def get_envelope(dict_env: Dict):
    """外皮の断熱性能を計算する。

    Args:
        dict_env (Dict): 外皮の仕様
    Returns:
        Q: 熱損失係数, W/(m2K)
        mu_H: 暖房期の日射取得係数, (W/m2)/(W/m2)
        mu_C: 冷房期の日射取得係数, (W/m2)/(W/m2)
        A_env: 外皮の面積の合計, m2
    """
    
    if dict_env is None:
        raise ValueError("外皮の仕様が指定されていません。")

    _, _, _, _, Q_dash, mu_H, mu_C, _ = section3_2.calc_insulation_performance(**dict_env)

    Q = section3_1.get_Q(Q_dash)

    A_env = dict_env.get('A_env')

    return Q, mu_H, mu_C, A_env

