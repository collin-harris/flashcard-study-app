from datetime import date, timedelta


def calculate_sm2(easiness: float, repetitions: int, interval: int, rating: int) -> tuple[float, int, int, date]:
    # Update repetitions
    if rating < 3:
        repetitions = 0 # Failed recall, start over
    else:
        repetitions += 1

    # Update easiness
    new_ef = easiness + (0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02))
    if new_ef < 1.3:
        new_ef = 1.3

    # Recalculate interval
    if repetitions <= 1:
        interval = 1
    elif repetitions == 2: 
        interval = 6
    else:
        interval = round(interval * new_ef)

    # Next review date
    next_review_date = date.today() + timedelta(days=interval)

    return new_ef, repetitions, interval, next_review_date