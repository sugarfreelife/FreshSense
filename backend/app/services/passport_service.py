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


def _next_evidence_action(
    *,
    vision: dict | None,
    ocr: dict | None,
    sensor: dict | None,
    product: dict | None,
    conflicts: list[dict],
) -> dict:
    """Choose one transparent follow-up based on this scan's evidence gaps."""
    if conflicts:
        return {
            "key": "resolve_conflict",
            "title": "Check the signals that disagree",
            "detail": "Verify the printed date and repeat any available measurement. Keep both observations visible; this prototype does not average conflicting evidence into a safety verdict.",
            "action_label": "Add a follow-up scan",
            "target": "scan",
        }

    if not (ocr or {}).get("expiry_date"):
        partial = (ocr or {}).get("expiry_text")
        detail = (
            f"The package stamp was only partly read ({partial}). Check the label and enter the full date, or track the batch without a date."
            if partial
            else "No complete package date was confirmed. Check the printed label and enter the date, or choose to track this batch without one."
        )
        return {
            "key": "confirm_date",
            "title": "Confirm the package date",
            "detail": detail,
            "action_label": "Review date in pantry form",
            "target": "pantry",
        }

    if not (product or {}).get("category"):
        return {
            "key": "identify_product",
            "title": "Identify this product",
            "detail": "The package text did not give a supported category. Add the product name and category so future scans can stay with the right item.",
            "action_label": "Add product details",
            "target": "pantry",
        }

    sensor_source = (sensor or {}).get("source", "legacy")
    if sensor_source in {"demo_estimate", "mixed"}:
        return {
            "key": "replace_demo_values",
            "title": "Review estimated environment values",
            "detail": "Illustrative temperature, humidity, or VOC values are not measurements. Replace them with readings from a calibrated sensor or clear them before comparing scans.",
            "action_label": "Review scan inputs",
            "target": "scan",
        }

    if (vision or {}).get("model_type", "prototype") == "prototype":
        return {
            "key": "repeat_observation",
            "title": "Build a same-item history",
            "detail": "The appearance model is a prototype. A later photo of this same item can add a time-stamped observation, but it will not validate food safety.",
            "action_label": "Add a follow-up scan",
            "target": "scan",
        }

    return {
        "key": "review_result",
        "title": "Review the recorded evidence",
        "detail": "The scan has a complete package date and product category. Keep the label and any future observations with this batch for traceability.",
        "action_label": "Review pantry entry",
        "target": "pantry",
    }


def build_passport(
    *,
    created_at: datetime,
    vision: dict | None,
    ocr: dict | None,
    sensor: dict | None,
    assessment: dict | None,
    product: dict | None = None,
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

    product = product or {}
    category = product.get("category")
    product_name = product.get("product_name")
    product_source = product.get("source", "unrecognized")
    if category:
        product_state = "used" if product_source == "package_text" else "context"
        if product_source == "package_text":
            matched = ", ".join(product.get("evidence") or [])
            observation = f"Package text suggests {category}" + (f" ({matched})" if matched else "") + "."
            explanation = "The category was matched from text read on the package; it is a label-based estimate."
        else:
            observation = f"{product_name or category} was entered as the food label."
            explanation = "This category came from the user label, not automatic image recognition."
    elif (ocr or {}).get("raw_text"):
        product_state = "context"
        observation = "Package text was found, but it did not identify a supported food category."
        explanation = "The printed text is retained below so the category match can be checked."
    else:
        product_state = "missing"
        observation = "No product category could be identified from visible package text."
        explanation = "A clear photo of the product name or front label helps identify packaged items."
    evidence.append({
        "key": "product",
        "title": "Product category",
        "state": product_state,
        "observation": observation,
        "explanation": explanation,
    })
    timeline.append({
        "key": "product",
        "title": "Product category checked",
        "state": "complete" if category else "missing",
        "detail": (
            f"{category} matched from package text."
            if product_source == "package_text" and category
            else f"{category} supplied as the user label."
            if category
            else observation
        ),
        "occurred_at": (ocr or {}).get("created_at") or created_at,
    })
    if (ocr or {}).get("provider") in {"unavailable", "tesseract_unavailable", "legacy"}:
        limitations.append("Automatic package-text reading is unavailable until an OCR engine is installed.")

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
            "detail": f"{(ocr or {}).get('provider', 'OCR')} read {expiry_date}.",
            "occurred_at": (ocr or {}).get("created_at") or created_at,
        })
        limitations.append("OCR can misread printed dates; check the package label directly.")
    elif (ocr or {}).get("date_detected") or (ocr or {}).get("raw_text"):
        partial_stamp = (ocr or {}).get("expiry_text")
        label = (ocr or {}).get("expiry_label")
        evidence.append({
            "key": "expiry",
            "title": "Expiry label",
            "state": "context",
            "observation": (
                f"Partial stamp read: {partial_stamp} after {label or 'an expiry label'}; the year was not read."
                if partial_stamp
                else "Text was found, but no expiry date could be read."
            ),
            "explanation": (
                "The partial date was kept as evidence but not used to calculate expiry because it has no year."
                if partial_stamp
                else "OCR text without a parsed date did not affect the expiry rules."
            ),
        })
        timeline.append({
            "key": "expiry",
            "title": "Expiry label checked",
            "state": "complete",
            "detail": (
                f"{(ocr or {}).get('provider', 'OCR')} read {(ocr or {}).get('expiry_text')} without a year."
                if (ocr or {}).get("expiry_text")
                else f"{(ocr or {}).get('provider', 'OCR')} found text, but no expiry date could be parsed."
            ),
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
        sensor_source = sensor.get("source", "user_entered")
        demo_estimate = sensor_source in {"demo_estimate", "mixed"}
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
        if sensor_source == "demo_estimate":
            explanation = "These are illustrative demo values, not measurements from a physical sensor. VOC cannot be inferred from an image. Replace or clear them before treating the result as measured evidence."
        elif sensor_source == "mixed":
            explanation = "This row combines user-entered values with auto-filled demo estimates; it is not a complete physical sensor measurement. Review each value."
        elif sensor_source == "legacy":
            explanation = "This older scan does not record where these values came from. Treat them as context, not verified sensor measurements."
        evidence.append({
            "key": "sensor",
            "title": "Sensor readings",
            "state": "context" if demo_estimate or sensor_source == "legacy" else (state if "sensor" in modalities else "context"),
            "observation": ("Demo estimates: " if sensor_source == "demo_estimate" else "Mixed demo and entered values: " if sensor_source == "mixed" else "") + ", ".join(values) + ".",
            "explanation": explanation,
        })
        timeline.append({
            "key": "sensor",
            "title": "Demo context added" if demo_estimate else "Environment context saved" if sensor_source == "legacy" else "Sensor readings added",
            "state": "complete" if demo_estimate else ("warning" if gas_high else "complete"),
            "detail": ("Illustrative values, not measured: " if sensor_source == "demo_estimate" else "Contains illustrative values: " if sensor_source == "mixed" else "Source not recorded: " if sensor_source == "legacy" else "") + ", ".join(values) + ".",
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

    next_action = _next_evidence_action(
        vision=vision,
        ocr=ocr,
        sensor=sensor,
        product=product,
        conflicts=conflicts,
    )

    return {
        "summary": summary,
        "explanation": explanation,
        "evidence": evidence,
        "timeline": timeline,
        "conflicts": conflicts,
        "limitations": limitations,
        "next_action": next_action,
    }
