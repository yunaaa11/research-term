import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent / "src"))

from src.main import run_research


def make_report_path(topic: str) -> Path:
    output_dir = Path("generated_reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_topic = re.sub(r'[\\/:*?"<>|\s]+', "_", topic).strip("_")
    safe_topic = safe_topic[:40] or "research"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return output_dir / f"report_{timestamp}_{safe_topic}.md"


if __name__ == "__main__":
    topic = input("请输入调研课题: ")
    print(f"\n正在为课题 [{topic}] 生成报告，请稍候...\n")

    final_output = run_research(topic)
    report_path = make_report_path(topic)
    with open(report_path, "w", encoding="utf-8") as file:
        file.write(final_output["report"])

    print("\n" + "=" * 30)
    print(f"报告生成完成，文件名: {report_path}")
    print("执行步骤:", " -> ".join(final_output["steps"]))
