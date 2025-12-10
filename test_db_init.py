import inspect, importlib
m = importlib.import_module("agent")
Agent = getattr(m, "HealthAgent", None)
if Agent is None:
    print("No HealthAgent in agent.py")
else:
    print("HealthAgent.add_goal signature:", inspect.signature(Agent.add_goal))
    print("HealthAgent.add_goal doc:", Agent.add_goal.__doc__)