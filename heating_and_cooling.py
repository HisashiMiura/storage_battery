from typing import Dict
import numpy as np

from pyhees import section2_2, section3_1, section3_2


def get01(spec: Dict):


    # 外皮の断熱性能の計算
    U_A, _, _, _, Q_dash, eta_H, eta_C, _ = section3_2.calc_insulation_performance(**spec['ENV'])
    
    # 熱損失係数
    Q = section3_1.get_Q(Q_dash)
    A_env = spec['ENV'].get('A_env')

    # 実質的な暖房機器の仕様を取得
    spec_MR, spec_OR = section2_2.get_virtual_heating_devices(
        region=spec['region'],
        H_MR=spec['H_MR'],
        H_OR=spec['H_OR']
    )

    # 暖房方式及び運転方法の区分
    mode_MR, mode_OR = section2_2.calc_heating_mode(
        region=spec['region'],
        H_MR=spec_MR,
        H_OR=spec_OR
    )

    # 暖房負荷の取得, MJ/h
    L_T_H_d_t_i, L_dash_H_R_d_t_i = section2_2.calc_heating_load(
        region=spec['region'],
        sol_region=spec['sol_region'],
        A_A=spec['A_A'],
        A_MR=spec['A_MR'],
        A_OR=spec['A_OR'],
        Q=Q,
        mu_H=eta_H,
        mu_C=eta_C,
        NV_MR=spec['NV_MR'],
        NV_OR=spec['NV_OR'],
        TS=spec['TS'],
        r_A_ufvnt=spec['r_A_ufvnt'],
        HEX=spec['HEX'],
        underfloor_insulation=spec['underfloor_insulation'],
        mode_H=spec['mode_H'],
        mode_C=spec['mode_C'],
        spec_MR=spec_MR,
        spec_OR=spec_OR,
        mode_MR=mode_MR,
        mode_OR=mode_OR,
        SHC=spec['SHC']
    )

    # 冷房負荷の取得, MJ/h
    L_CS_d_t, L_CL_d_t = section2_2.calc_cooling_load(
        region=spec['region'],
        A_A=spec['A_A'],
        A_MR=spec['A_MR'],
        A_OR=spec['A_OR'],
        Q=Q,
        mu_H=eta_H,
        mu_C=eta_C,
        NV_MR=spec['NV_MR'],
        NV_OR=spec['NV_OR'],
        r_A_ufvnt=spec['r_A_ufvnt'],
        underfloor_insulation=spec['underfloor_insulation'],
        mode_C=spec['mode_C'],
        mode_H=spec['mode_H'],
        mode_MR=mode_MR,
        mode_OR=mode_OR,
        TS=spec['TS'],
        HEX=spec['HEX']
    )
    
    # 1 時間当たりの冷房設備の設計一次エネルギー消費量, MJ/h
    E_C_d_t = section2_2.get_E_C_d_t(
        region=spec['region'],
        A_A=spec['A_A'],
        A_MR=spec['A_MR'],
        A_OR=spec['A_OR'],
        A_env=A_env,
        mu_H=eta_H,
        mu_C=eta_C,
        Q=Q,
        C_A=spec['C_A'],
        C_MR=spec['C_MR'],
        C_OR=spec['C_OR'],
        L_H_d_t=L_T_H_d_t_i,
        L_CS_d_t=L_CS_d_t,
        L_CL_d_t=L_CL_d_t,
        mode_C=spec['mode_C']
    )

    # 1 年当たりの冷房設備の設計一次エネルギー消費量, MJ/年
    E_C = np.sum(E_C_d_t)
    
    return L_T_H_d_t_i, L_dash_H_R_d_t_i, L_CS_d_t, L_CL_d_t, E_C
