# FreshSense interface direction

## Product feel

FreshSense should feel like a careful food inspection notebook: practical, evidence-led, and approachable for a student demo. The visual system uses quiet slate surfaces for supporting facts and fresh green for verified or helpful actions. Amber calls attention to incomplete evidence. Avoid claiming that a prototype score is a probability or a safety certification.

## Interface rules

- Preserve the existing light slate and green palette, rounded cards, and clear mobile-first spacing.
- Put the primary scan outcome first; show the product readout and printed-date result as distinct evidence.
- Show what text supported a category and whether the category came from the package or a user label.
- Keep OCR text available for inspection. Make missing OCR setup actionable and never imply an unread date was detected.
- Use visible keyboard focus, semantic headings, status messaging, and readable contrast.
- Explain model limits in plain language near the result instead of hiding them in technical metadata.

## Review checklist

- Check loading, success, missing OCR, and OCR failure states.
- Verify category evidence can be inspected and user-entered labels are not presented as image recognition.
- Verify expiry output names its source label when one was recognized.
- Check the result at a narrow viewport and with keyboard navigation.
