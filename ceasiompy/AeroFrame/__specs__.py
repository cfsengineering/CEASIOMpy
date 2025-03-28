from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy import log

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = False

# ===== CPACS inputs and outputs =====
cpacs_inout = CPACSInOut()


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")