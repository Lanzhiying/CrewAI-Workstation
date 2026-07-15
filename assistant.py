"""
CrewAI Personal Work Assistant — Official Flows Pattern
Analyst -> Reviewer (loop) -> Writer -> Save
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

from typing import Optional
from pydantic import BaseModel
from crewai import Agent, Task, Crew, Process
from crewai.flow.flow import Flow, listen, router, start
from crewai_tools import FileReadTool, ScrapeWebsiteTool

tool_file = FileReadTool()
tool_web = ScrapeWebsiteTool()


# === State ===
class WorkflowState(BaseModel):
    task_desc: str = ""
    file_path: str = ""
    analyst_output: str = ""
    feedback: Optional[str] = None
    valid: bool = False
    retry_count: int = 0
    final_output: str = ""


# === Flow ===
class PersonalWorkFlow(Flow[WorkflowState]):

    model = "deepseek-chat"
    max_tokens = 131072

    @start()
    def analyze(self):
        print("\n=== 1. Analyst: processing task ===")
        analyst = Agent(
            role="Analyst",
            llm={"model": self.model, "max_tokens": self.max_tokens},
            goal="Read files, analyze content, find issues, fix them, output structured data",
            backstory="Analysis Agent. Reads source files, verifies data, fixes issues directly.",
            tools=[tool_file, tool_web],
        )
        task = Task(
            description=self.state.task_desc,
            expected_output="Complete analyzed and supplemented content",
            agent=analyst,
        )
        crew = Crew(agents=[analyst], tasks=[task], process=Process.sequential, verbose=True)
        result = crew.kickoff()
        self.state.analyst_output = str(result.raw if hasattr(result, "raw") else result)
        print(f"Analyst output: {len(self.state.analyst_output)} chars")

    @router(analyze)
    def review(self):
        print("\n=== 2. Reviewer: checking quality ===")
        reviewer = Agent(
            role="Reviewer",
            llm={"model": self.model, "max_tokens": self.max_tokens},
            goal="Check content for completeness, accuracy, format. Return pass/fail with feedback.",
            backstory="QA Agent. Verifies content quality. If issues found, returns specific feedback for fixes.",
            tools=[tool_file],
        )
        review_in = (
            f"Original task: {self.state.task_desc}\n\n"
            f"Content to review:\n{self.state.analyst_output[:5000]}\n\n"
            f"Check if complete and accurate. Return VALID=true and feedback='' if OK. "
            f"Otherwise VALID=false and specify what needs fixing."
        )
        task = Task(
            description=review_in,
            expected_output="VALID=true or VALID=false with feedback",
            agent=reviewer,
        )
        crew = Crew(agents=[reviewer], tasks=[task], process=Process.sequential, verbose=True)
        result = crew.kickoff()
        output = str(result.raw if hasattr(result, "raw") else result)

        self.state.retry_count += 1
        self.state.valid = "valid" in output.lower() and "true" in output.lower()
        self.state.feedback = output
        print(f"Review {self.state.retry_count}: {'PASS' if self.state.valid else 'FAIL'}")

        if self.state.retry_count >= 3:
            return "max_retry"
        if self.state.valid:
            return "write"
        return "retry"

    @listen("retry")
    def retry_analyze(self):
        print(f"\n=== Retry {self.state.retry_count}: fixing issues ===")
        self.state.task_desc += f"\n\nFeedback from reviewer: {self.state.feedback}\nFix the issues above."
        self.analyze()
        return self.review()

    @listen("write")
    def write_final(self):
        print("\n=== 3. Writer: generating final document ===")
        writer = Agent(
            role="Writer",
            llm={"model": self.model, "max_tokens": self.max_tokens},
            goal="Format and polish the final document. Output complete content.",
            backstory="Writer Agent. Takes verified data and produces the polished final document.",
            tools=[tool_file],
        )
        task = Task(
            description=f"Format the following content into a clean, well-structured final document:\n\n{self.state.analyst_output}",
            expected_output="Complete formatted document",
            agent=writer,
        )
        crew = Crew(agents=[writer], tasks=[task], process=Process.sequential, verbose=True)
        result = crew.kickoff()
        self.state.final_output = str(result.raw if hasattr(result, "raw") else result)

    @listen("write")
    def save(self):
        print("\n=== 4. Save to file ===")
        safe = "".join(c for c in self.state.task_desc[:20] if c.isalnum() or c in " _").strip()
        fname = f"/workspace/work/output_{safe or 'result'}.md"
        os.makedirs("/workspace/work", exist_ok=True)
        with open(fname, "w", encoding="utf-8") as f:
            f.write(self.state.final_output)
        print(f"\n✅ Saved: {fname} ({len(self.state.final_output)} chars)")
        print(f"   Preview: {self.state.final_output[:300]}...")

    @listen("max_retry")
    def max_retry_exit(self):
        print(f"\n Max retries ({self.state.retry_count}) exceeded.")
        print(f"Partial output saved with what we have.")
        self.state.final_output = self.state.analyst_output
        self.save()


def main():
    print("CrewAI 工作助手（官方Flows模式：分析→审核循环→写作→保存）")
    print("=" * 55)

    while True:
        task_desc = input("\n输入任务（q退出）: ").strip()
        if task_desc.lower() == "q":
            break
        if not task_desc:
            continue

        flow = PersonalWorkFlow()
        flow.state.task_desc = task_desc
        flow.kickoff()


if __name__ == "__main__":
    main()
