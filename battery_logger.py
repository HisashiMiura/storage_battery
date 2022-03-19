import numpy as np
import pandas as pd


class BatteryLogger:

    def __init__(self, SC_d_t, E_E_dmd_excl_d_t, theta_ex_d_t, E_p_i_d_t):

        # 入力値
        self.SC_d_t = SC_d_t
        self.E_E_dmd_excl_d_t = E_E_dmd_excl_d_t
        self.theta_ex_d_t = theta_ex_d_t

        self.E_p_i_d_t = [
            np.zeros(8760),
            np.zeros(8760),
            np.zeros(8760),
            np.zeros(8760)
        ]

        for i in range(E_p_i_d_t.shape[0]):
            self.E_p_i_d_t[i] = E_p_i_d_t[i]

        # (1)
        self.E_E_PV_h_d_t = np.zeros(8760)
        # (2)
        self.E_E_PV_sell_d_t = np.zeros(8760)
        # (3)
        self.E_E_PV_chg_d_t = np.zeros(8760)
        # (4)
        self.E_E_PSS_h_d_t = np.zeros(8760)
        # (5)
        self.E_E_PSS_max_sup_d_t = np.zeros(8760)
        # (6)
        self.E_E_srpl_d_t = np.zeros(8760)
        # (7)
        self.E_E_dmd_incl_d_t = np.zeros(8760)
        # (8)
        self.E_E_aux_PSS_d_t = np.zeros(8760)
        # (9a)
        self.E_dash_dash_E_PV_chg_d_t = np.zeros(8760)
        # (10)
        self.E_dash_dash_E_srpl_d_t = np.zeros(8760)
        # (11)
        self.E_dash_dash_E_SB_sup_d_t = np.zeros(8760)
        # (12)
        self.E_E_PV_max_sup_d_t = np.zeros(8760)
        # (13)
        self.E_E_SB_max_sup_d_t = np.zeros(8760)
        # (14)
        self.E_dash_dash_E_PV_max_sup_d_t = np.zeros(8760)
        # (15)
        self.E_dash_dash_E_SB_max_sup_d_t = np.zeros(8760)
        # (16)
        self.E_E_SB_max_chg_d_t = np.zeros(8760)
        # (25)
        self.E_E_aux_PCS_d_t = np.zeros(8760)


