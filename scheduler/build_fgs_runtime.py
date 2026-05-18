from pathlib import Path
from openpyxl import load_workbook


def load_groups_from_excel(excel_path: str) -> list[str]:
    wb = load_workbook(excel_path, data_only=True)
    ws = wb["МАХ"]

    groups = []

    # В файле группы начинаются с 4 строки
    for row in ws.iter_rows(min_row=4, values_only=True):
        group = row[0]

        if not group:
            continue

        group = str(group).strip()

        if group.endswith(".0"):
            group = group[:-2]

        groups.append(group)

    return groups


def build_fgs_from_jsons(
    excel_path: str,
    json_dir: str
) -> dict[str, str]:

    groups = load_groups_from_excel(excel_path)
    json_files = list(Path(json_dir).glob("*.json"))

    fgs = {}

    for group in groups:
        fgs[group] = "8101,8102"

        for file_path in json_files:
            filename = file_path.stem

            # если группа упоминается в названии файла
            if group in filename:
                fgs[group] = filename
                break

    return fgs