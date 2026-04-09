from core.agent_loop import NanoAgent


if __name__ == "__main__":
    agent = NanoAgent()
    result = agent.run("我要为一个名为‘GreenEnergy’的初创公司写一份商业计划书，帮我写一份可以展示的前端页面")
    print(result)