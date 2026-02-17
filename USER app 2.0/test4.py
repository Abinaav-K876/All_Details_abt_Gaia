def _make_fake_node(idx: int) -> dict:
    """Simulated sensors: MQ135 (AQ), MQ7 (CO), DHT22 (temp, hum)."""
    import random
    return {
        "id": f"GS-AIR-{1000 + idx}",
        'pass': "",
        "mq135": round(random.uniform(50, 300), 1),  # ppm (relative)
        "mq7": round(random.uniform(5, 60), 1),  # ppm CO
        "temp": round(random.uniform(22, 34), 1),  # °C
        "hum": round(random.uniform(35, 70), 1),  # %
        "battery": random.randint(40, 100),
        "online": random.choice([True, True, True, False]),
    }