"""Single source of truth for simulation constants, the SLA definition and the power model parameters."""
import os

# --- Workload / execution ---
MIPS_PER_CORE = 2500.0

# --- SLA ---
# deadline = arrival_time + SLA_DEADLINE_SLACK * ideal_exec_time
# ideal_exec_time = workload_mi / (vcpus * MIPS_PER_CORE), i.e. runtime with no queueing or wake-up delay.
# A task violates its SLA when it finishes after its deadline.
SLA_DEADLINE_SLACK = float(os.environ.get("DCTWIN_SLA_SLACK", "1.5"))


def ideal_exec_time(workload_mi: float, vcpus: int) -> float:
    return workload_mi / (vcpus * MIPS_PER_CORE)


def task_deadline(arrival_time: float, workload_mi: float, vcpus: int, slack: float = None) -> float:
    if slack is None:
        slack = SLA_DEADLINE_SLACK
    return arrival_time + slack * ideal_exec_time(workload_mi, vcpus)


def is_sla_violation(finish_time: float, deadline: float) -> bool:
    return finish_time > deadline + 1e-9

# --- Engine ---
DT = 1.0  # simulation tick, seconds
DEFAULT_ARRIVAL_RATE = 3.0  # Poisson task arrivals, tasks per second
MAX_RECORDED_STEPS = 200  # step_metrics rows per server are downsampled to at most this many
OVERLOAD_THRESHOLD = 0.85  # utilization fraction above which a server counts as overloaded

# --- Power model ---
# Awake: P = P_idle + (P_max - P_idle) * u, with u = busy cores / total cores.
# Waking servers draw P_idle; sleeping servers draw P_SLEEP_W.
POWER_CLASSES = {  # cores -> (P_idle W, P_max W)
    32: (50.0, 220.0),
    64: (72.0, 335.0),
    96: (88.0, 410.0),
    128: (105.0, 490.0),
}
P_SLEEP_W = 8.0
WAKE_DELAY_S = 5.0  # time from dispatch to a sleeping server until it can start work
IDLE_TIMEOUT_S = 10.0  # an awake server with no work goes to sleep after this long (when sleep is enabled)

# --- RL reward ---
# reward per step = -(RL_W_ENERGY * Wh used) - (RL_W_SLA * SLA violations) - (RL_W_OVERLOAD * overload excess)
# where overload excess = sum over servers and ticks of max(0, u - OVERLOAD_THRESHOLD) * dt.
RL_W_ENERGY = 1.0
RL_W_SLA = 2.0
RL_W_OVERLOAD = 1.0

# --- Analytics flags (per run, from server_stats) ---
IDLE_FLAG_FRACTION = 0.8  # idle if asleep or awake-without-work for more than this share of the run
OVERLOAD_FLAG_FRACTION = 0.2  # overloaded if above OVERLOAD_THRESHOLD for more than this share of the run
