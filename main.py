import time
import asyncio
import curses
import random
from fire_animation import fire
from curses_tools import draw_frame, get_frame_size, read_controls
import itertools
from space_garbage import fly_garbage, obstacles_actual
from pathlib import Path
from physics import update_speed

TIC_TIMEOUT = 0.1

def open_and_read_frames(file):
    with open(file, 'r') as frame:
        return frame.read()

async def count_years(year_counter, level_duration_sec=3, increment=5):
    while True:
        await sleep(level_duration_sec)
        year_counter[0] += increment

async def show_year_counter(canvas, year_counter, start_year):
    _, width = canvas.getmaxyx()
    counter_lenght = 10
    year_str_pos_y = 1
    year_str_pos_x = round(width - 10) - round(counter_lenght)
    while True:
        current_year = start_year + year_counter[0]
        canvas.addstr(year_str_pos_y, year_str_pos_x,
                      'Year {}'.format(current_year))
        await asyncio.sleep(0)


async def sleep(sec=1):
    for i in range(int(sec * 10)):
        await asyncio.sleep(0)


async def show_gameover(canvas, window_height, window_width, frame):
    message_size_y, message_size_x = get_frame_size(frame)
    message_pos_y = round(window_height / 2) - round(message_size_y / 2)
    message_pos_x = round(window_width / 2) - round(message_size_x / 2)
    while True:
        draw_frame(canvas, message_pos_y, message_pos_x, frame)
        await asyncio.sleep(0)


def make_trash_list():
    trash_list = []
    directory = 'animation_frames/garbage'
    pathlist = Path(directory).glob('*')
    for path in pathlist:
        trash_list.append(open_and_read_frames(path))
    trash_tuple = tuple(trash_list)
    return trash_tuple[random.randint(0, len(trash_tuple) - 1)]

async def fill_orbit_with_garbage(canvas,
                                  coros,
                                  level,
                                  border_size,
                                  timeout_minimal=0.3):
    _, columns_number = canvas.getmaxyx()
    while True:
        pice_trash = make_trash_list()
        _, trash_column_size = get_frame_size(pice_trash)
        random_column = random.randint(
          border_size, columns_number - trash_column_size - border_size)
        trash = fly_garbage(canvas, random_column, pice_trash, speed=0.5)
        coros.append(trash)
        garbage_respawn_timeout = calculate_respawn_timeout(level)
        if garbage_respawn_timeout <= timeout_minimal:
            garbage_respawn_timeout = timeout_minimal
        await sleep(garbage_respawn_timeout)

def calculate_respawn_timeout(level, initial_timeout=9, complexity_factor=20):
    timeout_step = level[0] / complexity_factor
    respawn_timeout = initial_timeout - timeout_step
    return respawn_timeout


# анимация ракеты
async def rocket_play(canvas, coros, row, column, rocket_frames, level,
                      start_year):
    height, width = canvas.getmaxyx()
    rock_carousel = itertools.cycle(rocket_frames)
    play_rocket = next(rock_carousel)
    field_y, field_x = get_frame_size(play_rocket)
    position_x = round(column) - round(field_x / 2)
    position_y = round(row) - round(field_y / 2)
    game_over = open_and_read_frames(
      'animation_frames/game_over/game_over.txt')
    speed_x, speed_y = 0, 0
    for frame in itertools.cycle(rocket_frames):
        while True:
            control_axis_y, control_axis_x, sapce = read_controls(canvas)
            speed_x, speed_y = update_speed(speed_x,
                                            speed_y,
                                            control_axis_y,
                                            control_axis_x)
            current_year = start_year + level[0]
            if current_year >= 2020 and sapce:
                shot_pos_x = position_x + round(field_x / 2)
                shot_coro = fire(canvas, position_y, shot_pos_x)
                coros.append(shot_coro)
            position_x += speed_y
            position_y += speed_x
            get_cener_x = position_x + field_x
            get_cener_y = position_y + field_y
            frame_x = min(get_cener_x, width - 1) - field_x
            frame_y = min(get_cener_y, height - 1) - field_y
            frame_x = max(frame_x, 3)
            frame_y = max(frame_y, 3)
            draw_frame(canvas, frame_y, frame_x, frame)
            canvas.refresh()
            await sleep(0.1)
            draw_frame(canvas, frame_y, frame_x, frame, negative=True)
            frame = next(rock_carousel)
            for obstacle in obstacles_actual:
                if obstacle.has_collision(position_y, position_x):
                    game_over_coro = show_gameover(canvas,
                                                height,
                                                width,
                                                game_over)
                    coros.append(game_over_coro)
                    return


async def blink(canvas, row, column, symbol='*', tact=0):
    await sleep(0.5)
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(2)
        tact += 1
        canvas.addstr(row, column, symbol)
        await sleep(0.3)
        tact += 1
        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(0.5)
        tact += 1
        canvas.addstr(row, column, symbol)
        await sleep(0.3)

def draw(canvas):
    start_year = 1957
    level = [0]
    height, width = canvas.getmaxyx()
    coroutines = []
    canvas.border()
    curses.curs_set(False)
    canvas.refresh()
    canvas.nodelay(True)
    sapace_borders = 5
    bar_height = 2
    sb_begin_y = sb_begin_x = 0
    status_bar = canvas.derwin(bar_height, width, sb_begin_y, sb_begin_x)
    game_area_height = height - bar_height - sapace_borders
    game_area_width = width
    ga_begin_y = bar_height + sapace_borders
    ga_begin_x = 0
    game_area = canvas.derwin(game_area_height, game_area_width, ga_begin_y,
                              ga_begin_x)
    game_area.border()
    for i in range(100):
        star = random.choice(['+', '*', ':', '.'])
        coroutines.append(
          blink(canvas, random.randint(5, height - 5),
                random.randint(5, width - 5), star, random.randint(0, 3)))
    r1 = open_and_read_frames('animation_frames/rocket/rocket_frame_1.txt')
    r2 = open_and_read_frames('animation_frames/rocket/rocket_frame_2.txt')
    rocket_tuples = (r1, r2)
    Rock = rocket_play(canvas, coroutines,
                       height - 7,
                       width / 2,
                       rocket_tuples,
                       level, start_year)
    coroutines.append(Rock)
    count_years_coro = count_years(level)
    show_year_counter_coro = show_year_counter(status_bar, level, start_year)
    coroutines.append(count_years_coro)
    coroutines.append(show_year_counter_coro)
    garbage_coro = fill_orbit_with_garbage(canvas, coroutines, level,
                                           sapace_borders)
    coroutines.append(garbage_coro)
    while True:
        for i in coroutines.copy():
            try:
                i.send(None)
            except StopIteration:
                coroutines.remove(i)
        time.sleep(TIC_TIMEOUT)
        canvas.refresh()

if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)