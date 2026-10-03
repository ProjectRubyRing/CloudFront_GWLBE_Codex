"""Open only the generated workbook in an isolated, invisible Excel instance."""

import json
from pathlib import Path

import pythoncom
import win32com.client

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "validation"
VALIDATION.mkdir(exist_ok=True)
books = list((ROOT / "output").glob("*.xlsx"))
assert len(books) == 1
pdf = VALIDATION / "excel_render.pdf"
app = book = None
pythoncom.CoInitialize()
try:
    # DispatchEx starts our own Excel application; it does not attach to user workbooks.
    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    app.EnableEvents = False
    app.AskToUpdateLinks = False
    app.AutomationSecurity = 3
    book = app.Workbooks.Open(str(books[0]), 0, False)
    assert not book.ReadOnly, "Generated workbook was opened read-only"
    book.Styles.Item(1).Font.Name = "Meiryo UI"
    fitted = []
    for index in range(1, book.Worksheets.Count + 1):
        sheet = book.Worksheets.Item(index)
        sheet.UsedRange.Font.Name = "Meiryo UI"
        if not sheet.Name.startswith("02_"):
            last = sheet.AutoFilter.Range.Row + sheet.AutoFilter.Range.Rows.Count - 1
            sheet.Range(f"A7:F{last}").Rows.AutoFit()
            for r in range(7, last + 1):
                row = sheet.Rows.Item(r)
                row.RowHeight = min(409.5, max(42, float(row.RowHeight) + 5))
                del row
        fitted.append({"name": sheet.Name, "rows": sheet.UsedRange.Rows.Count, "columns": sheet.UsedRange.Columns.Count})
        del sheet
    book.Worksheets.Item(1).Activate()
    book.Save()
    book.ExportAsFixedFormat(0, str(pdf))
    result = {
        "status": "PASS", "excel_version": app.Version,
        "native_open_save": True, "autofit": "Microsoft Excel AutoFit + 5 pt padding, minimum 42 pt",
        "exported_pdf": str(pdf), "sheets": fitted,
        "live_aws_tests": "Not run", "powershell_attempt": "PS1 launch denied by execution policy; policy was not changed",
    }
    (VALIDATION / "excel_validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "excel_version": app.Version, "sheets": len(fitted), "native_open_save": True, "pdf_export": True}))
finally:
    if book is not None:
        book.Close(False)
        del book
    if app is not None:
        app.Quit()
        del app
    pythoncom.CoUninitialize()
