"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Function to run the PyCycle code for the turbofan engine

| Author: Francesco Marcucci
| Creation: 2023-12-12

"""

# Imports

import sys
import numpy as np
import openmdao.api as om
import pycycle.api as pyc

from scipy.constants import convert_temperature

from ceasiompy import log

# =================================================================================================
#   CONSTANTS
# =================================================================================================

BYPASS_VARS = {
    "T_tot_out_byp": ("DESIGN.byp_nozz.throat_total.flow.Fl_O:tot:T", "Rankine", "Celsius"),
    "V_stat_out_byp": ("DESIGN.byp_nozz.mux.Fl_O:stat:V", 0.3048, None),
    "MN_out_byp": ("DESIGN.byp_nozz.mux.Fl_O:stat:MN", None, None),
    "P_tot_out_byp": ("DESIGN.byp_nozz.throat_total.flow.Fl_O:tot:P", 6894.7573, None),
    "massflow_stat_out_byp": ("DESIGN.byp_nozz.mux.Fl_O:stat:W", 0.45359237, None),
    "T_stat_out_byp": ("DESIGN.byp_nozz.mux.Fl_O:stat:T", "Rankine", "Celsius"),
}

CORE_VARS = {
    "T_tot_out_core": ("DESIGN.core_nozz.throat_total.flow.Fl_O:tot:T", "Rankine", "Kelvin"),
    "V_stat_out_core": ("DESIGN.core_nozz.mux.Fl_O:stat:V", 0.3048, None),
    "MN_out_core": ("DESIGN.core_nozz.mux.Fl_O:stat:MN", None, None),
    "P_tot_out_core": ("DESIGN.core_nozz.throat_total.flow.Fl_O:tot:P", 6894.7573, None),
    "massflow_stat_out_core": ("DESIGN.core_nozz.mux.Fl_O:stat:W", 0.45359237, None),
    "T_stat_out_core": ("DESIGN.core_nozz.mux.Fl_O:stat:T", "Rankine", "Kelvin"),
}

# Functions

def get_pycycle_var(prob, var, conversion=None, temp_unit=None):
    val = prob.get_val(var)
    if conversion is not None and isinstance(conversion, (int, float)):
        val = val * conversion
    if isinstance(conversion, str) and temp_unit:
        val = convert_temperature(val, conversion, temp_unit)
    return val


def extract_engine_outputs(prob):
    """Extracts and converts all relevant engine outputs from the PyCycle problem."""
    outputs = {}
    for key, (var, conv, temp_unit) in BYPASS_VARS.items():
        outputs[key] = get_pycycle_var(prob, var, conv, temp_unit)
    for key, (var, conv, temp_unit) in CORE_VARS.items():
        outputs[key] = get_pycycle_var(prob, var, conv, temp_unit)
    return outputs


def turbofan_analysis(alt, MN, Fn):

    def viewer(prob, pt, file=sys.stdout):
        if pt == "DESIGN":
            MN = prob["DESIGN.fc.Fl_O:stat:MN"]
        else:
            MN = prob[pt + ".fc.Fl_O:stat:MN"]
        summary_data = (
            float(np.asarray(MN).squeeze()),
            float(np.asarray(prob[pt + ".fc.alt"]).squeeze()),
            float(np.asarray(prob[pt + ".inlet.Fl_O:stat:W"]).squeeze()),
            float(np.asarray(prob[pt + ".perf.Fn"]).squeeze()),
            float(np.asarray(prob[pt + ".perf.Fg"]).squeeze()),
            float(np.asarray(prob[pt + ".inlet.F_ram"]).squeeze()),
            float(np.asarray(prob[pt + ".perf.OPR"]).squeeze()),
            float(np.asarray(prob[pt + ".perf.TSFC"]).squeeze()),
            float(np.asarray(prob[pt + ".splitter.BPR"]).squeeze()),
        )
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
    prob.set_val("DESIGN.fc.alt", alt * 3.2808399, units="ft")
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

    with open("hbtf_des_view.out", "w") as viewer_file:
        viewer(prob, "DESIGN", file=viewer_file)
        prob.run_model()

    outputs = extract_engine_outputs(prob)
    return tuple(outputs[k] for k in list(BYPASS_VARS.keys()) + list(CORE_VARS.keys()))


def write_hbtf_file(
    file,
    t_tot_out_byp,
    v_stat_out_byp,
    mn_out_byp,
    p_tot_out_byp,
    massflow_stat_out_byp,
    t_stat_out_byp,
    t_tot_out_core,
    v_stat_out_core,
    mn_out_core,
    p_tot_out_core,
    massflow_stat_out_core,
    t_stat_out_core,
):
    lines = [
        f"{t_tot_out_byp=} [K]",
        f"{v_stat_out_core=} [m/s]",
        f"{mn_out_core=} [adim]",
        f"{p_tot_out_core=} [Pa]",
        f"{massflow_stat_out_core=} [kg/s]",
        f"{t_stat_out_core=} [K]",
        f"{t_tot_out_byp=} [K]",
        f"{t_tot_out_core=} []," f"{v_stat_out_byp=} [m/s]",
        f"{mn_out_byp=} [adim]",
        f"{p_tot_out_byp=} [Pa]",
        f"{massflow_stat_out_byp=} [kg/s]",
        f"{t_stat_out_byp=} [K]",
    ]
    file.write("\n".join(lines) + "\n")
    log.info("hbtf.dat file generated!")
    return file


# =================================================================================================
#   CLASSES
# =================================================================================================


class HBTF(pyc.Cycle):
    def setup(self):
        design = self.options["design"]
        # pyCycle reads thermo options early in setup (and behavior changed across versions).
        # Ensure they are set consistently, and choose a matching combustor fuel model.
        thermo_method = self.options["thermo_method"]
        if thermo_method == "TABULAR":
            if self.options["thermo_data"] is None:
                self.options["thermo_data"] = pyc.AIR_JETA_TAB_SPEC
            fuel_type = "FAR"
        elif thermo_method == "CEA":
            if self.options["thermo_data"] is None:
                self.options["thermo_data"] = pyc.species_data.janaf
            fuel_type = "Jet-A(g)"
        else:
            raise ValueError(f"Unsupported thermo_method={thermo_method!r}")

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
                map_data=pyc.HPCMap, bleed_names=["cool1", "cool2", "cust"], map_extrap=True
            ),
            promotes_inputs=[("Nmech", "HP_Nmech")],
        )
        self.add_subsystem("bld3", pyc.BleedOut(bleed_names=["cool3", "cool4"]))
        self.add_subsystem("burner", pyc.Combustor(fuel_type=fuel_type))
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
        self.add_subsystem(
            "lp_shaft", pyc.Shaft(num_ports=3), promotes_inputs=[("Nmech", "LP_Nmech")]
        )
        self.add_subsystem(
            "hp_shaft", pyc.Shaft(num_ports=2), promotes_inputs=[("Nmech", "HP_Nmech")]
        )
        self.add_subsystem("perf", pyc.Performance(num_nozzles=2, num_burners=1))

        # Connections
        self.connect("inlet.Fl_O:tot:P", "perf.Pt2")
        self.connect("hpc.Fl_O:tot:P", "perf.Pt3")
        self.connect("burner.Wfuel", "perf.Wfuel_0")
        self.connect("inlet.F_ram", "perf.ram_drag")
        self.connect("core_nozz.Fg", "perf.Fg_0")
        self.connect("byp_nozz.Fg", "perf.Fg_1")
        self.connect("fan.trq", "lp_shaft.trq_0")
        self.connect("lpc.trq", "lp_shaft.trq_1")
        self.connect("lpt.trq", "lp_shaft.trq_2")
        self.connect("hpc.trq", "hp_shaft.trq_0")
        self.connect("hpt.trq", "hp_shaft.trq_1")
        self.connect("fc.Fl_O:stat:P", "core_nozz.Ps_exhaust")
        self.connect("fc.Fl_O:stat:P", "byp_nozz.Ps_exhaust")

        balance = om.BalanceComp()
        self.add_subsystem("balance", balance)
        if design:
            balance.add_balance("W", units="lbm/s", eq_units="lbf")
            self.connect("balance.W", "fc.W")
            self.connect("perf.Fn", "balance.lhs:W")
            self.promotes("balance", inputs=[("rhs:W", "Fn_DES")])
            balance.add_balance("FAR", eq_units="degR", lower=1e-4, val=0.017)
            self.connect("balance.FAR", "burner.Fl_I:FAR")
            self.connect("burner.Fl_O:tot:T", "balance.lhs:FAR")
            self.promotes("balance", inputs=[("rhs:FAR", "T4_MAX")])
            balance.add_balance(
                "lpt_PR", val=1.5, lower=1.001, upper=8, eq_units="hp", use_mult=True, mult_val=-1
            )
            self.connect("balance.lpt_PR", "lpt.PR")
            self.connect("lp_shaft.pwr_in_real", "balance.lhs:lpt_PR")
            self.connect("lp_shaft.pwr_out_real", "balance.rhs:lpt_PR")
            balance.add_balance(
                "hpt_PR", val=1.5, lower=1.001, upper=8, eq_units="hp", use_mult=True, mult_val=-1
            )
            self.connect("balance.hpt_PR", "hpt.PR")
            self.connect("hp_shaft.pwr_in_real", "balance.lhs:hpt_PR")
            self.connect("hp_shaft.pwr_out_real", "balance.rhs:hpt_PR")

        # Flow connections
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
        self.pyc_connect_flow("hpc.cool1", "lpt.cool1", connect_stat=False)
        self.pyc_connect_flow("hpc.cool2", "lpt.cool2", connect_stat=False)
        self.pyc_connect_flow("bld3.cool3", "hpt.cool3", connect_stat=False)
        self.pyc_connect_flow("bld3.cool4", "hpt.cool4", connect_stat=False)

        # Solver settings
        newton = self.nonlinear_solver = om.NewtonSolver()
        newton.options["atol"] = 1e-8
        newton.options["rtol"] = 1e-99
        newton.options["iprint"] = 2
        newton.options["maxiter"] = 50
        newton.options["solve_subsystems"] = True
        newton.options["max_sub_solves"] = 1000
        newton.options["reraise_child_analysiserror"] = False
        ls = newton.linesearch = om.ArmijoGoldsteinLS()
        ls.options["maxiter"] = 3
        ls.options["rho"] = 0.75
        self.linear_solver = om.DirectSolver()
        super().setup()


class MPhbtf(pyc.MPCycle):
    def setup(self):
        # Pass thermo options at construction time for compatibility with newer pyCycle versions.
        self.pyc_add_pnt("DESIGN", HBTF(thermo_method="CEA", thermo_data=pyc.species_data.janaf))
        super().setup()
