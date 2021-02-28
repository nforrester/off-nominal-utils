#!/usr/bin/python

# Display a user's prediction and voting history and total score.

import sys
import requests
import datetime
import math

# Take username as an argument on the command line. If the username has spaces, you need to use quotes.
username = sys.argv[1]

# API REFERENCE
# https://deltayeet.net/ndb?leaderboard
# https://deltayeet.net/ndb?standing
# https://deltayeet.net/ndb?retired
# https://deltayeet.net/ndb?endorsements
# https://deltayeet.net/ndb?undorsements
# https://deltayeet.net/ndb/?votes
# https://deltayeet.net/ndb/?judged
# https://deltayeet.net/ndb/?prediction=401
# https://deltayeet.net/ndb/?endorsements=Thunderscreech
# https://deltayeet.net/ndb/?undorsements=Thunderscreech
# https://deltayeet.net/ndb/?votes=401
# https://deltayeet.net/ndb/?leaderboard=Thunderscreech
# https://deltayeet.net/ndb/?prediction=407

def ndb(question, arg=None):
    """
    Ask NDB API a question
    ndb('votes', '401') becomes https://deltayeet.net/ndb/?votes=401
    """
    query = 'https://deltayeet.net/ndb/?' + question
    if arg is not None:
        query += '=' + arg
    result = requests.get(query).json()
    return result

# Assemble a dict of all predictions by taking the union of standing, retired, and judged.
all_predictions = dict()
all_predictions.update(ndb('standing'))
all_predictions.update(ndb('retired'))
all_predictions.update(ndb('judged'))

# Get dicts of the user's endorsements and undorsements.
endorsements = ndb('endorsements', username)
undorsements = ndb('undorsements', username)

# Get the vote list.
votes = ndb('votes')

# Assemble dicts of the predictions the user made, endorsed, and undorsed.
predicted = {key: value for key, value in all_predictions.items() if value['user'] == username}
endorsed = {dorse['prediction_id']: all_predictions[dorse['prediction_id']] for dorse in endorsements.values() if int(dorse['prediction_id']) >= 50}
undorsed = {dorse['prediction_id']: all_predictions[dorse['prediction_id']] for dorse in undorsements.values() if int(dorse['prediction_id']) >= 50}

def bucket_predictions(predictions):
    """
    Given a dict of predictions, return the judged and standing ones in separate dicts.
    """
    for p in predictions.values():
        assert (p['type'] == 'judged') == (p['judged'] == '1')
    judged = {k: v for k, v in predictions.items() if v['type'] == 'judged'}
    standing = {k: v for k, v in predictions.items() if v['type'] == 'standing'}
    return judged, standing

def point_value(key, prediction):
    """
    Calculate how many day_points each prediction is worth to the user who made it.
    This only works on judged predictions.
    """
    assert(prediction['type'] == 'judged')
    v = votes[key]
    prescient = int(v['thumbs_up']) >= int(v['thumbs_down'])
    start = datetime.datetime.fromisoformat(prediction['date'])
    end = datetime.datetime.fromisoformat(prediction['due'])
    days = abs((end.date() - start.date()).days)
    if prescient:
        return days
    return -days

def print_and_score(predictions, invert_scores):
    """
    Display a group of predictions and return the total score resulting from them.
    If these are predictions the user undorsed, pass invert_scores=True,
    because the user is getting negative points relative to the predictor.
    """
    def score(key, prediction):
        """
        Return the point_value of the prediction either inverted or not, as appropriate.
        """
        if invert_scores:
            return -point_value(key, prediction)
        return point_value(key, prediction)

    # Separate predictions into judged and standing.
    judged, standing = bucket_predictions(predictions)

    # Print out judged predictions and how many points the user got from them.
    by_score = sorted(list(judged.items()), key=lambda x: score(*x))
    for key, prediction in by_score:
        print(score(key, prediction), 'POINTS: ', prediction['text'])

    # Print out predictions that have not been judged yet.
    by_due = sorted(list(standing.items()), key=lambda item: item[1]['due'])
    for key, prediction in by_due:
        print('FUTURE: ', prediction['text'])

    # Return the user's score from this group of predictions.
    return sum(map(lambda x: score(*x), judged.items()))

# Display the user's history and total score.
total_score = 0
print(username, 'PREDICTED:')
total_score += print_and_score(predicted, False)
print('')
print('')
print('')
print(username, 'ENDORSED:')
total_score += print_and_score(endorsed, False)
print('')
print('')
print('')
print(username, 'UNDORSED:')
total_score += print_and_score(undorsed, True)
print('')
print('')
print('')
print(username, 'COMPUTED SCORE:', total_score)
print(username, 'OFFICIAL SCORE:', ndb('leaderboard', username)[username]['day_points'])
