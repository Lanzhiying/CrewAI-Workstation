"""
CrewAI Personal Work Assistant
Official Process.hierarchical pattern — manager decomposes, assigns, reviews (built-in loop)
"""
import os

os.environ["OPENAI_API_KEY"] = os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
os.environ["OPENAI_BASE_URL"] = "https://api.deepseek.com/v1"
os.environ["OPENAI_MODEL_NAME"] = "deepseek-chat"
os.environ["CREWAI_TOOLS_ALLOW_UNSAFE_PATHS"] = "true"

from dotenv import load_dotenv
load_dotenv("/workspace/.env")
from crewai import Agent, Task, Crew, Process
from crewai_tools import FileReadTool, ScrapeWebsiteTool

tool_file = FileReadTool()
tool_web = ScrapeWebsiteTool()


def main():
    print("CrewAI 个人工作助手（官方 hierarchical 模式）")
    print("=" * 50)

    while True:
        task_desc = input("\n输入任务（q退出）: ").strip()
        if task_desc.lower() == "q":
            break
        if not task_desc:
            continue

        # Workers — manager assigns tasks to them
        analyst = Agent(
            role="Analyst",
            llm={"model": "deepseek-chat", "max_tokens": 8192},
            goal="Analyze data, verify compliance, check completeness",
            backstory="Expert at data analysis and standards compliance checking",
            tools=[tool_file, tool_web],
        )

        writer = Agent(
            role="Writer",
            llm={"model": "deepseek-chat", "max_tokens": 8192},
            goal="Write structured reports with findings and recommendations",
            backstory="Expert technical writer specializing in aviation and engineering reports",
            tools=[tool_file],
        )

        # Manager — decomposes, delegates, reviews (CrewAI built-in)
        manager = Agent(
            role="Project Manager",
            llm={"model": "deepseek-chat", "max_tokens": 8192},
            goal="Decompose tasks into the correct steps: 1) understand what's needed, 2) execute the work, 3) VERIFY the output is correct, 4) if issues found, fix them, 5) deliver final verified result.",
            backstory="You are an experienced PM with strong quality control. "
                      "Your standard workflow is: "
                      "1. READ/UNDERSTAND what the user needs "
                      "2. EXECUTE the work (write, supplement, translate, etc.) "
                      "3. VERIFY the output is correct and complete "
                      "4. If verification finds errors -> send back for FIX, then verify again "
                      "5. Output the FINAL VERIFIED result "
                      "The verification step is CRITICAL and must be a real quality check. "
                      "But verification means: check the OUTPUT for errors and fix them, "
                      "NOT produce a separate review/audit report. "
                      "The user should only see the final correct result, not an intermediate review.",
            allow_delegation=True,
        )

        task = Task(
            description=task_desc,
            expected_output="A complete, structured analysis report with findings, recommendations, and actionable next steps",
        )

        crew = Crew(
            agents=[analyst, writer],
            tasks=[task],
            process=Process.hierarchical,
            manager_agent=manager,
            verbose=True,
        )

        result = crew.kickoff()

        print("\n" + "=" * 50)
        print("FINAL OUTPUT:")
        print("=" * 50)
        print(str(result))

        safe = "".join(c for c in task_desc[:20] if c.isalnum() or c in " _").strip()
        fname = f"/workspace/work/output_{safe or 'result'}.md"
        os.makedirs("/workspace/work", exist_ok=True)
        with open(fname, "w", encoding="utf-8") as f:
            f.write(str(result))
        print(f"\nSaved: {fname}")


if __name__ == "__main__":
    main()
