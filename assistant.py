"""
CrewAI 4-Agent: Manager + Analyst + Reviewer + Writer
Writer saves to file during generation to bypass API output limits
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

tool_file = FileReadTool()
tool_web = ScrapeWebsiteTool()

@tool("FileSaver")
def save_section(content: str, filename: str = "output.md") -> str:
    """Append content to a file. Use this to save long output during generation.
    Args:
        content: The text content to append
        filename: Target filename (e.g., report.md)
    """
    path = f"/workspace/work/{filename}"
    os.makedirs("/workspace/work", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(content + "\n\n")
    return f"Section saved to {path}"

tool_saver = save_section


def main():
    print("CrewAI 4-Agent（Writer自动分段写入文件，突破输出限制）")
    print("=" * 55)

    last_task = ""
    while True:
        prompt = "\n输入任务（输入c继续上次任务，q退出）: "
        task_desc = input(prompt).strip()
        if task_desc.lower() == "q":
            break
        if task_desc.lower() == "c":
            if last_task:
                import glob
                parts = sorted(glob.glob("/workspace/work/part_*.md"))
                p = len(parts) + 1
                hint = f"\n\n继续第{p}部分。从上次中断处开始，不要重复已有内容。"
                task_desc = last_task + hint
                print(f"  \u2192 继续（第{p}部分）")
            else:
                print("  \u26a0\ufe0f 没有上次任务")
                continue
        if not task_desc:
            continue
        last_task = task_desc

        # Agents
        manager = Agent(
            role="Manager",
            llm={"model": "deepseek-chat", "max_tokens": 32768},
            goal="Understand requirements, decompose tasks, coordinate agents, control workflow, decide rework",
            backstory=("Workflow Manager. Breaks down user requests, assigns work to Analyst/Reviewer/Writer, "
                       "decides if rework is needed. Approves only when quality passes."),
            allow_delegation=True,
        )

        analyst = Agent(
            role="Analyst",
            llm={"model": "deepseek-chat", "max_tokens": 32768},
            goal="Read files, extract data, analyze, verify consistency, fix issues, output structured data",
            backstory="Analysis Agent. Reads source files, verifies data, finds and fixes issues.",
            tools=[tool_file, tool_web],
        )

        reviewer = Agent(
            role="Reviewer",
            llm={"model": "deepseek-chat", "max_tokens": 32768},
            goal="Check outputs for completeness, accuracy, format. Reject if not up to standard.",
            backstory="QA Agent. Verifies Analyst and Writer outputs. Returns issues or approves.",
            tools=[tool_file],
        )

        writer = Agent(
            role="Writer",
            llm={"model": "deepseek-chat", "max_tokens": 32768},
            goal="Generate final document. Use FileSaver to save output to file during generation.",
            backstory=("Writer Agent. You generate the final complete document. "
                       "CRITICAL: Use the FileSaver tool to save each section as you write it. "
                       "Do NOT try to return the full content in your response - the API will truncate it. "
                       "Instead: write section by section using FileSaver, "
                       "and only return a brief confirmation like 'Saved 5 sections to complete_report.md'. "
                       "This way the full document is saved to disk without truncation."),
            tools=[tool_file, tool_saver],
        )

        # Determine output filename
        is_cont = task_desc.startswith("\u7ee7\u7eed") or task_desc.strip() == "c"
        if is_cont:
            import glob
            parts = sorted(glob.glob("/workspace/work/part_*.md"))
            n = len(parts) + 1
            out_file = f"part_{n}.md"
        else:
            safe = "".join(c for c in task_desc[:20] if c.isalnum() or c in " _").strip()
            out_file = f"output_{safe or 'result'}.md"

        task = Task(
            description=task_desc + f"\n\nOutput filename to use with FileSaver: {out_file}",
            agent=writer,
            expected_output="Confirmation of saved file sections",
        )

        crew = Crew(
            agents=[analyst, reviewer, writer],
            tasks=[task],
            process=Process.hierarchical,
            manager_agent=manager,
            verbose=True,
        )

        result = crew.kickoff()

        # Check file size
        path = f"/workspace/work/{out_file}"
        if os.path.exists(path):
            sz = os.path.getsize(path)
            print(f"\n\u2705 {out_file} ({sz} bytes)")
        print(f"\nAgent确认：{str(result)[:200]}...")


if __name__ == "__main__":
    main()
