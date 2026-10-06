"""Build a traceable, human-readable explanation for one stored scan."""

from datetime import datetime


_RECOMMENDATIONS = {
    "CONSUME_NOW": "consume now",
    "CONSUME_SOON": "consume soon",
    "CHECK_EXPIRY": "check the expiry information before deciding",
    "CAUTION_DO_NOT_CONSUME": "do not consume based on the available warning signals",
}


def _humanize(value: str | None) -> str:
    return (value or "unknown").replace("_", " ").capitalize()


def build_passport(
    *,
    created_at: datetime,
    vision: dict | None,
    ocr: dict | None,
    sensor: dict | None,
    assessment: dict | None,
) -> dict:
    assessment = assessment or {}
    modalities = set(assessment.get("modalities_used") or [])
    freshness = assessment.get("freshness")
    recommendation = assessment.get("recommendation")
    summary = (
        f"{_humanize(freshness)} assessment. Recommendation: "
        f"{_RECOMMENDATIONS.get(recommendation, 'review the evidence')}."
    )

    evidence: list[dict] = []
    conflicts: list[dict] = []
    limitations: list[str] = []
    timeline: list[dict] = [
        {
            "key": "photo",
            "title": "Photo received",
            "state": "complete",
            "detail": "The uploaded image was saved for this scan.",
            "occurred_at": created_at,
        }
    ]

    if vision:
        confidence = vision.get("confidence")
        score = f"{float(confidence) * 100:.0f}%" if confidence is not None else "not available"
        model_type = vision.get("model_type", "prototype")
        visual = vision.get("visual_evidence") or {}
        details = []
        if "dark_pixel_ratio" in visual:
            details.append(f"{visual['dark_pixel_ratio'] * 100:.0f}% dark pixels")
        if "mean_brightness" in visual:
            details.append(f"mean brightness {visual['mean_brightness']:.0f}/255")
        if "brightness_variation" in visual:
            details.append(f"brightness variation {visual['brightness_variation']:.0f}/255")
        if "brown_pixel_ratio" in visual:
            details.append(f"{visual['brown_pixel_ratio'] * 100:.0f}% brown-toned pixels")
        if "green_pixel_ratio" in visual:
            details.append(f"{visual['green_pixel_ratio'] * 100:.0f}% green-toned pixels")
        observation = f"{_humanize(vision.get('freshness'))}; model score {score}."
        if details:
            observation += " Visual cues: " + ", ".join(details) + "."
        explanation = (
            "This is an image-based appearance estimate. Its score is not a calibrated probability."
            if model_type == "prototype"
            else "The trained image classifier produced this uncalibrated score; it is not a food-safety measurement."
        )
        evidence.append({
            "key": "vision",
            "title": "Appearance",
            "state": "used" if "vision" in modalities else "context",
            "observation": observation,
            "explanation": explanation,
        })
        timeline.append({
            "key": "vision",
            "title": "Appearance analyzed",
            "state": "complete",
            "detail": f"{model_type} · {vision.get('model_version', 'version unavailable')}",
            "occurred_at": vision.get("created_at") or created_at,
        })
        limitations.append(
            "A photo cannot confirm microbial safety, smell, or internal spoilage."
        )
        if model_type == "prototype":
            limitations.append(
                "The current appearance model is a color and brightness prototype, not a validated food-safety model."
            )
    else:
        evidence.append({
            "key": "vision",
            "title": "Appearance",
            "state": "missing",
            "observation": "No visual estimate is available.",
            "explanation": "Image evidence did not contribute to this result.",
        })

    expiry_date = (ocr or {}).get("expiry_date")
    if (
        vision
        and vision.get("freshness") == "fresh"
        and expiry_date
        and assessment.get("expiry_status") == "expired"
    ):
        conflicts.append({
            "key": "vision_expiry",
            "title": "Appearance and date disagree",
            "detail": "The image estimate looks fresh, but the detected package date has passed. Verify the label and follow the expiry warning.",
        })
    if expiry_date:
        days = assessment.get("days_remaining")
        expiry_status = assessment.get("expiry_status")
        state = "warning" if expiry_status in {"expired", "expiring_soon"} else "used"
        remaining = f" ({abs(days)} day(s) past date)" if days is not None and days < 0 else (
            f" ({days} day(s) remaining)" if days is not None else ""
        )
        evidence.append({
            "key": "expiry",
            "title": "Expiry label",
            "state": state,
            "observation": f"Detected date: {expiry_date}{remaining}.",
            "explanation": "The printed date was extracted by OCR and used by the expiry rules; verify it on the package.",
        })
        timeline.append({
            "key": "expiry",
            "title": "Expiry label checked",
            "state": "warning" if state == "warning" else "complete",
            "detail": f"OCR detected {expiry_date}.",
            "occurred_at": (ocr or {}).get("created_at") or created_at,
        })
        limitations.append("OCR can misread printed dates; check the package label directly.")
    elif (ocr or {}).get("date_detected") or (ocr or {}).get("raw_text"):
        evidence.append({
            "key": "expiry",
            "title": "Expiry label",
            "state": "context",
            "observation": "Text was found, but no expiry date could be read.",
            "explanation": "OCR text without a parsed date did not affect the expiry rules.",
        })
        timeline.append({
            "key": "expiry",
            "title": "Expiry label checked",
            "state": "complete",
            "detail": "Text was found, but no expiry date could be parsed.",
            "occurred_at": (ocr or {}).get("created_at") or created_at,
        })
        limitations.append("OCR can miss or misread printed dates; check the package label directly.")
    else:
        evidence.append({
            "key": "expiry",
            "title": "Expiry label",
            "state": "missing",
            "observation": "No expiry date was detected.",
            "explanation": "Expiry information did not contribute to this result.",
        })
        timeline.append({
            "key": "expiry",
            "title": "Expiry label checked",
            "state": "missing",
            "detail": "No date was detected in the image.",
            "occurred_at": (ocr or {}).get("created_at") or created_at,
        })

    if sensor and any(sensor.get(key) is not None for key in ("gas_value", "temperature", "humidity")):
        values = []
        if sensor.get("gas_value") is not None:
            values.append(f"VOC {sensor['gas_value']:g}")
        if sensor.get("temperature") is not None:
            values.append(f"{sensor['temperature']:g} °C")
        if sensor.get("humidity") is not None:
            values.append(f"{sensor['humidity']:g}% RH")
        gas_value = sensor.get("gas_value")
        gas_high = gas_value is not None and gas_value >= 700
        if gas_high and vision and vision.get("freshness") == "fresh":
            conflicts.append({
                "key": "vision_sensor",
                "title": "Appearance and VOC reading disagree",
                "detail": "The image estimate looks fresh, while the VOC reading is elevated. The reading is a warning signal, not a safety measurement.",
            })
        state = "warning" if gas_high else ("used" if gas_value is not None else "context")
        explanation = (
            "VOC is at or above the current 700-unit rule threshold."
            if gas_high
            else "VOC, when supplied, is checked against a fixed threshold; temperature and humidity are recorded as context."
        )
        evidence.append({
            "key": "sensor",
            "title": "Sensor readings",
            "state": state if "sensor" in modalities else "context",
            "observation": ", ".join(values) + ".",
            "explanation": explanation,
        })
        timeline.append({
            "key": "sensor",
            "title": "Sensor readings added",
            "state": "warning" if gas_high else "complete",
            "detail": ", ".join(values) + ".",
            "occurred_at": sensor.get("created_at") or created_at,
        })
    else:
        evidence.append({
            "key": "sensor",
            "title": "Sensor readings",
            "state": "missing",
            "observation": "No sensor readings were attached to this scan.",
            "explanation": "Gas, temperature, and humidity did not contribute to this result.",
        })
        timeline.append({
            "key": "sensor",
            "title": "Sensor readings",
            "state": "missing",
            "detail": "No sensor data was submitted.",
            "occurred_at": None,
        })

    warnings = assessment.get("warnings") or []
    if warnings:
        explanation = " ".join(warning.split(": ", 1)[-1] for warning in warnings)
    elif "vision" in modalities:
        explanation = (
            "The result follows the appearance estimate and any expiry or sensor evidence shown below."
        )
    else:
        explanation = "There is not enough measured evidence to make a reliable freshness judgment."
    timeline.append({
        "key": "decision",
        "title": "Recommendation generated",
        "state": "warning" if warnings else "complete",
        "detail": _RECOMMENDATIONS.get(recommendation, "Review the available evidence."),
        "occurred_at": assessment.get("created_at") or created_at,
    })

    return {
        "summary": summary,
        "explanation": explanation,
        "evidence": evidence,
        "timeline": timeline,
        "conflicts": conflicts,
        "limitations": limitations,
    }
