"""
Plot the results of the optimisation routine.
"""
import sys
import openmdao.api as om
import numpy as np
import matplotlib.pyplot as plt


def gen_plot(dic, ax, offset=False):
    """
    Generate plots.

    Parameters
    ----------
    dic : TYPE
        DESCRIPTION.
    ax : TYPE
        DESCRIPTION.
    offset : TYPE, optional
        DESCRIPTION. The default is False.
    sec : TYPE, optional
        DESCRIPTION. The default is False.

    Returns
    -------
    None.

    """
    isolate = False
    for key in key_dict:
        if key in dic:
            isolate = True
            lst = dic[key]
            iterations = np.arange(len(lst))
            plt.plot(iterations, lst, label=key)

    if not isolate:
        for key, lst in dic.items():
            iterations = np.arange(len(lst))
            if offset:
                ax.plot(iterations, lst-lst[0], label=key)
            else:
                plt.plot(iterations, lst, label=key)

    plt.legend()


def read_results():
    """
    Read the sql file.

    Returns
    -------
    None.

    """
    # Read recorded options
    path = './'
    cr = om.CaseReader(path + 'Driver_recorder.sql')
    # driver_cases = cr.list_cases('driver') (If  multiple recorders)

    cases = cr.get_cases()

    # Initiates dictionnaries
    case1 = cr.get_case(0)
    obj = case1.get_objectives()
    des = case1.get_design_vars()
    const = case1.get_constraints()
    print(const)

    for case in cases[0::]:
        for key, val in case.get_objectives().items():
            obj[key] = np.append(obj[key], val)

        for key, val in case.get_design_vars().items():
            des[key] = np.append(des[key], val)

        for key, val in case.get_constraints().items():
            const[key] = np.append(const[key], val)


    for keyo in obj.items():
        for key in des:
            fig, ax = plt.subplots()
            plt.plot(des[key], obj[keyo])

    # Plot for every iteration
    # fig, ax = plt.subplots()
    # gen_plot(obj, ax)
    # fig, ax = plt.subplots()
    # gen_plot(des, ax)
    # fig, ax = plt.subplots()
    # gen_plot(const, ax)

    # 3D plot
    # fig = plt.figure()
    # ax = fig.gca(projection='3d')
    # ax.scatter(des['indeps.wing2_span'],des['indeps.wing1_span'],-obj['objective.cl'])

    # ax.set_xlabel('Wing2 span')
    # ax.set_ylabel('Wing1 span')
    # ax.set_zlabel('Cl')

    plt.show()


if __name__ == "__main__":

    global key_dict
    key_dict = []
    if len(sys.argv)>1:
        for args in sys.argv:
            key_dict.append(args)
    read_results()
