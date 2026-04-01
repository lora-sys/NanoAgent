from core.agent_loop import NanoAgent


if __name__ == "__main__":
    agent = NanoAgent()
    result = agent.run("我要为一个名为‘GreenEnergy’的初创公司写一份商业计划书，并顺便帮我写一个展示页面的 HTML 原型。")
    print(result)