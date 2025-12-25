import database
import agent
import json

database.init_db()
agent.init_agent()
res = agent.get_agent().process_message('Show interviews')
print('AGENT RESULT:', json.dumps(res, indent=2, default=str))
print('DB:', database.get_all_interviews())
