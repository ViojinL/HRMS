from pathlib import Path
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet
from typing import cast

wb = openpyxl.Workbook()
ws = cast(Worksheet, wb.active or wb.create_sheet(title="员工导入测试"))
ws.title = "员工导入测试"
headers = [
    "姓名",
    "工号",
    "身份证号",
    "出生日期",
    "手机号",
    "邮箱",
    "部门编码",
    "岗位",
    "入职日期",
    "性别(male/female)",
]
ws.append(headers)

# 使用未占用的工号，避免与已有账号冲突
ws.append(
    [
        "测试员工A",
        "emp1010",
        "110101198801011111",
        "1988-01-01",
        "13800001111",
        "emp1010@test.com",
        "HR",
        "测试岗",
        "2025-01-01",
        "male",
    ]
)
ws.append(
    [
        "测试员工B",
        "emp1011",
        "110101198901011112",
        "1989-01-01",
        "13800002222",
        "emp1011@test.com",
        "TECH",
        "开发",
        "2025-02-01",
        "female",
    ]
)
output_dir = Path("hrms/docs")
output_dir.mkdir(parents=True, exist_ok=True)
wb.save(output_dir / "employee_bulk_test.xlsx")
print("template saved to", output_dir / "employee_bulk_test.xlsx")
