import numpy as np
import yaml
import pandas as pd
import math
from typing import Union, Tuple

from battery_logger import BatteryLogger

# 5. 太陽光発電設備による発電量のうちの自家消費分・売電分・充電分および蓄電設備による放電量のうちの自家消費分

def get_E_E_PV_h(E_E_srpl: float, E_E_PV_max_sup: float, E_E_dmd_incl: float, SC: bool) -> float:
    """1 時間当たりの太陽光発電設備による発電量のうちの自家消費分 (kWh/h)

    Args:
        E_E_srpl (float): 1 時間当たりの余剰電力量 (kWh/h)
        E_E_PV_max_sup (float): 1 時間当たりの太陽光発電設備による最大供給可能電力量の分電盤側における換算値 (kWh/h)
        E_E_dmd_incl (float): 1 時間当たりの蓄電設備の補機の消費電力量を含む電力需要 (kWh/h)
        SC (bool): 系統連系または独立運転の区分 (系統連系=True)

    Returns:
        float: 1 時間当たりの太陽光発電設備による発電量のうちの自家消費分 (kWh/h)
    """
    
    # 系統連携運転時の場合
    if SC:
        if E_E_srpl <= 0:
            # (1-1) 太陽光発電設備による発電量が住戸内の電力需要量以下である場合
            return E_E_PV_max_sup
        else:
            # (1-2) 太陽光発電設備による発電量が住戸内の電力需要を超える場合
            return E_E_dmd_incl
    
    # 独立運転時の場合
    else:
        if E_E_srpl <= 0:
            # (1-3) 太陽光発電設備による発電量が住戸内の電力需要量以下である場合
            return E_E_PV_max_sup
        else:
            # (1-4) 太陽光発電設備による発電量が住戸内の電力需要を超える場合
            return E_E_dmd_incl


def get_E_E_PV_sell(E_E_srpl: float, E_E_PV_chg: float, SC: bool) -> float:
    """1時間当たりの太陽光発電設備による発電量のうちの売電分 (kWh/h)

    Args:
        E_E_srpl (float): 1 時間当たりの余剰電力量 (kWh/h)
        E_E_PV_chg (float): 1時間当たりの太陽光発電設備による発電量の内の充電分の分電盤側における換算値 (kWh/h)
        SC (bool): 系統連系または独立運転の区分 (系統連系=True)

    Returns:
        float: 1時間当たりの太陽光発電設備による発電量のうちの売電分 (kWh/h)
    """
    # 系統連携運転時の場合
    if SC:
        if E_E_srpl <= 0:
            # (2-1) 太陽光発電設備による発電量が住戸内の電力需要量以下である場合
            return 0.0
        else:
            # (2-2) 太陽光発電設備による発電量が住戸内の電力需要を超える場合
            return E_E_srpl - E_E_PV_chg

    # 独立運転時の場合
    else:
        if E_E_srpl <= 0:
            # (2-3) 太陽光発電設備による発電量が住戸内の電力需要量以下である場合
            return 0.0
        else:
            # (2-4) 太陽光発電設備による発電量が住戸内の電力需要を超える場合
            return 0.0


def get_E_E_PV_chg(E_E_srpl: float, E_E_SB_max_chg: float, SC: bool) -> float:
    """ 1時間当たりの太陽光発電設備による発電量のうちの充電分の分電盤側における換算値 (kWh/h)

    Args:
        E_E_srpl (float): 1 時間当たりの余剰電力量 (kWh/h)
        E_E_SB_max_chg (float): 1時間当たりの蓄電池ユニットによる最大充電可能電力量の分電盤側における換算値 (kWh/h)
        SC (bool): 系統連系または独立運転の区分 (系統連系=True)

    Returns:
        float: 1時間当たりの太陽光発電設備による発電量のうちの充電分の分電盤側における換算値 (kWh/h)
    """
    # 系統連携運転時の場合
    if SC:
        if E_E_srpl <= 0:
            # (3-1) 太陽光発電設備による発電量が住戸内の電力需要量以下である場合
            return 0.0
        else:
            # (3-2) 太陽光発電設備による発電量が住戸内の電力需要を超える場合
            return min(E_E_srpl, E_E_SB_max_chg)

    # 独立運転時の場合
    else:
        if E_E_srpl <= 0:
            # (3-3) 太陽光発電設備による発電量が住戸内の電力需要量以下である場合
            return 0.0
        else:
            # (3-4) 太陽光発電設備による発電量が住戸内の電力需要を超える場合
            return min(E_E_srpl, E_E_SB_max_chg)


def get_E_E_PSS_h(E_E_srpl: float, E_E_dmd_incl: float, E_E_PSS_max_sup: float, E_E_PV_h: float, SC: bool) -> float:
    """1時間当たりの蓄電設備による放電量のうちの自家消費分 (kWh/h)

    Args:
        E_E_srpl (float): 1 時間当たりの余剰電力量 (kWh/h)
        E_E_dmd_incl (float): 1 時間当たりの蓄電設備の補機の消費電力量を含む電力需要 (kWh/h)
        E_E_PSS_max_sum (float): 1時間当たりの蓄電設備による最大供給可能電力量の分電盤側における換算値 (kWh/h)
        SC (bool): 系統連系または独立運転の区分 (系統連系=True)

    Returns:
        float: 1時間当たりの蓄電設備による放電量のうちの自家消費分 (kWh/h)
    """
    # 系統連携運転時の場合
    if SC:
        if E_E_srpl <= 0:
            # (4-1) 太陽光発電設備による発電量が住戸内の電力需要量以下である場合
            return min(E_E_dmd_incl, E_E_PSS_max_sup) - E_E_PV_h
        else:
            # (4-2) 太陽光発電設備による発電量が住戸内の電力需要を超える場合
            return 0.0
    else:
        # 独立運転時の場合
        if E_E_srpl <= 0:
            # (4-3) 太陽光発電設備による発電量が住戸内の電力需要量以下である場合
            return min(E_E_dmd_incl, E_E_PSS_max_sup) - E_E_PV_h
        else:
            # (4-4) 太陽光発電設備による発電量が住戸内の電力需要を超える場合
            return 0.0


# 6. 最大供給可能電力量および余剰電力量


def get_E_E_PSS_max_sup(E_E_PV_max_sup: float, E_E_SB_max_sup: float) -> float:
    """1時間当たりの蓄電設備による最大供給可能電力量の分電盤側における換算値 (kWh/h)

    Args:
        E_E_PV_max_sup (float): 1時間当たりの太陽光発電設備による最大供給可能電力量の分電盤側における換算値 (kWh/h)
        E_E_SB_max_sup (float): 1時間当たりの蓄電池ユニットによる最大供給可能電力量の分電盤側における換算値 (kWh/h)

    Returns:
        float: 1時間当たりの蓄電設備による最大供給可能電力量の分電盤側における換算値 (kWh/h)
    """
    return E_E_PV_max_sup + E_E_SB_max_sup


def get_E_E_srpl(E_E_PV_max_sup: float, E_E_dmd_incl: float) -> float:
    """ 1 時間当たりの余剰電力量 (kWh/h)

    Args:
        E_E_PV_max_sup (float): 1時間当たりの太陽光発電設備による最大供給可能電力量の分電盤側における換算値 (kWh/h)
        E_E_dmd_incl (float): 1 時間当たりの蓄電設備の補機の消費電力量を含む電力需要 (kWh/h)

    Returns:
        float:  1 時間当たりの余剰電力量 (kWh/h)
    """
    return max(E_E_PV_max_sup - E_E_dmd_incl, 0)


def get_E_E_dmd_incl(E_E_dmd_excl: float, E_E_aux_PSS: float) -> float:
    """1 時間当たりの蓄電設備の補機の消費電力量を含む電力需要 (kWh/h)

    Args:
        E_E_dmd_excl (float): 1時間当たりの蓄電設備の補機の消費電力量を除く電力需要 (kWh/h)
        E_E_aux_PSS (float): １時間あたりの蓄電設備の補機の消費電力量 (kWh/h)

    Returns:
        float: 1 時間当たりの蓄電設備の補機の消費電力量を含む電力需要 (kWh/h)
    """
    return E_E_dmd_excl + E_E_aux_PSS


# 7. 補機の消費電力


def get_E_E_aux_PSS(E_E_aux_PCS: float, E_E_aux_others: float) -> float:
    """１時間あたりの蓄電設備の補機の消費電力量 (kWh/h)

    Args:
        E_E_aux_PCS (float): 1時間当たりのパワーコンディショナの補機の消費電力量 (kWh/h)
        E_E_aux_others (float): 1時間当たりの表示・計測・操作ユニット等の消費電力量 (kWh/h)

    Returns:
        float: １時間あたりの蓄電設備の補機の消費電力量 (kWh/h)
    """
    return E_E_aux_PCS + E_E_aux_others


# 8. パワーコンディショナ（ハイブリット一体型）


# 8.1 太陽光発電設備による発電量のうちの充電分

def get_E_dash_dash_E_PV_chg(E_E_PV_chg, E_dash_dash_E_srpl, E_E_srpl, E_dash_dash_E_in_rtd_PVtoSB, alpha_PVtoSB, beta_PVtoSB, eta_ce_lim_PVtoSB):
    """1時間当たりの太陽光発電設備による発電量のうちの充電分 (kWh/h)

    Args:
        E_E_PV_chg (float): 1時間当たりの太陽光発電設備による発電量のうちの充電分の分電盤側における換算値 (kWh/h)
        E_dash_dash_E_srpl (float): 1時間当たりの余剰電力量の太陽光発電設備側における換算値 (kWh/h)
        E_E_srpl (float): 1時間当たりの余剰電力量 (kWh/h)
        E_dash_dash_E_in_rtd_PVtoSB (float): 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの太陽光発電設備側における定格入力電力量 (kWh/h)
        alpha_PVtoSB (float): 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の傾き (-)
        beta_PVtoSB (float): 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の切片 (-)
        eta_ce_lim_PVtoSB (float): 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの合成変換効率の下限 (-)

    Returns:
        float: 1時間当たりの太陽光発電設備による発電量のうちの充電分 (kWh/h)
    """
    if E_E_srpl <= 0:
        eta_ce = eta_ce_lim_PVtoSB
    else:
        eta_ce = E_dash_dash_E_srpl / E_E_srpl

    E_dash_dash_E_PV_chg = \
        f_E_dash_dash_out_PVtoSB(E_E_PV_chg * eta_ce, E_dash_dash_E_in_rtd_PVtoSB, alpha_PVtoSB, beta_PVtoSB, eta_ce_lim_PVtoSB)

    return E_dash_dash_E_PV_chg

# 8.2 余剰電力量の太陽光発電設備側における換算値


def get_E_dash_dash_E_srpl(E_E_srpl: float, E_dash_dash_E_in_rtd_PVtoDB: float, alpha_PVtoDB: float, beta_PVtoDB: float) -> float:
    """1時間当たりの余剰電力量の太陽光発電設備側における換算値 (kWh/h)

    Args:
        E_E_srpl (float): 1時間当たりの余剰電力量 (kWh/h)
        E_dash_dash_E_in_rtd_PVtoDB (float): 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの太陽光発電設備側における定格入力電力量 (kWh/h)
        alpha_PVtoDB (float): 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の傾き (-)
        beta_PVtoDB (float): 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の切片 (-)

    Returns:
        float: 1時間当たりの余剰電力量の太陽光発電設備側における換算値 (kWh/h)
    """
    return f_E_dash_dash_in_PVtoDB(E_E_srpl, E_dash_dash_E_in_rtd_PVtoDB, alpha_PVtoDB, beta_PVtoDB)


# 8.3 蓄電池ユニットによる放電量のうちの供給分



def get_E_dash_dash_E_SB_sup(E_E_SB_sup: float, E_dash_dash_E_in_rtd_SBtoDB: float, alpha_SBtoDB: float, beta_SBtoDB: float) -> float:
    """1時間当たりの蓄電池ユニットによる放電量のうちの供給分 (kWh/h)

    Args:
        E_E_SB_sup (float): 1時間当たりの蓄電池ユニットによる放電量のうちの供給分の分電盤側における換算値 (kWh/h)
        E_dash_dash_E_in_rtd_SBtoDB (float): 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの蓄電池ユニット側における定格入力電力量 (kWh/h)
        alpha_SBtoDB (float): 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の傾き (-)
        beta_SBtoDB (float): 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の切片 (-)

    Returns:
        float: 1時間当たりの蓄電池ユニットによる放電量のうちの供給分 (kWh/h)
    """
    return f_E_dash_dash_in_SBtoDB(E_E_SB_sup, E_dash_dash_E_in_rtd_SBtoDB, alpha_SBtoDB, beta_SBtoDB)


def get_E_E_SB_sup(E_E_PSS_h: float) -> float:
    """1時間当たりの蓄電池ユニットによる放電量のうちの供給分の分電盤側における換算値 (kWh/h)

    Args:
        E_E_PSS_h (float): 1時間当たりの蓄電設備による放電量のうちの自家消費分 (kWh/h)

    Returns:
        float: 1時間当たりの蓄電池ユニットによる放電量のうちの供給分の分電盤側における換算値 (kWh/h)
    """
    return E_E_PSS_h


# 8.4 最大供給可能電力量の分電盤側における換算値


def get_E_E_PV_max_sup(E_dash_dash_E_PV_max_sup: float, E_dash_dash_E_in_rtd_PVtoDB: float, alpha_PVtoDB: float, beta_PVtoDB: float, eta_ce_lim_PVtoDB: float) -> float:
    """1時間当たりの太陽光発電設備による最大供給可能電力量の分電盤側における換算値 (kWh/h)

    Args:
        E_dash_dash_E_PV_max_sup (float): 1時間当たりの太陽光発電設備による最大供給可能電力量 (kWh/h)
        E_dash_dash_E_in_rtd_PVtoDB (float): 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの太陽光発電設備側における定格入力電力量 (kWh/h)
        alpha_PVtoDB (float): 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の傾き (-)
        beta_PVtoDB (float): 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の切片 (-)
        eta_ce_lim_PVtoDB (float): 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの合成変換効率の下限 (-)

    Returns:
        float: 1時間当たりの太陽光発電設備による最大供給可能電力量の分電盤側における換算値 (kWh/h)
    """
    if E_dash_dash_E_PV_max_sup > 0:
        return f_E_out_PVtoDB(E_dash_dash_E_PV_max_sup, E_dash_dash_E_in_rtd_PVtoDB, alpha_PVtoDB, beta_PVtoDB, eta_ce_lim_PVtoDB)
    else:
        return 0.0


def get_E_E_SB_max_sup(E_dash_dash_E_SB_max_sup: float, E_dash_dash_E_in_rtd_SBtoDB: float, alpha_SBtoDB: float, beta_SBtoDB: float, eta_ce_lim_SBtoDB: float) -> float:
    """1時間当たりの蓄電池ユニットによる最大供給可能電力量の分電盤側における換算値 (kWh/h)

    Args:
        E_dash_dash_E_SB_max_sup (float): 1時間当たりの蓄電池ユニットによる最大供給可能電力量 (kWh/h)
        E_dash_dash_E_in_rtd_SBtoDB (float): 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの蓄電池ユニット側における定格入力電力量 (kWh/h)
        alpha_SBtoDB (float): 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の傾き (-)
        beta_SBtoDB (float): 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の切片 (-)
        eta_ce_lim_SBtoDB (float): 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの合成変換効率の下限 (-)

    Returns:
        float: 1時間当たりの蓄電池ユニットによる最大供給可能電力量の分電盤側における換算値 (kWh/h)
    """
    if E_dash_dash_E_SB_max_sup > 0:
        return f_E_out_SBtoDB(E_dash_dash_E_SB_max_sup, E_dash_dash_E_in_rtd_SBtoDB, alpha_SBtoDB, beta_SBtoDB, eta_ce_lim_SBtoDB)
    else:
        return 0.0


def get_E_dash_dash_E_PV_max_sup(E_dash_dash_E_PV_gen: float) -> float:
    """1時間当たりの太陽光発電設備による最大供給可能電力量 (kWh/h)

    Args:
        E_dash_dash_E_PV_gen (float): 1 時間当たりの太陽光発電設備による発電量 (kWh/h)

    Returns:
        float: 1時間当たりの太陽光発電設備による最大供給可能電力量 (kWh/h)
    """
    return E_dash_dash_E_PV_gen


def get_E_dash_dash_E_SB_max_sup(E_dash_dash_E_SB_max_dchg: float) -> float:
    """1時間当たりの蓄電池ユニットによる最大供給可能電力量 (kWh/h)

    Args:
        E_dash_dash_E_SB_max_dchg (float): 蓄電池ユニットによる最大放電可能電力量 (kWh/h)

    Returns:
        float: 1時間当たりの蓄電池ユニットによる最大供給可能電力量 (kWh/h)
    """
    return E_dash_dash_E_SB_max_dchg


# 8.5 最大充電可能電力量の分電盤側における換算値


def get_E_E_SB_max_chg(E_dash_dash_E_SB_max_chg: float, E_E_srpl: float, E_dash_dash_E_srpl: float, E_dash_dash_E_in_rtd_PVtoSB: float, alpha_PVtoSB: float, beta_PVtoSB: float, eta_ce_lim_PVtoSB: float) -> float:
    """1時間当たりの蓄電池ユニットによる最大充電可能電力量の分電盤側における換算値 (kWh/h)

    Args:
        E_dash_dash_E_SB_max_chg (float): 蓄電池ユニットによる最大充電可能電力量 (kWh/h)
        E_E_srpl (float): 1時間当たりの余剰電力量 (kWh/h)
        E_dash_dash_E_srpl (float): 1時間当たりの余剰電力量の太陽光発電設備側における換算値 (kWh/h)
        E_dash_dash_E_in_rtd_PVtoSB (float): 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの太陽光発電設備側における定格入力電力量 (kWh/h)
        alpha_PVtoSB (float): 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の傾き (-)
        beta_PVtoSB (float): 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の切片 (-)
        eta_ce_lim_PVtoDB (float): 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの合成変換効率の下限 (-)

    Returns:
        float: 1時間当たりの蓄電池ユニットによる最大充電可能電力量の分電盤側における換算値 (kWh/h)
    """
    if E_E_srpl == 0:
        return eta_ce_lim_PVtoSB
    return f_E_dash_dash_in_PVtoSB(E_dash_dash_E_SB_max_chg, E_dash_dash_E_in_rtd_PVtoSB, alpha_PVtoSB, beta_PVtoSB) * E_E_srpl / E_dash_dash_E_srpl


# 8.6  出力電力量および入力電力量を求める関数


# 8.6.1 太陽光発電設備から分電盤へ電力を送る場合


def f_E_out_PVtoDB(x_E_in: float, E_dash_dash_E_in_rtd_PVtoDB: float, alpha_PVtoDB: float, beta_PVtoDB: float, eta_ce_lim_PVtoDB: float) -> float:
    """太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの太陽光発電設備側における入力電力量から分電盤側における出力電力量を求める関数

    Args:
        x_E_in (float): 関数の引数(入力電力量) (kWh/h)
        E_dash_dash_E_in_rtd_PVtoDB (float): 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの太陽光発電設備側における定格入力電力量 (kWh/h)
        alpha_PVtoDB (float): 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の傾き (-)
        beta_PVtoDB (float): 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の切片 (-)
        eta_ce_lim_PVtoDB (float): 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの合成変換効率の下限 (-)
    
    Returns:
        float: 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの分電盤側における出力電力量 (kWh/h)
    """
    eta_ce_PVtoDB = get_eta_ce_PVtoDB(x_E_in, E_dash_dash_E_in_rtd_PVtoDB, alpha_PVtoDB, beta_PVtoDB, eta_ce_lim_PVtoDB)
    return eta_ce_PVtoDB * min(x_E_in, E_dash_dash_E_in_rtd_PVtoDB)


def get_eta_ce_PVtoDB(x_E_in: float, E_dash_dash_E_in_rtd_PVtoDB: float, alpha_PVtoDB: float, beta_PVtoDB: float, eta_ce_lim_PVtoDB: float) -> float:
    """太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの合成変換効率 (-)

    Args:
        x_E_in (float): 関数の引数(入力電力量) (kWh/h)
        E_dash_dash_E_in_rtd_PVtoDB (float): 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの太陽光発電設備側における定格入力電力量 (kWh/h)
        alpha_PVtoDB (float): 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の傾き (-)
        beta_PVtoDB (float): 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の切片 (-)
        eta_ce_lim_PVtoDB (float): 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの合成変換効率の下限 (-)

    Returns:
        float: 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの合成変換効率 (-)
    """
    eta_ce_PVtoDB = \
        f_eta_ec(x_E_in, E_dash_dash_E_in_rtd_PVtoDB, alpha_PVtoDB, beta_PVtoDB, eta_ce_lim_PVtoDB)
    return eta_ce_PVtoDB


def f_E_dash_dash_in_PVtoDB(x_E_out: float, E_dash_dash_E_in_rtd_PVtoDB: float, alpha_PVtoDB: float, beta_PVtoDB: float) -> float:
    """太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの蓄電池ユニット側における出力電力量から太陽光発電設備側における入力電力量を逆算する関数
    
    Args:
        x_E_out (float): 関数の引数 (出力電力量) (kWh/h)
        E_dash_dash_E_in_rtd_PVtoDB (float): 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの太陽光発電設備側における定格入力電力量 (kWh/h)
        alpha_PVtoDB (float): 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の傾き (-)
        beta_PVtoDB (float): 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の切片 (-)

    Returns:
        float: 太陽光発電設備から分電盤へ電力を送る場合のパワーコンディショナの太陽光発電設備側における入力電力量 (kWh/h)
    """
    return f_E_in(x_E_out, E_dash_dash_E_in_rtd_PVtoDB, alpha_PVtoDB, beta_PVtoDB)


# 8.6.2 太陽光発電設備から蓄電池ユニットへ電力を送る場合


def f_E_dash_dash_out_PVtoSB(x_E_in: float, E_dash_dash_E_in_rtd_PVtoSB: float, alpha_PVtoSB: float, beta_PVtoSB: float, eta_ce_lim_PVtoSB: float) -> float:
    """太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの太陽光発電設備側における入力電力量から蓄電池ユニット側における出力電力量を求める関数

    Args:
        x_E_in (float): 関数の引数 (入力電力量) (kWh/h)
        E_dash_dash_E_in_rtd_PVtoSB (float): 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの太陽光発電設備側における定格入力電力量 (kWh/h)
        alpha_PVtoSB (float): 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の傾き (-)
        beta_PVtoSB (float): 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の切片 (-)
        eta_ce_lim_PVtoSB (float): 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの合成変換効率の下限 (-)

        E_E_PV_chg (float): 1時間当たりの太陽光発電設備による発電量のうちの充電分の分電盤側における換算値 (kWh/h)
        E_dash_dash_E_srpl (float): 1時間当たりの余剰電力量の太陽光発電設備側における換算値 (kWh/h)
        E_E_srpl (float): 1時間当たりの余剰電力量 (kWh/h)

    Returns:
        float: 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの蓄電池ユニット側における出力電力量 (kWh/h)
    """
    eta_ce_PVtoSB = get_eta_ce_PVtoSB(x_E_in, E_dash_dash_E_in_rtd_PVtoSB, alpha_PVtoSB, beta_PVtoSB, eta_ce_lim_PVtoSB)

    return eta_ce_PVtoSB * min(x_E_in, E_dash_dash_E_in_rtd_PVtoSB)


def get_eta_ce_PVtoSB(x_E_in: float, E_dash_dash_E_in_rtd_PVtoSB: float, alpha_PVtoSB: float, beta_PVtoSB: float, eta_ce_lim_PVtoSB: float) -> float:
    """太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの合成変換効率 (-)

    Args:
        x_E_in (float): 関数の引数 (入力電力量) (kWh/h)
        E_dash_dash_E_in_rtd_PVtoSB (float): 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの太陽光発電設備側における定格入力電力量 (kWh/h)
        alpha_PVtoSB (float): 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の傾き (-)
        beta_PVtoSB (float): 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の切片 (-)
        eta_ce_lim_PVtoSB (float): 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの合成変換効率の下限 (-)

    Returns:
        float: 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの合成変換効率 (-)
    """
    eta_ce_PVtoSB = \
        f_eta_ec(x_E_in, E_dash_dash_E_in_rtd_PVtoSB, alpha_PVtoSB, beta_PVtoSB, eta_ce_lim_PVtoSB)
    return eta_ce_PVtoSB


def f_E_dash_dash_in_PVtoSB(x_E_out: float, E_dash_dash_E_in_rtd_PVtoSB: float, alpha_PVtoSB: float, beta_PVtoSB: float) -> float:
    """太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの蓄電池ユニット側における出力電力量から太陽光発電設備側における入力電力量を逆算する関数

    Args:
        x_E_out (float): 関数の引数 (出力電力量) (kWh/h)
        E_dash_dash_E_in_rtd_PVtoSB (float): 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの太陽光発電設備側における定格入力電力量 (kWh/h)
        alpha_PVtoSB (float): 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の傾き (-)
        beta_PVtoSB (float): 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の切片 (-)

    Returns:
        float: 太陽光発電設備から蓄電池ユニットへ電力を送る場合のパワーコンディショナの太陽光発電設備側における入力電力量 (kWh/h)
    """
    return f_E_in(x_E_out, E_dash_dash_E_in_rtd_PVtoSB, alpha_PVtoSB, beta_PVtoSB)


# 8.6.3 蓄電池ユニットから分電盤へ電力を送る場合


def f_E_out_SBtoDB(x_E_in: float, E_dash_dash_E_in_rtd_SBtoDB: float, alpha_SBtoDB: float, beta_SBtoDB: float, eta_ce_lim_SBtoDB: float) -> float:
    """蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの蓄電池ユニット側における入力電力量から分電盤側における出力電力量を求める関数

    Args:
        x_E_in (float): 関数の引数(入力電力量) (kWh/h)
        E_dash_dash_E_in_rtd_SBtoDB (float): 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの蓄電池ユニット側における定格入力電力量 (kWh/h)
        alpha_SBtoDB (float): 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の傾き (-)
        beta_SBtoDB (float): 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の切片 (-)
        eta_ce_lim_SBtoDB (float): 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの合成変換効率の下限 (-)

    Returns:
        float: 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの分電盤側における出力電力量 (kWh/h)
    """
    eta_ce_SBtoDB = get_eta_ce_SBtoDB(x_E_in, E_dash_dash_E_in_rtd_SBtoDB, alpha_SBtoDB, beta_SBtoDB, eta_ce_lim_SBtoDB)
    return eta_ce_SBtoDB * min(x_E_in, E_dash_dash_E_in_rtd_SBtoDB)


def get_eta_ce_SBtoDB(x_E_in: float, E_dash_dash_E_in_rtd_SBtoDB: float, alpha_SBtoDB: float, beta_SBtoDB: float, eta_ce_lim_SBtoDB: float) -> float:
    """蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの合成変換効率 (-)

    Args:
        x_E_in (float): 関数の引数(入力電力量) (kWh/h)
        E_dash_dash_E_in_rtd_SBtoDB (float): 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの蓄電池ユニット側における定格入力電力量 (kWh/h)
        alpha_SBtoDB (float): 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の傾き (-)
        beta_SBtoDB (float): 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の切片 (-)
        eta_ce_lim_SBtoDB (float): 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの合成変換効率の下限 (-)

    Returns:
        float: 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの合成変換効率 (-)
    """
    eta_ce_SBtoDB = \
        f_eta_ec(x_E_in, E_dash_dash_E_in_rtd_SBtoDB, alpha_SBtoDB, beta_SBtoDB, eta_ce_lim_SBtoDB)
    return eta_ce_SBtoDB


def f_E_dash_dash_in_SBtoDB(x_E_out: float, E_dash_dash_E_in_rtd_SBtoDB: float, alpha_SBtoDB: float, beta_SBtoDB: float) -> float:
    """蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの分電盤側における出力電力量から蓄電池ユニット側における入力電力量を逆算する関数

    Args:
        x_E_out (float): 関数の引数(出力電力量) (kWh/h)
        E_dash_dash_E_in_rtd_SBtoDB (float): 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの蓄電池ユニット側における定格入力電力量 (kWh/h)
        alpha_SBtoDB (float): 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の傾き (-)
        beta_SBtoDB (float): 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の切片 (-)

    Returns:
        float: 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの蓄電池ユニット側における入力電力量 (kWh/h)
    """
    return f_E_in(x_E_out, E_dash_dash_E_in_rtd_SBtoDB, alpha_SBtoDB, beta_SBtoDB)


# 8.6.4 合成変換効率を求める関数


def f_eta_ec(x_E_in: float, x_E_in_rtd: float, x_a: float, x_b: float, x_eta_ce_lim: float) -> float:
    """合成変換効率を求める関数
    
    Args:
        x_E_in (float): 関数の引数(入力電力量) (kWh/h)
        x_E_in_rtd (float): 関数の引数 (定格入力電力量) (kWh/h)
        x_a (float): 関数の引数 (パワーコンディショナの合成変換効率を求める回帰式の傾き) (-)
        x_b (float): 関数の引数 (パワーコンディショナの合成変換効率を求める回帰式の切片) (-)
        x_eta_ce_lim (float): 関数の引数 (合成変換効率の下限) (-)

    Retusn:
        float: 合成変換効率 (-)
    """
    if x_E_in <= 0:
        return x_eta_ce_lim
    elif x_E_in > 0:
        return max(x_a * x_E_in_rtd / min(x_E_in, x_E_in_rtd) + x_b, x_eta_ce_lim)


# 8.6.5 入力電力量を出力電力量から逆算する関数


def f_E_in(x_E_out: float, x_E_in_rtd: float, x_a: float, x_b: float) -> float:
    """入力電力量を出力電力量から逆算する関数

    Args:
        x_E_out (float): 関数の引数(出力電力量) (kWh/h)
        x_E_in_rtd (float): 関数の引数 (定格入力電力量) (kWh/h)
        x_a (float): 関数の引数 (パワーコンディショナの合成変換効率を求める回帰式の傾き) (-)
        x_b (float): 関数の引数 (パワーコンディショナの合成変換効率を求める回帰式の切片) (-)

    Returns:
        float: 入力電力量 (kWh/h)
    """
    r_lim_rtd = 0.25
    _E_in = min(max((-x_a * x_E_in_rtd + x_E_out) / x_b, x_E_in_rtd * r_lim_rtd), x_E_in_rtd) 
    if _E_in / x_E_in_rtd < 0.25:
        E_in = x_E_out / 0.96
    else:
        E_in = _E_in

    return E_in


# 8.7 補機の消費電力量


def get_E_E_aux_PCS(P_aux_PCS_oprt: float, tau_oprt_PSS: float, P_aux_PCS_stby: float) -> float:
    """1時間当たりのパワーコンディショナの補機の消費電力量 (kWh/h)

    Args:
        P_aux_PCS_oprt (float): 作動時におけるパワーコンディショナの補機の消費電力 (W)
        tau_oprt_PSS (float): 1時間当たりの蓄電設備の作動時間数 (h/h)
        P_aux_PCS_stby (float): 待機時におけるパワーコンディショナの補機の消費電力 (W)

    Returns:
        float: 1時間当たりのパワーコンディショナの補機の消費電力量 (kWh/h)
    """
    E_E_aux_PCS_d_t = \
        (P_aux_PCS_oprt * tau_oprt_PSS + P_aux_PCS_stby * (1.0 - tau_oprt_PSS)) / 1000
    return E_E_aux_PCS_d_t


# 8.8 パワーコンディショナの仕様

def get_PCS_spec(spec: dict) -> Tuple:
    """パワーコンディショナの仕様

    Args:
        spec (dict): 機器仕様

    Returns:
        Tuple: パワーコンディショナの仕様
    """
    return \
        spec['E_dash_dash_E_in_rtd_PVtoDB'], \
        spec['eta_ce_lim_PVtoDB'], \
        spec['alpha_PVtoDB'], \
        spec['beta_PVtoDB'], \
        spec['E_dash_dash_E_in_rtd_PVtoSB'], \
        spec['eta_ce_lim_PVtoSB'], \
        spec['alpha_PVtoSB'], \
        spec['beta_PVtoSB'], \
        spec['E_dash_dash_E_in_rtd_SBtoDB'], \
        spec['eta_ce_lim_SBtoDB'], \
        spec['alpha_SBtoDB'], \
        spec['beta_SBtoDB'], \
        spec['P_aux_PCS_oprt'], \
        spec['P_aux_PCS_stby']


# 9. 蓄電池ユニット


# 9.1 最大充電可能電力量


def get_E_dash_dash_E_SB_max_chg(I_max_chg: float, V_max_chg: float, delta_tau_max_chg: float) -> float:
    """蓄電池ユニットによる最大充電可能電力量の計算 式(26)

    Args:
        I_max_chg (float): 蓄電池ユニットが最大充電可能電力量を充電する時の電流 (A)
        V_max_chg (float): 蓄電池ユニットが最大充電可能電力量を充電する時の電圧 (V)
        delta_tau_max_chg (float): 蓄電池ユニットが最大充電可能電力量を充電する時間 (h)

    Returns:
        float: 蓄電池ユニットによる最大充電可能電力量 (kWh/h)
    """
    return I_max_chg * V_max_chg * delta_tau_max_chg / 1000


def get_V_max_chg(SOC_st0: float, SOC_star_max: float, T_amb_bmdl: float, type_batt: int, V_rtd_batt: float, I_max_chg: float, R_intr: float) -> float:
    """蓄電池ユニットが最大充電可能電力量を充電する時の電圧の計算 式(27)

    Args:
        SOC_st0 (float): 蓄電池が状態0にある場合の蓄電池の充電率 (-)
        SOC_star_max (float): 蓄電池ユニットが充電を停止する充電率 (-)
        T_amb_bmdl (float): 蓄電池モジュールの周囲温度 (K)
        type_batt (int): 蓄電池の種類 (-)
        V_rtd_batt (float): 蓄電池の定格電力 (V)
        I_max_chg (float): 蓄電池ユニットが最大充電可能電力量を充電するときの電流 (A)
        R_intr (float):蓄電池の内部抵抗 (Ω)

    Returns:
        float: 蓄電池ユニットが最大充電可能電力量を充電する時の電圧 (V)
    """

    # 充放電により蓄電池の状態が状態0(SOC_st0)から状態1(SOC_star_max)に変化する場合の開回路電圧の絶対値 (V)
    OCV = (f_OCV(SOC_st0, T_amb_bmdl, type_batt, V_rtd_batt) +
           f_OCV(SOC_star_max, T_amb_bmdl, type_batt, V_rtd_batt)) / 2

    # 蓄電池ユニットが最大充電可能電力量を充電する時の電圧 式(27)
    V_max_chg = OCV + I_max_chg * R_intr * (SOC_star_max - SOC_st0)

    if V_max_chg < 0:
        raise ValueError('V_max_chg < 0')

    return V_max_chg


def get_I_max_chg(C_oprt_chg: float, delta_tau_max_chg: float) -> float:
    """充電に対する蓄電池の電流 (A)

    Args:
        C_oprt_chg (float): 蓄電池の充電可能容量 (Ah)
        delta_tau_max_chg (float): 蓄電池ユニットが最大充電可能電力量を充電する時間 (h)

    Returns:
        float: 充電に対する蓄電池の電流 (A)
    """
    return C_oprt_chg / delta_tau_max_chg


def get_delta_tau_max_chg_d_t() -> np.ndarray:
    """日付d時刻tにおける蓄電池ユニットが最大充電可能電力量を充電する時間 (h)

    Returns:
        ndarray: 日付d時刻tにおける蓄電池ユニットが最大充電可能電力量を充電する時間 (h)
    """
    return np.repeat(1.0, 9760)


# 9.2 最大放電可能電力量


def get_E_dash_dash_E_SB_max_dchg(I_max_dchg: float, V_max_dchg: float, delta_tau_max_dchg: float) -> float:
    """蓄電池ユニットによる最大放電可能電力量 (kWh/h)

    Args:
        I_max_dchg (float): 蓄電池ユニットが最大放電可能電力量を放電する時の電流 (A)
        V_max_dchg (float): 蓄電池ユニットが最大放電可能電力量を放電する時の電圧 (V)
        delta_tau_max_dchg (float): 蓄電池ユニットが最大放電可能電力量を放電する時間 (h)

    Returns:
        float: 蓄電池ユニットによる最大放電可能電力量 (kWh/h)
    """
    return I_max_dchg * V_max_dchg * delta_tau_max_dchg / 1000


def get_V_max_dchg(SOC_st0: float, SOC_star_min: float, T_amb_bmdl: float, type_batt: int, V_rtd_batt: float, I_max_dchg: float, R_intr: float) -> float:
    """蓄電池ユニットが最大放電可能電力量を放電する時の電圧の計算 式(30)

    Args:
        SOC_st0 (float): 蓄電池が状態0にある場合の蓄電池の充電率 (-)
        SOC_star_min (float): 蓄電池ユニットが放電を停止する充電率 (-)
        T_amb_bmdl (float): 蓄電池モジュールの周囲温度 (K)
        type_batt (int): 蓄電池の種類 (-)
        V_rtd_batt (float): 蓄電池ので威嚇電圧 (V)
        I_max_dchg (float): 蓄電池ユニットが最大充電可能電力量を放電するときの電流 (A)
        R_intr (float):蓄電池の内部抵抗 (Ω)

    Returns:
        float: 蓄電池ユニットが最大放電可能電力量を放電する時の電圧 (V)
    """
    # 充放電により蓄電池の状態が状態0(SOC_st0)から状態1(SOC_star_min)に変化する場合の開回路電圧の絶対値 (V)
    OCV = (f_OCV(SOC_st0, T_amb_bmdl, type_batt, V_rtd_batt) + 
           f_OCV(SOC_star_min, T_amb_bmdl, type_batt, V_rtd_batt)) / 2

    # 蓄電池ユニットが最大放電可能電力量を放電する時の電圧 式(30)
    V_max_dchg = OCV - I_max_dchg * R_intr * (SOC_st0 - SOC_star_min)

    if V_max_dchg < 0:
        raise ValueError('V_max_dchg < 0')

    return V_max_dchg


def get_I_max_dchg(C_oprt_dchg: float, delta_tau_max_dchg: float) -> float:
    """蓄電池ユニットが最大放電可能電力量を放電する時の電流 (A)

    Args:
        C_oprt_dchg (float): 蓄電池の放電可能容量 (Ah)
        delta_tau_max_dchg (float): 蓄電池ユニットが最大放電可能電力量を放電する時間 (h)

    Returns:
        float: 蓄電池ユニットが最大放電可能電力量を放電する時の電流 (A)
    """
    return C_oprt_dchg / delta_tau_max_dchg


def get_delta_tau_max_dchg_d_t()-> np.ndarray:
    """日付d時刻tにおける蓄電池ユニットが最大放電可能電力量を放電する時間 (h)

    Returns:
        ndarray: 日付d時刻tにおける蓄電池ユニットが最大放電可能電力量を放電する時間 (h)
    """
    return np.repeat(1.0, 9760)


# 9.3 充電量


def get_E_dash_dash_E_SB_chg(E_dash_dash_E_PV_chg: float) -> float:
    """1時間当たりの蓄電池ユニットによる充電量 (kWh/h)

    Args:
        E_dash_dash_E_PV_chg (float): 1時間当たりの太陽光発電設備による発電量のうちの充電分 (kWh/h)

    Returns:
        float: 1時間当たりの蓄電池ユニットによる充電量 (kWh/h)
    """
    return E_dash_dash_E_PV_chg


# 9.4 放電量


def get_E_dash_dash_E_SB_dchg(E_dash_dash_E_SB_sup: float) -> float:
    """1時間当たりの蓄電池ユニットによる放電量 (kWh/h)

    Args:
        E_dash_dash_E_SB_sup (float): 1時間当たりの蓄電池ユニットによる放電量のうちの供給分 (kWh/h)

    Returns:
        float: 1時間当たりの蓄電池ユニットによる放電量 (kWh/h)
    """
    return E_dash_dash_E_SB_sup


# 9.5 蓄電量


# 9.5.1 充電可能容量

def get_C_oprt_chg(C_fc: float, SOC_star_max: float, SOC_star_min: float, C_oprt_dchg: float) -> float:
    """蓄電池の充電可能容量 (Ah)

    Args:
        C_fc (float): 蓄電池の満充電容量 (Ah)
        SOC_star_max (float): 蓄電池ユニットが充電を停止する充電率 (-)
        SOC_star_min (float): 蓄電池ユニットが放電を停止する充電率 (-)
        C_oprt_dchg (float): 蓄電池の放電可能容量 (Ah)

    Returns:
        float: 蓄電池の充電可能容量 (Ah)
    """
    return C_fc * (SOC_star_max - SOC_star_min) - C_oprt_dchg


# 9.5.2 放電可能容量

def get_C_oprt_dchg_0(C_fc: float, SOC_star_max: float, SOC_star_min: float, r_int_dchg_batt) -> float:
    """1月1日0時に終える蓄電池による放電可能容量 (Ah)

    Args:
        C_fc (float): 蓄電池の満充電容量 (Ah)
        SOC_star_max (float): 蓄電池ユニットが充電を停止する充電率 (-)
        SOC_star_min (float): 蓄電池ユニットが放電を停止する充電率 (-)
        r_int_dchg_batt (float): １月１日０時のおける蓄電池の充放電可能容量に対する放電可能容量の割合 (-)

    Returns:
        float: 1月1日0時に終える蓄電池による放電可能容量 (Ah)
    """
    #1月1日0時
    return C_fc * (SOC_star_max - SOC_star_min) * r_int_dchg_batt

def get_C_oprt_dchg(C_fc: float, SOC_st1_previoushour: float, SOC_star_min: float) -> float:
    """蓄電池の放電可能容量 (Ah)

    Args:
        C_fc (float): 蓄電池の満充電容量 (Ah)
        SOC_st1_previoushour (float): 前時間における蓄電池の放電可能容量 (Ah)
        SOC_star_min (float): 蓄電池ユニットが放電を停止する充電率 (-)

    Returns:
        float: 蓄電池の放電可能容量 (Ah)
    """
    #1月1日1時以降
    #※前時間の値を使うので注意が必要
    return  C_fc * (SOC_st1_previoushour - SOC_star_min)


def get_SOC_st0(SOC_star_min: float, C_oprt_dchg: float, C_fc: float) -> float:
    """蓄電池が状態0にある場合の蓄電池の充電率 (-)

    Args:
        SOC_star_min (float): 蓄電池ユニットが放電を停止する充電率 (-)
        C_oprt_dchg (float): 蓄電池の放電可能容量 (Ah)
        C_fc (float): 蓄電池の満充電容量 (Ah)

    Returns:
        float: 蓄電池が状態0にある場合の蓄電池の充電率 (-)
    """
    return SOC_star_min + C_oprt_dchg / C_fc


def get_SOC_st1(SOC_st0: float, SOC_star_max: float, SOC_star_min: float, I_chg: float, I_dchg: float, delta_tau_chg: float, delta_tau_dchg: float, C_fc: float, E_dash_dash_E_SB_chg: float, E_dash_dash_E_SB_dchg: float) -> float:
    """蓄電池が状態1にある場合の蓄電池の充電率 (-)

    Args:
        SOC_st0 (float): 蓄電池が状態0にある場合の蓄電池の充電率 (-)
        I_chg (float): 充電に対する蓄電池の電流 (A)
        I_dchg (float): 放電に対する蓄電池の電流 (A)
        delta_tau_chg (float): 蓄電池ユニットの充電時間 (h)
        delta_tau_dchg (float): 蓄電池ユニットの放電時間 (h)
        C_fc (float): 蓄電池の満充電容量 (Ah)
        E_dash_dash_E_SB_chg (float): 1時間当たりの蓄電池ユニットによる充電量 (kWh/h)
        E_dash_dash_E_SB_dchg (float): 1時間当たりの蓄電池ユニットによる放電量 (kWh/h)

    Returns:
        float: 蓄電池が状態1にある場合の蓄電池の充電率 (-)
    """
    if E_dash_dash_E_SB_chg > 0 and E_dash_dash_E_SB_dchg == 0:
        return min(SOC_st0 + I_chg * delta_tau_chg / C_fc, SOC_star_max)
    elif E_dash_dash_E_SB_chg == 0 and E_dash_dash_E_SB_dchg > 0:
        return max(SOC_st0 - I_dchg * delta_tau_dchg / C_fc, SOC_star_min)
    else:
        return SOC_st0


def get_I_chg(E_dash_dash_E_SB_chg: float, E_dash_dash_E_SB_dchg: float, V_OC: float, R_intr: float) -> float:
    """充電に対する蓄電池の電流 (A)

    Args:
        E_dash_dash_E_SB_chg (float): 1時間当たりの蓄電池ユニットによる充電量 (kWh/h)
        E_dash_dash_E_SB_dchg (float): 1時間当たりの蓄電池ユニットによる放電量 (kWh/h)
        V_OC (float): 蓄電池の閉回路電圧 (V)
        R_intr (float): 蓄電池の内部抵抗 (Ω)

    Returns:
        float: 充電に対する蓄電池の電流 (A)
    """
    if E_dash_dash_E_SB_chg > 0 and E_dash_dash_E_SB_dchg == 0:
        return (-1.0 * V_OC + math.sqrt(V_OC**2 + 4.0 * R_intr * E_dash_dash_E_SB_chg * 1000)) / (2.0 * R_intr)
    elif E_dash_dash_E_SB_chg == 0 and E_dash_dash_E_SB_dchg > 0:
        return 0.0
    else:
        return 0.0


def get_I_dchg(E_dash_dash_E_SB_chg: float, E_dash_dash_E_SB_dchg: float, V_OC: float, R_intr: float) -> float:
    """放電に対する蓄電池の電流 (A)

    Args:
        E_dash_dash_E_SB_chg (float): 1時間当たりの蓄電池ユニットによる充電量 (kWh/h)
        E_dash_dash_E_SB_dchg (float): 1時間当たりの蓄電池ユニットによる放電量 (kWh/h)
        V_OC (float): 蓄電池の閉回路電圧 (V)
        R_intr (float): 蓄電池の内部抵抗 (Ω)

    Returns:
        float: 放電に対する蓄電池の電流 (A)
    """
    if E_dash_dash_E_SB_chg > 0 and E_dash_dash_E_SB_dchg == 0:
        return 0.0
    elif E_dash_dash_E_SB_chg == 0 and E_dash_dash_E_SB_dchg > 0:
        return (V_OC - math.sqrt(max(0,V_OC**2 - 4.0 * R_intr * E_dash_dash_E_SB_dchg * 1000))) / (2.0 * R_intr)
    else:
        return 0.0



def get_V_OC(SOC_st0: float, SOC_hat_st1: float, E_dash_dash_E_SB_chg: float, E_dash_dash_E_SB_dchg: float, T_amb_bmdl: float, type_batt: int, V_rtd_batt: float) -> float:
    """蓄電池の閉回路電圧 (V)

    Args:
        SOC_st0 (float): 蓄電池が状態0にある場合の蓄電池の充電率 (-)
        SOC_hat_st1 (float): 蓄電池が状態1にある場合の蓄電池の充電率の仮値 (-)
        E_dash_dash_E_SB_chg (float): 1時間当たりの蓄電池ユニットによる充電量 (kWh/h)
        E_dash_dash_E_SB_dchg (float): 1時間当たりの蓄電池ユニットによる放電量 (kWh/h)
        T_amb_bmdl (float): 蓄電池モジュールの周囲温度 (K)
        type_batt (int): 蓄電池の種類 (-)
        V_rtd_batt (float): 蓄電池の定格電圧 (V)

    Returns:
        float: 蓄電池の閉回路電圧 (V)
    """

    if E_dash_dash_E_SB_chg > 0 or E_dash_dash_E_SB_dchg > 0:
        SOC_hat_st0 = get_SOC_hat_st0(SOC_st0)
        return (f_OCV(SOC_hat_st0, T_amb_bmdl, type_batt, V_rtd_batt) + 
                f_OCV(SOC_hat_st1, T_amb_bmdl, type_batt, V_rtd_batt)) / 2
    else:
        return 0.0


def get_SOC_hat_st0(SOC_st_0) -> float:
    """蓄電池が状態0にある場合の蓄電池の充電率の仮値 (-)

    Args:
        SOC_st_0 (float): 蓄電池が状態0にある場合の蓄電池の充電率 (-)

    Returns:
        float: 蓄電池が状態0にある場合の蓄電池の充電率の仮値 (-)
    """
    return SOC_st_0


def get_SOC_hat_st1(SOC_st0: float, C_fc: float, delta_t_chg: float, delta_t_dchg: float, V_rtd_batt: float, E_dash_dash_E_SB_chg: float, E_dash_dash_E_SB_dchg: float) -> float:
    """蓄電池が状態1にある場合の蓄電池の充電率の仮値 (-)

    Args:
        SOC_st0 (float): 蓄電池が状態0にある場合の蓄電池の充電率 (-)
        C_fc (float): 蓄電池の満充電容量 (Ah)
        delta_t_chg (float): 蓄電池ユニットの充電時間 (h)
        delta_t_dchg (float): 蓄電池ユニットの放電時間 (h)
        V_rtd_batt (float): 蓄電池の定格電圧 (V)
        E_dash_dash_E_SB_chg (float): 1時間当たりの蓄電池ユニットによる充電量 (kWh/h)
        E_dash_dash_E_SB_dchg (float): 1時間当たりの蓄電池ユニットによる放電量 (kWh/h)

    Returns:
        float: 蓄電池が状態1にある場合の蓄電池の充電率の仮値 (-)
    """
    if E_dash_dash_E_SB_chg > 0 and E_dash_dash_E_SB_dchg == 0:
        return SOC_st0 + E_dash_dash_E_SB_chg * 1000 / (C_fc / delta_t_chg) / V_rtd_batt
    elif E_dash_dash_E_SB_chg == 0 and E_dash_dash_E_SB_dchg > 0:
        return SOC_st0 - E_dash_dash_E_SB_dchg * 1000 / (C_fc / delta_t_dchg) / V_rtd_batt
    else:
        return SOC_st0


def get_R_intr(T_amb_bmdl: float, type_batt: int) -> float:
    """蓄電池の内部抵抗 (Ω)

    Args:
        T_amb_bmdl (float): 蓄電池モジュールの周囲温度 (K)
        type_batt (int): 蓄電池の種類 (-)

    Returns:
        float: 蓄電池の内部抵抗 (Ω)
    """
    return f_R_intr(T_amb_bmdl, type_batt)


# 9.5.3 充電時間・放電時間


def get_delta_tau_chg(E_dash_dash_E_SB_chg: float, E_dash_dash_E_SB_dchg: float) -> float:
    """蓄電池ユニットの充電時間 (h)

    Args:
        E_dash_dash_E_SB_chg (float): 1時間当たりの蓄電池ユニットによる充電量 (kWh/h)
        E_dash_dash_E_SB_dchg (float): 1時間当たりの蓄電池ユニットによる放電量 (kWh/h)

    Returns:
        float: 蓄電池ユニットの充電時間 (h)
    """
    if E_dash_dash_E_SB_chg > 0 and E_dash_dash_E_SB_dchg == 0:
        return 1
    elif E_dash_dash_E_SB_chg == 0 and E_dash_dash_E_SB_dchg > 0:
        return 0
    elif E_dash_dash_E_SB_chg == 0 and E_dash_dash_E_SB_dchg == 0:
        return 0
    else:
        raise ValueError("E_dash_dash_E_SB_chg = {}, E_dash_dash_E_SB_dchg = {}".format(E_dash_dash_E_SB_chg, E_dash_dash_E_SB_dchg))


def get_delta_tau_dchg(E_dash_dash_E_SB_chg: float, E_dash_dash_E_SB_dchg: float) -> float:
    """蓄電池ユニットの放電時間 (h)

    Args:
        E_dash_dash_E_SB_chg (float): 1時間当たりの蓄電池ユニットによる充電量 (kWh/h)
        E_dash_dash_E_SB_dchg (float): 1時間当たりの蓄電池ユニットによる放電量 (kWh/h)

    Returns:
        float: 蓄電池ユニットの放電時間 (h)
    """
    if E_dash_dash_E_SB_chg > 0  and E_dash_dash_E_SB_dchg == 0:
        return 0
    elif E_dash_dash_E_SB_chg == 0 and E_dash_dash_E_SB_dchg > 0:
        return 1
    elif E_dash_dash_E_SB_chg == 0 and E_dash_dash_E_SB_dchg == 0:
        return 0
    else:
        raise ValueError("E_dash_dash_E_SB_chg = {}, E_dash_dash_E_SB_dchg = {}".format(E_dash_dash_E_SB_chg, E_dash_dash_E_SB_dchg))


# 9.6 制御


def get_SOC_star_max(SOC_star_upper: float) -> float:
    """蓄電池ユニットが充電を停止する充電率 (-)

    Args:
        SOC_star_upper (float): 蓄電池の上限電圧に対応する充電率 (-)

    Returns:
        float: 蓄電池ユニットが充電を停止する充電率 (-)
    """
    # 式(43)
    SOC_star_max = SOC_star_upper
    return SOC_star_max


def get_SOC_star_min(SOC_star_lower: float, SOC_star_upper: float, r_LCP_batt: float, SC: bool) -> float:
    """蓄電池ユニットが放電を停止する充電率 (-)

    Args:
        SOC_star_lower (float): 蓄電池の下限電圧に対応する充電率 (-)
        SOC_star_upper (float): 蓄電池の上限電圧に対応する充電率 (-)
        r_LCP_batt (float): 蓄電池の充放電可能容量に対する放電停止残容量の割合 (-)
        SC (bool): 系統からの電力供給の有無

    Returns:
        float: 蓄電池ユニットが放電を停止する充電率 (-)
    """
    if SC:
        # 系統連携運転時の場合 式(44-1)
        return SOC_star_lower + r_LCP_batt * (SOC_star_upper - SOC_star_lower)
    else:
        # 独立運転時の場合 式(44-2)
        return SOC_star_lower


def get_C_fc_d_t(C_fc_rtd: float) -> np.ndarray:
    """日付d時刻tにおける蓄電池の満充電容量 (Ah)

    Args:
        C_fc_rtd (float): 蓄電池の初期満充電容量 (Ah)

    Returns:
        ndarray: 日付d時刻tにおける蓄電池の満充電容量 (Ah)
    """
    C_fc_d_t = C_fc_rtd
    return np.repeat(C_fc_d_t, 9760)


def get_C_fc_rtd(W_rtd_batt: float, V_rtd_batt: float) -> float:
    """蓄電池の初期満充電容量 (Ah)

    Args:
        W_rtd_batt (float): 蓄電池の定格容量 (kWh)
        V_rtd_batt (float): 蓄電池の定格電圧 (V)

    Returns:
        float: 蓄電池の初期満充電容量 (Ah)
    """
    C_fc_rtd = W_rtd_batt * 1000 / V_rtd_batt
    return C_fc_rtd



# 9.7 内部抵抗を表す関数


def f_R_intr(x_T_amb: float, x_type: type) -> float:
    """蓄電池の内部抵抗を表す関数

    Args:
        x_T_amb (float): 関数の引数 (蓄電池モジュールの周囲温度) (K)
        x_type (type): 関数の引数 (蓄電池の種類) (-)
    
    Returns:
        float: 蓄電池の内部抵抗 (Ω)
    """
    R_intr = 0.5
    return R_intr


# 9.8 開回路電圧を表す関数


def f_OCV(x_SOC: float, x_T_amb: float, x_type: type, x_Vrtd: float) -> float:
    """充放電により蓄電池の状態が状態𝛼から状態𝛽に変化する場合の開回路電圧の絶対値の関数定義 式(50a)

    Args:
        x_SOC (float): 蓄電池の充電率 (-)
        x_T_amb (float): 蓄電池モジュールの周囲温度 (K)
        x_type (int): 蓄電池の種類 (-)
        x_Vrtd (float): 蓄電池の定格電圧 (V)

    Returns:
        float: 充放電により蓄電池の状態が状態𝛼から状態𝛽に変化する場合の開回路電圧の絶対値 (V)
    """
    K_0 = get_K_0(x_T_amb, x_type)
    K_1 = get_K_1(x_T_amb, x_type)
    K_2 = get_K_2(x_T_amb, x_type)
    K_3 = get_K_3(x_T_amb, x_type)
    K_4 = get_K_4(x_T_amb, x_type)
    K_5 = get_K_5(x_T_amb, x_type)
    K_6 = get_K_6(x_T_amb, x_type)

    # 蓄電池の定格電圧により無次元化した開回路電圧 (-)
    nOCV = K_0 \
        + K_1 * (x_SOC**1) \
        + K_2 * (x_SOC**2) \
        + K_3 * (x_SOC**3) \
        + K_4 * (x_SOC**4) \
        + K_5 * (x_SOC**5) \
        + K_6 * (x_SOC**6)

    OCV = nOCV * x_Vrtd

    return OCV


def get_K_0(x_T_amb: float, x_type: type) -> float:
    """開回路電圧の絶対値を表す関数f_OCVの項の係数K_0 (-)

    Args:
        x_T_amb (float): 関数の引数 (蓄電池モジュールの周囲温度) (K)
        x_type (int): 関数の引数 (充電池の種類)

    Returns:
        float: 開回路電圧の絶対値を表す関数f_OCVの項の係数K_0 (-)
    """
    return 0.92027


def get_K_1(x_T_amb: float, x_type: type) -> float:
    """開回路電圧の絶対値を表す関数f_OCVの項の係数K_1 (-)

    Args:
        x_T_amb (float): 関数の引数 (蓄電池モジュールの周囲温度) (K)
        x_type (int): 関数の引数 (充電池の種類)

    Returns:
        float: 開回路電圧の絶対値を表す関数f_OCVの項の係数K_1 (-)
    """
    return 0.31524


def get_K_2(x_T_amb: float, x_type: type) -> float:
    """開回路電圧の絶対値を表す関数f_OCVの項の係数K_2 (-)

    Args:
        x_T_amb (float): 関数の引数 (蓄電池モジュールの周囲温度) (K)
        x_type (int): 関数の引数 (充電池の種類)

    Returns:
        float: 開回路電圧の絶対値を表す関数f_OCVの項の係数K_2 (-)
    """
    return -0.61051


def get_K_3(x_T_amb: float, x_type: type) -> float:
    """開回路電圧の絶対値を表す関数f_OCVの項の係数K_3 (-)

    Args:
        x_T_amb (float): 関数の引数 (蓄電池モジュールの周囲温度) (K)
        x_type (int): 関数の引数 (充電池の種類)

    Returns:
        float: 開回路電圧の絶対値を表す関数f_OCVの項の係数K_3 (-)
    """
    return 0.58010


def get_K_4(x_T_amb: float, x_type: type) -> float:
    """開回路電圧の絶対値を表す関数f_OCVの項の係数K_4 (-)

    Args:
        x_T_amb (float): 関数の引数 (蓄電池モジュールの周囲温度) (K)
        x_type (int): 関数の引数 (充電池の種類)

    Returns:
        float: 開回路電圧の絶対値を表す関数f_OCVの項の係数K_4 (-)
    """
    return 0.00003


def get_K_5(x_T_amb, x_type):
    """開回路電圧の絶対値を表す関数f_OCVの項の係数K_5 (-)

    Args:
        x_T_amb (float): 関数の引数 (蓄電池モジュールの周囲温度) (K)
        x_type (int): 関数の引数 (充電池の種類)

    Returns:
        float: 開回路電圧の絶対値を表す関数f_OCVの項の係数K_5 (-)
    """
    return -0.08345


def get_K_6(x_T_amb, x_type):
    """開回路電圧の絶対値を表す関数f_OCVの項の係数K_6 (-)

    Args:
        x_T_amb (float): 関数の引数 (蓄電池モジュールの周囲温度) (K)
        x_type (int): 関数の引数 (充電池の種類)

    Returns:
        float: 開回路電圧の絶対値を表す関数f_OCVの項の係数K_6 (-)
    """
    return -0.02122


# 9.9 蓄電池ユニットの仕様

def get_W_rtd_batt(spec: dict) -> float:
    """蓄電池の定格容量 (kWh)

    Args:
        spec (dict): 機器仕様

    Returns:
        float: 蓄電池の定格容量 (kWh)
    """
    return spec['W_rtd_batt']


def get_r_LCP_batt(spec: dict) -> float:
    """蓄電池の充放電可能容量に対する放電停止残容量の割合 (-)

    Args:
        spec (dict): 機器仕様

    Returns:
        float: 蓄電池の充放電可能容量に対する放電停止残容量の割合 (-)
    """
    return spec['r_LCP_batt']


def get_V_rtd_batt(spec: dict) -> float:
    """蓄電池の定格電圧 (V)

    Args:
        spec (dict): 機器仕様

    Returns:
        float: 蓄電池の定格電圧 (V)
    """
    return spec['V_rtd_batt']


def get_V_star_lower_batt(spec: dict) -> float:
    """蓄電池の下限電圧 (V)

    Args:
        spec (dict): 機器仕様

    Returns:
        float: 蓄電池の下限電圧 (V)
    """
    return spec['V_star_lower_batt']


def get_V_star_upper_batt(spec: dict) -> float:
    """蓄電池の上限電圧 (V)

    Args:
        spec (dict): 機器仕様

    Returns:
        float: 蓄電池の上限電圧 (V)
    """
    return spec['V_star_upper_batt']


def get_SOC_star_lower(spec):
    """蓄電池の下限電圧に対応する充電率 (-)

    Args:
        spec (dict): 機器仕様

    Returns:
        float: 蓄電池の下限電圧に対応する充電率 (-)
    """
    return spec['SOC_star_lower']


def get_SOC_star_upper(spec):
    """蓄電池の上限電圧に対応する充電率 (-)

    Args:
        spec (dict): 機器仕様

    Returns:
        float: 蓄電池の上限電圧に対応する充電率 (-)
    """
    return spec['SOC_star_upper']


def get_r_int_dchg_batt(spec):
    """1月1日0時のおける蓄電池の充放電可能容量に対する放電可能容量の割合 (-)

    Args:
        spec (dict): 機器仕様

    Returns:
        float: 1月1日0時のおける蓄電池の充放電可能容量に対する放電可能容量の割合 (-)
    """
    return spec['r_int_dchg_batt']


def get_type_batt(V_star_upper_batt: float, V_star_lower_batt: float) -> int:
    """蓄電池の種類 (-)

    Args:
        V_star_upper_batt (float): 蓄電池の上限電圧 (V)
        V_star_lower_batt (float): 蓄電池の下限電圧 (V)

    Returns:
        int: 蓄電池の種類 (-)
    """
    r =  V_star_upper_batt / V_star_lower_batt

    # 表 5 蓄電池の種類の区分
    if r >= 1.7:
        return 3
    elif r >= 1.45:
        return 2
    else:
        return 1

# 9.10 蓄電池モジュールの周囲温度


def get_T_amb_bmdl_d_t(theta_ex_d_t: np.ndarray) -> np.ndarray:
    """日付d時刻tにおける蓄電池モジュールの周囲温度 (K)

    Args:
        theta_ex_d_t (ndarray): 日付d時刻tにおける外気温度 (℃)

    Returns:
        ndarray: 日付d時刻tにおける蓄電池モジュールの周囲温度 (K)
    """
    # 外気温度を用いて絶対温度に換算
    return get_T(theta_ex_d_t)


# 9.11 系統からの電力供給の有無


def get_SC_d_t(df: pd.DataFrame) -> np.ndarray:
    """日付d時刻tにおける系統からの電力供給の有無 (-)

    Args:
        df (DataFrame): データフレーム

    Returns:
        ndarray: 日付d時刻tにおける系統からの電力供給の有無 (-)
    """
    return df['電力供給']


# 10. 表示・計測・操作ユニット等


# 10.1 消費電力量


def get_E_E_aux_others(P_aux_others_oprt: float, tau_oprt_PSS: float, P_aux_others_stby: float) -> float:
    """1時間当たりの表示・計測・操作ユニット等の消費電力量 (kWh/h)

    Args:
        P_aux_others_oprt (float): 作動時における表示・計測・操作ユニット等の消費電力 (W)
        tau_oprt_PSS (float): 1時間当たりの蓄電設備の作動時間数 (h/h)
        P_aux_others_stby (float): 待機時における表示・計測・操作ユニット等の消費電力 (W)

    Returns:
        float: 1時間当たりの表示・計測・操作ユニット等の消費電力量 (kWh/h)
    """
    return (P_aux_others_oprt * tau_oprt_PSS + P_aux_others_stby * (1 - tau_oprt_PSS)) / 1000


# 10.2 表示・計測・操作ユニット等の仕様


def get_table_6() -> dict:
    """表 6 表示・計測・操作ユニット等の仕様

    Returns:
        dict: 表 6 表示・計測・操作ユニット等の仕様
    """
    return {
        # 作動時における表示・計測・操作ユニット等の消費電力
        'P_aux_others_oprt': 3.0,
        # 待機時における表示・計測・操作ユニット等の消費電力
        'P_aux_others_stby': 2.0
    }

def get_P_aux_others_oprt() -> float:
    """作動時における表示・計測・操作ユニット等の消費電力 (W)

    Returns:
        float: 作動時における表示・計測・操作ユニット等の消費電力 (W)
    """
    return get_table_6()['P_aux_others_oprt']


def get_P_aux_others_stby() -> float:
    """待機時における表示・計測・操作ユニット等の消費電力 (W)

    Returns:
        float: 待機時における表示・計測・操作ユニット等の消費電力 (W)
    """
    return get_table_6()['P_aux_others_stby']


# 11. 蓄電設備の作動時間数


def get_tau_oprt_PSS(E_dash_dash_E_PV_gen: float, E_E_dmd_excl: float, E_dash_dash_E_SB_max_dchg: float) -> float:
    """ 1時間当たりの蓄電設備の作動時間数

    Args:
        E_dash_dash_E_PV_gen (float): 1 時間当たりの太陽光発電設備による発電量 (kWh/h)
        E_E_dmd_excl (float): 1 時間当たりのパワーコンディショナおよび蓄電池ユニットの補機の消費電力量を除く電力需要 (kWh/h)
        E_dash_dash_E_SB_max_dchg (float): 蓄電池ユニットによる最大放電可能電力量 (kWh/h)

    Returns:
        float: 1時間当たりの蓄電設備の作動時間数 [h]
    """
    if E_dash_dash_E_PV_gen > 0:
        # 太陽光発電設備による発電が行われている場合
        return 1.0
    else:
        # 太陽光発電設備による発電が行われていない場合
        if E_E_dmd_excl > 0 and E_dash_dash_E_SB_max_dchg > 0:
            return 1.0
        else:
            return 0.0


# 12. 太陽光発電設備による発電量


def get_E_dash_dash_E_PV_gen_d_t(n: int, E_p_i_d_t: np.ndarray, K_PM_i: np.ndarray, K_IN: float) -> float:
    """日付d時刻tにおける1時間当たりの太陽光発電設備による発電量 (kWh/h)

    Args:
        n (int): 太陽電池アレイの数
        E_p_i_d_t (ndarray): 日付dの時刻tにおける1時間当たりの太陽電池アレイiの発電量
        K_PM_i (ndarray): 太陽電池アレイiのアレイ不可整合補正係数 (-)
        K_IN (float): インバータ回路補正係数 (-)

    Returns:
        float: 日付d時刻tにおける1時間当たりの太陽光発電設備による発電量 (kWh/h)
    """
    E_dash_dash_E_PV_gen_d_t = np.sum(E_p_i_d_t[:n, :] / K_PM_i[:n], axis=0) / K_IN
    return E_dash_dash_E_PV_gen_d_t


def get_E_p_i_d_t(df: pd.DataFrame, n: int) -> np.ndarray:
    """日付dの時刻tにおける1時間当たりの太陽電池アレイiの発電量

    Args:
        df (DataFrame): データフレーム
        n (int): 太陽電池アレイの数

    Returns:
        ndarray: 日付dの時刻tにおける1時間当たりの太陽電池アレイiの発電量
    """
    return np.array([df['太陽電池アレイの発電量{}'.format(i+1)]  for i in range(n) ])


def get_n(spec: dict) -> int:
    """太陽電池アレイの数 (-)

    Args:
        spec (dict): 機器仕様

    Returns:
        int: 太陽電池アレイの数 (-)
    """
    return spec['n']


def get_K_IN(eta_IN_R: float) -> float:
    """インバータ回路補正係数 (-)

    Args:
        eta_IN_R (float): パワーコンディショナの定格負荷効率 (-)

    Returns:
        float: インバータ回路補正係数 (-)
    """
    return eta_IN_R / 0.97


def get_K_PM_i(spec: dict) -> float:
    """太陽電池アレイiのアレイ不可整合補正係数 (-)

    Args:
        spec (dict): 機器仕様

    Returns:
        float: 太陽電池アレイiのアレイ不可整合補正係数 (-)
    """
    return spec['K_PM']


def get_eta_IN_R(spec: dict) -> float:
    """パワーコンディショナの定格不可効率 (-)

    Args:
        spec (dict): 機器仕様

    Returns:
        float: パワーコンディショナの定格不可効率 (-)
    """
    return spec['eta_IN_R']


# 13. パワーコンディショナおよび蓄電設備の補機の消費電力量を除く電力需要


def get_E_E_dmd_excl_d_t(df: pd.DataFrame) -> np.ndarray:
    """日付d時刻tにおける１時間あたりのパワーコンディショナおよび蓄電設備の補機の消費電力量を除く電力需要 (kWh/h)

    Args:
        df (DataFrame): データフレーム

    Returns:
        ndarray: 日付d時刻tにおける１時間あたりのパワーコンディショナおよび蓄電設備の補機の消費電力量を除く電力需要 (kWh/h)
    """
    E_E_dmd_excl_d_t = df['電力需要'].values
    return E_E_dmd_excl_d_t


# 14. 外気温度


def get_theta_ex_d_t(df: pd.DataFrame) -> np.ndarray:
    """日付d時刻tにおける外気温度 (℃)

    Args:
        df (DataFrame): データフレーム

    Returns:
        ndarray: 日付d時刻tにおける外気温度 (℃)
    """
    theta_ex_d_t = df['外気温度'].values
    return theta_ex_d_t


# 15. 絶対温度


def get_T(theta: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """絶対温度 (K)

    Args:
        theta (float|ndarry): 空気温度 (℃)

    Returns:
        float|ndarray: 絶対温度 (K)
    """
    T = theta + 273.16
    return T

def calculate(spec: dict, SC_d_t, E_E_dmd_excl_d_t, theta_ex_d_t, E_p_i_d_t)-> pd.DataFrame:
    """機器仕様と時系列電力需要から出力値の計算を行う

    Args:
        spec (dict): 機器仕様
        df (DataFrame): データフレーム

    Returns:
        Tuple: 出力値(E_E_PV_chg_d_t, E_E_PSS_h_d_t, E_E_PV_h_d_t, E_E_PV_sell_d_t)
    """

    bl = BatteryLogger(SC_d_t=SC_d_t, E_E_dmd_excl_d_t=E_E_dmd_excl_d_t, theta_ex_d_t=theta_ex_d_t, E_p_i_d_t=E_p_i_d_t)

    # 系統からの電力供給の有無
    # SC_d_t = get_SC_d_t(df)

    # パワーコンディショナおよび蓄電設備の補機の消費電力量を除く電力需要
    # E_E_dmd_excl_d_t = get_E_E_dmd_excl_d_t(df)

    # 外気温度
    # theta_ex_d_t = get_theta_ex_d_t(df)

    # 8.8 パワーコンディショナの仕様

    E_dash_dash_E_in_rtd_PVtoDB, eta_ce_lim_PVtoDB, alpha_PVtoDB, beta_PVtoDB, \
    E_dash_dash_E_in_rtd_PVtoSB, eta_ce_lim_PVtoSB, alpha_PVtoSB, beta_PVtoSB, \
    E_dash_dash_E_in_rtd_SBtoDB, eta_ce_lim_SBtoDB, alpha_SBtoDB, beta_SBtoDB, \
    P_aux_PCS_oprt, P_aux_PCS_stby = get_PCS_spec(spec)
    
    # 12. 太陽光発電設備による発電量


    # 太陽光発電設備による発電量 式(54)
    eta_IN_R = get_eta_IN_R(spec)
    K_IN = get_K_IN(eta_IN_R)
    K_PM_i = get_K_PM_i(spec)
    n = get_n(spec)
    # E_p_i_d_t = get_E_p_i_d_t(df, n)
    E_dash_dash_E_PV_gen_d_t = get_E_dash_dash_E_PV_gen_d_t(n, E_p_i_d_t, K_PM_i, K_IN)


    # 蓄電池の満充電容量
    W_rtd_batt = get_W_rtd_batt(spec)
    V_rtd_batt = get_V_rtd_batt(spec)
    C_fc_rtd = get_C_fc_rtd(W_rtd_batt, V_rtd_batt)
    C_fc_d_t = get_C_fc_d_t(C_fc_rtd)

    # 10.2 表示・計測・操作ユニット等の仕様

    # 作動時における表示・計測・操作ユニット等の消費電力
    P_aux_others_oprt = get_P_aux_others_oprt()

    # 待機時における表示・計測・操作ユニット等の消費電力
    P_aux_others_stby = get_P_aux_others_stby()

    # 9.9 蓄電池ユニットの仕様

    # 蓄電池ユニットの仕様

    # 蓄電池の定格容量 [kWh]
    W_rtd_batt = get_W_rtd_batt(spec)

    # 蓄電池の充放電可能容量に対する放電天使残容量の割合 [-]
    r_LCP_batt = get_r_LCP_batt(spec)

    # 蓄電池の定格電圧 [V]
    V_rtd_batt = get_V_rtd_batt(spec)

    # 蓄電池の下限電圧 [V]
    V_star_lower_batt = get_V_star_lower_batt(spec)

    # 蓄電池の上限電圧 [V]
    V_star_upper_batt = get_V_star_upper_batt(spec)

    if V_star_lower_batt > V_star_upper_batt:
        raise ValueError('V_star_upper_batt < V_star_lower_batt')

    # 蓄電池の下限電圧に対応する充電率 (-)
    SOC_star_lower = get_SOC_star_lower(spec)

    # 蓄電池の上限電圧に対応する充電率 (-)
    SOC_star_upper = get_SOC_star_upper(spec)

    if SOC_star_lower > SOC_star_upper:
        raise ValueError('SOC_star_lower > SOC_star_upper')
 
    # 蓄電池の種類 (-)
    type_batt = get_type_batt(V_star_upper_batt, V_star_lower_batt)

    # 蓄電池モジュールの周囲温度
    T_amb_bmdl_d_t = get_T_amb_bmdl_d_t(theta_ex_d_t)

    # 1月1日0 時における蓄電池の充放電可能容量に対する放電可能容量の割合
    r_int_dchg_batt = get_r_int_dchg_batt(spec)

    # 蓄電池ユニットが最大充電可能電力量を充電する時間
    delta_tau_max_chg_d_t = get_delta_tau_max_chg_d_t()

    # 蓄電池ユニットが最大放電可能電力量を放電する時間
    delta_tau_max_dchg_d_t = get_delta_tau_max_dchg_d_t()

    # 9.10 蓄電池モジュールの周囲温度
    for dt, (SC, E_E_dmd_excl, E_dash_dash_E_PV_gen, T_amb_bmdl, C_fc, delta_tau_max_chg, delta_t_max_dchg) in enumerate(zip(SC_d_t, E_E_dmd_excl_d_t, E_dash_dash_E_PV_gen_d_t, T_amb_bmdl_d_t, C_fc_d_t, delta_tau_max_chg_d_t, delta_tau_max_dchg_d_t)):

        # 蓄電池ユニットが放電を停止する充電率 式(44)
        SOC_star_min = get_SOC_star_min(SOC_star_lower, SOC_star_upper, r_LCP_batt, SC)

        if SOC_star_min < 0:
            raise ValueError('SOC_star_min < 0')

        # 蓄電池ユニットが充電を停止する充電率 式(43)
        SOC_star_max = get_SOC_star_max(SOC_star_upper)

        if SOC_star_min > SOC_star_max:
            raise ValueError('SOC_star_min > SOC_star_max')

        # 放電可能容量 式(35)
        if dt == 0:
            # 1月1日0時の放電可能容量 式(35-1)
            C_oprt_dchg = get_C_oprt_dchg_0(C_fc, SOC_star_max, SOC_star_min, r_int_dchg_batt)
        else:
            # 1月1日1時以降の放電可能容量 式(35-2)
            C_oprt_dchg = get_C_oprt_dchg(C_fc, SOC_st1, SOC_star_min)

        # 蓄電池の充電可能容量 (Ah) 式(34)
        C_oprt_chg = get_C_oprt_chg(C_fc, SOC_star_max, SOC_star_min, C_oprt_dchg)



        # 9.1 最大充電可能電力量

        # 蓄電池ユニットが最大充電可能電力量を充電する時の電流 式(28)
        I_max_chg = get_I_max_chg(C_oprt_chg, delta_tau_max_chg)

        # 蓄電池の内部抵抗 式(40)
        R_intr = get_R_intr(T_amb_bmdl, type_batt)

        # 状態0にある場合の充電池の充電率 式(36-1)
        SOC_st0 =  get_SOC_st0(SOC_star_min, C_oprt_dchg, C_fc)

        # 蓄電池ユニットが最大充電可能電力量を充電する時の電圧 式(27)
        V_max_chg = get_V_max_chg(SOC_st0, SOC_star_max, T_amb_bmdl, type_batt, V_rtd_batt, I_max_chg, R_intr)

        # 蓄電池ユニットによる最大充電可能電力量 (kWh/h) 式(26)
        E_dash_dash_E_SB_max_chg = get_E_dash_dash_E_SB_max_chg(I_max_chg, V_max_chg, delta_tau_max_chg)

        # 9.5.1 充電可能容量

        # 放電可能容量 式(35-2)
        C_oprt_chg = get_C_oprt_chg(C_fc, SOC_star_max, SOC_star_min, C_oprt_dchg)


        # 蓄電池ユニットが最大放電可能電力量を放電する時の電流 式(31)
        I_max_dchg = get_I_max_dchg(C_oprt_dchg, delta_t_max_dchg)

        # 蓄電池ユニットが最大放電可能電力量を放電する時の電圧 式(30)
        V_max_dchg = get_V_max_dchg(SOC_st0, SOC_star_min, T_amb_bmdl, type_batt, V_rtd_batt, I_max_dchg, R_intr)

        # 蓄電池ユニットによる最大放電可能電力量 式(29)
        E_dash_dash_E_SB_max_dchg = get_E_dash_dash_E_SB_max_dchg(I_max_dchg, V_max_dchg, delta_t_max_dchg)

        # 11. 蓄電設備の作動時間数

        # 蓄電設備の作動時間数 式(53)
        tau_oprt_PSS = get_tau_oprt_PSS(E_dash_dash_E_PV_gen, E_E_dmd_excl, E_dash_dash_E_SB_max_dchg)


        # 8.7 補機の消費電力量

        E_E_aux_PCS = get_E_E_aux_PCS(P_aux_PCS_oprt, tau_oprt_PSS, P_aux_PCS_stby)

        # 表示・計測・操作ユニット等の消費電力量 式(52)
        E_E_aux_others = get_E_E_aux_others(P_aux_others_oprt, tau_oprt_PSS, P_aux_others_stby)

        # 7. 補機の消費電力

        # 蓄電設備の補機の消費電力量 式(8)
        E_E_aux_PSS = get_E_E_aux_PSS(E_E_aux_PCS, E_E_aux_others)


        # 9. 蓄電池ユニット

        # 9.5 蓄電量

        # 9.5.2 放電可能容量



        # 9.5.1 充電可能容量


        # 8. パワーコンディショナ（ハイブリット一体型）  


        # 8.4 最大供給可能電力量の分電盤側における換算値

        # 蓄電池ユニットによる最大供給可能電力量 式(15)
        E_dash_dash_E_SB_max_sup = get_E_dash_dash_E_SB_max_sup(E_dash_dash_E_SB_max_dchg)

        # 太陽光発電設備による最大供給可能電力量 式(14)
        E_dash_dash_E_PV_max_sup = get_E_dash_dash_E_PV_max_sup(E_dash_dash_E_PV_gen)

        # 蓄電池ユニットによる最大供給可能電力量の分電盤側における換算値 式(13)
        E_E_SB_max_sup = get_E_E_SB_max_sup(E_dash_dash_E_SB_max_sup, E_dash_dash_E_in_rtd_SBtoDB, alpha_SBtoDB, beta_SBtoDB, eta_ce_lim_SBtoDB)

        # 太陽光発電設備による最大供給可能電力量の分電盤側における換算値 式(12)

        E_E_PV_max_sup = get_E_E_PV_max_sup(E_dash_dash_E_PV_max_sup, E_dash_dash_E_in_rtd_PVtoDB, alpha_PVtoDB, beta_PVtoDB, eta_ce_lim_PVtoDB)


        # 6. 最大供給可能電力量および余剰電力量

        # 蓄電設備による最大供給可能電力量の分電盤側における換算値 式(5)
        E_E_PSS_max_sup = get_E_E_PSS_max_sup(E_E_PV_max_sup, E_E_SB_max_sup)

        # パワーコンディショナおよび蓄電設備の補機の消費電力量を含む電力需要 式(7)
        E_E_dmd_incl = get_E_E_dmd_incl(E_E_dmd_excl, E_E_aux_PSS)

        # 余剰電力量 式(6)
        E_E_srpl = get_E_E_srpl(E_E_PV_max_sup, E_E_dmd_incl)

        # 余剰電力量の太陽光発電設備側における換算値 式(10)
        if E_E_srpl > 0:
            E_dash_dash_E_srpl = get_E_dash_dash_E_srpl(E_E_srpl, E_dash_dash_E_in_rtd_PVtoDB, alpha_PVtoDB, beta_PVtoDB)
        else:
            E_dash_dash_E_srpl = 0

        # 蓄電池ユニットによる最大充電可能電力量の分電盤側における換算値 式(16)
        E_E_SB_max_chg = get_E_E_SB_max_chg(E_dash_dash_E_SB_max_chg, E_E_srpl, E_dash_dash_E_srpl, E_dash_dash_E_in_rtd_PVtoSB, alpha_PVtoSB, beta_PVtoSB, eta_ce_lim_PVtoSB)

        # 8.3 蓄電池ユニットによる放電量のうちの供給分

        # 8.2 余剰電力量の太陽光発電設備側における換算値

        # 5. 太陽光発電設備による発電量のうちの自家消費分・売電分・充電分および蓄電設備による放電量のうちの自家消費分

        # 太陽光発電設備による発電量のうちの自家消費分 式(1)
        E_E_PV_h = get_E_E_PV_h(E_E_srpl, E_E_PV_max_sup, E_E_dmd_incl, SC)

        # 太陽光発電設備による発電量のうちの充電分の分電盤側における換算値 式(3)
        E_E_PV_chg = get_E_E_PV_chg(E_E_srpl, E_E_SB_max_chg, SC)


        # 太陽光発電設備による発電量のうちの充電分 式(9)
        E_dash_dash_E_PV_chg = get_E_dash_dash_E_PV_chg(E_E_PV_chg, E_dash_dash_E_srpl, E_E_srpl, E_dash_dash_E_in_rtd_PVtoSB, alpha_PVtoSB, beta_PVtoSB, eta_ce_lim_PVtoSB)

        # 太陽光発電設備による発電量のうちの売電分 式(2)
        E_E_PV_sell = get_E_E_PV_sell(E_E_srpl, E_E_PV_chg, SC)

        # 蓄電設備による放電量のうちの自家消費分 式(4)
        E_E_PSS_h = get_E_E_PSS_h(E_E_srpl, E_E_dmd_incl, E_E_PSS_max_sup, E_E_PV_h, SC)


        # 蓄電池ユニットによる放電量のうちの供給分の分電盤側における換算値 式(11b)
        E_E_SB_sup = get_E_E_SB_sup(E_E_PSS_h)


        # 蓄電池ユニットによる放電量のうちの供給分 式(11a)
        if E_E_SB_sup > 0:
            E_dash_dash_E_SB_sup = get_E_dash_dash_E_SB_sup(E_E_SB_sup, E_dash_dash_E_in_rtd_SBtoDB, alpha_SBtoDB, beta_SBtoDB)
        else:
            E_dash_dash_E_SB_sup = 0

        # 蓄電池ユニットによる放電量 式(33)
        E_dash_dash_E_SB_dchg = get_E_dash_dash_E_SB_dchg(E_dash_dash_E_SB_sup)

        # 蓄電池ユニットによる充電量 式(32)
        E_dash_dash_E_SB_chg = get_E_dash_dash_E_SB_chg(E_dash_dash_E_PV_chg)



        # 蓄電池ユニットの充電時間
        delta_t_chg = get_delta_tau_chg(E_dash_dash_E_SB_chg, E_dash_dash_E_SB_dchg)

        # 蓄電池ユニットの放電時間
        delta_t_dchg = get_delta_tau_dchg(E_dash_dash_E_SB_chg, E_dash_dash_E_SB_dchg)

        # 蓄電池が状態1にある場合の蓄電池の充電率の仮値 式(39c)
        SOC_hat_st1 =  get_SOC_hat_st1(SOC_st0, C_fc, delta_t_chg, delta_t_dchg, V_rtd_batt, E_dash_dash_E_SB_chg, E_dash_dash_E_SB_dchg)

        # 蓄電池の開回路電圧 式(39a)
        V_OC = get_V_OC(SOC_st0, SOC_hat_st1, E_dash_dash_E_SB_chg, E_dash_dash_E_SB_dchg, T_amb_bmdl, type_batt, V_rtd_batt)

        # 充電に対する蓄電池の電流 式(37)
        I_chg = get_I_chg(E_dash_dash_E_SB_chg, E_dash_dash_E_SB_dchg, V_OC, R_intr)

        # 放電に対する蓄電池の電流 式(38)
        I_dchg = get_I_dchg(E_dash_dash_E_SB_chg, E_dash_dash_E_SB_dchg, V_OC, R_intr)
        
        # 状態1にある場合の充電池の充電率 式(36-2)
        SOC_st1 =  get_SOC_st1(SOC_st0, SOC_star_max, SOC_star_min, I_chg, I_dchg, delta_t_chg, delta_t_dchg, C_fc, E_dash_dash_E_SB_chg, E_dash_dash_E_SB_dchg)
        #print('SOC_st1={}, SOC_star_min={}, SOC_star_max={}'.format(SOC_st1, SOC_star_min, SOC_star_max))

        # (1)
        bl.E_E_PV_h_d_t[dt] = E_E_PV_h
        # (2)
        bl.E_E_PV_sell_d_t[dt] = E_E_PV_sell
        # (3)
        bl.E_E_PV_chg_d_t[dt] = E_E_PV_chg
        # (4)
        bl.E_E_PSS_h_d_t[dt] = E_E_PSS_h
        # (5)
        bl.E_E_PSS_max_sup_d_t[dt] = E_E_PSS_max_sup
        # (6)
        bl.E_E_srpl_d_t[dt] = E_E_srpl
        # (7)
        bl.E_E_dmd_incl_d_t[dt] = E_E_dmd_incl
        # (8)
        bl.E_E_aux_PSS_d_t[dt] = E_E_aux_PSS
        # (9a)
        bl.E_dash_dash_E_PV_chg_d_t[dt] = E_dash_dash_E_PV_chg
        # (10)
        bl.E_dash_dash_E_srpl_d_t[dt] = E_dash_dash_E_srpl
        # (11)
        bl.E_dash_dash_E_SB_sup_d_t[dt] = E_dash_dash_E_SB_sup
        # (12)
        bl.E_E_PV_max_sup_d_t[dt] = E_E_PV_max_sup
        # (13)
        bl.E_E_SB_max_sup_d_t[dt] = E_E_SB_max_sup
        # (14)
        bl.E_dash_dash_E_PV_max_sup_d_t[dt] = E_dash_dash_E_PV_max_sup
        # (15)
        bl.E_dash_dash_E_SB_max_sup_d_t[dt] = E_dash_dash_E_SB_max_sup
        # (16)
        bl.E_E_SB_max_chg_d_t[dt] = E_E_SB_max_chg
        # (25)
        bl.E_E_aux_PCS_d_t[dt] = E_E_aux_PCS


    output_data = pd.DataFrame(
        [
            bl.SC_d_t,
            bl.E_E_dmd_excl_d_t,
            bl.theta_ex_d_t,
            bl.E_p_i_d_t[0],
            bl.E_p_i_d_t[1],
            bl.E_p_i_d_t[2],
            bl.E_p_i_d_t[3],
            bl.E_E_PV_h_d_t,
            bl.E_E_PV_sell_d_t,
            bl.E_E_PV_chg_d_t,
            bl.E_E_PSS_h_d_t,
            bl.E_E_PSS_max_sup_d_t,
            bl.E_E_srpl_d_t,
            bl.E_E_dmd_incl_d_t,
            bl.E_E_aux_PSS_d_t,
            bl.E_dash_dash_E_PV_chg_d_t,
            bl.E_dash_dash_E_srpl_d_t,
            bl.E_dash_dash_E_SB_sup_d_t,
            bl.E_E_PV_max_sup_d_t,
            bl.E_E_SB_max_sup_d_t,
            bl.E_dash_dash_E_PV_max_sup_d_t,
            bl.E_dash_dash_E_SB_max_sup_d_t,
            bl.E_E_SB_max_chg_d_t,
            bl.E_E_aux_PCS_d_t
        ],
        index=[
            "SC",
            "E_E_dmd_excl",
            "theta_ex_d_t",
            "E_p_0",
            "E_p_1",
            "E_p_2",
            "E_p_3",
            "E_E_PV_h",
            "E_E_PV_sell",
            "E_E_PV_chg",
            "E_E_PSS_h",
            "E_E_PSS_max_sup",
            "E_E_srpl",
            "E_E_dmd_incl",
            "E_E_aux_PSS",
            "E_dash_dash_E_PV_chg",
            "E_dash_dash_E_srpl",
            "E_dash_dash_E_SB_sup",
            "E_E_PV_max_sup",
            "E_E_SB_max_sup",
            "E_dash_dash_E_PV_max_sup",
            "E_dash_dash_E_SB_max_sup",
            "E_E_SB_max_chg",
            "E_E_aux_PCS"
        ]
    ).transpose()

    return output_data

