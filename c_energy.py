import numpy as np


class Energy:

    def __init__(self, f_prim: float):
        """所持する変数をnp.zeros（配列数8760）で初期化する。

        Args:
            f_prim: 電気の量 1kWh を熱量に換算する係数, kJ/kWh
        """

        # 電気の量 1kWh を熱量に換算する係数, kJ/kWh
        self.f_prim = f_prim

        # 暖房設備の消費電力量, kWh/h
        self.E_E_Hs = np.zeros(8760)

        # 暖房設備のガス消費量, MJ/h
        self.E_G_Hs = np.zeros(8760)

        # 暖房設備の灯油消費量, MJ/h
        self.E_K_Hs = np.zeros(8760)

        # 暖房設備のその他の燃料による一次エネルギー消費量, MJ/h
        self.E_M_Hs = np.zeros(8760)

        # 暖房設備の未処理暖房負荷の設計一次エネルギー消費量相当値, MJ/h
        self.E_UT_Hs = np.zeros(8760)

        # 冷房設備の消費電力量, kWh/h
        self.E_E_Cs = np.zeros(8760)

        # 冷房設備のガス消費量, MJ/h
        self.E_G_Cs = np.zeros(8760)

        # 冷房設備の灯油消費量, MJ/h
        self.E_K_Cs = np.zeros(8760)

        # 冷房設備のその他の燃料による一次エネルギー消費量, MJ/h
        self.E_M_Cs = np.zeros(8760)

        # 冷房設備の未処理暖房負荷の設計一次エネルギー消費量相当値, MJ/h
        self.E_UT_Cs = np.zeros(8760)


    def get_E_Hs(self):
        """暖房一次エネルギー消費量を計算する。

        Returns:
            np.ndarray: 日付 d の時刻 t における暖房一次エネルギー消費量, MJ/h
        """

        return self.E_E_Hs * self.f_prim / 1000 + self.E_G_Hs + self.E_K_Hs + self.E_M_Hs + self.E_UT_Hs

    def get_E_H(self):
        """年間の暖房一次エネルギー消費量を計算する。

        Returns:
            float: 年間の暖房一次エネルギー消費量, MJ/year
        """

        return np.sum(self.get_E_Hs())

    def get_E_UT_H(self):
        """年間暖房設備の未処理暖房負荷の設計一次エネルギー消費量相当値を取得する。

        Returns:
            年間暖房設備の未処理暖房負荷の設計一次エネルギー消費量相当値, MJ/year
        """

        return np.sum(self.E_UT_Hs)

    def get_E_Cs(self):
        """冷房一次エネルギー消費量を計算する。
    
        Returns:
            np.ndarray: 日付 d の時刻 t における冷房一次エネルギー消費量, MJ/h
        """

        return self.E_E_Cs * self.f_prim / 1000 + self.E_G_Cs + self.E_K_Cs + self.E_M_Cs + self.E_UT_Cs

    def get_E_C(self):
        """年間の冷房一次エネルギー消費量を計算する。

        Returns:
            float: 年間の冷房一次エネルギー消費量, MJ/year
        """

        return np.sum(self.get_E_Cs())
    
    def get_E_UT_C(self):
        """年間冷房設備の未処理暖房負荷の設計一次エネルギー消費量相当値を取得する。

        Returns:
            年間冷房設備の未処理暖房負荷の設計一次エネルギー消費量相当値, MJ/year
        """

        return np.sum(self.E_UT_Cs)
    
