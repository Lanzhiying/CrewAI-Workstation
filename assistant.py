"""
CrewAI 工作助手 — 显式顺序流程
Manager拆解 → Analyst执行 → Reviewer审核 → Writer输出最终成品
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv("/workspace/.env")
except ImportError:
    pass

os.environ["OPENAI_API_KEY"] = os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
os.environ["OPENAI_BASE_URL"] = "https://api.deepseek.com/v1"
os.environ["OPENAI_MODEL_NAME"] = "deepseek-chat"
os.environ["CREWAI_TOOLS_ALLOW_UNSAFE_PATHS"] = "true"

from crewai import Agent, Task, Crew, Process
from crewai_tools import FileReadTool, ScrapeWebsiteTool

tool_file = FileReadTool()
tool_web = ScrapeWebsiteTool()


def main():
    print("CrewAI 4-Agent 顺序流程")
    print("=" * 50)

    while True:
        task_desc = input("\n输入任务（q退出）: ").strip()
        if task_desc.lower() == "q":
            break
        if not task_desc:
            continue

        # Agents
        manager = Agent(
            role="Manager",
            llm={"model": "deepseek-chat", "max_tokens": 8192},
            goal="Understand the request, decompose into concrete steps, monitor execution, decide rework",
            backstory="You orchestrate the workflow. You assign specific tasks to Analyst, Reviewer, and Writer.",
            allow_delegation=True,
        )

        analyst = Agent(
            role="Analyst",
            llm={"model": "deepseek-chat", "max_tokens": 8192},
            goal="Read files, extract data, analyze, verify consistency, fix issues, output structured data",
            backstory="Analysis Agent. Reads source files, verifies data, finds and fixes issues.",
            tools=[tool_file, tool_web],
        )

        reviewer = Agent(
            role="Reviewer",
            llm={"model": "deepseek-chat", "max_tokens": 8192},
            goal="Check outputs for completeness, accuracy, format. Reject if not up to standard.",
            backstory="QA Agent. Verifies Analyst and Writer outputs. Returns issues or approves.",
            tools=[tool_file],
        )

        writer = Agent(
            role="Writer",
            llm={"model": "deepseek-chat", "max_tokens": 8192},
            goal="Generate the final deliverable from verified data. Output the COMPLETE content, not a summary.",
            backstory="Writer Agent. Takes verified data and produces the final document. "
                      "OUTPUT THE FULL CONTENT, not a description of what was done. "
                      "The user needs to see the actual supplemented/translated/generated document.",
            tools=[tool_file],
        )

        # Tasks
        task_analyze = Task(
            description=f"Task 1 - ANALYZE: {task_desc}\n\nRead the relevant files, analyze what needs to be done, produce the supplemented/updated content.",
            agent=analyst,
            expected_output="Updated content with all changes applied",
        )

        task_review = Task(
            description="Task 2 - REVIEW: Check the Analyst's output for completeness and accuracy. If issues found, specify what needs fixing.",
            agent=reviewer,
            expected_output="Approved content or specific issues to fix",
        )

        task_write = Task(
            description="Task 3 - WRITE: Take the approved content and produce the FINAL COMPLETE deliverable. "
                        "Output the ENTIRE document content, not a summary. The user must see the full result.",
            agent=writer,
            expected_output="Complete final document with full content",
        )

        crew = Crew(
            agents=[analyst, reviewer, writer],
            tasks=[task_analyze, task_review, task_write],
            process=Process.hierarchical,
            manager_agent=manager,
            verbose=True,
        )

        result = crew.kickoff()
        output = str(result)

        safe = "".join(c for c in task_desc[:20] if c.isalnum() or c in " _").strip()
        fname = f"/workspace/work/output_{safe or 'result'}.md"
        os.makedirs("/workspace/work", exist_ok=True)
        with open(fname, "w", encoding="utf-8") as f:
            f.write(output)

        print(f"\n✅ 已保存：{fname}  ({len(output)} 字符)")
        print(f"   预览：{output[:300]}...")
        print(f"   完整内容用 cat {fname} 查看")


if __name__ == "__main__":
    main()
