import argparse
import random
from dataclasses import dataclass
from typing import Iterator, List, Optional, Tuple

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


@dataclass
class SortConfig:
    min_wait_ticks: int = 3
    max_wait_ticks: int = 12
    guilt_probability: float = 0.65
    productive_nudge_probability: float = 0.20
    max_steps: int = 600
    panic_steps: int = 400
    frame_ms: int = 120


@dataclass
class Snapshot:
    values: List[int]
    action: str
    step: int
    total_wait: int
    guilt_swaps: int
    helpful_swaps: int
    highlights: Tuple[int, ...] = ()
    done: bool = False
    sorted_now: bool = False


def is_sorted(values: List[int]) -> bool:
    return all(values[i] <= values[i + 1] for i in range(len(values) - 1))


def count_inversions(values: List[int]) -> int:
    inv = 0
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            if values[i] > values[j]:
                inv += 1
    return inv


def first_inversion_index(values: List[int]) -> Optional[int]:
    for i in range(len(values) - 1):
        if values[i] > values[i + 1]:
            return i
    return None


def procrastination_sort_events(values: List[int], cfg: SortConfig) -> Iterator[Snapshot]:
    arr = values.copy()
    step = 0
    total_wait = 0
    guilt_swaps = 0
    helpful_swaps = 0

    yield Snapshot(
        values=arr.copy(),
        action="Staring at the list... building motivation.",
        step=step,
        total_wait=total_wait,
        guilt_swaps=guilt_swaps,
        helpful_swaps=helpful_swaps,
        sorted_now=is_sorted(arr),
    )

    while step < cfg.max_steps:
        if is_sorted(arr):
            yield Snapshot(
                values=arr.copy(),
                action="Somehow sorted. Claiming this was intentional.",
                step=step,
                total_wait=total_wait,
                guilt_swaps=guilt_swaps,
                helpful_swaps=helpful_swaps,
                done=True,
                sorted_now=True,
            )
            return

        wait_ticks = random.randint(cfg.min_wait_ticks, cfg.max_wait_ticks)
        for tick in range(wait_ticks):
            if step >= cfg.max_steps:
                break
            step += 1
            total_wait += 1
            yield Snapshot(
                values=arr.copy(),
                action=f"Procrastinating... {tick + 1}/{wait_ticks}",
                step=step,
                total_wait=total_wait,
                guilt_swaps=guilt_swaps,
                helpful_swaps=helpful_swaps,
                sorted_now=False,
            )

        if step >= cfg.max_steps:
            break

        did_action = False

        if len(arr) > 1 and random.random() < cfg.guilt_probability:
            i, j = sorted(random.sample(range(len(arr)), 2))
            before = count_inversions(arr)
            arr[i], arr[j] = arr[j], arr[i]
            after = count_inversions(arr)

            step += 1
            guilt_swaps += 1
            helped = after < before
            if helped:
                helpful_swaps += 1

            mood = "That actually helped." if helped else "That felt productive, but wasn't."
            yield Snapshot(
                values=arr.copy(),
                action=f"Out-of-guilt swap: {i} <-> {j}. {mood}",
                step=step,
                total_wait=total_wait,
                guilt_swaps=guilt_swaps,
                helpful_swaps=helpful_swaps,
                highlights=(i, j),
                sorted_now=is_sorted(arr),
            )
            did_action = True

        if (not did_action) and len(arr) > 1 and random.random() < cfg.productive_nudge_probability:
            inv_i = first_inversion_index(arr)
            if inv_i is not None:
                arr[inv_i], arr[inv_i + 1] = arr[inv_i + 1], arr[inv_i]
                step += 1
                yield Snapshot(
                    values=arr.copy(),
                    action=f"Accidental productivity at {inv_i}/{inv_i + 1}.",
                    step=step,
                    total_wait=total_wait,
                    guilt_swaps=guilt_swaps,
                    helpful_swaps=helpful_swaps,
                    highlights=(inv_i, inv_i + 1),
                    sorted_now=is_sorted(arr),
                )
                did_action = True

        if not did_action:
            step += 1
            yield Snapshot(
                values=arr.copy(),
                action="Opened another tab instead of sorting.",
                step=step,
                total_wait=total_wait,
                guilt_swaps=guilt_swaps,
                helpful_swaps=helpful_swaps,
                sorted_now=is_sorted(arr),
            )

    # Panic mode: deadline is near, so the sort finally makes progress.
    panic_count = 0
    while not is_sorted(arr) and panic_count < cfg.panic_steps:
        inv_i = first_inversion_index(arr)
        if inv_i is None:
            break
        arr[inv_i], arr[inv_i + 1] = arr[inv_i + 1], arr[inv_i]
        panic_count += 1
        step += 1
        yield Snapshot(
            values=arr.copy(),
            action="Deadline panic swap!",
            step=step,
            total_wait=total_wait,
            guilt_swaps=guilt_swaps,
            helpful_swaps=helpful_swaps,
            highlights=(inv_i, inv_i + 1),
            sorted_now=is_sorted(arr),
        )

    done_sorted = is_sorted(arr)
    yield Snapshot(
        values=arr.copy(),
        action=(
            "Sorted at the last moment. Stress levels were optimal."
            if done_sorted
            else "Still not sorted. Maybe tomorrow."
        ),
        step=step,
        total_wait=total_wait,
        guilt_swaps=guilt_swaps,
        helpful_swaps=helpful_swaps,
        done=True,
        sorted_now=done_sorted,
    )


def build_values(size: int, seed: int) -> List[int]:
    random.seed(seed)
    return random.sample(range(5, size * 8 + 5), size)


def run_visualizer(values: List[int], cfg: SortConfig) -> None:
    fig, ax = plt.subplots(figsize=(12, 7), dpi=110)
    fig.patch.set_facecolor("#eaf3ff")
    ax.set_facecolor("#f8fbff")

    x = list(range(len(values)))
    max_v = max(values) if values else 1

    base_color = "#4d8ef7"
    bars = ax.bar(x, values, width=0.85, color=base_color, edgecolor="#2156a5", linewidth=0.7)

    ax.set_title("Procrastination Sort Visualizer", fontsize=18, color="#0f3f78", pad=15, weight="bold")
    ax.set_xlabel("Index", fontsize=12, color="#1f4f8c")
    ax.set_ylabel("Value", fontsize=12, color="#1f4f8c")
    ax.set_ylim(0, max_v * 1.2)
    ax.grid(axis="y", alpha=0.25, color="#7aa7df")

    for spine in ax.spines.values():
        spine.set_color("#7aa7df")

    status = ax.text(
        0.015,
        0.96,
        "",
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=11,
        color="#0f3f78",
        bbox=dict(boxstyle="round,pad=0.45", facecolor="#dcecff", edgecolor="#7aa7df", alpha=0.95),
    )

    events = procrastination_sort_events(values, cfg)

    def update(snapshot: Snapshot):
        local_max = max(snapshot.values) if snapshot.values else 1
        ax.set_ylim(0, max(local_max * 1.2, 10))

        for i, (bar, value) in enumerate(zip(bars, snapshot.values)):
            bar.set_height(value)
            if i in snapshot.highlights:
                bar.set_color("#ff9f6e")
                bar.set_edgecolor("#b65320")
                bar.set_linewidth(1.4)
            elif snapshot.sorted_now:
                bar.set_color("#43c27a")
                bar.set_edgecolor("#1d7d49")
                bar.set_linewidth(0.9)
            else:
                intensity = 0.45 + (value / max(local_max, 1)) * 0.45
                bar.set_color((0.2, 0.45, 0.95, intensity))
                bar.set_edgecolor("#2156a5")
                bar.set_linewidth(0.7)

        status_text = (
            f"Action: {snapshot.action}\n"
            f"Step: {snapshot.step}    Wait Ticks: {snapshot.total_wait}\n"
            f"Guilt Swaps: {snapshot.guilt_swaps}    Helpful Swaps: {snapshot.helpful_swaps}\n"
            f"Sorted: {'Yes' if snapshot.sorted_now else 'No'}"
        )
        status.set_text(status_text)

        if snapshot.done:
            anim.event_source.stop()

        return (*bars, status)

    anim = FuncAnimation(fig, update, frames=events, interval=cfg.frame_ms, repeat=False, blit=False)
    plt.tight_layout()
    plt.show()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Procrastination Sort with a visualizer.")
    parser.add_argument("--size", type=int, default=22, help="Number of values in the list.")
    parser.add_argument("--seed", type=int, default=17, help="Random seed for reproducible input list.")
    parser.add_argument("--speed", type=int, default=120, help="Frame duration in milliseconds.")
    parser.add_argument("--min-wait", type=int, default=3, help="Minimum procrastination ticks per cycle.")
    parser.add_argument("--max-wait", type=int, default=12, help="Maximum procrastination ticks per cycle.")
    parser.add_argument(
        "--values",
        type=str,
        default="",
        help="Optional comma-separated list, e.g. 9,1,5,3,2",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.values.strip():
        values = [int(x.strip()) for x in args.values.split(",") if x.strip()]
        if len(values) < 2:
            raise ValueError("Please provide at least two numbers in --values.")
    else:
        if args.size < 2:
            raise ValueError("--size must be at least 2.")
        values = build_values(args.size, args.seed)

    cfg = SortConfig(
        min_wait_ticks=max(1, args.min_wait),
        max_wait_ticks=max(args.min_wait, args.max_wait),
        frame_ms=max(25, args.speed),
    )

    run_visualizer(values, cfg)


if __name__ == "__main__":
    main()
