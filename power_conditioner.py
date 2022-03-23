import numpy as np
from typing import Union, Tuple
import math


class PowerConditioner:

    def __init__(self, spec: dict):
        """パワーコンディショナーに関するプロパティを設定する。

        Args:
            spec (Dict): 蓄電設備に関する仕様
        """

        self.E_dash_dash_E_in_rtd_PVtoDB = spec['E_dash_dash_E_in_rtd_PVtoDB']
        self.eta_ce_lim_PVtoDB = spec['eta_ce_lim_PVtoDB']
        self.alpha_PVtoDB = spec['alpha_PVtoDB']
        self.beta_PVtoDB = spec['beta_PVtoDB']
        self.E_dash_dash_E_in_rtd_PVtoSB = spec['E_dash_dash_E_in_rtd_PVtoSB']
        self.eta_ce_lim_PVtoSB = spec['eta_ce_lim_PVtoSB']
        self.alpha_PVtoSB = spec['alpha_PVtoSB']
        self.beta_PVtoSB = spec['beta_PVtoSB']
        # 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの蓄電池ユニット側における定格入力電力量, kWh/h
        self.E_dash_dash_E_in_rtd_SBtoDB = spec['E_dash_dash_E_in_rtd_SBtoDB']
        # 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの合成変換効率の下限, -
        self.eta_ce_lim_SBtoDB = spec['eta_ce_lim_SBtoDB']
        # 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の傾き, -
        self.alpha_SBtoDB = spec['alpha_SBtoDB']
        # 蓄電池ユニットから分電盤へ電力を送る場合のパワーコンディショナの合成変換効率を求める回帰式の切片, -
        self.beta_SBtoDB = spec['beta_SBtoDB']
        # 作動時におけるパワーコンディショナの補機の消費電力, W
        self.P_aux_PCS_oprt = spec['P_aux_PCS_oprt']
        # 待機時におけるパワーコンディショナの補機の消費電力, W
        self.P_aux_PCS_stby = spec['P_aux_PCS_stby']


        # 作動時における表示・計測・操作ユニット等の消費電力, W
        self.P_aux_others_oprt = 3.0

        # 待機時における表示・計測・操作ユニット等の消費電力, W
        self.P_aux_others_stby = 2.0

    def get_E_E_srpl_d_t(self, E_E_PV_max_sup_d_t: float, E_E_dmd_incl_d_t: float) -> float:
        """ 1 時間当たりの余剰電力量

        Args:
            E_E_PV_max_sup_d_t: 日付 d の時刻 t における1時間当たりの太陽光発電設備による最大供給可能電力量の分電盤側における換算値, kWh/h
            E_E_dmd_incl_d_t: 日付 d の時刻 t における1 時間当たりの蓄電設備の補機の消費電力量を含む電力需要, kWh/h

        Returns:
            日付 d の時刻 t における1 時間当たりの余剰電力量, kWh/h
        """

        return max(E_E_PV_max_sup_d_t - E_E_dmd_incl_d_t, 0)

    def get_E_E_dmd_incl_d_t(self, E_E_dmd_excl_d_t: float, E_E_aux_PSS_d_t: float) -> float:
        """1 時間当たりの蓄電設備の補機の消費電力量を含む電力需要

        Args:
            E_E_dmd_excl_d_t: 日付 d の時刻 t における1時間当たりの蓄電設備の補機の消費電力量を除く電力需要, kWh/h
            E_E_aux_PSS_d_t: 日付 d の時刻 t における1時間あたりの蓄電設備の補機の消費電力量, kWh/h

        Returns:
            日付 d の時刻 t における1 時間当たりの蓄電設備の補機の消費電力量を含む電力需要, kWh/h
        """

        return E_E_dmd_excl_d_t + E_E_aux_PSS_d_t

    def get_E_E_PSS_max_sup_d_t(self, E_E_PV_max_sup_d_t: float, E_E_SB_max_sup_d_t: float) -> float:
        """1時間当たりの蓄電設備による最大供給可能電力量の分電盤側における換算値

        Args:
            E_E_PV_max_sup_d_t: 日付 d の時刻 t における1時間当たりの太陽光発電設備による最大供給可能電力量の分電盤側における換算値, kWh/h
            E_E_SB_max_sup_d_t: 日付 d の時刻 t における1時間当たりの蓄電池ユニットによる最大供給可能電力量の分電盤側における換算値, kWh/h

        Returns:
            日付 d の時刻 t における1時間当たりの蓄電設備による最大供給可能電力量の分電盤側における換算値, kWh/h
        """

        return E_E_PV_max_sup_d_t + E_E_SB_max_sup_d_t

    def get_E_E_PV_max_sup_d_t(self, E_dash_dash_E_PV_max_sup_d_t: float) -> float:
        """1時間当たりの太陽光発電設備による最大供給可能電力量の分電盤側における換算値

        Args:
            E_dash_dash_E_PV_max_sup_d_t: 日付 d の時刻 t における1時間当たりの太陽光発電設備による最大供給可能電力量, kWh/h

        Returns:
            日付 d の時刻 t における1時間当たりの太陽光発電設備による最大供給可能電力量の分電盤側における換算値, kWh/h
        """

        if E_dash_dash_E_PV_max_sup_d_t > 0:

            eta_ce_PVtoDB = PowerConditioner.f_eta_ec(E_dash_dash_E_PV_max_sup_d_t, self.E_dash_dash_E_in_rtd_PVtoDB, self.alpha_PVtoDB, self.beta_PVtoDB, self.eta_ce_lim_PVtoDB)

            return eta_ce_PVtoDB * min(E_dash_dash_E_PV_max_sup_d_t, self.E_dash_dash_E_in_rtd_PVtoDB)

        else:

            return 0.0

    def get_E_E_SB_max_sup_d_t(self, E_dash_dash_E_SB_max_sup_d_t: float) -> float:
        """蓄電池ユニットによる最大供給可能電力量の分電盤側における換算値

        Args:
            E_dash_dash_E_SB_max_sup_d_t: 日付 d の時刻 t における1時間当たりの蓄電池ユニットによる最大供給可能電力量, kWh/h

        Returns:
            日付 d の時刻 t における1時間当たりの蓄電池ユニットによる最大供給可能電力量の分電盤側における換算値, kWh/h
        """

        if E_dash_dash_E_SB_max_sup_d_t > 0:

            eta_ce_SBtoDB = PowerConditioner.f_eta_ec(E_dash_dash_E_SB_max_sup_d_t, self.E_dash_dash_E_in_rtd_SBtoDB, self.alpha_SBtoDB, self.beta_SBtoDB, self.eta_ce_lim_SBtoDB)

            return eta_ce_SBtoDB * min(E_dash_dash_E_SB_max_sup_d_t, self.E_dash_dash_E_in_rtd_SBtoDB)
        
        else:

            return 0.0

    def get_E_dash_dash_E_PV_max_sup_d_t(self, E_dash_dash_E_PV_gen_d_t: float) -> float:
        """1時間当たりの太陽光発電設備による最大供給可能電力量, kWh/h

        Args:
            E_dash_dash_E_PV_gen_d_t: 日付 d の時刻 t における1 時間当たりの太陽光発電設備による発電量, kWh/h

        Returns:
            日付 d の時刻 t における1時間当たりの太陽光発電設備による最大供給可能電力量, kWh/h
        """

        return E_dash_dash_E_PV_gen_d_t

    def get_E_dash_dash_E_SB_max_sup_d_t(self, E_dash_dash_E_SB_max_dchg_d_t: float) -> float:
        """1時間当たりの蓄電池ユニットによる最大供給可能電力量, kWh/h

        Args:
            E_dash_dash_E_SB_max_dchg_d_t: 日付 d の時刻 t における蓄電池ユニットによる最大放電可能電力量, kWh/h

        Returns:
            日付 d の時刻 t における1時間当たりの蓄電池ユニットによる最大供給可能電力量, kWh/h
        """

        E_dash_dash_E_SB_max_sup_d_t = E_dash_dash_E_SB_max_dchg_d_t

        return E_dash_dash_E_SB_max_sup_d_t

    def get_E_E_aux_PSS_d_t(self, E_E_aux_PCS_d_t: float, E_E_aux_others_d_t: float) -> float:
        """1 時間あたりの蓄電設備の補機の消費電力量

        Args:
            E_E_aux_PCS_d_t: 日付 d の時刻 t における1時間当たりのパワーコンディショナの補機の消費電力量, kWh/h
            E_E_aux_others_d_t: 日付 d の時刻 t における1時間当たりの表示・計測・操作ユニット等の消費電力量, kWh/h

        Returns:
            日付 d の時刻 t における1時間あたりの蓄電設備の補機の消費電力量, kWh/h
        """

        E_E_aux_PSS_d_t = E_E_aux_PCS_d_t + E_E_aux_others_d_t

        return E_E_aux_PSS_d_t

    def get_E_E_aux_others_d_t(self, tau_oprt_PSS_d_t: float) -> float:
        """表示・計測・操作ユニット等の消費電力量 (kWh/h)

        Args:
            tau_oprt_PSS_d_t: 日付 d の時刻 t における 1 時間当たりの蓄電設備の作動時間数, h/h

        Returns:
            日付 d の時刻 t における 1 時間当たりの表示・計測・操作ユニット等の消費電力量, kWh/h
        """

        return (self.P_aux_others_oprt * tau_oprt_PSS_d_t + self.P_aux_others_stby * (1 - tau_oprt_PSS_d_t)) / 1000


    def get_E_E_aux_PCS_d_t(self, tau_oprt_PSS_d_t: float) -> float:
        """パワーコンディショナの補機の消費電力量

        Args:
            tau_oprt_PSS_d_t: 日付 d の時刻 t における 1 時間当たりの蓄電設備の作動時間数, h/h

        Returns:
            日付 d の時刻 t における 1 時間当たりのパワーコンディショナの補機の消費電力量, kWh/h
        """

        E_E_aux_PCS_d_t = (self.P_aux_PCS_oprt * tau_oprt_PSS_d_t + self.P_aux_PCS_stby * (1.0 - tau_oprt_PSS_d_t)) / 1000

        return E_E_aux_PCS_d_t


    def get_tau_oprt_PSS_d_t(self, E_dash_dash_E_PV_gen_d_t: float, E_E_dmd_excl_d_t: float, E_dash_dash_E_SB_max_dchg_d_t: float) -> float:
        """ 1時間当たりの蓄電設備の作動時間数

        Args:
            E_dash_dash_E_PV_gen_d_t: 日付 d の時刻 t における 1 時間当たりの太陽光発電設備による発電量, kWh/h
            E_E_dmd_excl_d_t: 日付 d の時刻 t における 1 時間当たりのパワーコンディショナおよび蓄電池ユニットの補機の消費電力量を除く電力需要, kWh/h
            E_dash_dash_E_SB_max_dchg_d_t: 日付 d の時刻 t における蓄電池ユニットによる最大放電可能電力量, kWh/h

        Returns:
            日付 d の時刻 t における 1 時間当たりの蓄電設備の作動時間数, h
        """

        if E_dash_dash_E_PV_gen_d_t > 0:
            # 太陽光発電設備による発電が行われている場合
            return 1.0
        else:
            # 太陽光発電設備による発電が行われていない場合
            if E_E_dmd_excl_d_t > 0 and E_dash_dash_E_SB_max_dchg_d_t > 0:
                return 1.0
            else:
                return 0.0
    
    @staticmethod
    def f_E_in(x_E_out: float, x_E_in_rtd: float, x_a: float, x_b: float) -> float:
        """入力電力量を出力電力量から逆算する関数

        Args:
            x_E_out: 関数の引数(出力電力量), kWh/h
            x_E_in_rtd: 関数の引数 (定格入力電力量), kWh/h
            x_a: 関数の引数 (パワーコンディショナの合成変換効率を求める回帰式の傾き), -
            x_b: 関数の引数 (パワーコンディショナの合成変換効率を求める回帰式の切片), -

        Returns:
            入力電力量, kWh/h
        """

        r_lim_rtd = 0.25

        _E_in = min(max((-x_a * x_E_in_rtd + x_E_out) / x_b, x_E_in_rtd * r_lim_rtd), x_E_in_rtd) 

        if _E_in / x_E_in_rtd < 0.25:
            E_in = x_E_out / 0.96
        else:
            E_in = _E_in

        return E_in

    @staticmethod
    def f_eta_ec(x_E_in: float, x_E_in_rtd: float, x_a: float, x_b: float, x_eta_ce_lim: float) -> float:
        """合成変換効率を求める関数
    
        Args:
            x_E_in: 関数の引数(入力電力量), kWh/h
            x_E_in_rtd: 関数の引数 (定格入力電力量), kWh/h
            x_a: 関数の引数 (パワーコンディショナの合成変換効率を求める回帰式の傾き), -
            x_b: 関数の引数 (パワーコンディショナの合成変換効率を求める回帰式の切片), -
            x_eta_ce_lim: 関数の引数 (合成変換効率の下限), -

        Retusn:
            合成変換効率, -
        """
    
        if x_E_in <= 0:
            return x_eta_ce_lim
        elif x_E_in > 0:
            return max(x_a * x_E_in_rtd / min(x_E_in, x_E_in_rtd) + x_b, x_eta_ce_lim)




