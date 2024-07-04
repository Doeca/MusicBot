import json


def get_warn_times(user_id: int):
    with open("./config/adbaner/data.json", 'rw') as f:
        data = json.load(f)
        for user in data:
            if user['user_id'] == user_id:
                return user['warn_times']


def set_warn(user_id: int, reason):
    with open("./config/adbaner/data.json", 'rw') as f:
        data = json.load(f)
        for user in data:
            if user['user_id'] == user_id:
                user['warn_times'] += 1
                user['warn_reasons'].append(reason)
                return user['warn_times']
        data.append({"user_id": user_id, "warn_times": 1,
                    "warn_reasons": [reason]})
        json.dump(data, f)


def is_black(user_id: int) -> tuple[bool, str]:
    with open("./config/adbaner/black.json", 'rw') as f:
        black_list = json.load(f)
        for user in black_list:
            if user['user_id'] == user_id:
                return (True, user['reason'])
        return (False, "")
