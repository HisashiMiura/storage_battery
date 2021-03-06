from typing import Dict
import numpy as np
from math import radians, ceil
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

from pyhees import section2_1
import pvbatt
import energy_calc
from energy_logger import EnergyLogger
import graph_control

def calc_total_energy(spec: Dict):

    results = section2_1.calc_E_T(spec)
    
    # ---- 事前データ読み込み ----

    e, E_S, _, _ = energy_calc.run(spec=spec)

    # 年間の暖房設備の設計一次エネルギー消費量, MJ/year
    E_H = e.get_E_H()

    # 年間の冷房設備の設計一次エネルギー消費量, MJ/year
    E_C = e.get_E_C()
    
    # 1 年当たりの機械換気設備の設計一次エネルギー消費量
    E_V = e.get_E_V()

    # 1 年当たりの照明設備の設計一次エネルギー消費量
    E_L = e.get_E_L()

    E_W = e.get_E_W() + e.get_E_CG()

    # 年間の設計消費電力量（二次）, kWh/year
    E_E = Decimal(e.get_E_E()).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    
    # 年間の設計ガス消費量, MJ/year
    E_G = Decimal(e.get_E_G()).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

    # 年間の設計灯油消費量, MJ/year
    E_K = Decimal(e.get_E_K()).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

    # 1年当たりのその他の設計一次エネルギー消費量
    E_M = e.get_E_AP() + e.get_E_CC()

    E_E_gen = np.sum(e.E_E_PVs + e.E_E_CG_gens)

    # 1 年当たりの設計一次エネルギー消費量（MJ/年）(s2-2-1)
    E_T_star = E_H + E_C + E_V + E_L + E_W - E_S + E_M

    # 小数点以下一位未満の端数があるときはこれを切り上げてMJをGJに変更する
    E_T = ceil(E_T_star / 100) / 10  # (1)

    # 1 年当たりの未処理暖房負荷の設計一次エネルギー消費量相当値, MJ/年
    # 小数点以下一位未満の端数があるときは、これを四捨五入する。, MJ/年
    E_UT_H = Decimal(e.get_E_UT_H()).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    E_UT_C = Decimal(e.get_E_UT_C()).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    UPL = E_UT_H + E_UT_C

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
    print('ガス（二次） MJ/年 (30929.2) : ' + str(E_G))
    print('灯油（二次） MJ/年 (0.0) : ' + str(E_K))
    print('発電量（二次） kWh/年 :(3879.96) : ' + str(E_E_gen))
    print('未処理負荷 (427.1) : ' + str(UPL))

    return e

def calc_with_pvbatt(spec: Dict, pvbatt_spec: Dict):

    if spec["CG"] is not None:
        raise Exception('蓄電池の計算をするにあたって当面の間コージェネレーション設備の設置は考えないことにします。')
    
    if spec["PV"] is None:
        raise Exception('太陽光発電の設置は必須とします。')

    e, _ = energy_calc.run(spec=spec)

    # インバータ回路補正係数
    K_IN = energy_calc.get_K_IN(etr_IN_R=spec["PV"]["etr_IN_r"])

    # アレイ回路補正係数
    K_PM_i =[energy_calc.get_K_PM_i(pv_type=panel["pv_type"]) for panel in spec["PV"]["panels"]]

    pvbatt_spec["K_IN"] = K_IN
    pvbatt_spec["K_PM"] = K_PM_i

    # 系統からの電力供給の有無
    SC_d_t = np.ones(8760)

    # パワーコンディショナおよび蓄電設備の補機の消費電力量を除く電力需要
    E_E_dmd_excl_d_t = e.E_E_Hs + e.E_E_Cs + e.E_E_Vs + e.E_E_Ls + e.E_E_Ws + e.E_E_APs + e.E_E_CCs

    # 外気温度
    theta_ex_d_t = energy_calc.get_outdoor_temp(region=spec["region"])

    # 太陽光発電設備による発電量 式(54)
    E_p_i_d_t = e.E_E_PVs_is

    output_data = pvbatt.calculate(pvbatt_spec, SC_d_t, E_E_dmd_excl_d_t,
        theta_ex_ds_ts=theta_ex_d_t,
        E_p_is_ds_ts=E_p_i_d_t)

    output_data.to_csv("output.csv", index=False, encoding="SHIFT-JIS")

    return e, output_data


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
        "PV": {
            "etr_IN_r": 0.9,
            "panels": [
                {
                    "P_p_i": 4.0,
                    "P_alpha": 0.0,
                    "P_beta": radians(30.0),
                    "pv_type": '結晶シリコン系',
                    "pv_setup": '屋根置き型'
                }
            ]
        },
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

    pvbatt_spec = {
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
        "r_int_dchg_batt": 0.6,
    }

    #  e = calc_total_energy(spec=spec)

    e, eb = calc_with_pvbatt(spec=spec, pvbatt_spec=pvbatt_spec)

    e.get_df().to_csv("energy_output.csv", index=False, encoding="SHIFT-JIS")

    print("E_E_PV_h(1735.0): " + str(round(np.sum(eb["E_E_PV_h"].values))))
    print("E_E_PV_sell(269.0): " + str(round(np.sum(eb["E_E_PV_sell"].values))))
    print("E_E_PV_chg(2157.0): " + str(round(np.sum(eb["E_E_PV_chg"].values))))
    print("E_E_PSS_h(890.0): " + str(round(np.sum(eb["E_E_PSS_h"].values))))
