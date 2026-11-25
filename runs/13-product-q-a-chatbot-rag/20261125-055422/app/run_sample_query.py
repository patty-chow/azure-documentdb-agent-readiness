from db import get_db
import app

def run():
    db = get_db()
    q = 'What is the battery life of the smartwatch?'
    retrieved = app.retrieve_top_k(db, q, top_k=5)
    print('Retrieved:')
    for item, score in retrieved:
        print(item.get('chunk_id'), 'score=', score)

if __name__ == '__main__':
    run()
