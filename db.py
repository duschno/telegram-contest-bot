import os
import psycopg2
import datetime
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager


DATABASE_URL = os.environ['DATABASE_URL']
connectionpool = SimpleConnectionPool(1, 18, dsn=DATABASE_URL, sslmode='require')


@contextmanager
def getcursor():
    con = connectionpool.getconn()
    try:
        yield con.cursor()
        con.commit()
    except psycopg2.Error as e:
        print('getcursor error: {}'.format(e))
    finally:
        connectionpool.putconn(con)


def get_game_status():
    try:
        with getcursor() as cur:
            cur.execute("""SELECT isgoing
                           FROM status
                           WHERE id = 1""")
            isgoing = cur.fetchall()
    except psycopg2.Error as e:
        print('db error: {}'.format(e))
    else:
        return isgoing[0][0]


def set_game_status(isstarted):
    try:
        with getcursor() as cur:
            cur.execute("""UPDATE status
                           SET isgoing = (%s)
                           WHERE id = 1""",
                           (isstarted,))
    except psycopg2.Error as e:
        print('db error: {}'.format(e))


def add_player(id, username, first_name, last_name):
    isinbase = True
    try:
        with getcursor() as cur:
            cur.execute("""SELECT tlg_id
                           FROM players
                           WHERE tlg_id = (%s)""",
                           (id,))
            if len(cur.fetchall()) == 0:
                isinbase = False
                cur.execute("""INSERT INTO players (tlg_id, username, first_name, last_name)
                               VALUES (%s, %s, %s, %s)""",
                               (id, username, first_name, last_name))
    except psycopg2.Error as e:
        print('db error: {}'.format(e))
    finally:
        return isinbase


def add_answer(id, key, time, status, text):
    isnotanswered = None
    try:
        with getcursor() as cur:
            cur.execute("""SELECT isright
                           FROM answers
                           WHERE player_id = (%s) AND qn_id = (%s)""",
                           (id, key))
            if len(cur.fetchall()) != 0:
                isnotanswered = False
            else:
                isnotanswered = True
                dt = datetime.datetime.utcfromtimestamp(time) + datetime.timedelta(hours=3)
                cur.execute("""INSERT INTO answers (player_id, qn_id, isright, ans_time, ans_text)
                               VALUES (%s, %s, %s, %s, %s)""",
                               (id, key, status, dt, text))
    except psycopg2.Error as e:
        print('db error: {}'.format(e))
    finally:
        return isnotanswered


def get_ids():
    players_list = []
    try:
        with getcursor() as cur:
            cur.execute("""SELECT tlg_id
                           FROM players""")
            players_list = [line[0] for line in cur.fetchall()]
    except psycopg2.Error as e:
        print('db error: {}'.format(e))
    finally:
        return players_list


def get_players():
    players_list = []
    try:
        with getcursor() as cur:
            cur.execute("""SELECT tlg_id, first_name, last_name,
                           COUNT(CASE WHEN isright THEN 1 END) AS correct,
                           COUNT(CASE WHEN isright = false THEN 1 END) AS wrong,
                           MAX(CASE WHEN isright THEN ans_time ELSE NULL END) AS last_correct
                           FROM players LEFT JOIN answers
                           ON tlg_id = player_id
                           GROUP BY tlg_id, first_name, last_name
                           ORDER BY correct DESC, last_correct ASC NULLS LAST, wrong DESC""")
            players_list = cur.fetchall()
    except psycopg2.Error as e:
        print('db error: {}'.format(e))
    finally:
        return players_list


def players_to_list(users):
    msg = '*№*. Name _Correct/Wrong/Total_ `Last correct`\n\n'
    for i, user in enumerate(users):
        if user[2] is None:
            last_name = ''
        else:
            last_name = ' ' + user[2]
        if user[5] is None:
            last_correct = ''
        else:
            last_correct = ' `{:%H:%M:%S}`'.format(user[5])
        msg += "*{0}*. [{2}{3}](tg://user?id={1}) _{4}/{5}/{6}_{7}\n".format(i + 1, user[0], user[1], last_name,
                                                                             user[3], user[4], user[3] + user[4],
                                                                             last_correct)
    return msg
