"""Shared structured text for the workbook and the standalone Markdown guide."""

SECTIONS = []


def section(number, name, intro, rows, kind="detail"):
    # Rows: topic, elementary explanation, detailed mechanism, practical implication, sources.
    result = dict(number=number, name=name, sheet=f"{number:02d}_{name}", intro=intro, rows=rows, kind=kind)
    SECTIONS.append(result)
    return result


def row(topic, easy, detail, practical, refs):
    return (topic, easy, detail, practical, refs)

