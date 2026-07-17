from .session import SESSION_TOOLS
from .parameters import PARAMETERS_TOOLS
from .geometry import GEOMETRY_TOOLS
from .solver import SOLVER_TOOLS

# Aggregate all tools into a single list to be imported by the adapter
ALL_TOOLS = SESSION_TOOLS + PARAMETERS_TOOLS + GEOMETRY_TOOLS + SOLVER_TOOLS
