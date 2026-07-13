"""
CrewAI Personal Work Assistant
分解 -> 执行 -> 审核 (不达标循环)
"""
import os, sys
from crewai_tools import FileReadTool, ScrapeWebsiteTool
from crewai.flow.flow import Flow, listen, start


class Workflow(Flow):
    model = "gpt-4o"

    @start()
    def decompose(self):
        print("\n" + "=" * 50)
        print("1 分解：拆解任务")
        print("=" * 50)
        from crewai import Agent, Task, Crew

        agent = Agent(
            role="项目经理",
            goal="将任务拆解为3-5个步骤",
            backstory="资深项目管理",
        )
        task = Task(
            description=f"将以下任务拆解为步骤：\n{self.state['task']}",
            agent=agent,
            expected_output="步骤清单",
        )
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        self.state["plan"] = str(result)
        print(f"  计划：{str(result)[:300]}...")

    @listen(decompose)
    def execute(self):
        loop = self.state.get("loop", 1)
        print("\n" + "=" * 50)
        print(f"2 执行 （第{loop}轮）")
        print("=" * 50)
        from crewai import Agent, Task, Crew

        agent = Agent(
            role="执行专员", goal="按计划交付成品",
            backstory="高效执行者",
            tools=[FileReadTool(), ScrapeWebsiteTool()],
        )
        feedback = self.state.get("feedback", "")
        desc = f"任务：{self.state['task']}\n计划：{self.state.get('plan','')}"
        if feedback:
            desc += f"\n\n审核意见（需修）：{feedback}"
        task = Task(description=desc, agent=agent, expected_output="交付物")
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        self.state["draft"] = str(result)
        print(f"  完成：{len(str(result))} 字符")

    @listen(execute)
    def verify(self):
        loop = self.state.get("loop", 1)
        print("\n" + "=" * 50)
        print(f"3 审核 （第{loop}轮）")
        print("=" * 50)
        from crewai import Agent, Task, Crew

        agent = Agent(
            role="质量审核员",
            goal="严格审核，不达标必须打回",
            backstory="苛刻的质检专家",
            tools=[FileReadTool(), ScrapeWebsiteTool()],
        )
        task = Task(
            description=f"审核交付物是否达标。\n需求：{self.state['task']}\n交付物：{self.state['draft']}\n\n达标回复：通过\n不达标回复：不通过+具体意见",
            agent=agent, expected_output="通过/不通过",
        )
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        verdict = str(crew.kickoff()).strip()
        print(f"  结论：{verdict[:200]}")

        self.state["loop"] = loop + 1
        self.state["last_verdict"] = verdict

        if "通过" in verdict:
            print("\n 合格！交付")
            self.state["done"] = True
        elif loop >= 5:
            print("\n 达最大次数，强制交付")
            self.state["done"] = True
        else:
            print("\n 不达标，打回修改")
            self.state["feedback"] = verdict
            self.state["done"] = False

    @listen(verify)
    def check(self):
        if not self.state.get("done", False):
            print("-> 回到执行...")
            return self.execute()


if __name__ == "__main__":
    print("CrewAI 个人工作助手（分解->执行->审核循环）")
    print("=" * 50)
    while True:
        task = input("\n输入任务（q退出）: ").strip()
        if task.lower() == "q":
            break
        if not task:
            continue

        flow = Workflow()
        flow.state["task"] = task
        flow.state["loop"] = 1
        flow.state["feedback"] = ""
        flow.state["done"] = False
        flow.kickoff()

        final = flow.state.get("draft", "")
        print("\n" + "=" * 50)
        print("最终交付物：")
        print("=" * 50)
        print(final[:1000])
        if len(final) > 1000:
            print(f"\n...（共 {len(final)} 字符）")

        safe = "".join(c for c in task[:20] if c.isalnum() or c in " _")
        fname = f"/workspace/work/output_{safe.strip() or 'result'}.md"
        os.makedirs("/workspace/work", exist_ok=True)
        with open(fname, "w", encoding="utf-8") as f:
            f.write(final)
        print(f"\n已保存：{fname}")
