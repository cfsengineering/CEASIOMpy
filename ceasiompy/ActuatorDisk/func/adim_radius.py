def adimensionalize_radius(radius, hub_radius, stations):
    r = np.linspace(0, 1, stations)
    i_hub = np.abs(r - hub_radius / radius).argmin()
    if r[i_hub] < hub_radius:
        i_hub += 1
