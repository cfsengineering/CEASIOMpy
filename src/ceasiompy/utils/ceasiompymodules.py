# =================================================================================================
#   IMPORTS
# =================================================================================================

from functools import total_ordering

# =================================================================================================
#   CLASSES
# =================================================================================================


@total_ordering
class CEASIOMpyModule:
    def __init__(
        self: "CEASIOMpyModule",
        module_name: str,
        module_status: bool,
        res_dir: bool,
    ) -> None:
        self.module_name: str = module_name
        self.module_status: bool = module_status
        self.res_dir: bool = res_dir

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CEASIOMpyModule):
            return NotImplemented
        return self.module_name == other.module_name

    def __lt__(self, other: "CEASIOMpyModule") -> bool:
        if not isinstance(other, CEASIOMpyModule):
            return NotImplemented
        return self.module_name < other.module_name
