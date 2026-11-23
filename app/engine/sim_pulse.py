"""
app/engine/sim_pulse.py — Generator Sim Pulse & Ticking Clock Deterministik

Sim Pulse adalah direktif pendek yang menggerakkan dinamika skenario
(momentum naik/turun, tekanan waktu, dsb.) tanpa menunggu LLM.

Deterministik & dapat direproduksi per cabang menggunakan:
    random.Random(f"{rng_seed}:{node_id}:{turn_index}")
sehingga cabang yang sama selalu mendapat pulsa yang sama,
sambil cabang berbeda bisa berbeda.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

# Template pulsa (tetap, urut tetap) — dipilih oleh RNG ber-seed.
_PULSE_TEMPLATES: list[str] = [
    "Tekanan waktu naik: tenggat kecil mendekat, keputusan mendesak.",
    "Suasana ruang menghangat; obrolan ringan membuka topik baru.",
    "Satu aktor mulai curiga terhadap informasi yang ia terima.",
    "Perubahan jadwal memaksa penundaan rencana yang sudah disusun.",
    "Pilihan baru terbuka berkat bantuan pihak ketiga.",
    "Ketegangan lama membesar menjadi konflik terbuka.",
    "Aktor menerima pesan misterius yang mengubah prioritas.",
    "Sumber daya menipis; efisiensi menjadi fokus semua pihak.",
]


@dataclass(frozen=True)
class SimPulse:
    """Satu paket Sim Pulse + Ticking Clock untuk satu giliran."""

    directive: str
    ticking_clock: str


def generate_sim_pulse(
    *,
    rng_seed: int,
    node_id: str,
    turn_index: int,
) -> SimPulse:
    """Hasilkan Sim Pulse deterministik untuk (rng_seed, node, giliran).

    Panggilan berulang dengan argumen identik menjamin hasil identik
    (byte-for-byte), sesuai desain KV prefix cache.
    """
    rng = random.Random(f"{rng_seed}:{node_id}:{turn_index}")
    template = _PULSE_TEMPLATES[rng.randrange(len(_PULSE_TEMPLATES))]
    swing = rng.randint(-1, 1)
    momentum = "naik" if swing > 0 else ("turun" if swing < 0 else "stabil")
    return SimPulse(
        directive=f"Sim Pulse T{turn_index}: {template}",
        ticking_clock=f"T{turn_index} | momentum {momentum}",
    )
