import sys

import numpy as np

import openmdao.api as om

import pycycle.api as pyc

import re

from scipy.constants import convert_temperature


def run_turbofan_analysis_test(alt, MN):
    class HBTF(pyc.Cycle):
        def setup(self):

            # Setup the problem by including all the relevant components here - comp, burner, turbine etc

            # Create any relevant short hands here:

            design = self.options["design"]

            USE_TABULAR = False
            if USE_TABULAR:
                self.options["thermo_method"] = "TABULAR"
                self.options["thermo_data"] = pyc.AIR_JETA_TAB_SPEC
                FUEL_TYPE = "FAR"
            else:
                self.options["thermo_method"] = "CEA"
                self.options["thermo_data"] = pyc.species_data.janaf
                FUEL_TYPE = "Jet-A(g)"

            # Add subsystems to build the engine deck:
            self.add_subsystem("fc", pyc.FlightConditions())
            self.add_subsystem("inlet", pyc.Inlet())

            self.add_subsystem(
                "fan",
                pyc.Compressor(map_data=pyc.FanMap, bleed_names=[], map_extrap=True),
                promotes_inputs=[("Nmech", "LP_Nmech")],
            )
            self.add_subsystem("splitter", pyc.Splitter())
            self.add_subsystem("duct4", pyc.Duct())
            self.add_subsystem(
                "lpc",
                pyc.Compressor(map_data=pyc.LPCMap, map_extrap=True),
                promotes_inputs=[("Nmech", "LP_Nmech")],
            )
            self.add_subsystem("duct6", pyc.Duct())
            self.add_subsystem(
                "hpc",
                pyc.Compressor(
                    map_data=pyc.HPCMap,
                    bleed_names=["cool1", "cool2", "cust"],
                    map_extrap=True,
                ),
                promotes_inputs=[("Nmech", "HP_Nmech")],
            )
            self.add_subsystem("bld3", pyc.BleedOut(bleed_names=["cool3", "cool4"]))
            self.add_subsystem("burner", pyc.Combustor(fuel_type=FUEL_TYPE))
            self.add_subsystem(
                "hpt",
                pyc.Turbine(
                    map_data=pyc.HPTMap, bleed_names=["cool3", "cool4"], map_extrap=True
                ),
                promotes_inputs=[("Nmech", "HP_Nmech")],
            )
            self.add_subsystem("duct11", pyc.Duct())
            self.add_subsystem(
                "lpt",
                pyc.Turbine(
                    map_data=pyc.LPTMap, bleed_names=["cool1", "cool2"], map_extrap=True
                ),
                promotes_inputs=[("Nmech", "LP_Nmech")],
            )
            self.add_subsystem("duct13", pyc.Duct())
            self.add_subsystem("core_nozz", pyc.Nozzle(nozzType="CV", lossCoef="Cv"))

            self.add_subsystem("byp_bld", pyc.BleedOut(bleed_names=["bypBld"]))
            self.add_subsystem("duct15", pyc.Duct())
            self.add_subsystem("byp_nozz", pyc.Nozzle(nozzType="CV", lossCoef="Cv"))

            # Create shaft instances. Note that LP shaft has 3 ports! => no gearbox
            self.add_subsystem(
                "lp_shaft",
                pyc.Shaft(num_ports=3),
                promotes_inputs=[("Nmech", "LP_Nmech")],
            )
            self.add_subsystem(
                "hp_shaft",
                pyc.Shaft(num_ports=2),
                promotes_inputs=[("Nmech", "HP_Nmech")],
            )
            self.add_subsystem("perf", pyc.Performance(num_nozzles=2, num_burners=1))

            # Now use the explicit connect method to make connections -- connect(<from>, <to>)

            # Connect the inputs to perf group
            self.connect("inlet.Fl_O:tot:P", "perf.Pt2")
            self.connect("hpc.Fl_O:tot:P", "perf.Pt3")
            self.connect("burner.Wfuel", "perf.Wfuel_0")
            self.connect("inlet.F_ram", "perf.ram_drag")
            self.connect("core_nozz.Fg", "perf.Fg_0")
            self.connect("byp_nozz.Fg", "perf.Fg_1")

            # LP-shaft connections
            self.connect("fan.trq", "lp_shaft.trq_0")
            self.connect("lpc.trq", "lp_shaft.trq_1")
            self.connect("lpt.trq", "lp_shaft.trq_2")
            # HP-shaft connections
            self.connect("hpc.trq", "hp_shaft.trq_0")
            self.connect("hpt.trq", "hp_shaft.trq_1")
            # Ideally expanding flow by conneting flight condition static pressure to nozzle exhaust pressure
            self.connect("fc.Fl_O:stat:P", "core_nozz.Ps_exhaust")
            self.connect("fc.Fl_O:stat:P", "byp_nozz.Ps_exhaust")

            balance = self.add_subsystem("balance", om.BalanceComp())
            if design:
                balance.add_balance("W", units="lbm/s", eq_units="lbf")
                # Here balance.W is implicit state variable that is the OUTPUT of balance object
                self.connect(
                    "balance.W", "fc.W"
                )  # Connect the output of balance to the relevant input
                self.connect(
                    "perf.Fn", "balance.lhs:W"
                )  # This statement makes perf.Fn the LHS of the balance eqn.
                self.promotes("balance", inputs=[("rhs:W", "Fn_DES")])

                balance.add_balance("FAR", eq_units="degR", lower=1e-4, val=0.017)
                self.connect("balance.FAR", "burner.Fl_I:FAR")
                self.connect("burner.Fl_O:tot:T", "balance.lhs:FAR")
                self.promotes("balance", inputs=[("rhs:FAR", "T4_MAX")])

                # Note that for the following two balances the mult val is set to -1 so that the NET torque is zero
                balance.add_balance(
                    "lpt_PR",
                    val=1.5,
                    lower=1.001,
                    upper=8,
                    eq_units="hp",
                    use_mult=True,
                    mult_val=-1,
                )
                self.connect("balance.lpt_PR", "lpt.PR")
                self.connect("lp_shaft.pwr_in_real", "balance.lhs:lpt_PR")
                self.connect("lp_shaft.pwr_out_real", "balance.rhs:lpt_PR")

                balance.add_balance(
                    "hpt_PR",
                    val=1.5,
                    lower=1.001,
                    upper=8,
                    eq_units="hp",
                    use_mult=True,
                    mult_val=-1,
                )
                self.connect("balance.hpt_PR", "hpt.PR")
                self.connect("hp_shaft.pwr_in_real", "balance.lhs:hpt_PR")
                self.connect("hp_shaft.pwr_out_real", "balance.rhs:hpt_PR")

            # Set up all the flow connections:
            self.pyc_connect_flow("fc.Fl_O", "inlet.Fl_I")
            self.pyc_connect_flow("inlet.Fl_O", "fan.Fl_I")
            self.pyc_connect_flow("fan.Fl_O", "splitter.Fl_I")
            self.pyc_connect_flow("splitter.Fl_O1", "duct4.Fl_I")
            self.pyc_connect_flow("duct4.Fl_O", "lpc.Fl_I")
            self.pyc_connect_flow("lpc.Fl_O", "duct6.Fl_I")
            self.pyc_connect_flow("duct6.Fl_O", "hpc.Fl_I")
            self.pyc_connect_flow("hpc.Fl_O", "bld3.Fl_I")
            self.pyc_connect_flow("bld3.Fl_O", "burner.Fl_I")
            self.pyc_connect_flow("burner.Fl_O", "hpt.Fl_I")
            self.pyc_connect_flow("hpt.Fl_O", "duct11.Fl_I")
            self.pyc_connect_flow("duct11.Fl_O", "lpt.Fl_I")
            self.pyc_connect_flow("lpt.Fl_O", "duct13.Fl_I")
            self.pyc_connect_flow("duct13.Fl_O", "core_nozz.Fl_I")
            self.pyc_connect_flow("splitter.Fl_O2", "byp_bld.Fl_I")
            self.pyc_connect_flow("byp_bld.Fl_O", "duct15.Fl_I")
            self.pyc_connect_flow("duct15.Fl_O", "byp_nozz.Fl_I")

            # Bleed flows:
            self.pyc_connect_flow("hpc.cool1", "lpt.cool1", connect_stat=False)
            self.pyc_connect_flow("hpc.cool2", "lpt.cool2", connect_stat=False)
            self.pyc_connect_flow("bld3.cool3", "hpt.cool3", connect_stat=False)
            self.pyc_connect_flow("bld3.cool4", "hpt.cool4", connect_stat=False)

            # Specify solver settings:
            newton = self.nonlinear_solver = om.NewtonSolver()
            newton.options["atol"] = 1e-8

            # set this very small, so it never activates and we rely on atol
            newton.options["rtol"] = 1e-99
            newton.options["iprint"] = 2
            newton.options["maxiter"] = 50
            newton.options["solve_subsystems"] = True
            newton.options["max_sub_solves"] = 1000
            newton.options["reraise_child_analysiserror"] = False
            # ls = newton.linesearch = BoundsEnforceLS()
            ls = newton.linesearch = om.ArmijoGoldsteinLS()
            ls.options["maxiter"] = 3
            ls.options["rho"] = 0.75
            # ls.options['print_bound_enforce'] = True

            self.linear_solver = om.DirectSolver()

            super().setup()

    class MPhbtf(pyc.MPCycle):
        def setup(self):

            self.pyc_add_pnt(
                "DESIGN", HBTF(thermo_method="CEA")
            )  # Create an instance of the High Bypass ratio Turbofan

            self.set_input_defaults("DESIGN.inlet.MN", 0.751)
            self.set_input_defaults("DESIGN.fan.MN", 0.4578)
            self.set_input_defaults("DESIGN.splitter.BPR", 5.105)
            self.set_input_defaults("DESIGN.splitter.MN1", 0.3104)
            self.set_input_defaults("DESIGN.splitter.MN2", 0.4518)
            self.set_input_defaults("DESIGN.duct4.MN", 0.3121)
            self.set_input_defaults("DESIGN.lpc.MN", 0.3059)
            self.set_input_defaults("DESIGN.duct6.MN", 0.3563)
            self.set_input_defaults("DESIGN.hpc.MN", 0.2442)
            self.set_input_defaults("DESIGN.bld3.MN", 0.3000)
            self.set_input_defaults("DESIGN.burner.MN", 0.1025)
            self.set_input_defaults("DESIGN.hpt.MN", 0.3650)
            self.set_input_defaults("DESIGN.duct11.MN", 0.3063)
            self.set_input_defaults("DESIGN.lpt.MN", 0.4127)
            self.set_input_defaults("DESIGN.duct13.MN", 0.4463)
            self.set_input_defaults("DESIGN.byp_bld.MN", 0.4489)
            self.set_input_defaults("DESIGN.duct15.MN", 0.4589)
            self.set_input_defaults("DESIGN.LP_Nmech", 4666.1, units="rpm")
            self.set_input_defaults("DESIGN.HP_Nmech", 14705.7, units="rpm")

            # --- Set up bleed values -----

            self.pyc_add_cycle_param("inlet.ram_recovery", 0.9990)
            self.pyc_add_cycle_param("duct4.dPqP", 0.0048)
            self.pyc_add_cycle_param("duct6.dPqP", 0.0101)
            self.pyc_add_cycle_param("burner.dPqP", 0.0540)
            self.pyc_add_cycle_param("duct11.dPqP", 0.0051)
            self.pyc_add_cycle_param("duct13.dPqP", 0.0107)
            self.pyc_add_cycle_param("duct15.dPqP", 0.0149)
            self.pyc_add_cycle_param("core_nozz.Cv", 0.9933)
            self.pyc_add_cycle_param("byp_bld.bypBld:frac_W", 0.005)
            self.pyc_add_cycle_param("byp_nozz.Cv", 0.9939)
            self.pyc_add_cycle_param("hpc.cool1:frac_W", 0.050708)
            self.pyc_add_cycle_param("hpc.cool1:frac_P", 0.5)
            self.pyc_add_cycle_param("hpc.cool1:frac_work", 0.5)
            self.pyc_add_cycle_param("hpc.cool2:frac_W", 0.020274)
            self.pyc_add_cycle_param("hpc.cool2:frac_P", 0.55)
            self.pyc_add_cycle_param("hpc.cool2:frac_work", 0.5)
            self.pyc_add_cycle_param("bld3.cool3:frac_W", 0.067214)
            self.pyc_add_cycle_param("bld3.cool4:frac_W", 0.101256)
            self.pyc_add_cycle_param("hpc.cust:frac_P", 0.5)
            self.pyc_add_cycle_param("hpc.cust:frac_work", 0.5)
            self.pyc_add_cycle_param("hpc.cust:frac_W", 0.0445)
            self.pyc_add_cycle_param("hpt.cool3:frac_P", 1.0)
            self.pyc_add_cycle_param("hpt.cool4:frac_P", 0.0)
            self.pyc_add_cycle_param("lpt.cool1:frac_P", 1.0)
            self.pyc_add_cycle_param("lpt.cool2:frac_P", 0.0)
            self.pyc_add_cycle_param("hp_shaft.HPX", 250.0, units="hp")

            super().setup()

    import time

    prob = om.Problem()

    prob.model = mp_hbtf = MPhbtf()

    prob.setup()

    prob.set_val("DESIGN.fan.PR", 1.685)
    prob.set_val("DESIGN.fan.eff", 0.8948)

    prob.set_val("DESIGN.lpc.PR", 1.935)
    prob.set_val("DESIGN.lpc.eff", 0.9243)

    prob.set_val("DESIGN.hpc.PR", 9.369)
    prob.set_val("DESIGN.hpc.eff", 0.8707)

    prob.set_val("DESIGN.hpt.eff", 0.8888)
    prob.set_val("DESIGN.lpt.eff", 0.8996)

    prob.set_val("DESIGN.fc.alt", alt, units="ft")
    prob.set_val("DESIGN.fc.MN", MN)

    prob.set_val("DESIGN.T4_MAX", 2857, units="degR")
    prob.set_val("DESIGN.Fn_DES", 5900.0, units="lbf")

    # Set initial guesses for balances
    prob["DESIGN.balance.FAR"] = 0.025
    prob["DESIGN.balance.W"] = 100.0
    prob["DESIGN.balance.lpt_PR"] = 4.0
    prob["DESIGN.balance.hpt_PR"] = 3.0
    prob["DESIGN.fc.balance.Pt"] = 5.2
    prob["DESIGN.fc.balance.Tt"] = 440.0

    prob.set_solver_print(level=-1)
    # prob.set_solver_print(level=2, depth=1)

    prob.run_model()

    print()

    # Obtaining variables names

    # variable_names = open("variables_hptf.txt", "w")
    # print(
    #     prob.model.list_outputs(val=True, units=True, implicit=False),
    #     file=variable_names,
    # )

    # BYPASS VARIABLES
    T_tot_out_byp = convert_temperature(
        (prob.get_val("DESIGN.byp_nozz.throat_total.flow.Fl_O:tot:T")),
        "Rankine",
        "Celsius",
    )
    V_stat_out_byp = prob.get_val("DESIGN.byp_nozz.mux.Fl_O:stat:V") * 0.3048
    MN_out_byp = prob.get_val("DESIGN.byp_nozz.mux.Fl_O:stat:MN")
    P_tot_out_byp = (
        prob.get_val("DESIGN.byp_nozz.throat_total.flow.Fl_O:tot:P") * 6894.7573
    )  # Pa
    massflow_stat_out_byp = (
        prob.get_val("DESIGN.byp_nozz.mux.Fl_O:stat:W") * 0.45359237
    )  # kg/s
    T_stat_out_byp = convert_temperature(
        (prob.get_val("DESIGN.byp_nozz.mux.Fl_O:stat:T")), "Rankine", "Celsius"
    )  # celsius

    # CORE VARIABLES
    T_tot_out_core = convert_temperature(
        (prob.get_val("DESIGN.core_nozz.throat_total.flow.Fl_O:tot:T")),
        "Rankine",
        "Kelvin",
    )
    V_stat_out_core = prob.get_val("DESIGN.core_nozz.mux.Fl_O:stat:V") * 0.3048
    MN_out_core = prob.get_val("DESIGN.core_nozz.mux.Fl_O:stat:MN")
    P_tot_out_core = (
        prob.get_val("DESIGN.core_nozz.throat_total.flow.Fl_O:tot:P") * 6894.7573
    )  # Pa
    massflow_stat_out_core = (
        prob.get_val("DESIGN.core_nozz.mux.Fl_O:stat:W") * 0.45359237
    )  # kg/s
    T_stat_out_core = convert_temperature(
        (prob.get_val("DESIGN.core_nozz.mux.Fl_O:stat:T")), "Rankine", "Kelvin"
    )  # celsius

    res = np.array(
        [
            T_tot_out_byp,
            V_stat_out_byp,
            MN_out_byp,
            P_tot_out_byp,
            massflow_stat_out_byp,
            T_stat_out_byp,
            T_tot_out_core,
            V_stat_out_core,
            MN_out_core,
            P_tot_out_core,
            massflow_stat_out_core,
            T_stat_out_core,
        ]
    )
    print(f"T_tot_out_core = {T_tot_out_core} [K]")
    print(f"V_stat_out_core = {V_stat_out_core} [m/s]")
    print(f"MN_out_core = {MN_out_core} [adim]")
    print(f"P_tot_out_core = {P_tot_out_core} [Pa]")
    print(f"massflow_out_core = {massflow_stat_out_core} [kg/s]")
    print(f"T_stat_out_core = {T_stat_out_core} [K]")
    print(f"T_tot_out_byp = {T_tot_out_byp} [K]")
    print(f"V_stat_out_byp = {V_stat_out_byp} [m/s]")
    print(f"MN_out_byp = {MN_out_byp} [adim]")
    print(f"P_tot_out_byp = {P_tot_out_byp} [Pa]")
    print(f"massflow_stat_out_byp = {massflow_stat_out_byp} [kg/s]")
    print(f"T_stat_out_core = {T_stat_out_core} [K]")

    return res


if __name__ == "__main__":

    alt = float(input("insert altitude [ft]: "))

    MN = float(input("insert mach number[adim]: "))

    run_turbofan_analysis_test(alt, MN)
    print("temperature [celsius], stat velocity [m/s], MN for bypass and core")
