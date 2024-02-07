"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Function to run the PyCycle code for the turbojet engine

Python version: >=3.8

| Author: Giacomo Benedetti and Francesco Marcucci
| Creation: 2023-12-12

"""

import openmdao.api as om

import pycycle.api as pyc

from scipy.constants import convert_temperature

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger()

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def turbojet_analysis(alt, MN, Fn):
    class Turbojet(pyc.Cycle):
        def setup(self):

            USE_TABULAR = True

            if USE_TABULAR:
                self.options["thermo_method"] = "TABULAR"
                self.options["thermo_data"] = pyc.AIR_JETA_TAB_SPEC
                FUEL_TYPE = "FAR"

            design = self.options["design"]

            # Add engine elements
            self.add_subsystem("fc", pyc.FlightConditions())
            self.add_subsystem("inlet", pyc.Inlet())
            self.add_subsystem(
                "comp",
                pyc.Compressor(map_data=pyc.AXI5, map_extrap=True),
                promotes_inputs=["Nmech"],
            )
            self.add_subsystem("burner", pyc.Combustor(fuel_type=FUEL_TYPE))
            self.add_subsystem(
                "turb", pyc.Turbine(map_data=pyc.LPT2269), promotes_inputs=["Nmech"]
            )
            self.add_subsystem("nozz", pyc.Nozzle(nozzType="CD", lossCoef="Cv"))
            self.add_subsystem("shaft", pyc.Shaft(num_ports=2), promotes_inputs=["Nmech"])
            self.add_subsystem("perf", pyc.Performance(num_nozzles=1, num_burners=1))

            # Connect flow stations
            self.pyc_connect_flow("fc.Fl_O", "inlet.Fl_I", connect_w=False)
            self.pyc_connect_flow("inlet.Fl_O", "comp.Fl_I")
            self.pyc_connect_flow("comp.Fl_O", "burner.Fl_I")
            self.pyc_connect_flow("burner.Fl_O", "turb.Fl_I")
            self.pyc_connect_flow("turb.Fl_O", "nozz.Fl_I")

            # Make other non-flow connections
            # Connect turbomachinery elements to shaft
            self.connect("comp.trq", "shaft.trq_0")
            self.connect("turb.trq", "shaft.trq_1")

            # Connnect nozzle exhaust to freestream static conditions
            self.connect("fc.Fl_O:stat:P", "nozz.Ps_exhaust")

            # Connect outputs to perfomance element
            self.connect("inlet.Fl_O:tot:P", "perf.Pt2")
            self.connect("comp.Fl_O:tot:P", "perf.Pt3")
            self.connect("burner.Wfuel", "perf.Wfuel_0")
            self.connect("inlet.F_ram", "perf.ram_drag")
            self.connect("nozz.Fg", "perf.Fg_0")

            # Add balances for design and off-design
            balance = self.add_subsystem("balance", om.BalanceComp())
            if design:

                balance.add_balance("W", units="lbm/s", eq_units="lbf", rhs_name="Fn_target")
                self.connect("balance.W", "inlet.Fl_I:stat:W")
                self.connect("perf.Fn", "balance.lhs:W")

                balance.add_balance(
                    "FAR", eq_units="degR", lower=1e-4, val=0.017, rhs_name="T4_target"
                )
                self.connect("balance.FAR", "burner.Fl_I:FAR")
                self.connect("burner.Fl_O:tot:T", "balance.lhs:FAR")

                balance.add_balance(
                    "turb_PR", val=1.5, lower=1.001, upper=8, eq_units="hp", rhs_val=0.0
                )
                self.connect("balance.turb_PR", "turb.PR")
                self.connect("shaft.pwr_net", "balance.lhs:turb_PR")

            newton = self.nonlinear_solver = om.NewtonSolver()
            newton.options["atol"] = 1e-6
            newton.options["rtol"] = 1e-6
            newton.options["iprint"] = 2
            newton.options["maxiter"] = 15
            newton.options["solve_subsystems"] = True
            newton.options["max_sub_solves"] = 100
            newton.options["reraise_child_analysiserror"] = False

            self.linear_solver = om.DirectSolver()

            super().setup()

    class MPTurbojet(pyc.MPCycle):
        def setup(self):
            self.pyc_add_pnt("DESIGN", Turbojet())

            self.set_input_defaults("DESIGN.Nmech", 8070.0, units="rpm")
            self.set_input_defaults("DESIGN.inlet.MN", 0.60)
            self.set_input_defaults("DESIGN.comp.MN", 0.020)  # .2
            self.set_input_defaults("DESIGN.burner.MN", 0.020)  # .2
            self.set_input_defaults("DESIGN.turb.MN", 0.4)

            self.pyc_add_cycle_param("burner.dPqP", 0.03)
            self.pyc_add_cycle_param("nozz.Cv", 0.99)

            super().setup()

    import time

    # defining the optimization problem

    prob = om.Problem()

    prob.model = MPTurbojet()
    prob.setup(check=False)

    # define input values
    prob.set_val("DESIGN.fc.alt", alt, units="ft")
    prob.set_val("DESIGN.fc.MN", MN)
    prob.set_val("DESIGN.balance.Fn_target", Fn, units="lbf")
    prob.set_val("DESIGN.balance.T4_target", 2370.0, units="degR")
    prob.set_val("DESIGN.comp.PR", 13.5)
    prob.set_val("DESIGN.comp.eff", 0.83)
    prob.set_val("DESIGN.turb.eff", 0.86)

    if Fn > 2700:
        prob["DESIGN.balance.FAR"] = 0.0175506829934
        prob["DESIGN.balance.W"] = 75.453135137
        prob["DESIGN.balance.turb_PR"] = 4.46138725662
        prob["DESIGN.fc.balance.Pt"] = 14.6955113159
        prob["DESIGN.fc.balance.Tt"] = 518.665288153

    elif 2700 <= Fn < 850:
        prob["DESIGN.balance.FAR"] = 0.0175506829934
        prob["DESIGN.balance.W"] = 50.453135137
        prob["DESIGN.balance.turb_PR"] = 4.46138725662
        prob["DESIGN.fc.balance.Pt"] = 14.6955113159
        prob["DESIGN.fc.balance.Tt"] = 518.665288153

    else:
        prob["DESIGN.balance.FAR"] = 0.0175506829934
        prob["DESIGN.balance.W"] = 10.453135137
        prob["DESIGN.balance.turb_PR"] = 4.46138725662
        prob["DESIGN.fc.balance.Pt"] = 14.6955113159
        prob["DESIGN.fc.balance.Tt"] = 518.665288153

    prob.set_solver_print(level=-1)
    # prob.set_solver_print(level=2, depth=1)

    prob.run_model()

    print()

    # command to visualize all the output of the system
    # a = prob.model.list_outputs(val=True, units=True)

    T_tot_out = convert_temperature(
        (prob.get_val("DESIGN.nozz.throat_total.flow.Fl_O:tot:T")), "Rankine", "Kelvin"
    )
    V_stat_out = (prob.get_val("DESIGN.nozz.mux.Fl_O:stat:V")) * 0.3048
    MN_out = prob.get_val("DESIGN.nozz.mux.Fl_O:stat:MN")
    T_stat_out = convert_temperature(
        prob.get_val("DESIGN.nozz.mux.Fl_O:stat:T"), "Rankine", "Kelvin"
    )  # celsius
    massflow_stat_out = prob.get_val("DESIGN.nozz.mux.Fl_O:stat:W") * 0.45359237  # kg/s
    P_tot_out = prob.get_val("DESIGN.nozz.throat_total.flow.Fl_O:tot:P") * 6894.7573  # Pa
    P_stat_out = prob.get_val("DESIGN.nozz.mux.Fl_O:stat:P") * 6894.7573  # Pa

    return (
        T_tot_out,
        V_stat_out,
        MN_out,
        P_tot_out,
        massflow_stat_out,
        T_stat_out,
        P_stat_out,
    )


def write_turbojet_file(
    file,
    T_tot_out,
    V_stat_out,
    MN_out,
    P_tot_out,
    massflow_stat_out,
    T_stat_out,
    P_stat_out,
):

    file.write(f"T_tot_out = {T_tot_out} [K]\n")
    file.write(f"V_stat_out = {V_stat_out} [m/s]\n")
    file.write(f"MN_out = {MN_out} [adim]\n")
    file.write(f"P_tot_out = {P_tot_out} [Pa]\n")
    file.write(f"massflow_out = {massflow_stat_out} [kg/s]\n")
    file.write(f"T_stat_out = {T_stat_out} [K]\n")
    file.write(f"P_stat_out = {P_stat_out} [Pa]\n")

    log.info("turbojet.dat file generated!")

    return file
