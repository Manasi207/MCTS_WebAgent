# backend/mcts/variants/__init__.py
from .basic_mcts import run_basic_mcts
from .r_mcts import run_r_mcts
from .world_model_mcts import run_wm_mcts
from .rag_mcts import run_rag_mcts

VARIANT_RUNNERS = {
    "basic-mcts": run_basic_mcts,
    "r-mcts":     run_r_mcts,
    "wm-mcts":    run_wm_mcts,
    "rag-mcts":   run_rag_mcts,
}

__all__ = [
    "run_basic_mcts",
    "run_r_mcts",
    "run_wm_mcts",
    "run_rag_mcts",
    "VARIANT_RUNNERS",
]