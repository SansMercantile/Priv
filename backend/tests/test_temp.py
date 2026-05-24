import asyncio
import traceback
import unittest.mock as mock
from backend.multi_agent.multi_agent_system import MultiAgentSystem
from backend.multi_agent.fundamental_agent import FundamentalAgent

async def main():
    system = MultiAgentSystem(mock.Mock())
    # Match registration arguments in test_agents.py
    # FundamentalAgent(multi_agent_system.config, multi_agent_system.api_client, multi_agent_system.database)
    agent_id = "test_fund"
    try:
        agent = FundamentalAgent(
            agent_id=agent_id,
            broker=mock.Mock(),
            config=system.config,
            api_client=system.api_client,
            database=system.database
        )
        print("Instantiated FundamentalAgent successfully.")
    except Exception as e:
        print("Failed to instantiate FundamentalAgent:")
        traceback.print_exc()
        return

    try:
        res = await system.register_agent(agent)
        print("Registration result:", res)
    except Exception as e:
        print("Failed to register FundamentalAgent:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
