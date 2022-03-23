import numpy as np
import yaml
import pandas as pd
import math
from typing import Union, Tuple

from battery_logger import BatteryLogger
from battery import Battery
from power_conditioner import PowerConditioner

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
    return PowerConditioner.f_E_in(x_E_out, E_dash_dash_E_in_rtd_PVtoDB, alpha_PVtoDB, beta_PVtoDB)


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
        PowerConditioner.f_eta_ec(x_E_in, E_dash_dash_E_in_rtd_PVtoSB, alpha_PVtoSB, beta_PVtoSB, eta_ce_lim_PVtoSB)
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
    return PowerConditioner.f_E_in(x_E_out, E_dash_dash_E_in_rtd_PVtoSB, alpha_PVtoSB, beta_PVtoSB)


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
    return PowerConditioner.f_E_in(x_E_out, E_dash_dash_E_in_rtd_SBtoDB, alpha_SBtoDB, beta_SBtoDB)


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


# 12. 太陽光発電設備による発電量


def get_E_dash_dash_E_PV_gen_ds_ts(E_p_is_ds_ts: np.ndarray, K_PM_is: list, K_IN: float) -> float:
    """日付d時刻tにおける1時間当たりの太陽光発電設備による発電量 (kWh/h)

    Args:
        E_p_is_ds_ts: 日付 d の時刻 t における1時間当たりの太陽電池アレイ i の発電量, kWh/h
        K_PM_is: 太陽電池アレイiのアレイ不可整合補正係数 (-)
        K_IN (float): インバータ回路補正係数 (-)

    Returns:
        float: 日付d時刻tにおける1時間当たりの太陽光発電設備による発電量 (kWh/h)
    """

    E_dash_dash_E_PV_gen_d_t = np.sum(E_p_is_ds_ts / np.array(K_PM_is).reshape(-1, 1), axis=0) / K_IN

    return E_dash_dash_E_PV_gen_d_t


def calculate(spec: dict, SC_ds_ts: np.ndarray, E_E_dmd_excl_ds_ts: np.ndarray, theta_ex_ds_ts: np.ndarray, E_p_is_ds_ts: np.ndarray)-> pd.DataFrame:
    """機器仕様と時系列電力需要から出力値の計算を行う

    Args:
        spec: 機器仕様
        SC_ds_ts: 系統からの電力供給の有無 [8760]
        E_E_dmd_excl_ds_ts: 日付 d の時刻 t における1時間当たりの蓄電設備の補機の消費電力量を除く電力需要 [8760], kWh/h
        theta_ex_ds_ts: 日付 d の時刻 t における外気温度 [8760], ℃
        E_p_is_ds_ts: 日付 d の時刻 t における1時間当たりの太陽電池アレイ i の発電量 [i, 8760], kWh/h

    Returns:
        計算結果
    """

    bl = BatteryLogger(SC_d_t=SC_ds_ts, E_E_dmd_excl_d_t=E_E_dmd_excl_ds_ts, theta_ex_d_t=theta_ex_ds_ts, E_p_i_d_t=E_p_is_ds_ts)

    # 8.8 パワーコンディショナの仕様

    E_dash_dash_E_in_rtd_PVtoDB, _, alpha_PVtoDB, beta_PVtoDB, \
    E_dash_dash_E_in_rtd_PVtoSB, eta_ce_lim_PVtoSB, alpha_PVtoSB, beta_PVtoSB, \
    E_dash_dash_E_in_rtd_SBtoDB, _, alpha_SBtoDB, beta_SBtoDB, _, _ = get_PCS_spec(spec)

    pc = PowerConditioner(spec=spec)
    
    # 12. 太陽光発電設備による発電量

    # 太陽光発電設備による発電量 式(52)
    K_IN = spec["K_IN"]
    K_PM_is = spec['K_PM']
    E_dash_dash_E_PV_gen_ds_ts = get_E_dash_dash_E_PV_gen_ds_ts(E_p_is_ds_ts=E_p_is_ds_ts, K_PM_is=K_PM_is, K_IN=K_IN)

    bt = Battery(spec=spec)

    for n in range(8760):
        
        SC_d_t = SC_ds_ts[n]
        E_dash_dash_E_PV_gen_d_t = E_dash_dash_E_PV_gen_ds_ts[n]

        # 蓄電池ユニットによる最大充放電可能電力量, kWh/h
        E_dash_dash_E_SB_max_chg_d_t, E_dash_dash_E_SB_max_dchg_d_t = bt.calc_E_dash_dash_E_SB_max_d_t(theta_ex_d_t=theta_ex_ds_ts[n], SC_d_t=SC_ds_ts[n])

        # 蓄電設備の作動時間数 式(53)
        tau_oprt_PSS_d_t = pc.get_tau_oprt_PSS_d_t(E_dash_dash_E_PV_gen_d_t=E_dash_dash_E_PV_gen_d_t, E_E_dmd_excl_d_t=E_E_dmd_excl_ds_ts[n], E_dash_dash_E_SB_max_dchg_d_t=E_dash_dash_E_SB_max_dchg_d_t)

        # パワーコンディショナの補機の消費電力量, kWh/h
        E_E_aux_PCS_d_t = pc.get_E_E_aux_PCS_d_t(tau_oprt_PSS_d_t=tau_oprt_PSS_d_t)

        # 表示・計測・操作ユニット等の消費電力量 式(52)
        E_E_aux_others_d_t = pc.get_E_E_aux_others_d_t(tau_oprt_PSS_d_t=tau_oprt_PSS_d_t)

        # 蓄電設備の補機の消費電力量 式(8)
        E_E_aux_PSS_d_t = pc.get_E_E_aux_PSS_d_t(E_E_aux_PCS_d_t=E_E_aux_PCS_d_t, E_E_aux_others_d_t=E_E_aux_others_d_t)

        # 蓄電池ユニットによる最大供給可能電力量 式(15)
        E_dash_dash_E_SB_max_sup_d_t = pc.get_E_dash_dash_E_SB_max_sup_d_t(E_dash_dash_E_SB_max_dchg_d_t=E_dash_dash_E_SB_max_dchg_d_t)

        # 太陽光発電設備による最大供給可能電力量 式(14)
        E_dash_dash_E_PV_max_sup_d_t = pc.get_E_dash_dash_E_PV_max_sup_d_t(E_dash_dash_E_PV_gen_d_t=E_dash_dash_E_PV_gen_d_t)

        # 蓄電池ユニットによる最大供給可能電力量の分電盤側における換算値 式(13)
        E_E_SB_max_sup_d_t = pc.get_E_E_SB_max_sup_d_t(E_dash_dash_E_SB_max_sup_d_t=E_dash_dash_E_SB_max_sup_d_t)

        # 太陽光発電設備による最大供給可能電力量の分電盤側における換算値 式(12)
        E_E_PV_max_sup_d_t = pc.get_E_E_PV_max_sup_d_t(E_dash_dash_E_PV_max_sup_d_t=E_dash_dash_E_PV_max_sup_d_t)

        # 蓄電設備による最大供給可能電力量の分電盤側における換算値 式(5)
        E_E_PSS_max_sup_d_t = pc.get_E_E_PSS_max_sup_d_t(E_E_PV_max_sup_d_t=E_E_PV_max_sup_d_t, E_E_SB_max_sup_d_t=E_E_SB_max_sup_d_t)

        # パワーコンディショナおよび蓄電設備の補機の消費電力量を含む電力需要 式(7)
        E_E_dmd_incl_d_t = pc.get_E_E_dmd_incl_d_t(E_E_dmd_excl_d_t=E_E_dmd_excl_ds_ts[n], E_E_aux_PSS_d_t=E_E_aux_PSS_d_t)

        # 余剰電力量 式(6)
        E_E_srpl_d_t = pc.get_E_E_srpl_d_t(E_E_PV_max_sup_d_t=E_E_PV_max_sup_d_t, E_E_dmd_incl_d_t=E_E_dmd_incl_d_t)

        # 余剰電力量の太陽光発電設備側における換算値 式(10)
        if E_E_srpl_d_t > 0:
            E_dash_dash_E_srpl = get_E_dash_dash_E_srpl(E_E_srpl_d_t, E_dash_dash_E_in_rtd_PVtoDB, alpha_PVtoDB, beta_PVtoDB)
        else:
            E_dash_dash_E_srpl = 0

        # 蓄電池ユニットによる最大充電可能電力量の分電盤側における換算値 式(16)
        E_E_SB_max_chg = get_E_E_SB_max_chg(E_dash_dash_E_SB_max_chg_d_t, E_E_srpl_d_t, E_dash_dash_E_srpl, E_dash_dash_E_in_rtd_PVtoSB, alpha_PVtoSB, beta_PVtoSB, eta_ce_lim_PVtoSB)

        # 太陽光発電設備による発電量のうちの自家消費分 式(1)
        E_E_PV_h = get_E_E_PV_h(E_E_srpl_d_t, E_E_PV_max_sup_d_t, E_E_dmd_incl_d_t, SC_d_t)

        # 太陽光発電設備による発電量のうちの充電分の分電盤側における換算値 式(3)
        E_E_PV_chg = get_E_E_PV_chg(E_E_srpl_d_t, E_E_SB_max_chg, SC_d_t)

        # 太陽光発電設備による発電量のうちの充電分 式(9)
        E_dash_dash_E_PV_chg = get_E_dash_dash_E_PV_chg(E_E_PV_chg, E_dash_dash_E_srpl, E_E_srpl_d_t, E_dash_dash_E_in_rtd_PVtoSB, alpha_PVtoSB, beta_PVtoSB, eta_ce_lim_PVtoSB)

        # 太陽光発電設備による発電量のうちの売電分 式(2)
        E_E_PV_sell = get_E_E_PV_sell(E_E_srpl_d_t, E_E_PV_chg, SC_d_t)

        # 蓄電設備による放電量のうちの自家消費分 式(4)
        E_E_PSS_h = get_E_E_PSS_h(E_E_srpl_d_t, E_E_dmd_incl_d_t, E_E_PSS_max_sup_d_t, E_E_PV_h, SC_d_t)

        # 蓄電池ユニットによる放電量のうちの供給分の分電盤側における換算値 式(11b)
        E_E_SB_sup = get_E_E_SB_sup(E_E_PSS_h)

        # 蓄電池ユニットによる放電量のうちの供給分 式(11a)
        if E_E_SB_sup > 0:
            E_dash_dash_E_SB_sup = get_E_dash_dash_E_SB_sup(E_E_SB_sup, E_dash_dash_E_in_rtd_SBtoDB, alpha_SBtoDB, beta_SBtoDB)
        else:
            E_dash_dash_E_SB_sup = 0

        # 状態1にある場合の充電池の充電率 式(36-2)
        # 次の時刻で使用するために蓄電池の充電率を書き換える。
        bt.update_SOC_st1_d_t(E_dash_dash_E_PV_chg_d_t=E_dash_dash_E_PV_chg, E_dash_dash_E_SB_sup_d_t=E_dash_dash_E_SB_sup, theta_ex_d_t=theta_ex_ds_ts[n], SC_d_t=SC_ds_ts[n])

        # (1)
        bl.E_E_PV_h_d_t[n] = E_E_PV_h
        # (2)
        bl.E_E_PV_sell_d_t[n] = E_E_PV_sell
        # (3)
        bl.E_E_PV_chg_d_t[n] = E_E_PV_chg
        # (4)
        bl.E_E_PSS_h_d_t[n] = E_E_PSS_h
        # (5)
        bl.E_E_PSS_max_sup_d_t[n] = E_E_PSS_max_sup_d_t
        # (6)
        bl.E_E_srpl_d_t[n] = E_E_srpl_d_t
        # (7)
        bl.E_E_dmd_incl_d_t[n] = E_E_dmd_incl_d_t
        # (8)
        bl.E_E_aux_PSS_d_t[n] = E_E_aux_PSS_d_t
        # (9a)
        bl.E_dash_dash_E_PV_chg_d_t[n] = E_dash_dash_E_PV_chg
        # (10)
        bl.E_dash_dash_E_srpl_d_t[n] = E_dash_dash_E_srpl
        # (11)
        bl.E_dash_dash_E_SB_sup_d_t[n] = E_dash_dash_E_SB_sup
        # (12)
        bl.E_E_PV_max_sup_d_t[n] = E_E_PV_max_sup_d_t
        # (13)
        bl.E_E_SB_max_sup_d_t[n] = E_E_SB_max_sup_d_t
        # (14)
        bl.E_dash_dash_E_PV_max_sup_d_t[n] = E_dash_dash_E_PV_max_sup_d_t
        # (15)
        bl.E_dash_dash_E_SB_max_sup_d_t[n] = E_dash_dash_E_SB_max_sup_d_t
        # (16)
        bl.E_E_SB_max_chg_d_t[n] = E_E_SB_max_chg
        # (25)
        bl.E_E_aux_PCS_d_t[n] = E_E_aux_PCS_d_t


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

