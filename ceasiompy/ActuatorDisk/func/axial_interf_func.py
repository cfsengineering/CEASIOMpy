def axial_interference_function(lagrangian_moltiplicator, non_dimensional_radius):
    """
    Function to calculate the axial intereference factor useful to calculate properly the thrust
    coefficient distribution

    Args:
        lagrangian_moltiplicator (float): Lagrangian moltiplicator [-]
        non_dimensional_radius (float): Non dimensional radius [-]

    Returns:
        axial_interference_factor (float):  Axial interference factor[-]
    """

    axial_interference_factor = (lagrangian_moltiplicator * non_dimensional_radius**2) / (
        non_dimensional_radius**2 + (1 + lagrangian_moltiplicator) ** 2
    )
    return axial_interference_factor
