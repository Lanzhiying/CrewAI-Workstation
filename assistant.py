"""
CrewAI Personal Work Assistant
Usage: python assistant.py
"""
import os, sys
from crewai import Agent, Task, Crew


def run():
    task_desc = input("\n输入任务: ").strip()
    if not task_desc:
        return

    # Agent 1: Project Manager
    manager = Agent(
        role="项目经理",
        goal="将复杂任务拆解成清晰的步骤，分配执行，审核结果",
        backstory="你是一个经验丰富的项目经理，擅长将模糊的需求转化为可执行的计划",
        allow_delegation=True,
    )

    # Agent 2: Executor
    executor = Agent(
        role="执行专员",
        goal="根据计划逐步骤执行，交付完整可用的成果",
        backstory="你是一个高效的执行者，能够按要求完成各类文档、分析和写作任务",
    )

    # Agent 3: Reviewer
    reviewer = Agent(
        role="质量审核员",
        goal="审核交付物是否达标，不达标则反馈修改意见",
        backstory="你是一个严格的质量审核员，对细节极其挑剔",
    )

    # Tasks
    decompose = Task(
        description=f"将以下任务拆解为3-5个可执行的步骤：\n{task_desc}\n\n输出步骤清单和交付格式要求",
        agent=manager,
        expected_output="步骤清单和交付要求",
    )

    execute_task = Task(
        description=f"根据计划执行以下任务，输出完整的交付物：\n{task_desc}",
        agent=executor,
        expected_output="完整的交付文档",
    )

    review_task = Task(
        description=f"审核交付物是否满足以下标准：1)完整性 2)准确性 3)可直接使用\n\n如果达标则确认，不达标则给出具体的修改意见",
        agent=reviewer,
        expected_output="审核结论（通过/需修改）及修改意见",
    )

    crew = Crew(
        agents=[manager, executor, reviewer],
        tasks=[decompose, execute_task, review_task],
        verbose=True,
    )

    result = crew.kickoff()
    print("\n" + "=" * 50)
    print("最终交付物：")
    print("=" * 50)
    print(result)

    safe = "".join(c for c in task_desc[:20] if c.isalnum() or c in " _")
    with open(f"work/output_{safe.strip() or 'result'}.md", "w", encoding="utf-8") as f:
        f.write(str(result))
    print(f"\n已保存至 work/output_{safe.strip() or 'result'}.md")


if __name__ == "__main__":
    print("CrewAI 个人工作助手")
    print("=" * 30)
    while True:
        run()
        c = input("\n继续? (Enter=继续, q=退出): ").strip()
        if c.lower() == "q":
            break
