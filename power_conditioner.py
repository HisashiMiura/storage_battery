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
        self.E_dash_dash_E_in_rtd_SBtoDB = spec['E_dash_dash_E_in_rtd_SBtoDB']
        self.eta_ce_lim_SBtoDB = spec['eta_ce_lim_SBtoDB']
        self.alpha_SBtoDB = spec['alpha_SBtoDB']
        self.beta_SBtoDB = spec['beta_SBtoDB']
        # 作動時におけるパワーコンディショナの補機の消費電力, W
        self.P_aux_PCS_oprt = spec['P_aux_PCS_oprt']
        # 待機時におけるパワーコンディショナの補機の消費電力, W
        self.P_aux_PCS_stby = spec['P_aux_PCS_stby']


        # 作動時における表示・計測・操作ユニット等の消費電力, W
        self.P_aux_others_oprt = 3.0

        # 待機時における表示・計測・操作ユニット等の消費電力, W
        self.P_aux_others_stby = 2.0


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


