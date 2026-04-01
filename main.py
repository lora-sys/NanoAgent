from core.agent_loop import NanoAgent


if __name__ == "__main__":
    agent = NanoAgent()
    result = agent.run("帮我写一个 FastAPI 用户登录模块，要求支持 JWT 和数据库")
    print(result)