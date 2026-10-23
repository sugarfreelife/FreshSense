# FreshSense showcase demo

## Demo flow

1. Start FreshSense on the computer with `start-dev.cmd`; use `start-phone.cmd` when a phone on the same Wi-Fi should open it.
2. Sign in with the local demo account `demo@example.com` / `FreshSenseDemo2026!`.
3. Open **Scan a purchase**. For a packaged item, frame both its product name and the printed date; tap to focus, avoid glare, and retake a blurry photo.
4. Review the package text, category evidence, OCR result, model limits, and Freshness Passport. Do not present a prototype score as a probability or safety certification.
5. Add the purchase to Pantry. Enter the quantity, correct the category if needed, and confirm the date or enter it from the label.
6. Set the storage location, opened date, storage notes, and optional reminder window on the batch.
7. Show the batch-level date watch and use-next cue. Explain that it sorts recorded package dates and is an organizing aid.

The local demo accounts are seeded without fake scan results or pantry dates. Use a real package photo or a clearly identified sample image during a presentation.

## Phone smoke-check

- Connect the phone and PC to the same trusted Wi-Fi network.
- Start with `start-phone.cmd` on the PC and open the exact phone URL printed in its terminal; the launcher chooses and reports a free port.
- Sign in, grant camera access, capture a package, retake it, submit it, and confirm the result page loads.
- Verify date entry, quantity save, storage details, reminder preference, and navigation in portrait and landscape.
- Local browser notifications require permission and FreshSense to remain open. They are not delivered while the browser/app is closed.
- If the PC firewall blocks the phone connection, allow the development server on the private network only.

## Evaluation protocol

Collect package photos with permission, write down the exact package category and printed date, and assign every item/batch to one `group_id`. Keep a group's photos entirely in either train or validation. Do not add personal details, faces, or private account labels.

Use `data/metadata/package_label_template.csv` as a local manifest. Keep photos and completed manifests out of Git. Run end-to-end package recognition evaluation from the repository root:

```powershell
python backend/scripts/evaluate_package_labels.py data/metadata/package_labels.csv --output data/reports/package_labels.json
```

The report measures exact category matches and expiry-date reads on validation images, lists OCR engines used, and refuses groups split across training and validation. It does not invent missing values, and results should be reported with the image and group counts. Use the paired sensor/expiry collection and fusion evaluation protocol in `data/README.md` for any multimodal comparison.
