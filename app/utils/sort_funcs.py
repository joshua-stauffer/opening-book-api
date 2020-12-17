from datetime import datetime

def average_descendent_easiness(move):
    """Get the average easiness of children of move object
    args:
    move -- Move class object
    """
    # if no children, prefer lines with continuations while also
    # preventing division by zero by returning arbitrary number > 5
    if not move.children:
        return 10
    return sum(m.easiness for m in move.children if m.easiness != None) \
                / len(move.children)

def sort_by_date(move):
    """Returns move.next_review, unless None, then returns datetime.now()"""
    if not move.next_review:
        return datetime.now()
    return move.next_review