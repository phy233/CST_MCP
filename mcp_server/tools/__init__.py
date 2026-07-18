from .array import ARRAY_TOOLS
from .boundary import BOUNDARY_TOOLS
from .farfield import FARFIELD_TOOLS
from .geometry import GEOMETRY_TOOLS
from .materials import MATERIALS_TOOLS
from .mesh import MESH_TOOLS
from .monitors import MONITORS_TOOLS
from .optimization import OPTIMIZATION_TOOLS
from .parameters import PARAMETERS_TOOLS
from .port import PORT_TOOLS
from .results import RESULTS_TOOLS
from .session import SESSION_TOOLS
from .solver import SOLVER_TOOLS
from .sweep import SWEEP_TOOLS

# Aggregate all tools into a single list to be imported by the adapter
ALL_TOOLS = ARRAY_TOOLS + BOUNDARY_TOOLS + FARFIELD_TOOLS + GEOMETRY_TOOLS + MATERIALS_TOOLS + MESH_TOOLS + MONITORS_TOOLS + OPTIMIZATION_TOOLS + PARAMETERS_TOOLS + PORT_TOOLS + RESULTS_TOOLS + SESSION_TOOLS + SOLVER_TOOLS + SWEEP_TOOLS
