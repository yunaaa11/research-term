import sys
import os

# 将 src 目录加入环境路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.main import run_research
if __name__=="__main__":
    topic=input("请输入调研课题：")
    print(f"\n正在为课题[{topic}]生成报告，请稍后...\n")
    final_output=run_research(topic)
    #保存结果
    with open("final_report.md","w",encoding="utf-8") as f:
        f.write(final_output['report'])
    
    print("\n"+"="*30)
    print("报告生成成功！文件名：final_report.md")
    print("执行步骤：","->".join(final_output['steps']))