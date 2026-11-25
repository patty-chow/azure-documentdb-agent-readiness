import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src import agent

if __name__ == '__main__':
    res = agent.answer_question('C123', 'How is the client positioned for rising interest rates?', top_k=3)
    print('Answer:')
    print(res['answer'])
    print('\nRetrieved:')
    for r in res['retrieved']:
        print(r.get('title'), r.get('score'))
