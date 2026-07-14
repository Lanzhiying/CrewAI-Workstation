"""
CrewAI Personal Work Assistant
4-Agent: Manager -> Analyst -> Reviewer -> Writer (with loop)
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
from crewai.tools import tool

@tool("FileWriteTool")
def write_to_file(content: str, filepath: str) -> str:
    """Write content to a file. Use this to save long output directly instead of returning it in chat.
    Args:
        content: The full content to write
        filepath: Path to save the file (e.g., /workspace/work/output.md)
    """
    import os
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return f"File saved to {filepath}"

tool_write = write_to_file

tool_file = FileReadTool()
tool_web = ScrapeWebsiteTool()


def main():
    print("CrewAI 工作助手（4 Agent：拆解→分析→审核→输出）")
    print("=" * 50)

    while True:
        task_desc = input("\n输入任务（q退出）: ").strip()
        if task_desc.lower() == "q":
            break
        if not task_desc:
            continue

        # 1. Manager — 理解需求、拆解任务、调度、判断是否返工
        manager = Agent(
            role="Manager",
            llm={"model": "deepseek-chat", "max_tokens": 8192},
            goal="Understand requirements, decompose tasks, coordinate agents, control workflow, decide rework",
            backstory="You are a Workflow Manager. You break down the user's request into steps. "
                      "You assign work to Analyst, Reviewer, and Writer in the correct order. "
                      "After Review, if issues are found, you send the task back for fixing. "
                      "You only approve the final output when it passes all quality checks.",
            allow_delegation=True,
        )

        # 2. Analyst — 读文件、提取数据、分析、校验、修正、输出结构化数据
        analyst = Agent(
            role="Analyst",
            llm={"model": "deepseek-chat", "max_tokens": 8192},
            goal="Read files, extract data, analyze content, verify consistency, fix issues, output structured data",
            backstory="You are an Analysis Agent. You read source files using FileReadTool, "
                      "extract relevant data, analyze the content carefully, "
                      "verify data consistency and accuracy, "
                      "and directly FIX any issues you find. "
                      "You output clean, structured data for the next step.",
            tools=[tool_file, tool_web],
        )

        # 3. Reviewer — 检查 Analyst 和 Writer 的输出，验证完整性/准确性/格式，不通过则退回
        reviewer = Agent(
            role="Reviewer",
            llm={"model": "deepseek-chat", "max_tokens": 8192},
            goal="Check Analyst and Writer outputs for completeness, accuracy, and format compliance. Reject if not up to standard.",
            backstory="You are a Quality Assurance Agent. You carefully review the outputs of Analyst and Writer. "
                      "You check: completeness (nothing missing), accuracy (facts correct), "
                      "format compliance (matches requirements). "
                      "If the output passes all checks, you approve it. "
                      "If not, you clearly state what needs to be fixed and reject it.",
            tools=[tool_file],
        )

        # 4. Writer — 根据已验证的数据生成最终文档，优化表达与排版，输出可直接交付的成果
        writer = Agent(
            role="Writer",
            llm={"model": "deepseek-chat", "max_tokens": 8192},
            goal="Generate final documents from verified data, optimize expression and formatting, output deliverable-ready results",
            backstory="You are a Content Generation Agent. You take verified, reviewed data "
                      "and transform it into polished, well-formatted final documents. "
                      "You ensure the output is complete, readable, and ready for delivery. "
                      "You do NOT introduce new content — you format and polish what has been verified. IMPORTANT: After generating the content, use the FileWriteTool to save it directly to a file. Then return a brief summary of what was saved.",
            tools=[tool_file, tool_write],
        )

        task = Task(
            description=task_desc,
            expected_output="A complete, accurate, well-formatted deliverable that meets all requirements",
        )

        crew = Crew(
            agents=[analyst, reviewer, writer],
            tasks=[task],
            process=Process.hierarchical,
            manager_agent=manager,
            verbose=True,
        )

        result = crew.kickoff()

        print("\n" + "=" * 50)
        print("最终交付物：")
        print("=" * 50)
        print(str(result))

        safe = "".join(c for c in task_desc[:20] if c.isalnum() or c in " _").strip()
        fname = f"/workspace/work/output_{safe or 'result'}.md"
        os.makedirs("/workspace/work", exist_ok=True)
        with open(fname, "w", encoding="utf-8") as f:
            f.write(str(result))
        print(f"\n已保存：{fname}")


if __name__ == "__main__":
    main()
