import numpy as np


class Energy:

    def __init__(self, f_prim: float):
        """所持する変数をnp.zeros（配列数8760）で初期化する。

        Args:
            f_prim: 電気の量 1kWh を熱量に換算する係数, kJ/kWh
        """

        # 電気の量 1kWh を熱量に換算する係数, kJ/kWh
        self.f_prim = f_prim

        # 暖房設備の消費電力量 [8760], kWh/h
        self.E_E_Hs = np.zeros(8760)

        # 暖房設備のガス消費量 [8760], MJ/h
        self.E_G_Hs = np.zeros(8760)

        # 暖房設備の灯油消費量 [8760], MJ/h
        self.E_K_Hs = np.zeros(8760)

        # 暖房設備のその他の燃料による一次エネルギー消費量 [8760], MJ/h
        self.E_M_Hs = np.zeros(8760)

        # 暖房設備の未処理暖房負荷の設計一次エネルギー消費量相当値 [8760], MJ/h
        self.E_UT_Hs = np.zeros(8760)

        # 冷房設備の消費電力量 [8760], kWh/h
        self.E_E_Cs = np.zeros(8760)

        # 冷房設備のガス消費量 [8760], MJ/h
        self.E_G_Cs = np.zeros(8760)

        # 冷房設備の灯油消費量 [8760], MJ/h
        self.E_K_Cs = np.zeros(8760)

        # 冷房設備のその他の燃料による一次エネルギー消費量 [8760], MJ/h
        self.E_M_Cs = np.zeros(8760)

        # 冷房設備の未処理暖房負荷の設計一次エネルギー消費量相当値 [8760], MJ/h
        self.E_UT_Cs = np.zeros(8760)

        # 換気設備の消費電力量 [8760], kWh/h
        self.E_E_Vs = np.zeros(8760)

        # 照明設備の消費電力量 [8760], kWh/h
        self.E_E_Ls = np.zeros(8760)

        # 給湯設備の消費電力量 [8760], kWh/h
        self.E_E_Ws = np.zeros(8760)

        # 給湯設備のガス消費量 [8760], MJ/h
        self.E_G_Ws = np.zeros(8760)

        # 給湯設備の灯油消費量 [8760], MJ/h
        self.E_K_Ws = np.zeros(8760)

        # 給湯設備のその他の燃料による一次エネルギー消費量 [8760], MJ/h
        self.E_M_Ws = np.zeros(8760)


    def get_E_H(self):
        """年間の暖房一次エネルギー消費量を計算する。

        Returns:
            float: 年間の暖房一次エネルギー消費量, MJ/year
        """

        E_Hs = self.E_E_Hs * self.f_prim / 1000 + self.E_G_Hs + self.E_K_Hs + self.E_M_Hs + self.E_UT_Hs

        return np.sum(E_Hs)

    def get_E_UT_H(self):
        """年間の暖房設備の未処理暖房負荷の設計一次エネルギー消費量相当値を取得する。

        Returns:
            年間の暖房設備の未処理暖房負荷の設計一次エネルギー消費量相当値, MJ/year
        """

        return np.sum(self.E_UT_Hs)

    def get_E_C(self):
        """年間の冷房一次エネルギー消費量を計算する。

        Returns:
            float: 年間の冷房一次エネルギー消費量, MJ/year
        """

        E_Cs = self.E_E_Cs * self.f_prim / 1000 + self.E_G_Cs + self.E_K_Cs + self.E_M_Cs + self.E_UT_Cs

        return np.sum(E_Cs)
    
    def get_E_UT_C(self):
        """年間冷房設備の未処理暖房負荷の設計一次エネルギー消費量相当値を取得する。

        Returns:
            年間冷房設備の未処理暖房負荷の設計一次エネルギー消費量相当値, MJ/year
        """

        return np.sum(self.E_UT_Cs)
    
    def get_E_V(self):
        """年間の機械換気設備の設計一次エネルギー消費量を計算する。

        Returns:
            年間の機械換気設備の設計一次エネルギー消費量, MJ/year
        """

        return np.sum(self.E_E_Vs) * self.f_prim / 1000

    def get_E_L(self):
        """年間の照明設備の設計一次エネルギー消費量を計算する。

        Returns:
            年間の照明設備の設計一次エネルギー消費量, MJ/year
        """

        return np.sum(self.E_E_Ls) * self.f_prim / 1000

    def get_E_W(self):
        """年間の給湯一次エネルギー消費量を計算する。

        Returns:
            float: 年間の給湯一次エネルギー消費量, MJ/year
        """

        E_Ws = self.E_E_Ws * self.f_prim / 1000 + self.E_G_Ws + self.E_K_Ws + self.E_M_Ws

        return np.sum(E_Ws)


