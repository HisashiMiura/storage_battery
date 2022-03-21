import numpy as np
from typing import Union, Tuple
import math


class Battery:

    def __init__(self, spec: dict):
        """蓄電池に関するプロパティを設定する。

        Args:
            spec (Dict): 蓄電設備に関する仕様
        """

        # 9.9 蓄電池ユニットの仕様（表4）

        # 蓄電池の定格容量, kWh
        self.W_rtd_batt = spec['W_rtd_batt']

        # 蓄電池の充放電可能容量に対する放電停止残容量の割合, -
        self.r_LCP_batt = spec['r_LCP_batt']

        # 蓄電池の定格電圧, V
        self.V_rtd_batt = spec['V_rtd_batt']

        # 蓄電池の下限電圧, V
        self.V_star_lower_batt = spec['V_star_lower_batt']

        # 蓄電池の上限電圧, V
        self.V_star_upper_batt = spec['V_star_upper_batt']

        # 上限・下限が逆転していないかどうかのチェック
        if self.V_star_lower_batt > self.V_star_upper_batt:
            raise ValueError('V_star_upper_batt < V_star_lower_batt')

        # 蓄電池の下限電圧に対応する充電率, -
        self.SOC_star_lower = spec['SOC_star_lower']

        # 蓄電池の上限電圧に対応する充電率, -
        self.SOC_star_upper = spec['SOC_star_upper']

        # 上限・下限が逆転していないかどうかのチェック
        if self.SOC_star_lower > self.SOC_star_upper:
            raise ValueError('SOC_star_lower > SOC_star_upper')

        # 蓄電池の種類, -
        self.type_batt = self.get_type_batt(
            V_star_upper_batt=self.V_star_upper_batt,
            V_star_lower_batt=self.V_star_lower_batt
        )

        # 蓄電池の初期満充電容量, Ah
        self.C_fc_rtd = self.get_C_fc_rtd(W_rtd_batt=self.W_rtd_batt, V_rtd_batt=self.V_rtd_batt)

        # 1月1日0時のおける蓄電池の充放電可能容量に対する放電可能容量の割合, -
        self.r_int_dchg_batt = spec['r_int_dchg_batt']

        # 充電池の充電率, -
        # 書き換え可能
        # TODO: 将来的にはログがとれるようにしておいた方が良い。
        # 1月1日0:00の値を入力しておく。
        self.SOC_d_t = self.SOC_star_upper * self.r_int_dchg_batt + self.SOC_star_lower * (1 - self.r_int_dchg_batt)

    def update_SOC_st1_d_t(self, E_dash_dash_E_PV_chg_d_t: float, E_dash_dash_E_SB_sup_d_t: float, theta_ex_d_t: float, SC_d_t: float):

        T_amb_bmdl_d_t, SOC_star_min_d_t, SOC_star_max_d_t, C_fc_d_t, R_intr_d_t = self.calc_common_parameters(theta_ex_d_t=theta_ex_d_t, SC_d_t=SC_d_t)

        # 日付 d の時刻 t における 1 時間当たりの蓄電池ユニットによる充放電量（充電を正、放電を負とする）, kWh/h
        E_dash_dash_E_SB_d_t = self.get_E_dash_dash_E_SB_d_t(E_dash_dash_E_PV_chg_d_t=E_dash_dash_E_PV_chg_d_t, E_dash_dash_E_SB_sup_d_t=E_dash_dash_E_SB_sup_d_t)

        # 日付 d の時刻 t における蓄電池ユニットの充放電時間, h
        delta_tau_d_t = self.get_delta_tau_d_t(E_dash_dash_E_SB_d_t=E_dash_dash_E_SB_d_t)

        # 蓄電池が状態1にある場合の蓄電池の充電率の仮値 式(39c)
        SOC_hat_st1_d_t = self.get_SOC_hat_st1_d_t(C_fc_d_t=C_fc_d_t, delta_tau_d_t=delta_tau_d_t, E_dash_dash_E_SB_d_t=E_dash_dash_E_SB_d_t)

        # 蓄電池の開回路電圧 式(39a)
        V_OC_d_t = self.get_V_OC_d_t(SOC_hat_st1_d_t=SOC_hat_st1_d_t, T_amb_bmdl_d_t=T_amb_bmdl_d_t)

        # 日付 d の時刻 t における充放電に対する蓄電池の電流（充電を正、放電を負とする）, A
        I_d_t = self.get_I_d_t(E_dash_dash_E_SB_d_t=E_dash_dash_E_SB_d_t, V_OC_d_t=V_OC_d_t, R_intr_d_t=R_intr_d_t)

        # 状態1にある場合の充電池の充電率 式(36-2)
        SOC_st1 = self.get_SOC_st1_d_t(SOC_star_max_d_t=SOC_star_max_d_t, SOC_star_min_d_t=SOC_star_min_d_t, C_fc_d_t=C_fc_d_t, delta_tau_d_t=delta_tau_d_t, I_d_t=I_d_t)

        # アップデート
        self.SOC_d_t = SOC_st1


    def get_SOC_st1_d_t(self, SOC_star_max_d_t: float, SOC_star_min_d_t: float, C_fc_d_t: float, delta_tau_d_t: float, I_d_t: float) -> float:
        """蓄電池が状態1にある場合の蓄電池の充電率 (-)

        Args:
            C_fc (float): 蓄電池の満充電容量 (Ah)
            delta_tau: 蓄電池ユニットの充放電時間, h
            I_d_t: 日付 d の時刻 t における充放電に対する蓄電池の電流（充電を正、放電を負とする）, A

        Returns:
            float: 蓄電池が状態1にある場合の蓄電池の充電率 (-)
        """

        SOC_st1 = self.SOC_d_t + I_d_t * delta_tau_d_t / C_fc_d_t

        if SOC_st1 > SOC_star_max_d_t:
            return SOC_star_max_d_t
        elif SOC_st1 < SOC_star_min_d_t:
            return SOC_star_min_d_t
        else:
            return SOC_st1

    def get_I_d_t(self, E_dash_dash_E_SB_d_t: float, V_OC_d_t: float, R_intr_d_t: float) -> float:
        """充放電に対する蓄電池の電流（充電を正、放電を負とする）

        Args:
            E_dash_dash_E_SB_d_t: 日付 d の時刻 t における1 時間当たりの蓄電池ユニットによる充放電量（充電を正、放電を負とする）, kWh/h
            V_OC_d_t: 日付 d の時刻 t における蓄電池の閉回路電圧, V
            R_intr_d_t: 日付 d の時刻 t における蓄電池の内部抵抗, Ω

        Returns:
            日付 d の時刻 t における充放電に対する蓄電池の電流（充電を正、放電を負とする）, A
        """

        return (math.sqrt(max(0, V_OC_d_t**2 + 4.0 * R_intr_d_t * E_dash_dash_E_SB_d_t * 1000)) - V_OC_d_t) / (2.0 * R_intr_d_t)

    def get_V_OC_d_t(self, SOC_hat_st1_d_t: float, T_amb_bmdl_d_t: float) -> float:
        """蓄電池の閉回路電圧

        Args:
            SOC_hat_st1_d_t: 日付 d の時刻 t における蓄電池が状態1にある場合の蓄電池の充電率の仮値, -
            T_amb_bmdl_d_t: 日付 d の時刻 t における蓄電池モジュールの周囲温度, K

        Returns:
            float: 日付 d の時刻 t における蓄電池の閉回路電圧 (V)
        """

        # 日付 d の時刻 t における蓄電池が状態0にある場合の蓄電池の充電率の仮値, -
        SOC_hat_st0 = self.SOC_d_t

        V_OC_d_t = (
            Battery.f_OCV(x_SOC=SOC_hat_st0, x_T_amb=T_amb_bmdl_d_t, x_type=self.type_batt, x_Vrtd=self.V_rtd_batt) 
            + Battery.f_OCV(x_SOC=SOC_hat_st1_d_t, x_T_amb=T_amb_bmdl_d_t, x_type=self.type_batt, x_Vrtd=self.V_rtd_batt)
        ) / 2

        return V_OC_d_t

    def get_SOC_hat_st1_d_t(self, C_fc_d_t: float, delta_tau_d_t: float, E_dash_dash_E_SB_d_t: float) -> float:
        """蓄電池が状態1にある場合の蓄電池の充電率の仮値 (-)

        Args:
            C_fc_d_t: 日付 d の時刻 t における蓄電池の満充電容量, Ah
            delta_tau_d_t: 日付 d の時刻 t における蓄電池の充放電時間, h
            E_dash_dash_E_SB_d_t: 1 時間当たりの蓄電池ユニットによる充放電量, kWh/h

        Returns:
            float: 日付 d の時刻 t における蓄電池が状態1にある場合の蓄電池の充電率の仮値, -
        """

        if E_dash_dash_E_SB_d_t == 0:
            return self.SOC_d_t
        else:
            return self.SOC_d_t + E_dash_dash_E_SB_d_t * 1000 / (C_fc_d_t / delta_tau_d_t) / self.V_rtd_batt

    def get_delta_tau_d_t(self, E_dash_dash_E_SB_d_t: float) -> float:
        """蓄電池ユニットの充放電時間

        Args:
            E_dash_dash_E_SB_d_t: 日付 d の時刻 t における 1 時間当たりの蓄電池ユニットによる充放電量（充電を正、放電を負とする）, kWh/h

        Returns:
            日付 d の時刻 t における蓄電池ユニットの充放電時間, h
        """

        if E_dash_dash_E_SB_d_t == 0.0:
            return 0.0
        else:
            return 1.0

    def get_E_dash_dash_E_SB_d_t(self, E_dash_dash_E_PV_chg_d_t: float, E_dash_dash_E_SB_sup_d_t: float) -> float:
        """蓄電池ユニットによる充放電量（充電を正、放電を負とする）

        Args:
            E_dash_dash_E_PV_chg_d_t: 日付 d の時刻 t における 太陽光発電設備による発電量のうちの充電分, kWh/h
            E_dash_dash_E_SB_sup_d_t: 日付 d の時刻 t における 蓄電池ユニットによる放電量のうちの供給分, kWh/h

        Raises:
            ValueError: 充電分と供給分（放電分）がともに正となる状態は発生しない前提の評価となっているため、両者が正の場合にはエラーをだす。

        Returns:
            日付 d の時刻 t における 1 時間当たりの蓄電池ユニットによる充放電量（充電を正、放電を負とする）, kWh/h
        """
        
        if E_dash_dash_E_PV_chg_d_t > 0 and E_dash_dash_E_SB_sup_d_t == 0:
            E_dash_dash_E_SB_d_t = E_dash_dash_E_PV_chg_d_t
        elif E_dash_dash_E_PV_chg_d_t == 0 and E_dash_dash_E_SB_sup_d_t > 0:
            E_dash_dash_E_SB_d_t = - E_dash_dash_E_SB_sup_d_t
        elif E_dash_dash_E_PV_chg_d_t == 0 and E_dash_dash_E_SB_sup_d_t == 0:
            E_dash_dash_E_SB_d_t = 0
        else:
            raise ValueError("E_dash_dash_E_PV_chg = {}, E_dash_dash_E_SB_sup = {}".format(E_dash_dash_E_PV_chg_d_t, E_dash_dash_E_SB_sup_d_t))

        return E_dash_dash_E_SB_d_t

    def calc_E_dash_dash_E_SB_max_d_t(self, theta_ex_d_t: float, SC_d_t: float) -> float:
        """蓄電池ユニットによる最大充放電可能電力量

        Args:
            theta_ex_d_t: 日付 d 時刻 t における外気温度, ℃
            SC_d_t: 系統からの電力供給の有無

        Returns:
            日付 d の時刻 t における蓄電池ユニットによる最大充電可能電力量, kWh/h
            日付 d の時刻 t における蓄電池ユニットによる最大放電可能電力量, kWh/h
        """

        # 日付 d 時刻 t における蓄電池モジュールの周囲温度, K
        # 日付 d 時刻 t における蓄電池ユニットが放電を停止する充電率, -
        # 日付 d 時刻 t における蓄電池ユニットが放電を停止する充電率, -
        # 日付 d 時刻 t における蓄電池の満充電容量, Ah
        # 日付 d の時刻 t における蓄電池の内部抵抗, Ω
        T_amb_bmdl_d_t, SOC_star_min_d_t, SOC_star_max_d_t, C_fc_d_t, R_intr_d_t = self.calc_common_parameters(theta_ex_d_t=theta_ex_d_t, SC_d_t=SC_d_t)

        # 蓄電池ユニットが最大充電可能電力量を充電する時間
        delta_tau_max_chg_d_t = self.get_delta_tau_max_chg_d_t()

        # 蓄電池の充電可能容量 (Ah) 式(34)
        C_oprt_chg_d_t = self.get_C_oprt_chg_d_t(C_fc_d_t=C_fc_d_t, SOC_star_max_d_t=SOC_star_max_d_t)

        # 蓄電池ユニットが最大充電可能電力量を充電する時の電流 式(28)
        I_max_chg_d_t = self.get_I_max_chg_d_t(C_oprt_chg_d_t=C_oprt_chg_d_t, delta_tau_max_chg_d_t=delta_tau_max_chg_d_t)

        # 蓄電池ユニットが最大充電可能電力量を充電する時の電圧 式(27)
        V_max_chg_d_t = self.get_V_max_chg_d_t(SOC_star_max_d_t=SOC_star_max_d_t, T_amb_bmdl_d_t=T_amb_bmdl_d_t, I_max_chg_d_t=I_max_chg_d_t, R_intr_d_t=R_intr_d_t)

        # 蓄電池ユニットによる最大充電可能電力量 (kWh/h) 式(26)
        E_dash_dash_E_SB_max_chg_d_t = self.get_E_dash_dash_E_SB_max_chg_d_t(I_max_chg_d_t=I_max_chg_d_t, V_max_chg_d_t=V_max_chg_d_t, delta_tau_max_chg_d_t=delta_tau_max_chg_d_t)

        # 蓄電池ユニットが最大放電可能電力量を放電する時間
        delta_tau_max_dchg_d_t = self.get_delta_tau_max_dchg_d_t()
        
        # 放電可能容量, Ah 式(35)
        C_oprt_dchg_d_t = self.get_C_oprt_dchg_d_t(C_fc_d_t=C_fc_d_t, SOC_star_min_d_t=SOC_star_min_d_t)

        # 蓄電池ユニットが最大放電可能電力量を放電する時の電流 式(31)
        I_max_dchg_d_t = self.get_I_max_dchg_d_t(C_oprt_dchg_d_t=C_oprt_dchg_d_t, delta_tau_max_dchg_d_t=delta_tau_max_dchg_d_t)

        # 蓄電池ユニットが最大放電可能電力量を放電する時の電圧 式(30)
        V_max_dchg_d_t = self.get_V_max_dchg_d_t(SOC_star_min_d_t=SOC_star_min_d_t, T_amb_bmdl_d_t=T_amb_bmdl_d_t, I_max_dchg_d_t=I_max_dchg_d_t, R_intr_d_t=R_intr_d_t)

        # 蓄電池ユニットによる最大放電可能電力量 式(29)
        E_dash_dash_E_SB_max_dchg_d_t = self.get_E_dash_dash_E_SB_max_dchg_d_t(I_max_dchg_d_t=I_max_dchg_d_t, V_max_dchg_d_t=V_max_dchg_d_t, delta_tau_max_dchg_d_t=delta_tau_max_dchg_d_t)

        return E_dash_dash_E_SB_max_chg_d_t, E_dash_dash_E_SB_max_dchg_d_t


    def get_E_dash_dash_E_SB_max_dchg_d_t(self, I_max_dchg_d_t: float, V_max_dchg_d_t: float, delta_tau_max_dchg_d_t: float) -> float:
        """蓄電池ユニットによる最大放電可能電力量

        Args:
            I_max_dchg_d_t: 日付 d の時刻 t における蓄電池ユニットが最大放電可能電力量を放電する時の電流, A
            V_max_dchg_d_t: 日付 d の時刻 t における蓄電池ユニットが最大放電可能電力量を放電する時の電圧, V
            delta_tau_max_dchg_d_t: 日付 d の時刻 t における蓄電池ユニットが最大放電可能電力量を放電する時間, h

        Returns:
            日付 d の時刻 t における蓄電池ユニットによる最大放電可能電力量, kWh/h
        """

        E_dash_dash_E_SB_max_dchg_d_t = I_max_dchg_d_t * V_max_dchg_d_t * delta_tau_max_dchg_d_t / 1000

        return E_dash_dash_E_SB_max_dchg_d_t


    def get_E_dash_dash_E_SB_max_chg_d_t(self, I_max_chg_d_t: float, V_max_chg_d_t: float, delta_tau_max_chg_d_t: float) -> float:
        """蓄電池ユニットによる最大充電可能電力量

        Args:
            I_max_chg_d_t: 日付 d の時刻 t における蓄電池ユニットが最大充電可能電力量を充電する時の電流, A
            V_max_chg_d_t: 日付 d の時刻 t における蓄電池ユニットが最大充電可能電力量を充電する時の電圧, V
            delta_tau_max_chg_d_t: 日付 d の時刻 t における蓄電池ユニットが最大充電可能電力量を充電する時間, h

        Returns:
            日付 d の時刻 t における蓄電池ユニットによる最大充電可能電力量, kWh/h
        """

        E_dash_dash_E_SB_max_chg_d_t = I_max_chg_d_t * V_max_chg_d_t * delta_tau_max_chg_d_t / 1000

        return E_dash_dash_E_SB_max_chg_d_t


    def get_V_max_dchg_d_t(self, SOC_star_min_d_t: float, T_amb_bmdl_d_t: float, I_max_dchg_d_t: float, R_intr_d_t: float) -> float:
        """蓄電池ユニットが最大放電可能電力量を放電する時の電圧

        Args:
            SOC_star_min_d_t: 日付 d の時刻 t における蓄電池ユニットが放電を停止する充電率, -
            T_amb_bmdl_d_t: 日付 d の時刻 t における蓄電池モジュールの周囲温度, K
            I_max_dchg_d_t: 日付 d の時刻 t における蓄電池ユニットが最大充電可能電力量を放電するときの電流, A
            R_intr_d_t: 日付 d の時刻 t における蓄電池の内部抵抗, Ω

        Returns:
            日付 d の時刻 t における蓄電池ユニットが最大放電可能電力量を放電する時の電圧, V
        """

        # 充放電により蓄電池の状態が状態0(SOC_st0)から状態1(SOC_star_min)に変化する場合の開回路電圧の絶対値 (V)
        OCV = (self.f_OCV(x_SOC=self.SOC_d_t, x_T_amb=T_amb_bmdl_d_t, x_type=self.type_batt, x_Vrtd=self.V_rtd_batt) + 
            self.f_OCV(x_SOC=SOC_star_min_d_t, x_T_amb=T_amb_bmdl_d_t, x_type=self.type_batt, x_Vrtd=self.V_rtd_batt)) / 2

        # 蓄電池ユニットが最大放電可能電力量を放電する時の電圧 式(30)
        V_max_dchg_d_t = OCV - I_max_dchg_d_t * R_intr_d_t * (self.SOC_d_t - SOC_star_min_d_t)

        if V_max_dchg_d_t < 0:
            raise ValueError('V_max_dchg < 0')

        return V_max_dchg_d_t

    def get_V_max_chg_d_t(self, SOC_star_max_d_t: float, T_amb_bmdl_d_t: float, I_max_chg_d_t: float, R_intr_d_t: float) -> float:
        """蓄電池ユニットが最大充電可能電力量を充電する時の電圧

        Args:
            SOC_star_max_d_t: 日付 d の時刻 t における蓄電池ユニットが充電を停止する充電率, -
            T_amb_bmdl_d_t: 日付 d の時刻 t における蓄電池モジュールの周囲温度, K
            I_max_chg_d_t: 日付 d の時刻 t における蓄電池ユニットが最大充電可能電力量を充電するときの電流, A
            R_intr_d_t: 日付 d の時刻 t における蓄電池の内部抵抗, Ω

        Returns:
            日付 d の時刻 t における蓄電池ユニットが最大充電可能電力量を充電する時の電圧, V
        """

        # 充放電により蓄電池の状態が状態0(SOC_st0)から状態1(SOC_star_max)に変化する場合の開回路電圧の絶対値 (V)
        OCV = (self.f_OCV(x_SOC=self.SOC_d_t, x_T_amb=T_amb_bmdl_d_t, x_type=self.type_batt, x_Vrtd=self.V_rtd_batt) +
            self.f_OCV(x_SOC=SOC_star_max_d_t, x_T_amb=T_amb_bmdl_d_t, x_type=self.type_batt, x_Vrtd=self.V_rtd_batt)) / 2

        # 蓄電池ユニットが最大充電可能電力量を充電する時の電圧 式(27)
        V_max_chg_d_t = OCV + I_max_chg_d_t * R_intr_d_t * (SOC_star_max_d_t - self.SOC_d_t)

        if V_max_chg_d_t < 0:
            raise ValueError('V_max_chg < 0')

        return V_max_chg_d_t

    def get_I_max_dchg_d_t(self, C_oprt_dchg_d_t: float, delta_tau_max_dchg_d_t: float) -> float:
        """蓄電池ユニットが最大放電可能電力量を放電する時の電流

        Args:
            C_oprt_dchg_d_t: 日付 d の時刻 t における蓄電池の放電可能容量,Ah
            delta_tau_max_dchg_d_t: 日付 d の時刻 t における蓄電池ユニットが最大放電可能電力量を放電する時間, h

        Returns:
            日付 d の時刻 t における蓄電池ユニットが最大放電可能電力量を放電する時の電流, A
        """

        I_max_dchg_d_t = C_oprt_dchg_d_t / delta_tau_max_dchg_d_t

        return I_max_dchg_d_t


    def get_I_max_chg_d_t(self, C_oprt_chg_d_t: float, delta_tau_max_chg_d_t: float) -> float:
        """充電に対する蓄電池の電流

        Args:
            C_oprt_chg_d_t: 日付 d の時刻 t における蓄電池の充電可能容量, Ah
            delta_tau_max_chg_d_t: 日付 d の時刻 t における蓄電池ユニットが最大充電可能電力量を充電する時間, h

        Returns:
            日付 d の時刻 t における充電に対する蓄電池の電流, A
        """

        I_max_chg_d_t = C_oprt_chg_d_t / delta_tau_max_chg_d_t

        return I_max_chg_d_t

    def get_delta_tau_max_dchg_d_t(self)-> float:
        """蓄電池ユニットが最大放電可能電力量を放電する時間

        Returns:
            日付 d 時刻 t における蓄電池ユニットが最大放電可能電力量を放電する時間, h
        """

        return 1.0

    def get_delta_tau_max_chg_d_t(self) -> float:
        """蓄電池ユニットが最大充電可能電力量を充電する時間

        Returns:
            日付 d 時刻 t における蓄電池ユニットが最大充電可能電力量を充電する時間, h
        """

        return 1.0

    def calc_common_parameters(self, theta_ex_d_t: float, SC_d_t: float) -> Tuple[float, float, float, float, float, float]:
        """蓄電池ユニットによる最大充放電可能電力量の計算および充電池の充電率の更新に共通に使用されるパラメータを計算する

        Args:
            theta_ex_d_t: 日付 d 時刻 t における外気温度, ℃
            SC_d_t: 系統からの電力供給の有無

        Returns:
            日付 d 時刻 t における蓄電池モジュールの周囲温度, K
            日付 d 時刻 t における蓄電池ユニットが放電を停止する充電率, -
            日付 d 時刻 t における蓄電池ユニットが放電を停止する充電率, -
            日付 d 時刻 t における蓄電池の満充電容量, Ah
            日付 d 時刻 t における状態0にある場合の充電池の充電率, -
            日付 d の時刻 t における蓄電池の内部抵抗, Ω
        """

        # 蓄電池モジュールの周囲温度
        T_amb_bmdl_d_t = self.get_T_amb_bmdl_d_t(theta_ex_d_t=theta_ex_d_t)

        # 蓄電池ユニットが放電を停止する充電率 式(44)
        SOC_star_min_d_t = self.get_SOC_star_min_d_t(SC_d_t=SC_d_t)

        # 蓄電池ユニットが充電を停止する充電率 式(43)
        SOC_star_max_d_t = self.get_SOC_star_max_d_t()

        # 日付 d 時刻 t における蓄電池の満充電容量, Ah
        C_fc_d_t = self.get_C_fc_d_t()

        # 蓄電池の内部抵抗 式(40)
        R_intr_d_t = self.get_R_intr_d_t(T_amb_bmdl_d_t=T_amb_bmdl_d_t)
        
        return T_amb_bmdl_d_t, SOC_star_min_d_t, SOC_star_max_d_t, C_fc_d_t, R_intr_d_t

    def get_R_intr_d_t(self, T_amb_bmdl_d_t: float) -> float:
        """蓄電池の内部抵抗

        Args:
            T_amb_bmdl_d_t: 日付 d の時刻 t における蓄電池モジュールの周囲温度, K

        Returns:
            日付 d の時刻 t における蓄電池の内部抵抗, Ω
        """

        def f_R_intr(x_T_amb: float, x_type: int) -> float:
            """蓄電池の内部抵抗を表す関数

            Args:
                x_T_amb: 関数の引数 (蓄電池モジュールの周囲温度), K
                x_type: 関数の引数 (蓄電池の種類), -
            
            Returns:
                蓄電池の内部抵抗, Ω
            
            Notes:
                9.7 内部抵抗を表す関数
            """
            
            R_intr = 0.5
            
            return R_intr

        R_intr_d_t = f_R_intr(x_T_amb=T_amb_bmdl_d_t, x_type=self.type_batt)

        return R_intr_d_t

    def get_C_oprt_chg_d_t(self, C_fc_d_t: float, SOC_star_max_d_t: float) -> float:
        """蓄電池の充電可能容量 (Ah)

        Args:
            C_fc_d_t: 日付 d の時刻 t における蓄電池の満充電容量, Ah
            SOC_star_max_d_t: 日付 d の時刻 t における蓄電池ユニットが充電を停止する充電率, -

        Returns:
            float: 日付 d の時刻 t における蓄電池の充電可能容量, Ah
        """

        return C_fc_d_t * (SOC_star_max_d_t - self.SOC_d_t)

    def get_C_oprt_dchg_d_t(self, C_fc_d_t: float, SOC_star_min_d_t: float) -> float:
        """蓄電池の放電可能容量

        Args:
            C_fc_d_t: 日付 d の時刻 t における蓄電池の満充電容量, Ah
            SOC_star_min_d_t: 日付 d の時刻 t における蓄電池ユニットが放電を停止する充電率, -

        Returns:
            日付 d の時刻 t における蓄電池の放電可能容量, Ah
        
        Notes:
            9.5.2 放電可能容量
            式(35)
        """

        C_oprt_dchg_d_t = C_fc_d_t * (self.SOC_d_t - SOC_star_min_d_t)

        return C_oprt_dchg_d_t

    def get_C_fc_d_t(self) -> float:
        """蓄電池の満充電容量

        Args:
            C_fc_rtd: 蓄電池の初期満充電容量, Ah

        Returns:
            ndarray: 日付 d 時刻 t における蓄電池の満充電容量, Ah
        
        Nots:
            式(45)
            蓄電池の満充電容量は、実際には周囲温度や劣化の程度により異なるが、本算定方法においては一定として扱うこととする。
        """

        C_fc_d_t =  self.C_fc_rtd

        return C_fc_d_t

    def get_SOC_star_max_d_t(self) -> float:
        """蓄電池ユニットが充電を停止する充電率

        Returns:
            日付 d 時刻 t における蓄電池ユニットが充電を停止する充電率, -
        
        Notes:
            式(43)
        """

        SOC_star_max_d_t = self.SOC_star_upper

        return SOC_star_max_d_t

    def get_SOC_star_min_d_t(self, SC_d_t: bool) -> float:
        """蓄電池ユニットが放電を停止する充電率 (-)

        Args:
            SC: 系統からの電力供給の有無

        Returns:
            蓄電池ユニットが放電を停止する充電率, -

        Notes:
            式(44)
        """

        if SC_d_t:
            # 系統連携運転時の場合 式(44-1)
            return self.SOC_star_lower + self.r_LCP_batt * (self.SOC_star_upper - self.SOC_star_lower)
        else:
            # 独立運転時の場合 式(44-2)
            return self.SOC_star_lower

    def get_T_amb_bmdl_d_t(self, theta_ex_d_t: float) -> float:
        """蓄電池モジュールの周囲温度

        Args:
            theta_ex_d_t: 日付 d 時刻 t における外気温度, ℃

        Returns:
            ndarray: 日付 d 時刻 t における蓄電池モジュールの周囲温度, K
        """

        return get_T(theta_ex_d_t)

    @staticmethod
    def get_C_fc_rtd(W_rtd_batt: float, V_rtd_batt: float) -> float:
        """蓄電池の初期満充電容量

        Args:
            W_rtd_batt: 蓄電池の定格容量, kWh
            V_rtd_batt: 蓄電池の定格電圧, V

        Returns:
            float: 蓄電池の初期満充電容量, Ah
        
        Notes:
            式(46)
        """

        C_fc_rtd = W_rtd_batt * 1000 / V_rtd_batt
        return C_fc_rtd

    @staticmethod
    def get_type_batt(V_star_upper_batt: float, V_star_lower_batt: float) -> int:
        """蓄電池の種類 (-)

        Args:
            V_star_upper_batt (float): 蓄電池の上限電圧 (V)
            V_star_lower_batt (float): 蓄電池の下限電圧 (V)

        Returns:
            int: 蓄電池の種類 (-)
        
        Notes:
            表5 蓄電池の種類の区分 
        """

        r =  V_star_upper_batt / V_star_lower_batt

        if r >= 1.7:
            return 3
        elif r >= 1.45:
            return 2
        else:
            return 1

    @staticmethod
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

        def get_K_0(x_T_amb: float, x_type: type) -> float:
            """開回路電圧の絶対値を表す関数f_OCVの項の係数K_0

            Args:
                x_T_amb: 関数の引数 (蓄電池モジュールの周囲温度), K
                x_type: 関数の引数 (充電池の種類)

            Returns:
                開回路電圧の絶対値を表す関数f_OCVの項の係数K_0, -
            """

            return 0.92027


        def get_K_1(x_T_amb: float, x_type: type) -> float:
            """開回路電圧の絶対値を表す関数f_OCVの項の係数K_1, -

            Args:
                x_T_amb: 関数の引数 (蓄電池モジュールの周囲温度), K
                x_type: 関数の引数 (充電池の種類)

            Returns:
                float: 開回路電圧の絶対値を表す関数f_OCVの項の係数K_1, -
            """

            return 0.31524


        def get_K_2(x_T_amb: float, x_type: type) -> float:
            """開回路電圧の絶対値を表す関数f_OCVの項の係数K_2, -

            Args:
                x_T_amb: 関数の引数 (蓄電池モジュールの周囲温度), K
                x_type: 関数の引数 (充電池の種類)

            Returns:
                開回路電圧の絶対値を表す関数f_OCVの項の係数K_2, -
            """

            return -0.61051


        def get_K_3(x_T_amb: float, x_type: type) -> float:
            """開回路電圧の絶対値を表す関数f_OCVの項の係数K_3, -

            Args:
                x_T_amb: 関数の引数 (蓄電池モジュールの周囲温度), K
                x_type: 関数の引数 (充電池の種類)

            Returns:
                開回路電圧の絶対値を表す関数f_OCVの項の係数K_3, -
            """

            return 0.58010


        def get_K_4(x_T_amb: float, x_type: type) -> float:
            """開回路電圧の絶対値を表す関数f_OCVの項の係数K_4, -

            Args:
                x_T_amb: 関数の引数 (蓄電池モジュールの周囲温度), K
                x_type: 関数の引数 (充電池の種類)

            Returns:
                開回路電圧の絶対値を表す関数f_OCVの項の係数K_4, -
            """

            return 0.00003


        def get_K_5(x_T_amb, x_type):
            """開回路電圧の絶対値を表す関数f_OCVの項の係数K_5, -

            Args:
                x_T_amb: 関数の引数 (蓄電池モジュールの周囲温度), K
                x_type: 関数の引数 (充電池の種類)

            Returns:
                開回路電圧の絶対値を表す関数f_OCVの項の係数K_5, -
            """

            return -0.08345


        def get_K_6(x_T_amb, x_type):
            """開回路電圧の絶対値を表す関数f_OCVの項の係数K_6, -

            Args:
                x_T_amb: 関数の引数 (蓄電池モジュールの周囲温度), K
                x_type: 関数の引数 (充電池の種類)

            Returns:
                開回路電圧の絶対値を表す関数f_OCVの項の係数K_6, -
            """

            return -0.02122


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



def get_T(theta: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """絶対温度 (K)

    Args:
        theta (float|ndarry): 空気温度 (℃)

    Returns:
        float|ndarray: 絶対温度 (K)
    """
    T = theta + 273.16
    return T







