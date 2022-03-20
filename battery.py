import numpy as np
from typing import Union 


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
        self.SOC_st1 = self.SOC_star_upper * self.r_int_dchg_batt + self.SOC_star_lower * (1 - self.r_int_dchg_batt)

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

    def get_SOC_st0(self) -> float:
        """蓄電池が状態0にある場合の蓄電池の充電率 (-)

        Returns:
            float: 蓄電池が状態0にある場合の蓄電池の充電率 (-)
        """

        return self.SOC_st1

    def get_C_oprt_chg_d_t(self, C_fc_d_t: float, SOC_star_max_d_t: float) -> float:
        """蓄電池の充電可能容量 (Ah)

        Args:
            C_fc_d_t: 日付 d の時刻 t における蓄電池の満充電容量, Ah
            SOC_star_max_d_t: 日付 d の時刻 t における蓄電池ユニットが充電を停止する充電率, -

        Returns:
            float: 日付 d の時刻 t における蓄電池の充電可能容量, Ah
        """

        return C_fc_d_t * (SOC_star_max_d_t - self.SOC_st1)

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

        C_oprt_dchg_d_t = C_fc_d_t * (self.SOC_st1 - SOC_star_min_d_t)

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
            float: 蓄電池ユニットが放電を停止する充電率, -

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


def get_T(theta: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """絶対温度 (K)

    Args:
        theta (float|ndarry): 空気温度 (℃)

    Returns:
        float|ndarray: 絶対温度 (K)
    """
    T = theta + 273.16
    return T







