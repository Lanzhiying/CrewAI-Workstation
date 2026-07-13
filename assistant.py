"""
CrewAI Workflow: decompose -> execute -> verify (loop)
Simple sequential Crew without Flow API to avoid encoding issues.
"""
import os
from crewai import Agent, Task, Crew, Process

api_key = os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
os.environ["OPENAI_API_KEY"] = api_key
os.environ["OPENAI_BASE_URL"] = "https://api.deepseek.com/v1"
os.environ["OPENAI_MODEL_NAME"] = "deepseek-chat"


def run_once(task_text, plan=None, feedback=""):
    """Run one complete cycle: decompose (if no plan) -> execute -> verify"""

    if not plan:
        print("n=== 1. Decompose ===")
        manager = Agent(role="project manager", goal="decompose task into steps", backstory="PM")
        t1 = Task(description=f"Decompose into steps: {task_text}", agent=manager, expected_output="steps")
        c1 = Crew(agents=[manager], tasks=[t1], verbose=False)
        plan = str(c1.kickoff())
        print(f"  Plan: {plan[:200]}...")

    print(f"n=== 2. Execute ===")
    # Auto-read files mentioned in task
    import re
    file_refs = re.findall(r'/workspace/work/[^s]+', task_text)
    injected = task_text
    for fp in file_refs:
        if os.path.exists(fp):
            with open(fp, 'r', encoding='utf-8') as fh:
                content = fh.read()
            injected += f"nn=== File: {fp} ===n{content}"

    desc = f"Task: {injected}nPlan: {plan}"
    if feedback:
        desc += f"nFeedback to address: {feedback}"
    execu = Agent(role="Executor", goal="produce output", backstory="doer", llm="deepseek-chat", verbose=False)
    t2 = Task(description=desc, agent=execu, expected_output="deliverable")
    c2 = Crew(agents=[execu], tasks=[t2], verbose=False)
    draft = str(c2.kickoff())
    print(f"  Done: {len(draft)} chars")

    print(f"n=== 3. Verify ===")
    veri = Agent(role="Reviewer", goal="check quality", backstory="QC expert", llm="deepseek-chat", verbose=False)
    t3 = Task(
        description=f"Review if this output meets requirements.nTask: {task_text}nOutput: {draft}nReply PASS or FAIL + reasons.",
        agent=veri,
        expected_output="PASS or FAIL",
    )
    c3 = Crew(agents=[veri], tasks=[t3], verbose=False)
    verdict = str(c3.kickoff()).strip()
    print(f"  Verdict: {verdict[:200]}")

    return draft, plan, verdict


def main():
    print("CrewAI Assistant (decompose -> execute -> verify loop)")
    print("=" * 40)

    while True:
        task = input("nTask (q to quit): ").strip()
        if task.lower() == "q":
            break
        if not task:
            continue

        plan = None
        final = ""
        for i in range(1, 6):
            print(f"n--- Round {i} ---")
            draft, plan, verdict = run_once(task, plan, "" if i == 1 else verdict)
            final = draft

            if "PASS" in verdict.upper() or i >= 5:
                print("n" + "=" * 40)
                print("FINAL OUTPUT:")
                print("=" * 40)
                print(final[:1000])
                if len(final) > 1000:
                    print(f"... ({len(final)} total chars)")

                safe = "".join(c for c in task[:20] if c.isalnum() or c in " _").strip()
                fname = f"/workspace/work/output_{safe or 'result'}.txt"
                os.makedirs("/workspace/work", exist_ok=True)
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(final)
                print(f"nSaved: {fname}")
                break

            print("nFAIL -> revising...")


if __name__ == "__main__":
    main()
