"""Run-time settings. Override with environment variables or the CLI flags in run_agent.py."""
import os
from dataclasses import dataclass, field


@dataclass
class Config:
    data_store: str = os.getenv("BFA_DATA_STORE", "data/battery_data_store")  # folder of per-cell CSVs
    out_dir: str = os.getenv("BFA_OUT_DIR", "agent_outputs")
    model: str = os.getenv("BFA_MODEL", "llama3.1:8b")
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    use_llm: bool = True

    # A123 APR18650M1A (LFP/graphite) as used in Severson et al. (2019)
    nominal_ah: float = 1.1
    eol_ah: float = 0.88          # 80 % of nominal

    plot_dir: str = field(init=False)

    def __post_init__(self):
        self.plot_dir = os.path.join(self.out_dir, "plots")

    def make_dirs(self):
        os.makedirs(self.plot_dir, exist_ok=True)
