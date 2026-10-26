# FreshSense UI behavior contract

## Audience and scope

FreshSense is an English-first, mobile-first food package and batch tracker. Personal mode keeps household inventory private to the signed-in account. Seller mode uses a business workspace with owner/manager/staff roles; the API scopes stock and business scans to workspace membership. A staff account must already exist before an owner adds it. The browser's selected workspace is a convenience only; it never grants access by itself.

## Canonical UI map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Select/Listbox | Native HTML `<select>` | This contract | Native | Keyboard and touch in scan and inventory flows |
| Date | Native HTML `input type=date` | This contract | Native | ISO date save and reload in inventory |
| Form | Form-level `reportValidity()` plus workflow checks | This contract and page handlers | Create, edit | Required field and invalid date/quantity paths |
| Scrollbar | Global application stylesheet | `DESIGN.md` and `frontend/src/index.css` | Standard plus WebKit fallback | Narrow/desktop browser render |
| Toast | Shared `ToastProvider` | `frontend/src/components/Toast.tsx` | Success, info, error | Live-region feedback on mutation |
| CRUD | Shared TanStack Query hooks | `frontend/src/api/hooks.ts` and backend API | Save, edit, remove | Inventory and scan integration flow |
| Inventory export | `frontend/src/inventoryCsv.ts` | Inventory source plus active search/filter | CSV download of visible batches | Escaping, formula-safe fields, filtered scope |

## Canonical controls

- Dates use the browser's native `input type=date`. The API exchanges ISO `YYYY-MM-DD` dates; display formatting follows the browser locale.
- Select/Listbox controls use native `<select>` for platform keyboard, touch, and screen-reader behavior.
- Application forms call `reportValidity()` on submit, then apply workflow-specific checks before sending data. Errors remain visible beside the form or in a live notification.
- Notifications use the shared `ToastProvider`; persistent row updates also announce inline status.
- Global focus, selection, accent, scrollbar, and reduced-motion behavior belongs to `frontend/src/index.css`.
- CRUD operations use `frontend/src/api/hooks.ts`; successful mutations invalidate their relevant TanStack Query data, while failed mutations keep the current values for retry.

## Scan and inventory flows

- Sign-in and registration lead into the dashboard. Protected routes send signed-out users to sign-in.
- A scan requires an image and a network connection. Image analysis happens on the server; the UI shows a pending state while OCR and image checks run.
- Package text, recognized category, parsed label date, sensor source, and the model's limitations remain separate evidence. Missing dates are never invented; the user can confirm, enter, or leave a batch undated.
- Saving a scan as a batch requires a product name, quantity from 1 to 9,999, and an explicit date choice. Each purchase/delivery is a separate record.
- Inventory edits save by field. A failure is reported and the user can retry without losing the row's existing data.
- Inventory search and date filters apply immediately. Search is not written to the URL or browser history because pantry and stock product names can be private; a clear-search button resets results and returns keyboard focus to the search field.
- Inventory CSV export includes only the batches currently visible under the selected filter and search. It includes package-date source, quantity, status, storage context, and notes; spreadsheet formula-leading text is neutralized.
- Removing a batch is a destructive action and requires the browser confirmation dialog.
- Offline mode explains that new analysis needs a connection. The PWA may show its cached shell; it does not cache private API results.

## Trust and safety copy

- Prototype model scores are not probabilities or food-safety certifications.
- The Adaptive Review Queue is a transparent, unvalidated organizing heuristic.
- Demo sensor estimates are labeled as examples; VOC is never inferred from a photo.
- OCR output is evidence for the user to check against the printed package.
