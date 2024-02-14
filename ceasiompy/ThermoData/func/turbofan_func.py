"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Function to run the PyCycle code for the turbofan engine

Python version: >=3.8

| Author: Francesco Marcucci
| Creation: 2023-12-12

"""
import sys

import openmdao.api as om

import pycycle.api as pyc

from scipy.constants import convert_temperature

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger()

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def turbofan_analysis(alt, MN, Fn):
    class HBTF(pyc.Cycle):
        def setup(self):

            # Setup the problem by including all the relevant components here

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
                pyc.Turbine(map_data=pyc.HPTMap, bleed_names=["cool3", "cool4"], map_extrap=True),
                promotes_inputs=[("Nmech", "HP_Nmech")],
            )
            self.add_subsystem("duct11", pyc.Duct())
            self.add_subsystem(
                "lpt",
                pyc.Turbine(map_data=pyc.LPTMap, bleed_names=["cool1", "cool2"], map_extrap=True),
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
            # Ideally expanding flow by conneting flight condition static
            # pressure to nozzle exhaust pressure
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

                # Note that for the following two balances
                # the mult val is set to -1 so that the NET torque is zero
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

            super().setup()

    def viewer(prob, pt, file=sys.stdout):
        """
        print a report of all the relevant cycle properties
        """

        if pt == "DESIGN":
            MN = prob["DESIGN.fc.Fl_O:stat:MN"]
            # LPT_PR = prob["DESIGN.balance.lpt_PR"]
            # HPT_PR = prob["DESIGN.balance.hpt_PR"]
            # FAR = prob["DESIGN.balance.FAR"]
        else:
            MN = prob[pt + ".fc.Fl_O:stat:MN"]
            # LPT_PR = prob[pt + ".lpt.PR"]
            # HPT_PR = prob[pt + ".hpt.PR"]
            # FAR = prob[pt + ".balance.FAR"]

        summary_data = (
            MN,
            prob[pt + ".fc.alt"],
            prob[pt + ".inlet.Fl_O:stat:W"],
            prob[pt + ".perf.Fn"],
            prob[pt + ".perf.Fg"],
            prob[pt + ".inlet.F_ram"],
            prob[pt + ".perf.OPR"],
            prob[pt + ".perf.TSFC"],
            prob[pt + ".splitter.BPR"],
        )

        print(file=file, flush=True)
        print(file=file, flush=True)
        print(file=file, flush=True)
        print(
            "----------------------------------------------------------------------------",
            file=file,
            flush=True,
        )
        print("                              POINT:", pt, file=file, flush=True)
        print(
            "----------------------------------------------------------------------------",
            file=file,
            flush=True,
        )
        print("                       PERFORMANCE CHARACTERISTICS", file=file, flush=True)
        print(
            "    Mach      Alt       W      Fn      Fg    Fram     OPR     TSFC      BPR ",
            file=file,
            flush=True,
        )
        print(
            " %7.5f  %7.1f %7.3f %7.1f %7.1f %7.1f %7.3f  %7.5f  %7.3f" % summary_data,
            file=file,
            flush=True,
        )

        fs_names = [
            "fc.Fl_O",
            "core_nozz.Fl_O",
            "byp_nozz.Fl_O",
        ]
        fs_full_names = [f"{pt}.{fs}" for fs in fs_names]
        pyc.print_flow_station(prob, fs_full_names, file=file)

    prob = om.Problem()

    prob.model = MPhbtf()

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
    prob.set_val("DESIGN.Fn_DES", Fn * 0.2248089431, units="lbf")  # 1 N = 0.2248089431 lbf

    # Set initial guesses for balances
    prob["DESIGN.balance.FAR"] = 0.1
    prob["DESIGN.balance.W"] = 10.0
    prob["DESIGN.balance.lpt_PR"] = 2
    prob["DESIGN.balance.hpt_PR"] = 2.0
    prob["DESIGN.fc.balance.Pt"] = 2
    prob["DESIGN.fc.balance.Tt"] = 500.0

    prob.set_solver_print(level=-1)
    prob.set_solver_print(level=2, depth=1)

    viewer_file = open("hbtf_des_view.out", "w")

    # for PC in [1, 0.9]:
    #     viewer(prob, "DESIGN", file=viewer_file)
    #     prob.run_model()
    # print()

    viewer(prob, "DESIGN", file=viewer_file)
    prob.run_model()

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
    P_tot_out_byp = prob.get_val("DESIGN.byp_nozz.throat_total.flow.Fl_O:tot:P") * 6894.7573  # Pa
    massflow_stat_out_byp = prob.get_val("DESIGN.byp_nozz.mux.Fl_O:stat:W") * 0.45359237  # kg/s
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
    massflow_stat_out_core = prob.get_val("DESIGN.core_nozz.mux.Fl_O:stat:W") * 0.45359237  # kg/s
    T_stat_out_core = convert_temperature(
        (prob.get_val("DESIGN.core_nozz.mux.Fl_O:stat:T")), "Rankine", "Kelvin"
    )  # celsius

    return (
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
    )


def write_hbtf_file(
    file,
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
):

    file.write(f"T_tot_out_core = {T_tot_out_core} [K]\n")
    file.write(f"V_stat_out_core = {V_stat_out_core} [m/s]\n")
    file.write(f"MN_out_core = {MN_out_core} [adim]\n")
    file.write(f"P_tot_out_core = {P_tot_out_core} [Pa]\n")
    file.write(f"massflow_out_core = {massflow_stat_out_core} [kg/s]\n")
    file.write(f"T_stat_out_core = {T_stat_out_core} [K]\n")
    file.write(f"T_tot_out_byp = {T_tot_out_byp} [K]\n")
    file.write(f"V_stat_out_byp = {V_stat_out_byp} [m/s]\n")
    file.write(f"MN_out_byp = {MN_out_byp} [adim]\n")
    file.write(f"P_tot_out_byp = {P_tot_out_byp} [Pa]\n")
    file.write(f"massflow_stat_out_byp = {massflow_stat_out_byp} [kg/s]\n")
    file.write(f"T_stat_out_byp = {T_stat_out_byp} [K]\n")

    log.info("hbtf.dat file generated!")

    return file
