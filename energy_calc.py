from typing import Dict
import numpy as np

from c_energy import Energy
from pyhees import section2_1, section2_2
from pyhees import section3_1, section3_2, section3_1_heatingday
from pyhees import section4_1
from pyhees import section7_1, section7_1_b
from pyhees import section10

def run(spec: Dict):
    """エネルギー消費量を計算する。

    Args:
        spec (Dict): 仕様（入力値）
    """

    # 電気の量 1kWh を熱量に換算する係数, kJ/kWh
    f_prim = section2_1.get_f_prim()

    # 仮想居住人数
    n_p = section2_2.get_n_p(A_A=spec['A_A'])

    # 熱損失係数, W/(m2K)
    # 暖房期の日射取得係数, (W/m2)/(W/m2)
    # 冷房期の日射取得係数, (W/m2)/(W/m2)
    # 外皮の面積の合計, m2
    Q, mu_H, mu_C, A_env = get_envelope(dict_env=spec["ENV"])

    # 実質的な暖房機器の仕様を取得
    spec_MR, spec_OR = section2_2.get_virtual_heating_devices(spec['region'], spec['H_MR'], spec['H_OR'])

    # 暖房方式及び運転方法の区分
    mode_MR, mode_OR = section2_2.calc_heating_mode(region=spec['region'], H_MR=spec_MR, H_OR=spec_OR)

    # 暖房負荷の取得
    L_T_H_d_t_i, L_dash_H_R_d_t_i = section2_2.calc_heating_load(
        spec['region'], spec['sol_region'],
        spec['A_A'], spec['A_MR'], spec['A_OR'],
        Q, mu_H, mu_C, spec['NV_MR'], spec['NV_OR'], spec['TS'], spec['r_A_ufvnt'], spec['HEX'],
        spec['underfloor_insulation'], spec['mode_H'], spec['mode_C'],
        spec_MR, spec_OR, mode_MR, mode_OR, spec['SHC'])

    # 実質的な温水暖房機の仕様を取得
    spec_HS = section2_2.get_virtual_heatsource(spec['region'], spec['H_HS'])

    # 暖房日の計算
    if spec['SHC'] is not None and spec['SHC']['type'] == '空気集熱式':
        heating_flag_d = section3_1_heatingday.get_heating_flag_d(L_dash_H_R_d_t_i)
    else:
        heating_flag_d = None

    # 冷房負荷の取得
    L_CS_d_t, L_CL_d_t = \
        section2_2.calc_cooling_load(spec['region'], spec['A_A'], spec['A_MR'], spec['A_OR'], Q, mu_H, mu_C,
                          spec['NV_MR'], spec['NV_OR'], spec['r_A_ufvnt'], spec['underfloor_insulation'],
                          spec['mode_C'], spec['mode_H'], mode_MR, mode_OR, spec['TS'], spec['HEX'])

    E_E_H_d_t, E_G_H_d_t, E_K_H_d_t, E_M_H_d_t, E_UT_H_d_t = get_E_H_d_t(
        spec['region'], spec['sol_region'], spec['A_A'], spec['A_MR'], spec['A_OR'],
        A_env, mu_H, mu_C, Q,
        spec['mode_H'],
        spec['H_A'], spec_MR, spec_OR, spec_HS, mode_MR, mode_OR, spec['CG'], spec['SHC'],
        heating_flag_d, L_T_H_d_t_i, L_CS_d_t, L_CL_d_t)

    # 1 時間当たりの冷房設備の設計一次エネルギー消費量 (4)
    E_E_C_d_t, E_G_C_d_t, E_K_C_d_t, E_M_C_d_t, E_UT_C_d_t =get_E_C_d_t(
        spec['region'], spec['A_A'], spec['A_MR'], spec['A_OR'],
        A_env, mu_H, mu_C, Q,
        spec['C_A'], spec['C_MR'], spec['C_OR'],
        L_T_H_d_t_i, L_CS_d_t, L_CL_d_t, spec['mode_C'])

    E_E_V_d_t = section2_2.calc_E_E_V_d_t(n_p, spec['A_A'], spec['V'], spec['HEX'])

    E_E_L_d_t = section2_2.calc_E_E_L_d_t(n_p, spec['A_A'], spec['A_MR'], spec['A_OR'], spec['L'])

    # 温水暖房負荷の計算
    L_HWH = section2_2.calc_L_HWH(spec['A_A'], spec['A_MR'], spec['A_OR'], spec['HEX'], spec['H_HS'], spec['H_MR'],
                           spec['H_OR'], Q, spec['SHC'], spec['TS'], mu_H, mu_C, spec['NV_MR'], spec['NV_OR'],
                           spec['r_A_ufvnt'], spec['region'], spec['sol_region'], spec['underfloor_insulation'],
                           spec['CG'])

    # その他または設置しない場合、Dict HW にデフォルト設備を上書きしたものを取得する。
    # 設置する場合は HW と spec_HW は同じ。
    # spec_HW は HW の DeepCopy
    spec_HW = section7_1_b.get_virtual_hotwater(spec['region'], spec['HW'])

    # 1時間当たりの給湯設備の消費電力量, kWh/h
    # 給湯設備が無い場合・コージェネレーションの場合は0とする。
    E_E_W_d_t = section7_1.calc_E_E_W_d_t(n_p=n_p, L_HWH=L_HWH, heating_flag_d=heating_flag_d, region=spec['region'], sol_region=spec['sol_region'], HW=spec_HW, SHC=spec['SHC'])

    # 1時間当たりの給湯設備のガス消費量, MJ/h
    # 引数に A_A が指定されているが使用されていないので、None をわたすようにした。
    E_G_W_d_t = section7_1.calc_E_G_W_d_t(n_p=n_p, L_HWH=L_HWH, heating_flag_d=heating_flag_d, A_A=None, region=spec['region'], sol_region=spec['sol_region'], HW=spec_HW, SHC=spec['SHC'])

    # 1時間当たりの給湯設備の灯油消費量, MJ/h
    # 引数として L_HWH, A_A が指定されているが使用されていないのでNoneをわたした。
    E_K_W_d_t = section7_1.calc_E_K_W_d_t(n_p=n_p, L_HWH=None, heating_flag_d=heating_flag_d, A_A=None, region=spec['region'], sol_region=spec['sol_region'], HW=spec_HW, SHC=spec['SHC'])

    # 1時間当たりの給湯設備のその他の燃料による一次エネルギー消費量, MJ/h
    E_M_W_d_t = section7_1.get_E_M_W_d_t()
    
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

    e = Energy(f_prim=section2_1.get_f_prim())

    e.E_E_Hs = E_E_H_d_t
    e.E_G_Hs = E_G_H_d_t
    e.E_K_Hs = E_K_H_d_t
    e.E_M_Hs = E_M_H_d_t
    e.E_UT_Hs = E_UT_H_d_t

    e.E_E_Cs = E_E_C_d_t
    e.E_G_Cs = E_G_C_d_t
    e.E_K_Cs = E_K_C_d_t
    e.E_M_Cs = E_M_C_d_t
    e.E_UT_Cs = E_UT_C_d_t

    e.E_E_Vs = E_E_V_d_t

    e.E_E_Ls = E_E_L_d_t

    e.E_E_Ws = E_E_W_d_t
    e.E_G_Ws = E_G_W_d_t
    e.E_K_Ws = E_K_W_d_t
    e.E_M_Ws = E_M_W_d_t

    e.E_E_APs = E_E_AP_d_t
    e.E_G_APs = E_G_AP_d_t
    e.E_K_APs = E_K_AP_d_t
    e.E_M_APs = E_M_AP_d_t

    e.E_E_CCs = E_E_CC_d_t
    e.E_G_CCs = E_G_CC_d_t
    e.E_K_CCs = E_K_CC_d_t
    e.E_M_CCs = E_M_CC_d_t

    return spec_HW, n_p, f_prim, spec_MR, spec_OR, mode_MR, mode_OR, L_T_H_d_t_i, spec_HS, heating_flag_d, e


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

    # 暖房設備の消費電力量（kWh/h）(6a)
    E_E_H_d_t = section4_1.get_E_E_H_d_t(region, sol_region, A_A, A_MR, A_OR, A_env, mu_H, mu_C, Q, H_A, spec_MR, spec_OR, spec_HS,
                                mode_MR, mode_OR, CG, SHC, heating_flag_d, L_T_H_d_t_i, L_CS_d_t_i, L_CL_d_t_i)

    # 暖房設備のガス消費量（MJ/h）(6b)
    E_G_H_d_t = section4_1.get_E_G_H_d_t(region, A_A, A_MR, A_OR, H_A, spec_MR, spec_OR, spec_HS, mode_MR, mode_OR, CG, L_T_H_d_t_i)

    # 暖房設備の灯油消費量（MJ/h）(6c)
    E_K_H_d_t = section4_1.calc_E_K_H_d_t(region, A_A, A_MR, A_OR, H_A, spec_MR, spec_OR, spec_HS, mode_MR, mode_OR, CG, L_T_H_d_t_i)

    # 暖房設備のその他の燃料による一次エネルギー消費量（MJ/h）(6d)
    E_M_H_d_t = section4_1.calc_E_M_H_d_t(region, A_A, A_MR, A_OR, H_A, spec_MR, spec_OR, spec_HS, L_T_H_d_t_i)

    # 暖房設備の未処理暖房負荷の設計一次エネルギー消費量相当値, MJ/h
    E_UT_H_d_t = section4_1.calc_E_UT_H_d_t(region, A_A, A_MR, A_OR, A_env, mu_H, mu_C, Q, mode_H, H_A, spec_MR, spec_OR, spec_HS, mode_MR, mode_OR,
                                    CG, L_T_H_d_t_i, L_CS_d_t_i, L_CL_d_t_i)

    return E_E_H_d_t, E_G_H_d_t, E_K_H_d_t, E_M_H_d_t, E_UT_H_d_t


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

    E_E_C_d_t = section2_2.calc_E_E_C_d_t(region, A_A, A_MR, A_OR, A_env, mu_H, mu_C, Q, C_A, C_MR, C_OR, L_H_d_t, L_CS_d_t, L_CL_d_t)
    E_G_C_d_t = section2_2.calc_E_G_C_d_t()
    E_K_C_d_t = section2_2.calc_E_K_C_d_t()
    E_M_C_d_t = section2_2.calc_E_M_C_d_t()
    E_UT_C_d_t = section2_2.calc_E_UT_C_d_t(region, A_A, A_MR, A_OR, A_env, mu_H, mu_C, Q, C_A, C_MR, C_OR, L_H_d_t, L_CS_d_t, L_CL_d_t, mode_C)

    return E_E_C_d_t, E_G_C_d_t, E_K_C_d_t, E_M_C_d_t, E_UT_C_d_t

