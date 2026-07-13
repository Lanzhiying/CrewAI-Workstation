"""
CrewAI Personal Work Assistant
Uses Process.hierarchical — manager decomposes, delegates, reviews (built-in loop)
"""
import os, re

os.environ["OPENAI_API_KEY"] = os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
os.environ["OPENAI_BASE_URL"] = "https://api.deepseek.com/v1"
os.environ["OPENAI_MODEL_NAME"] = "deepseek-chat"

from crewai import Agent, Task, Crew, Process
from crewai_tools import FileReadTool, ScrapeWebsiteTool


def main():
    print("CrewAI 个人工作助手（主管自动分派+审核循环）")
    print("=" * 50)

    while True:
        task = input("n输入任务（q退出）: ").strip()
        if task.lower() == "q":
            break
        if not task:
            continue

        # Auto-inject file content (only for files < 3000 chars to save tokens)
        for fp in re.findall(r'/workspace/work/[^s]+', task):
            if os.path.exists(fp):
                with open(fp, "r", encoding="utf-8") as f:
                    content = f.read()
                if len(content) < 3000:
                    task += f"nn=== File: {fp} ===n{content}"
                else:
                    task += f"nn(File {fp} is {len(content)} chars, use FileReadTool to read)"

        # 主管——拆解任务、分配、审核
        manager = Agent(
            role="项目经理",
            goal="拆解任务、分配给合适的员工、审核成果、不达标则退回修改",
            backstory="你是一个严谨的项目经理，擅长将复杂需求拆解为可执行的步骤。"
                      "你分配任务给员工后，会严格审核成果。如果不达标，你会给出具体修改意见并退回。"
                      "只有完全达标才确认交付。",
            llm="deepseek-chat",
            allow_delegation=True,
        )

        # 员工1——分析/研究
        analyst = Agent(
            role="分析专员",
            goal="根据分配的任务进行数据核查、合规检查、逻辑验证",
            backstory="你擅长数据分析和标准核查，能发现设计中的问题",
            llm="deepseek-chat",
            tools=[FileReadTool(), ScrapeWebsiteTool()],
        )

        # 员工2——写作/报告
        writer = Agent(
            role="报告撰写专员",
            goal="根据分析结果撰写结构化的完整报告",
            backstory="你擅长将分析结果转化为清晰、结构化的文字报告",
            llm="deepseek-chat",
            tools=[FileReadTool()],
        )

        crew = Crew(
            agents=[manager, analyst, writer],
            tasks=[
                Task(
                    description=task,
                    expected_output="完整的分析报告",
                )
            ],
            process=Process.hierarchical,
            manager_agent=manager,
            verbose=True,
        )

        result = crew.kickoff()
        print("n" + "=" * 50)
        print("最终交付物：")
        print("=" * 50)
        print(str(result))

        safe = "".join(c for c in task[:20] if c.isalnum() or c in " _").strip()
        fname = f"/workspace/work/output_{safe or 'result'}.md"
        os.makedirs("/workspace/work", exist_ok=True)
        with open(fname, "w", encoding="utf-8") as f:
            f.write(str(result))
        print(f"n已保存：{fname}")


if __name__ == "__main__":
    main()
