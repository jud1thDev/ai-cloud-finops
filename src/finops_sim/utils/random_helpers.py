"""Seeded random helpers for reproducible generation."""

from __future__ import annotations

import random
import string


class SeededRandom:
    """Wrapper around random.Random with convenience methods."""

    def __init__(self, seed: int) -> None:
        self.seed = seed
        self._rng = random.Random(seed)

    def integer(self, low: int, high: int) -> int:
        return self._rng.randint(low, high)

    def floating(self, low: float, high: float) -> float:
        return self._rng.uniform(low, high)

    def choice(self, seq: list) -> object:
        return self._rng.choice(seq)

    def sample(self, seq: list, k: int) -> list:
        return self._rng.sample(seq, k)

    def shuffle(self, seq: list) -> None:
        self._rng.shuffle(seq)

    def gauss(self, mu: float, sigma: float) -> float:
        return self._rng.gauss(mu, sigma)

    def resource_name(self, prefix: str = "res") -> str:
        suffix = "".join(self._rng.choices(string.ascii_lowercase + string.digits, k=6))
        return f"{prefix}-{suffix}"

    def ip_address(self, prefix: str = "10.0") -> str:
        return f"{prefix}.{self._rng.randint(0, 255)}.{self._rng.randint(1, 254)}"

    def percentage(self, mean: float, std: float, clip: bool = True) -> float:
        val = self._rng.gauss(mean, std)
        if clip:
            val = max(0.0, min(100.0, val))
        return round(val, 2)

    def timeseries(
        self,
        length: int,
        pattern: str = "normal",
        **kwargs,
    ) -> list[float]:
        """Generate a time series of given length.

        Patterns:
        - zero: all zeros
        - constant: constant value
        - normal: gaussian noise around mean
        - spike: normal with random spikes
        - sawtooth: periodic ramp
        - step_down: high then drops
        """
        if pattern == "zero":
            return [0.0] * length

        if pattern == "constant":
            val = kwargs.get("value", 50.0)
            return [val] * length

        if pattern == "normal":
            mean = kwargs.get("mean", 50.0)
            std = kwargs.get("std", 10.0)
            clip_min = kwargs.get("clip_min", 0.0)
            clip_max = kwargs.get("clip_max", 100.0)
            return [
                round(max(clip_min, min(clip_max, self._rng.gauss(mean, std))), 2)
                for _ in range(length)
            ]

        if pattern == "spike":
            mean = kwargs.get("mean", 30.0)
            std = kwargs.get("std", 5.0)
            spike_chance = kwargs.get("spike_chance", 0.05)
            spike_mult = kwargs.get("spike_mult", 3.0)
            series = []
            for _ in range(length):
                val = self._rng.gauss(mean, std)
                if self._rng.random() < spike_chance:
                    val *= spike_mult
                series.append(round(max(0.0, val), 2))
            return series

        if pattern == "sawtooth":
            period = kwargs.get("period", 24)
            low = kwargs.get("low", 10.0)
            high = kwargs.get("high", 80.0)
            return [
                round(low + (high - low) * ((i % period) / period), 2)
                for i in range(length)
            ]

        if pattern == "step_down":
            high_val = kwargs.get("high", 70.0)
            low_val = kwargs.get("low", 10.0)
            step_at = kwargs.get("step_at", length // 2)
            std = kwargs.get("std", 5.0)
            return [
                round(
                    max(
                        0.0,
                        self._rng.gauss(
                            high_val if i < step_at else low_val, std
                        ),
                    ),
                    2,
                )
                for i in range(length)
            ]

        if pattern == "step":
            # Monotonic step (increasing or decreasing)
            start = kwargs.get("start", 10.0)
            step_val = kwargs.get("step", 1.0)
            direction = kwargs.get("direction", "increasing")
            std = kwargs.get("std", 0.0)
            mult = 1.0 if direction == "increasing" else -1.0
            return [
                round(max(0.0, start + mult * step_val * i + self._rng.gauss(0, std)), 2)
                for i in range(length)
            ]

        if pattern == "normal_with_spike":
            # Normal distribution with periodic spikes
            mean = kwargs.get("mean", 50.0)
            std = kwargs.get("std", 10.0)
            spike_chance = kwargs.get("spike_chance", 0.05)
            spike_mult = kwargs.get("spike_mult", 3.0)
            series = []
            for _ in range(length):
                val = self._rng.gauss(mean, std)
                if self._rng.random() < spike_chance:
                    val *= spike_mult
                series.append(round(max(0.0, val), 2))
            return series

        if pattern == "spike_cycle":
            # Periodic spike cycles (e.g., scale-out/in)
            period = kwargs.get("period", 48)
            low = kwargs.get("low", 2.0)
            high = kwargs.get("high", 15.0)
            std = kwargs.get("std", 1.0)
            series = []
            for i in range(length):
                phase = (i % period) / period
                # Quick spike up, slow decay
                if phase < 0.2:
                    base = low + (high - low) * (phase / 0.2)
                else:
                    base = high - (high - low) * ((phase - 0.2) / 0.8)
                series.append(round(max(0.0, base + self._rng.gauss(0, std)), 2))
            return series

        if pattern == "decreasing_linear":
            start = kwargs.get("start", 80.0)
            end = kwargs.get("end", 20.0)
            std = kwargs.get("std", 3.0)
            return [
                round(
                    max(0.0, start + (end - start) * i / max(length - 1, 1) + self._rng.gauss(0, std)),
                    2,
                )
                for i in range(length)
            ]

        if pattern == "varying_constant":
            # Constant with slight random variation
            value = kwargs.get("value", 50.0)
            variance = kwargs.get("variance", 0.1)
            return [
                round(max(0.0, value * (1 + self._rng.gauss(0, variance))), 2)
                for _ in range(length)
            ]

        raise ValueError(f"Unknown pattern: {pattern}")
