from typing import Dict
import numpy as np
from math import radians, ceil
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

from pyhees.section2_1 import calc_E_T
from pyhees import section2_1, section2_2, section10

import pvbatt
from pyhees import section11_2
from pyhees import section9_1

import energy_calc

def calc_total_energy(spec: Dict):

    results = calc_E_T(spec)
    
    # ---- 事前データ読み込み ----

    E_E_dmd_d_t, f_prim, e, E_G_CG_sell = energy_calc.run(spec=spec)

    # ---- 二次エネの計算 ----

    # 年間の暖房設備の設計一次エネルギー消費量, MJ/year
    E_H = e.get_E_H()

    # 年間の冷房設備の設計一次エネルギー消費量, MJ/year
    E_C = e.get_E_C()
    
    # 1 年当たりの未処理暖房負荷の設計一次エネルギー消費量相当値, MJ/年
    # 小数点以下一位未満の端数があるときは、これを四捨五入する。, MJ/年
    E_UT_H = Decimal(e.get_E_UT_H()).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    E_UT_C = Decimal(e.get_E_UT_C()).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

    UPL = E_UT_H + E_UT_C

    # 1 年当たりの機械換気設備の設計一次エネルギー消費量
    E_V = e.get_E_V()

    # 1 年当たりの照明設備の設計一次エネルギー消費量
    E_L = e.get_E_L()

    E_W = e.get_E_W() + e.get_E_CG()

    # 1時間当たりの設計消費電力量（二次）, kWh/h
    E_E_d_t = e.E_E_Hs + e.E_E_Cs + e.E_E_Vs + e.E_E_Ls + e.E_E_Ws + e.E_E_APs + e.E_E_CCs - e.E_E_PV_hs - e.E_E_CG_hs

    # 1 年当たりの設計消費電力量（kWh/年）
    E_E = calc_E_E(e.E_E_Hs, e.E_E_Cs, e.E_E_CG_hs, e.E_E_Ws, e.E_E_Ls, e.E_E_Vs, e.E_E_APs, e.E_E_CCs, e.E_E_PVs, e.E_E_PV_hs, E_E_dmd_d_t, E_E_d_t)
    
    E_gen = (np.sum(e.E_E_PVs) + np.sum(e.E_E_CG_gens)) * f_prim / 1000

    # 1 年当たりの設計ガス消費量（MJ/年）
    E_G = calc_E_G(e.E_G_Hs, e.E_G_Cs, e.E_G_Ws, e.E_G_CGs, e.E_G_APs, e.E_G_CCs, spec['A_A'])

    # 1 年当たりの設計灯油消費量（MJ/年）
    E_K = calc_E_K(e.E_K_Hs, e.E_K_Cs, e.E_K_Ws, e.E_K_CGs, e.E_K_APs, e.E_K_CCs)

    E_E_gen = np.sum(e.E_E_PVs + e.E_E_CG_gens)

    # 1年当たりのその他の設計一次エネルギー消費量
    E_M = e.get_E_AP() + e.get_E_CC()

    # 1年当たりのエネルギー利用効率化設備による設計一次エネルギー消費量の削減量 (MJ/yr) (14)
    # 次の E_S_h と E_S_sell を足す
    # E_S_h: 1年当たりのエネルギー利用効率化設備による発電量のうちの自家消費分に係る一次エネルギー消費量の控除量 (MJ/yr) (15)
    # E_S_sell: 1年当たりのコージェネレーション設備の売電量に係る設計一次エネルギー消費量の控除量 (MJ/yr) (16)
    #   E_S_sell = E_G_CG_sell
    #   1年当たりのコージェネレーション設備の売電量に係る設計一次エネルギー消費量の控除量 (MJ/yr) (16)
    # この値は1時間ごとには計算できない。
    E_S = np.sum(e.E_E_PV_hs + e.E_E_CG_hs) * f_prim / 1000 + E_G_CG_sell

    # 1 年当たりの設計一次エネルギー消費量（MJ/年）(s2-2-1)
    E_T_star = E_H + E_C + E_V + E_L + E_W - E_S + E_M

    # 小数点以下一位未満の端数があるときはこれを切り上げてMJをGJに変更する
    E_T = ceil(E_T_star / 100) / 10  # (1)



    print('===============================')
    print('参照値: ' + str(results[0]))
    print('計算値: ' + str(E_T))
    print('暖房: ' + str( round(E_H/1000, 1)))
    print('冷房: ' + str( round(E_C/1000, 1)))
    print('換気: ' + str( round(E_V/1000, 1)))
    print('照明: ' + str( round(E_L/1000, 1)))
    print('給湯: ' + str( round(E_W/1000, 1)))
    print('自家消費分: ' + str( round(E_S/1000, 1)))
    print('その他: ' + str( round(E_M/1000, 1)))
    print('電気（二次）kWh/年 (3873.4) : ' + str(E_E))
    print('電気（一次）kWh/年 (37804.384) : ' + str(E_E * f_prim / 1000))
    print('ガス（二次） MJ/年 (30929.2) : ' + str(E_G))
    print('灯油（二次） MJ/年 (0.0) : ' + str(E_K))
    print('発電量（一次） MJ/年 (37868.41...) : ' + str(E_gen))
    print('発電量（二次） kWh/年 :(3879.96) : ' + str(E_E_gen))
    print('未処理負荷 (427.1) : ' + str(UPL))


def calc_E_E(E_E_H_d_t, E_E_C_d_t, E_E_CG_h_d_t, E_E_W_d_t, E_E_L_d_t, E_E_V_d_t, E_E_AP_d_t, E_E_CC_d_t, E_E_PV_d_t, E_E_PV_h_d_t, E_E_dmd_d_t, E_E_d_t):
    """1 年当たりの設計消費電力量（kWh/年）
    Args:
      PV(ndarray, optional, optional): 太陽光発電設備のリスト, defaults to None
    Returns:
      1 年当たりの設計消費電力量（kWh/年）: 1 年当たりの設計消費電力量（kWh/年）
    """
    
    E_E = sum(E_E_H_d_t) \
          + sum(E_E_C_d_t) \
          + sum(E_E_V_d_t) \
          + sum(E_E_L_d_t) \
          + sum(E_E_W_d_t) \
          + sum(E_E_AP_d_t) \
          + sum(E_E_CC_d_t) \
          - sum(E_E_PV_h_d_t) \
          - sum(E_E_CG_h_d_t)  # (25)

    print(E_E)
    print(sum(E_E_d_t))

    # 小数点以下一位未満の端数があるときは、これを四捨五入する。
    return Decimal(E_E).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)


def calc_E_G(E_G_H_d_t, E_G_C_d_t, E_G_W_d, E_G_CG_d_t, E_G_AP_d_t, E_G_CC_d_t, A_A):
    """1 年当たりの設計ガス消費量（MJ/年）

    Args:
      A_A(float): 床面積の合計 (m2)

    Returns:
      float: 1 年当たりの設計ガス消費量（MJ/年）

    """

    E_G = sum(E_G_H_d_t) \
          + sum(E_G_C_d_t) \
          + sum(E_G_W_d) \
          + sum(E_G_CG_d_t) \
          + sum(E_G_AP_d_t) \
          + sum(E_G_CC_d_t)  # (26)

    # 小数点以下一位未満の端数があるときは、これを四捨五入する。
    return Decimal(E_G).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)


def calc_E_K(E_K_H_d_t, E_K_C_d_t, E_K_W_d_t, E_K_CG_d_t, E_K_AP_d_t, E_K_CC_d_t):
    """1 年当たりの設計灯油消費量（MJ/年）

    Args:
 
    Returns:
      float: 1 年当たりの設計灯油消費量（MJ/年）

    """
    
    # 1年当たりの設計灯油消費量（MJ / 年）
    E_K_raw = sum(E_K_H_d_t) \
              + sum(E_K_C_d_t) \
              + sum(E_K_W_d_t) \
              + sum(E_K_CG_d_t) \
              + sum(E_K_AP_d_t) \
              + sum(E_K_CC_d_t)  # (27)

    # 小数点以下一位未満の端数があるときは、これを四捨五入する。
    E_K = Decimal(E_K_raw).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

    return E_K


if __name__ == '__main__':

    spec = {
        "region": 6,
        "type": "一般住宅",
        "reference": {
            "reference_year": None
        },
        "tatekata": "戸建住宅",
        "sol_region": 3,
        "A_A": 120.08,
        "A_MR": 29.81,
        "A_OR": 51.34,
        "NV_MR": 0,
        "NV_OR": 0,
        "TS": False,
        "r_A_ufvnt": None,
        "underfloor_insulation": None,
        "mode_H": "居室のみを暖房する方式でかつ主たる居室とその他の居室ともに温水暖房を設置する場合に該当しない場合",
        "mode_C": "居室のみを冷房する方式",
        "H_A": None,
        "H_MR": {
            "type": "ルームエアコンディショナー",
            "e_class": None,
            "dualcompressor": False
        },
        "H_OR": {
            "type": "ルームエアコンディショナー", 
            "e_class": None, 
            "dualcompressor": False
        }, 
        "H_HS": None,
        "C_A": None,
        "C_MR": {
            "type": "ルームエアコンディショナー",
            "e_class": None,
            "dualcompressor": False
        },
        "C_OR": {
            "type": "ルームエアコンディショナー",
            "e_class": None,
            "dualcompressor": False
        },
        "HW": {
            "has_bath": True,
            "hw_type": "ガス従来型給湯機",
            "hybrid_category": None,
            "e_rtd": None,
            "e_dash_rtd": None,
            "kitchen_watersaving_A": False,
            "kitchen_watersaving_C": False,
            "shower_watersaving_A": False,
            "shower_watersaving_B": False,
            "washbowl_watersaving_C": False,
            "bath_insulation": False,
            "bath_function": "ふろ給湯機(追焚あり)",
            "pipe_diameter": "上記以外"
        },
        "V": {
            "type": "ダクト式第二種換気設備又はダクト式第三種換気設備",
            "input": "評価しない",
            "N": 0.5
        },
        "HEX": None,
        "L": {
            "has_OR": True,
            "has_NO": True,
            "A_OR": 51.34,
            "MR_installed": "設置しない",
            "OR_installed": "設置しない",
            "NO_installed": "設置しない"
        },
        "SHC": None,
        "PV": [
            {
                "P_p_i": 4.0,
                "P_alpha": 0.0,
                "P_beta": radians(30.0),
                "pv_type": '結晶シリコン系',
                "pv_setup": '屋根置き型',
                "etr_IN_r": 0.9
            }
        ],
        "CG": None,
        "ENV": {
            "method": "当該住宅の外皮面積の合計を用いて評価する",
            "A_env": 307.51,
            "A_A": 120.08,
            "U_A": 0.87,
            "eta_A_H": 4.3,
            "eta_A_C": 2.8
        }
    }

    calc_total_energy(spec=spec)

    spec = {
        "E_dash_dash_E_in_rtd_PVtoDB": 6.0,
        "eta_ce_lim_PVtoDB": 0.6,
        "alpha_PVtoDB": -0.0126,
        "beta_PVtoDB": 0.975,
        "E_dash_dash_E_in_rtd_PVtoSB": 6.0,
        "eta_ce_lim_PVtoSB": 0.6,
        "alpha_PVtoSB": -0.025,
        "beta_PVtoSB": 0.975,
        "E_dash_dash_E_in_rtd_SBtoDB": 6.0,
        "eta_ce_lim_SBtoDB": 0.6,
        "alpha_SBtoDB": -0.036,
        "beta_SBtoDB": 0.975,
        "P_aux_PCS_oprt": 25.0,
        "P_aux_PCS_stby": 2.0,
        "r_LCP_batt": 0.2,
        "V_rtd_batt": 177.6,
        "V_star_lower_batt": 129.6,
        "V_star_upper_batt": 196.8,
        "SOC_star_lower": 0.2,
        "SOC_star_upper": 0.8,
        "W_rtd_batt": 12.0,
        "n": 1,
        "K_IN": 2.0,
        "K_PM": [1.0],
        "eta_IN_R": 1.0,
        
        "r_int_dchg_batt": 0.6,
    }

    # 時系列電力需要読み込み
    # columns = ["電力供給", "外気温度", "電力需要", "太陽電池アレイの発電量1"]
    df = pd.read_csv("input.csv", encoding="SHIFT-JIS")

#    print("入力ファイルの表示")
#    print(df)
    
    output_data = pvbatt.calculate(spec, df)

    output_data.to_csv("output.csv", index=False, encoding="SHIFT-JIS")
