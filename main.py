from typing import Dict
import numpy as np
from math import radians, ceil
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN
import pandas as pd

from pyhees.section2_1 import calc_E_T
from pyhees import section2_1, section2_2, section3_1, section3_2, section10
from pyhees.section2_1_b import get_f_prim
from pyhees.section4_1 import calc_heating_load, calc_heating_mode, get_virtual_heating_devices, get_virtual_heatsource, \
    get_E_E_H_d_t, get_E_G_H_d_t, calc_E_K_H_d_t, calc_E_M_H_d_t, calc_E_UT_H_d_t
from pyhees.section9_1 import calc_E_E_PV_d_t
from simplejson import load

import pvbatt2
import pvbatt
from pyhees import section11_2
from pyhees import section9_1
from pyhees import section4_1, section5, section6, section7_1, section7_1_b, section8

def calc_total_energy(spec: Dict):

    results = calc_E_T(spec)
    
    # ---- 事前データ読み込み ----

    # 日射量データの読み込み
    solrad = None
    if (spec['SHC'] is not None or spec['PV'] is not None) and 'sol_region' in spec:
        if spec['sol_region'] is not None:
            solrad = section11_2.load_solrad(spec['region'], spec['sol_region'])

    # ---- 外皮の計算 ----

    # 外皮の断熱性能の計算
    if spec['ENV'] is not None:
        U_A, _, _, _, Q_dash, eta_H, eta_C, _ = section3_2.calc_insulation_performance(**spec['ENV'])
        # 熱損失係数
        Q = section3_1.get_Q(Q_dash)
        A_env = spec['ENV'].get('A_env')
    else:
        Q = None
        eta_H, eta_C = None, None
        A_env = None

    # ---- 暖房設備 ----

    # 1 時間当たりの暖房設備の設計一次エネルギー消費量

    # 実質的な暖房機器の仕様を取得
    spec_MR, spec_OR = section2_2.get_virtual_heating_devices(spec['region'], spec['H_MR'], spec['H_OR'])

    # 暖房方式及び運転方法の区分
    mode_MR, mode_OR = section2_2.calc_heating_mode(region=spec['region'], H_MR=spec_MR, H_OR=spec_OR)

    # ---- 暖房負荷 ----

    # 暖房負荷の取得
    L_T_H_d_t_i, L_dash_H_R_d_t_i = section2_2.calc_heating_load(
        spec['region'], spec['sol_region'],
        spec['A_A'], spec['A_MR'], spec['A_OR'],
        Q, eta_H, eta_C, spec['NV_MR'], spec['NV_OR'], spec['TS'], spec['r_A_ufvnt'], spec['HEX'],
        spec['underfloor_insulation'], spec['mode_H'], spec['mode_C'],
        spec_MR, spec_OR, mode_MR, mode_OR, spec['SHC'])

    # ---- 冷房負荷 ----

    # 冷房負荷の取得
    L_CS_d_t, L_CL_d_t = \
        section2_2.calc_cooling_load(spec['region'], spec['A_A'], spec['A_MR'], spec['A_OR'], Q, eta_H, eta_C,
                          spec['NV_MR'], spec['NV_OR'], spec['r_A_ufvnt'], spec['underfloor_insulation'],
                          spec['mode_C'], spec['mode_H'], mode_MR, mode_OR, spec['TS'], spec['HEX'])

    # ---- 冷房設備 ----

    # 1 時間当たりの冷房設備の設計一次エネルギー消費量 (4)
    E_C_d_t, E_E_C_d_t, E_G_C_d_t, E_K_C_d_t, E_M_C_d_t, E_UT_C_d_t =get_E_C_d_t(
        spec['region'], spec['A_A'], spec['A_MR'], spec['A_OR'],
                  A_env, eta_H, eta_C, Q,
                  spec['C_A'], spec['C_MR'], spec['C_OR'],
                  L_T_H_d_t_i, L_CS_d_t, L_CL_d_t, spec['mode_C'])

    # 1 年当たりの冷房設備の設計一次エネルギー消費量
    E_C = np.sum(E_C_d_t)

    # ---- 暖房設備 ----

    # 1 時間当たりの暖房設備の設計一次エネルギー消費量

    # 実質的な温水暖房機の仕様を取得
    spec_HS = section2_2.get_virtual_heatsource(spec['region'], spec['H_HS'])

    # 暖房日の計算
    if spec['SHC'] is not None and spec['SHC']['type'] == '空気集熱式':
        from pyhees.section3_1_heatingday import get_heating_flag_d

        heating_flag_d = get_heating_flag_d(L_dash_H_R_d_t_i)
    else:
        heating_flag_d = None

    E_H_d_t, E_E_H_d_t, E_G_H_d_t, E_K_H_d_t, E_M_H_d_t, E_UT_H_d_t = get_E_H_d_t(spec['region'], spec['sol_region'], spec['A_A'], spec['A_MR'], spec['A_OR'],
                  A_env, eta_H, eta_C, Q,
                  spec['mode_H'],
                  spec['H_A'], spec_MR, spec_OR, spec_HS, mode_MR, mode_OR, spec['CG'], spec['SHC'],
                  heating_flag_d, L_T_H_d_t_i, L_CS_d_t, L_CL_d_t)
    
    E_H = np.sum(E_H_d_t)

    # 1 年当たりの未処理暖房負荷の設計一次エネルギー消費量相当値, MJ/年
    E_UT_H_raw = sum(E_UT_H_d_t)  # (28)

    # 小数点以下一位未満の端数があるときは、これを四捨五入する。, MJ/年
    E_UT_H = Decimal(E_UT_H_raw).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

    UPL = E_UT_H

    # 温水暖房負荷の計算
    L_HWH = section2_2.calc_L_HWH(spec['A_A'], spec['A_MR'], spec['A_OR'], spec['HEX'], spec['H_HS'], spec['H_MR'],
                           spec['H_OR'], Q, spec['SHC'], spec['TS'], eta_H, eta_C, spec['NV_MR'], spec['NV_OR'],
                           spec['r_A_ufvnt'], spec['region'], spec['sol_region'], spec['underfloor_insulation'],
                           spec['CG'])


    # ---- 給湯/コージェネ設備 ----

    # その他または設置しない場合、Dict HW にデフォルト設備を上書きしたものを取得する。
    # 設置する場合は HW と spec_HW は同じ。
    # spec_HW は HW の DeepCopy
    spec_HW = section7_1_b.get_virtual_hotwater(spec['region'], spec['HW'])

    # 仮想居住人数
    n_p = section2_2.get_n_p(A_A=spec['A_A'])

    # 暖房日の計算
    heating_flag_d = section2_2.calc_heating_flag_d(
        A_A=spec['A_A'],
        A_MR=spec['A_MR'],
        A_OR=spec['A_OR'],
        HEX=spec['HEX'],
        H_MR=spec['H_MR'],
        H_OR=spec['H_OR'],
        Q=Q,
        SHC=spec['SHC'],
        TS=spec['TS'],
        mu_H=eta_H,
        mu_C=eta_C,
        NV_MR=spec['NV_MR'],
        NV_OR=spec['NV_OR'],
        r_A_ufvnt=spec['r_A_ufvnt'],
        region=spec['region'],
        sol_region=spec['sol_region'],
        underfloor_insulation=spec['underfloor_insulation']
    )
    
    # ---- 照明,換気,その他設備 ----

    # 1 年当たりの照明設備の設計一次エネルギー消費量
    E_L, E_E_L_d_t = calc_E_L(spec['A_A'], spec['A_MR'], spec['A_OR'], spec['L'])

    # 1 年当たりの機械換気設備の設計一次エネルギー消費量
    E_V, E_E_V_d_t = calc_E_V(spec['A_A'], spec['V'], spec['HEX'])

    #region その他の一次エネルギー消費量

    # 1時間当たりの家電の消費電力量, kWh/h
    E_E_AP_d_t = section10.calc_E_E_AP_d_t(n_p)

    # 1時間当たりの家電のガス消費量, MJ/h
    E_G_AP_d_t = section10.get_E_G_AP_d_t()

    # 1時間当たりの家電の灯油消費量, MJ/h
    E_K_AP_d_t = section10.get_E_K_AP_d_t()

    # 1時間当たりの家電のその他の燃料による一次エネルギー消費量, MJ/h
    E_M_AP_d_t = section10.get_E_M_AP_d_t()

    # 1時間当たりの調理の消費電力量, kWh/h
    E_E_CC_d_t = section10.get_E_E_CC_d_t()

    # 1時間当たりの調理のガス消費量, MJ/h
    E_G_CC_d_t = section10.calc_E_G_CC_d_t(n_p)

    # 1時間当たりの調理の灯油消費量, MJ/h
    E_K_CC_d_t = section10.get_E_K_CC_d_t()

    # 1時間当たりの調理のその他の燃料による一次エネルギー消費量, MJ/h
    E_M_CC_d_t = section10.get_E_M_CC_d_t()

    #endregion
    
    # 1 年当たりの給湯設備（コージェネレーション設備を含む）の設計一次エネルギー消費量
    # E_W: 1時間当たりの給湯設備またはコージェネレーション設備のガス消費量 (MJ/h)
    # E_E_CG_gen_d_t: 1時間当たりのコージェネレーション設備による発電量 (kWh/h)
    # E_E_CG_h_d_t: 1時間当たりのコージェネレーション設備による発電量のうちの自家消費分 (kWh/h)
    # E_E_TU_aux_d_t: 1時間当たりのタンクユニットの補機消費電力量 (kWh/h)
    # E_E_CG_h_d_t: 上記と同じ
    # E_G_CG_ded: 1年あたりのコージェネレーション設備のガス消費量のうちの売電に係る控除対象分 (MJ/yr)
    # e_BB_ave: 給湯時のバックアップボイラーの年間平均効率 (-)
    # Q_CG_h: 1年あたりのコージェネレーション設備による製造熱量のうちの自家消費算入分 (MJ/yr)
    E_W, E_E_CG_gen_d_t, E_E_TU_aux_d_t, E_G_CG_ded, e_BB_ave, Q_CG_h, E_E_W_d_t, E_G_W_d, E_K_W_d_t, E_G_CG_d_t, E_K_CG_d_t \
            = calc_E_W(E_E_H_d_t, E_E_C_d_t, E_E_V_d_t, E_E_L_d_t, E_E_AP_d_t, spec_MR, spec_OR, mode_MR, mode_OR, spec_HS, L_T_H_d_t_i, n_p, heating_flag_d, spec['A_A'], spec['region'], spec['sol_region'], spec_HW, spec['SHC'], spec['CG'], L_HWH,
                      spec['H_HS'], spec['A_MR'], spec['A_OR'], Q, eta_H, eta_C,
                      spec['NV_MR'], spec['NV_OR'], spec['TS'], spec['r_A_ufvnt'], spec['HEX'],
                      spec['underfloor_insulation'])
    
    f_prim = section2_1.get_f_prim()

    if spec['CG'] is not None:
        has_CG = True
        has_CG_reverse = spec['CG']["reverse"] if 'reverse' in spec['CG'] else False
    else:
        has_CG = False
        has_CG_reverse = False

    # 太陽光発電が設置されているか否か
    if spec['PV'] is not None:
        has_PV = True
    else:
        has_PV = False
    
    # 1時間当たりの太陽光発電設備による発電量(s9-1 1), kWh/h
    if has_PV:
        E_E_PV_d_t = section9_1.calc_E_E_PV_d_t(spec['PV'], solrad)
    else:
        E_E_PV_d_t = np.zeros(24 * 365)

    # 1時間当たりの電力需要, KWh/h
    E_E_dmd_d_t = section2_2.get_E_E_dmd_d_t(E_E_H_d_t, E_E_C_d_t, E_E_V_d_t, E_E_L_d_t, E_E_W_d_t, E_E_AP_d_t)

    # 1時間当たりのコージェネレーション設備による発電量のうちの自家消費分 (kWh/h) (19-1)(19-2)
    # コージェネレーション設備による発電量と電力需要を比較する。
    # PV よりもコージェネレーション設備による発電量が優先的に自家消費分にまわされる。
    E_E_CG_h_d_t = section2_2.get_E_E_CG_h_d_t(E_E_CG_gen_d_t, E_E_dmd_d_t, has_CG)

    # 1 時間当たりの太陽光発電設備による消費電力削減量（自家消費分） (17-1)(17-2), kWh/h
    # コージェネレーション設備による発電量を考慮した残りの電力需要と比較して太陽光発電設備による自家消費分を決める。
    E_E_PV_h_d_t = section2_2.get_E_E_PV_h_d_t(E_E_PV_d_t, E_E_dmd_d_t, E_E_CG_h_d_t, has_PV)

    # 1時間当たりのコージェネレーション設備による売電量(二次エネルギー) (kWh/h) (24-1)(24-2)
    E_E_CG_sell_d_t = section2_2.get_E_E_CG_sell_d_t(E_E_CG_gen_d_t, E_E_CG_h_d_t, has_CG_reverse)

    # 1年当たりのコージェネレーション設備による売電量（一次エネルギー換算値）(MJ/yr) (23)
    E_CG_sell = np.sum(E_E_CG_sell_d_t) * f_prim / 1000

    # 1年当たりのコージェネレーション設備による発電量のうちの自己消費分 (kWH/yr) (s8 4)
    E_E_CG_self = section2_2.get_E_E_CG_self(E_E_TU_aux_d_t)

    # エネルギー利用効率化設備による設計一次エネルギー消費量の削減量
    E_E_CG_h = section2_2.get_E_E_CG_h(E_E_CG_h_d_t)

    # ---- 二次エネの計算 ----

    # 1時間当たりの設計消費電力量（二次）, kWh/h
    E_E_d_t = E_E_H_d_t + E_E_C_d_t + E_E_V_d_t + E_E_L_d_t + E_E_W_d_t + E_E_AP_d_t + E_E_CC_d_t - E_E_PV_h_d_t - E_E_CG_h_d_t

    # 1 年当たりの設計消費電力量（kWh/年）
    E_E = calc_E_E(E_E_H_d_t, E_E_C_d_t, E_E_CG_h_d_t, E_E_W_d_t, E_E_L_d_t, E_E_V_d_t, E_E_AP_d_t, E_E_CC_d_t, E_E_PV_d_t, E_E_PV_h_d_t, E_E_dmd_d_t, E_E_d_t)
    
    E_gen = (np.sum(E_E_PV_d_t) + np.sum(E_E_CG_gen_d_t)) * f_prim / 1000

    # 1 年当たりの設計ガス消費量（MJ/年）
    E_G = calc_E_G(E_G_H_d_t, E_G_C_d_t, E_G_W_d, E_G_CG_d_t, E_G_AP_d_t, E_G_CC_d_t, spec['A_A'])

    # 1 年当たりの設計灯油消費量（MJ/年）
    E_K = calc_E_K(E_K_H_d_t, E_K_C_d_t, E_K_W_d_t, E_K_CG_d_t,  E_K_AP_d_t, E_K_CC_d_t)

    E_E_gen = np.sum(E_E_PV_d_t + E_E_CG_gen_d_t)

    # 1年当たりのその他の設計一次エネルギー消費量
    E_M = np.sum(
        E_E_AP_d_t * f_prim / 1000 + E_G_AP_d_t + E_K_AP_d_t + E_M_AP_d_t
        + E_E_CC_d_t * f_prim / 1000 + E_G_CC_d_t + E_K_CC_d_t + E_M_CC_d_t
    )

    # 1年当たりのコージェネレーション設備による売電量に係るガス消費量の控除量 (MJ/yr) (20)
    # この値は1時間ごとには計算できない。
    E_G_CG_sell = section2_2.calc_E_G_CG_sell(E_CG_sell, E_E_CG_self, E_E_CG_h, E_G_CG_ded, e_BB_ave, Q_CG_h, has_CG)

    # 1年当たりのエネルギー利用効率化設備による設計一次エネルギー消費量の削減量 (MJ/yr) (14)
    # 次の E_S_h と E_S_sell を足す
    # E_S_h: 1年当たりのエネルギー利用効率化設備による発電量のうちの自家消費分に係る一次エネルギー消費量の控除量 (MJ/yr) (15)
    # E_S_sell: 1年当たりのコージェネレーション設備の売電量に係る設計一次エネルギー消費量の控除量 (MJ/yr) (16)
    #   E_S_sell = E_G_CG_sell
    #   1年当たりのコージェネレーション設備の売電量に係る設計一次エネルギー消費量の控除量 (MJ/yr) (16)
    # この値は1時間ごとには計算できない。
    E_S = np.sum(E_E_PV_h_d_t + E_E_CG_h_d_t) * f_prim / 1000 + E_G_CG_sell

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
    print('コージェネ (0.0) : ' + str(E_E_CG_h))
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


# 1 時間当たりの暖房設備の設計一次エネルギー消費量
def get_E_H_d_t(region, sol_region, A_A, A_MR, A_OR, A_env, mu_H, mu_C, Q, mode_H, H_A, spec_MR, spec_OR, spec_HS, mode_MR, mode_OR, CG, SHC,
                heating_flag_d, L_T_H_d_t_i, L_CS_d_t_i, L_CL_d_t_i):
    """1 時間当たりの暖房設備の設計一次エネルギー消費量

    Args:
      region(int): 省エネルギー地域区分
      sol_region(int): 年間の日射地域区分(1-5)
      A_A(float): 床面積の合計 (m2)
      A_MR(float): 主たる居室の床面積 (m2)
      A_OR(float): その他の居室の床面積 (m2)
      mode_H(str): 暖房方式
      H_A(dict): 暖房方式
      spec_MR(dict): 暖房機器の仕様
      spec_OR(dict): 暖房機器の仕様
      spec_HS(dict): 温水暖房機の仕様
      mode_MR(str): 主たる居室の運転方法 (連続運転|間歇運転)
      mode_OR(str): その他の居室の運転方法 (連続運転|間歇運転)
      CG(dict): コージェネレーションの機器
      SHC(dict): 集熱式太陽熱利用設備の仕様
      heating_flag_d(ndarray): 暖房日
      L_H_A_d_t(ndarray): 暖房負荷
      L_T_H_d_t_i(ndarray): 暖房区画i=1-5それぞれの暖房負荷
      L_CS_d_t_i(ndarray): 暖冷房区画iの 1 時間当たりの冷房顕熱負荷
      L_CL_d_t_i(ndarray): 暖冷房区画iの 1 時間当たりの冷房潜熱負荷
      A_env: param mu_H:
      mu_C: param Q:
      mu_H: param Q:
      Q: 

    Returns:
      ndarray: 1 時間当たりの暖房設備の設計一次エネルギー消費量

    """

    # 電気の量 1kWh を熱量に換算する係数
    f_prim = section2_1.get_f_prim()

    # 暖房設備の消費電力量（kWh/h）(6a)
    E_E_H_d_t = get_E_E_H_d_t(region, sol_region, A_A, A_MR, A_OR, A_env, mu_H, mu_C, Q, H_A, spec_MR, spec_OR, spec_HS,
                                mode_MR, mode_OR, CG, SHC, heating_flag_d, L_T_H_d_t_i, L_CS_d_t_i, L_CL_d_t_i)

    # 暖房設備のガス消費量（MJ/h）(6b)
    E_G_H_d_t = get_E_G_H_d_t(region, A_A, A_MR, A_OR, H_A, spec_MR, spec_OR, spec_HS, mode_MR, mode_OR, CG, L_T_H_d_t_i)

    # 暖房設備の灯油消費量（MJ/h）(6c)
    E_K_H_d_t = calc_E_K_H_d_t(region, A_A, A_MR, A_OR, H_A, spec_MR, spec_OR, spec_HS, mode_MR, mode_OR, CG, L_T_H_d_t_i)

    # 暖房設備のその他の燃料による一次エネルギー消費量（MJ/h）(6d)
    E_M_H_d_t = calc_E_M_H_d_t(region, A_A, A_MR, A_OR, H_A, spec_MR, spec_OR, spec_HS, L_T_H_d_t_i)

    # 暖房設備の未処理暖房負荷の設計一次エネルギー消費量相当値, MJ/h
    E_UT_H_d_t = calc_E_UT_H_d_t(region, A_A, A_MR, A_OR, A_env, mu_H, mu_C, Q, mode_H, H_A, spec_MR, spec_OR, spec_HS, mode_MR, mode_OR,
                                    CG, L_T_H_d_t_i, L_CS_d_t_i, L_CL_d_t_i)

    E_H_d_t = E_E_H_d_t * f_prim / 1000 + E_G_H_d_t + E_K_H_d_t + E_M_H_d_t + E_UT_H_d_t  # (3)

    return E_H_d_t, E_E_H_d_t, E_G_H_d_t, E_K_H_d_t, E_M_H_d_t, E_UT_H_d_t


def get_E_C_d_t(region, A_A, A_MR, A_OR, A_env, mu_H, mu_C, Q, C_A, C_MR, C_OR, L_H_d_t, L_CS_d_t, L_CL_d_t, mode_C):
    """1 時間当たりの冷房設備の設計一次エネルギー消費量 (4)

    Args:
      region(int): 省エネルギー地域区分
      A_A(float): 床面積の合計 (m2)
      A_MR(float): 主たる居室の床面積 (m2)
      A_OR(float): その他の居室の床面積 (m2)
      C_A(dict): 冷房方式
      C_MR(dict): 主たる居室の冷房機器
      C_OR(dict): その他の居室の冷房機器
      L_CS_A_d_t(ndarray): 冷房負荷
      L_CL_A_d_t(ndarray): 冷房負荷
      L_CS_d_t_i(ndarray): 暖冷房区画iの 1 時間当たりの冷房顕熱負荷
      L_CL_d_t_i(ndarray): 暖冷房区画iの 1 時間当たりの冷房潜熱負荷
      A_env: param mu_H:
      mu_C: param Q:
      L_H_d_t: param L_CS_d_t:
      L_CL_d_t: param mode_C:
      mu_H: param Q:
      L_CS_d_t: param mode_C:
      Q: 
      mode_C: 

    Returns:
      ndarray: 1 時間当たりの冷房設備の設計一次エネルギー消費量 (4)

    """
    # 電気の量 1kWh を熱量に換算する係数
    f_prim = section2_1.get_f_prim()

    E_E_C_d_t = section2_2.calc_E_E_C_d_t(region, A_A, A_MR, A_OR, A_env, mu_H, mu_C, Q, C_A, C_MR, C_OR, L_H_d_t, L_CS_d_t, L_CL_d_t)
    E_G_C_d_t = section2_2.calc_E_G_C_d_t()
    E_K_C_d_t = section2_2.calc_E_K_C_d_t()
    E_M_C_d_t = section2_2.calc_E_M_C_d_t()
    E_UT_C_d_t = section2_2.calc_E_UT_C_d_t(region, A_A, A_MR, A_OR, A_env, mu_H, mu_C, Q, C_A, C_MR, C_OR, L_H_d_t, L_CS_d_t, L_CL_d_t, mode_C)

    E_C_d_t = E_E_C_d_t * f_prim / 1000 + E_G_C_d_t + E_K_C_d_t + E_M_C_d_t + E_UT_C_d_t  # (5)

    return E_C_d_t, E_E_C_d_t, E_G_C_d_t, E_K_C_d_t, E_M_C_d_t, E_UT_C_d_t


# 1 年当たりの給湯設備（コージェネレーション設備を含む）の設計一次エネルギー消費量
def calc_E_W(
    E_E_H_d_t, E_E_C_d_t, E_E_V_d_t, E_E_L_d_t, E_E_AP_d_t,
    spec_MR, spec_OR, mode_MR, mode_OR, spec_HS, L_T_H_d_t_i, n_p, heating_flag_d, A_A, region, sol_region, spec_HW, SHC, CG, L_HWH, H_HS=None,
    A_MR=None, A_OR=None, Q=None, mu_H=None, mu_C=None, NV_MR=None, NV_OR=None, TS=None,
    r_A_ufvnt=None, HEX=None, underfloor_insulation=None):
    """1 年当たりの給湯設備（コージェネレーション設備を含む）の設計一次エネルギー消費量

    Args:
        n_p: 仮想居住人数
        heating_flag_d: 暖房日
        A_A(float): 床面積の合計 (m2)
        region(int): 省エネルギー地域区分
        sol_region(int): 年間の日射地域区分(1-5)
        HW(dict): 給湯機の仕様
        SHC(dict): 集熱式太陽熱利用設備の仕様
        CG(dict): コージェネレーションの機器
        H_A(dict, optional, optional): 暖房方式, defaults to None
        H_HS(dict, optional, optional): 温水暖房機の仕様, defaults to None
        C_A(dict, optional, optional): 冷房方式, defaults to None
        C_MR(dict, optional, optional): 主たる居室の冷房機器, defaults to None
        C_OR(dict, optional, optional): その他の居室の冷房機器, defaults to None
        V(dict, optional, optional): 換気設備仕様辞書, defaults to None
        L(dict, optional, optional): 照明設備仕様辞書, defaults to None
        A_MR(float, optional, optional): 主たる居室の床面積 (m2), defaults to None
        A_OR(float, optional, optional): その他の居室の床面積 (m2), defaults to None
        Q(float, optional, optional): 当該住戸の熱損失係数 (W/m2K), defaults to None
        mu_H(float, optional, optional): 断熱性能の区分݆における日射取得性能の区分݇の暖房期の日射取得係数, defaults to None
        mu_C(float, optional, optional): 断熱性能の区分݆における日射取得性能の区分݇の冷房期の日射取得係数, defaults to None
        NV_MR(float, optional, optional): 主たる居室における通風の利用における相当換気回数, defaults to None
        NV_OR(float, optional, optional): その他の居室における通風の利用における相当換気回数, defaults to None
        TS(bool, optional, optional): 蓄熱, defaults to None
        r_A_ufvnt(float, optional, optional): 床下換気, defaults to None
        HEX(dict, optional, optional): 熱交換器型設備仕様辞書, defaults to None
        underfloor_insulation(bool, optional, optional): 床下空間が断熱空間内である場合はTrue, defaults to None
        mode_H(str, optional, optional): 暖房方式, defaults to None
        mode_C(str, optional, optional): 冷房方式, defaults to None
        A_env: Default value = None)

    Returns:
        tuple: 1 年当たりの給湯設備（コージェネレーション設備を含む）の設計一次エネルギー消費量

    """

    # 1時間当たりの給湯設備の消費電力量, kWh/h
    E_E_W_d_t = section7_1.calc_E_E_W_d_t(n_p=n_p, L_HWH=L_HWH, heating_flag_d=heating_flag_d, region=region, sol_region=sol_region, HW=spec_HW, SHC=SHC)

    # 1時間当たりの給湯設備のガス消費量, MJ/h
    # 引数に A_A が指定されているが使用されていないので、None をわたすようにした。
    E_G_W_d_t = section7_1.calc_E_G_W_d_t(n_p=n_p, L_HWH=L_HWH, heating_flag_d=heating_flag_d, A_A=None, region=region, sol_region=sol_region, HW=spec_HW, SHC=SHC)

    # 1時間当たりの給湯設備の灯油消費量, MJ/h
    # 引数として L_HWH, A_A が指定されているが使用されていないのでNoneをわたした。
    E_K_W_d_t = section7_1.calc_E_K_W_d_t(n_p=n_p, L_HWH=None, heating_flag_d=heating_flag_d, A_A=None, region=region, sol_region=sol_region, HW=spec_HW, SHC=SHC)

    # 1時間当たりの給湯設備のその他の燃料による一次エネルギー消費量, MJ/h
    E_M_W_d_t = section7_1.get_E_M_W_d_t()
    
    # 電気の量 1kWh を熱量に換算する係数
    f_prim = get_f_prim()

    if spec_HW is None:
        return 0.0, np.zeros(24 * 365), np.zeros(24 * 365), \
               np.zeros(24 * 365), np.zeros(24 * 365), np.zeros(24 * 365), E_E_W_d_t, E_G_W_d_t, E_K_W_d_t, np.zeros(24 * 365), np.zeros(365*24)

    elif spec_HW['hw_type'] != 'コージェネレーションを使用する':
        E_W_d = E_E_W_d_t * f_prim / 1000 + E_G_W_d_t + E_K_W_d_t + E_M_W_d_t  # (9)

        # (8a)
        E_W = np.sum(E_W_d)

        return E_W, np.zeros(24 * 365), np.zeros(24 * 365), \
               np.zeros(24 * 365), np.zeros(24 * 365), np.zeros(24 * 365), E_E_W_d_t, E_G_W_d_t, E_K_W_d_t, np.zeros(24 * 365), np.zeros(365*24)
    else:

        # その他または設置しない場合
        spec_HW = section7_1.get_virtual_hotwater(region, HW)

        # 温水暖房負荷の計算
        if H_HS is not None:
            import pyhees.section4_1 as H

            # 暖房方式及び運転方法の区分
            spec_HS = H.get_virtual_heatsource(region, H_HS)

            L_T_H_d_t_i, _ = H.calc_L_H_d_t(region, sol_region, A_A, A_MR, A_OR, None, None, spec_MR, spec_OR, mode_MR,
                                            mode_OR, Q, mu_H, mu_C, NV_MR, NV_OR, TS, r_A_ufvnt, HEX, SHC, underfloor_insulation)
        else:
            spec_HS = None
            L_T_H_d_t_i = None

        # 1時間当たりの給湯設備の消費電力量 (s7-1 1)
        # E_E_W_d_t = section7_1.calc_E_E_W_d_t(n_p, L_T_H_d_t_i, heating_flag_d, region, sol_region, HW, SHC)

        # 1時間当たりの電力需要 (28)
        E_E_dmd_d_t = section2_2.get_E_E_dmd_d_t(E_E_H_d_t, E_E_C_d_t, E_E_V_d_t, E_E_L_d_t, E_E_W_d_t, E_E_AP_d_t)

        # ふろ機能の修正
        if spec_HW['hw_type'] is not None:
            bath_function = section7_1.get_normalized_bath_function(spec_HW['hw_type'], spec_HW['bath_function'])
        else:
            bath_function = None

        L_dashdash_k_d_t, L_dashdash_s_d_t, L_dashdash_w_d_t, L_dashdash_b1_d_t, L_dashdash_b2_d_t, L_dashdash_ba1_d_t, L_dashdash_ba2_d_t = calc_L_dashdash_d_t(spec_HW, heating_flag_d, n_p, region, sol_region, SHC, bath_function)

        # 1日当たりのコージェネレーション設備の一次エネルギー消費量
        E_G_CG_d_t, E_E_CG_gen_d_t, E_G_CG_ded, E_E_CG_self, Q_CG_h, E_E_TU_aux_d_t, e_BB_ave = \
            section8.calc_E_G_CG_d_t(bath_function, CG, E_E_dmd_d_t,
                            L_dashdash_k_d_t, L_dashdash_w_d_t, L_dashdash_s_d_t, L_dashdash_b1_d_t,
                            L_dashdash_b2_d_t,
                            L_dashdash_ba1_d_t, L_dashdash_ba2_d_t,
                            spec_HS, spec_MR, spec_OR, A_A, A_MR, A_OR, region, mode_MR, mode_OR,
                            L_T_H_d_t_i)

        # 1時間当たりのコージェネレーション設備の灯油消費量
        E_K_CG_d_t = np.zeros(365 * 24)

        # (8b)
        E_CG = np.sum(E_G_CG_d_t)

        return E_CG, E_E_CG_gen_d_t, E_E_TU_aux_d_t, E_G_CG_ded, e_BB_ave, Q_CG_h, E_E_W_d_t, E_G_W_d_t, E_K_W_d_t, E_G_CG_d_t, E_K_CG_d_t


def calc_L_dashdash_d_t(spec_HW, heating_flag_d, n_p, region, sol_region, SHC, bath_function):

    if spec_HW['hw_type'] is not None:

        # 給湯負荷の生成
        args = {
            'n_p': n_p,
            'region': region,
            'sol_region': sol_region,
            'has_bath': spec_HW['has_bath'],
            'bath_function': bath_function,
            'pipe_diameter': spec_HW['pipe_diameter'],
            'kitchen_watersaving_A': spec_HW['kitchen_watersaving_A'],
            'kitchen_watersaving_C': spec_HW['kitchen_watersaving_C'],
            'shower_watersaving_A': spec_HW['shower_watersaving_A'],
            'shower_watersaving_B': spec_HW['shower_watersaving_B'],
            'washbowl_watersaving_C': spec_HW['washbowl_watersaving_C'],
            'bath_insulation': spec_HW['bath_insulation']
        }
        if SHC is not None:
            if SHC['type'] == '液体集熱式':
                args.update({
                    'type': SHC['type'],
                    'ls_type': SHC['ls_type'],
                    'A_sp': SHC['A_sp'],
                    'P_alpha_sp': SHC['P_alpha_sp'],
                    'P_beta_sp': SHC['P_beta_sp'],
                    'W_tnk_ss': SHC['W_tnk_ss']
                })
            elif SHC['type'] == '空気集熱式':
                args.update({
                    'type': SHC['type'],
                    'hotwater_use': SHC['hotwater_use'],
                    'heating_flag_d': heating_flag_d,
                    'A_col': SHC['A_col'],
                    'P_alpha': SHC['P_alpha'],
                    'P_beta': SHC['P_beta'],
                    'V_fan_P0': SHC['V_fan_P0'],
                    'd0': SHC['d0'],
                    'd1': SHC['d1'],
                    'W_tnk_ass': SHC['W_tnk_ass']
                })
            else:
                raise ValueError(SHC['type'])

        hotwater_load = section7_1.calc_hotwater_load(**args)

        L_dashdash_k_d_t = hotwater_load['L_dashdash_k_d_t']
        L_dashdash_s_d_t = hotwater_load['L_dashdash_s_d_t']
        L_dashdash_w_d_t = hotwater_load['L_dashdash_w_d_t']
        L_dashdash_b1_d_t = hotwater_load['L_dashdash_b1_d_t']
        L_dashdash_b2_d_t = hotwater_load['L_dashdash_b2_d_t']
        L_dashdash_ba1_d_t = hotwater_load['L_dashdash_ba1_d_t']
        L_dashdash_ba2_d_t = hotwater_load['L_dashdash_ba2_d_t']

    return L_dashdash_k_d_t,L_dashdash_s_d_t,L_dashdash_w_d_t,L_dashdash_b1_d_t,L_dashdash_b2_d_t,L_dashdash_ba1_d_t,L_dashdash_ba2_d_t


def calc_E_L(A_A, A_MR, A_OR, L):
    """1 年当たりの照明設備の設計一次エネルギー消費量

    Args:
      A_A(float): 床面積の合計 (m2)
      A_MR(float): 主たる居室の床面積 (m2)
      A_OR(float): その他の居室の床面積 (m2)
      L(dict): 照明設備仕様辞書

    Returns:
      ndarray: 1 年当たりの照明設備の設計一次エネルギー消費量

    """
    
    # 電気の量 1kWh を熱量に換算する係数
    f_prim = get_f_prim()

    n_p = section2_2.get_n_p(A_A)

    E_E_L_d_t = section2_2.calc_E_E_L_d_t(n_p, A_A, A_MR, A_OR, L)

    E_L = np.sum(E_E_L_d_t) * f_prim / 1000  # (7)

    return E_L, E_E_L_d_t


def calc_E_V(A_A, V, HEX):
    """1 年当たりの機械換気設備の設計一次エネルギー消費量

    Args:
      A_A(float): 床面積の合計[m^2]
      V(dict): 換気設備仕様辞書
      HEX(dict): 熱交換器型設備仕様辞書

    Returns:
      float: 1 年当たりの機械換気設備の設計一次エネルギー消費量

    """
    
    # 電気の量 1kWh を熱量に換算する係数
    f_prim = get_f_prim()

    n_p = section2_2.get_n_p(A_A)

    E_E_V_d_t = section2_2.calc_E_E_V_d_t(n_p, A_A, V, HEX)

    # (6)
    E_V = np.sum(E_E_V_d_t) * f_prim / 1000

    return E_V, E_E_V_d_t


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
