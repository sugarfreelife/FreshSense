"""Validation of sensor ranges. Returns (ok, errors)."""

GAS_MIN, GAS_MAX = 0.0, 5000.0
TEMP_MIN, TEMP_MAX = -40.0, 85.0
HUM_MIN, HUM_MAX = 0.0, 100.0


def validate_reading(gas_value=None, temperature=None, humidity=None) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if gas_value is not None and not (GAS_MIN <= float(gas_value) <= GAS_MAX):
        errors.append(f"gas_value out of range [{GAS_MIN}, {GAS_MAX}]")
    if temperature is not None and not (TEMP_MIN <= float(temperature) <= TEMP_MAX):
        errors.append(f"temperature out of range [{TEMP_MIN}, {TEMP_MAX}]")
    if humidity is not None and not (HUM_MIN <= float(humidity) <= HUM_MAX):
        errors.append(f"humidity out of range [{HUM_MIN}, {HUM_MAX}]")
    if gas_value is None and temperature is None and humidity is None:
        errors.append("At least one of gas_value, temperature, humidity is required")
    return (len(errors) == 0, errors)
