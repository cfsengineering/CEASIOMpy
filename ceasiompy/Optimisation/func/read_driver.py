"""
Plot the results of the optimisation routine.
"""
import sys
import openmdao.api as om
import numpy as np
import matplotlib.pyplot as plt


def gen_plot(dic, objective=False, constrains=False):
    """
    Generate plots.

    Parameters
    ----------
    dic : TYPE
        DESCRIPTION.
    objective : TYPE, optional
        DESCRIPTION. The default is False.
    constrains : TYPE, optional
        DESCRIPTION. The default is False.

    Returns
    -------
    None.

    """
    iterations = len(dic)

    plt.figure()
    if objective:
        for key, lst in dic.items():
            iterations = np.arange(len(lst))
            plt.plot(iterations, -lst+lst[0], label=key)
            plt.legend()
    elif constrains:
        for key, lst in dic.items():
            if 'const' in key:
                iterations = np.arange(len(lst))
                plt.plot(iterations, lst-lst[0], label=key)
                plt.legend()
    else:
        for key, lst in dic.items():
            iterations = np.arange(len(lst))
            plt.plot(iterations, lst-lst[0], label=key)
            plt.legend()


def read_results(optim_dir_path, routine_type):
    """
    Read sql file.

    Returns
    -------
    None.

    """
    # Read recorded options
    path = optim_dir_path
    cr = om.CaseReader(path + '/Driver_recorder.sql')
    # driver_cases = cr.list_cases('driver') (If  multiple recorders)

    cases = cr.get_cases()

    # Initiates dictionnaries
    case1 = cr.get_case(0)
    obj = case1.get_objectives()
    des = case1.get_design_vars()
    const = case1.get_constraints()

    for case in cases[1::]:
        for key, val in case.get_objectives().items():
            obj[key] = np.append(obj[key], val)

        for key, val in case.get_design_vars().items():
            des[key] = np.append(des[key], val)

        for key, val in case.get_constraints().items():
            if 'const' in key:
                const[key] = np.append(const[key], val)

    # Datapoints for DoE
    if routine_type.upper() == 'DOE':
        fig = plt.figure()
        r = 0
        c = 1
        cols_per_row = 5
        nbR = len(obj.keys()) + len(des.keys()) % cols_per_row
        nbC = cols_per_row

        for keyo, valo in obj.items():
            plt.ylabel(keyo)
            for key, val in des.items():
                plt.subplot(nbR, nbC, c+r*nbC)
                plt.scatter(val, valo)
                plt.xlabel(key)
                if c == 1:
                    plt.ylabel(keyo)
                c += 1
                if c > cols_per_row:
                    r += 1
                    c = 1
            c = 1
            r += 1

    # Iterative evolution for Optim
    gen_plot(obj, objective=True)
    gen_plot(des)
    gen_plot(const, constrains=True)

    # 3D plot
    # fig = plt.figure()
    # ax = fig.gca(projection='3d')
    # ax.scatter(des['indeps.wing2_span'],des['indeps.wing1_span'],-obj['objective.cl'])

    plt.show()


if __name__ == "__main__":

    global key_dict
    key_dict = []
    if len(sys.argv)>1:
        for args in sys.argv:
            key_dict.append(args)
    read_results()

