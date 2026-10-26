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
