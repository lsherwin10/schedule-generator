#!/usr/bin/env python
#%%
from datetime import datetime, date, timedelta
import os
import pandas as pd
import pprint
import random
from typing import Dict, List, Set, Tuple
import sys

pp = pprint.PrettyPrinter(indent=4)


class Shift:
    def __init__(self, d, t):
        self.d = d
        self.t = t

    def get_day(self) -> date:
        return self.d

    def get_time(self) -> str:
        return self.t

    def set_day(self, val: date):
        self.d = val

    def set_time(self, val: str):
        self.t = val


def get_week_dates(start_date: date) -> List[date]:
    dates = [start_date]
    td = timedelta(days=1)
    for i in range(1, 7):
        dates.append(dates[i - 1] + td)
    return dates


def init_shifts(sd: date) -> Dict[date, List[str]]:
    dates = get_week_dates(sd)
    res = dict()
    for d in dates:
        res[d] = ["11:30-3:30", "11:30-3:30", "12:30-4:30", "3:30-7:30", "3:30-7:30"]
    return res


def init_data() -> pd.DataFrame:
    path = os.path.join(os.path.abspath(__file__ + "/../"), "seniority.csv")
    seniority = pd.read_csv(path, header=None, skiprows=1)
    global seniority_list
    global available_shifts
    global rem_shift_count
    global dates_worked
    global days_off
    global unavailable
    unavailable = set()
    seniority_list = [
        "mike",
        "hannah",
        "mikayla",
        "lauren",
        "aidan",
        "raegan",
        "ayva",
        "dylan",
        "gabe",
        "mia",
        "mikey",
        "sarah",
        "zak",
    ]
    dates_worked = {k: set() for k in seniority_list}
    days_off = {k: set() for k in seniority_list}
    global data
    data = pd.DataFrame(index=seniority_list, columns=["num_days_worked", "level"])
    for col in seniority.columns:
        gs = set(seniority[int(col)].dropna().str.lower())
        data.loc[list(gs), "level"] = int(col) + 1
    data.loc["mike", "level"] = 0
    data.loc[:, "num_days_worked"] = 0

    global start_date
    start_date = datetime.today().date()

    get_days_off()

    # start_date = datetime.strptime(input("Input a start date (m/d/yy): "), '%m/%d/%y').date()
    # start_date = datetime.strptime(days_off.columns[0], "%Y-%m-%d").date()
    # start_date = date(year=2021, month=8, day=7)
    # 0 = Monday, 1 = Tuesday, etc.

    available_shifts = init_shifts(start_date)

    dates = get_week_dates(start_date)

    schedule = pd.DataFrame(index=seniority_list, columns=dates)
    return schedule


def remove_shift(s: Shift):
    sd = s.get_day()
    st = s.get_time()
    global available_shifts
    try:
        available_shifts[sd].remove(st)
        if available_shifts[sd] == []:
            available_shifts.pop(sd, None)
    except ValueError:
        print("Shift already taken...")
        sys.exit(1)


def set_meet_days(df: pd.DataFrame) -> pd.DataFrame:
    global dates_worked
    global days_off
    tues_thurs_dates = list(
        filter(lambda x: x.weekday() == 1 or x.weekday() == 3, df.columns)
    )
    for d in tues_thurs_dates:
        if d not in days_off["mike"]:
            df.loc[["mike"], d] = "3:30-7:30"
            data.loc["mike", "num_days_worked"] += 1
            dates_worked["mike"].add(d)
            remove_shift(Shift(d, "3:30-7:30"))

        if d not in days_off["zak"]:
            df.loc[["zak"], d] = "3:30-7:30"
            data.loc["zak", "num_days_worked"] += 1
            dates_worked["zak"].add(d)
            remove_shift(Shift(d, "3:30-7:30"))

    return df


def set_hannah_days(df: pd.DataFrame) -> pd.DataFrame:
    wkday_dates = list(filter(lambda x: x.weekday() < 5, df.columns))
    for d in wkday_dates:
        if d not in days_off["hannah"]:
            df.loc["hannah", d] = "11:30-3:30"
            data.loc["hannah", "num_days_worked"] += 1
            dates_worked["hannah"].add(d)
            remove_shift(Shift(d, "11:30-3:30"))

    return df


def get_days_off():
    global start_date
    global unavailable
    filename = os.path.join(os.path.abspath(__file__ + "/../"), "off_days.csv")
    off_days = pd.read_csv(filename, index_col=0)
    off_days.columns = off_days.columns.map(
        lambda x: datetime.strptime(x, "%Y-%m-%d").date()
    )
    # display(off_days)
    start_date = off_days.columns[0]
    global days_off
    for col in off_days.columns:
        g_off = off_days[col].dropna()
        # display(off_days[col].dropna())
        # print(g_dict)
        for g in g_off.index:
            days_off[g].add(col)
            if len(days_off[g]) == 7:
                unavailable.add(g)

    # for g in data.index:
    #     inp = input(
    #         f"Input days off for {g.capitalize()} (m/d/yy, separated by commas): "
    #     )
    #     if inp == "":
    #         days = []
    #     else:
    #         days = [
    #             datetime.strptime(x.strip(), "%m/%d/%y").date() for x in inp.split(",")
    #         ]
    #     days = set(days)
    #     if g in days_off:
    #         days_off[g] = days_off[g] | days
    #     else:
    #         days_off[g] = days


def get_light_guards(lvl: int) -> Set[str]:
    # takes in the set of all guards separated by seniority and an int denoting
    #   the seniority level to select, and returns a subset of that seniority
    #   level containing all of the guards who have less than the most number
    #   of shifts, or returns all guards if they all have the same number of
    #   shifts
    global data
    gs = data[(data["level"] == lvl) & (~data.index.isin(unavailable))]
    min_days = min(gs["num_days_worked"].values)
    min_guards = gs[gs["num_days_worked"] == min_days].index.values

    return set(min_guards)


def get_lvl6_conflict_times(
    lvl6_sch_df: pd.DataFrame, days: Set[date]
) -> Dict[date, Set[str]]:
    global data
    lvl6_sch_df = lvl6_sch_df[~lvl6_sch_df.isin(days)]
    res = dict()
    for col in lvl6_sch_df.columns:
        res[col] = set(lvl6_sch_df[col].values)
    # print(f'Conflict times: {res}')
    return res


def get_lvl6_conflicts(sch: pd.DataFrame, g: str) -> Dict[date, Set[str]]:
    global data
    lvl6_sch_df = sch[(data["level"] == 6) & (~data.index.isin(unavailable))]
    lvl6_sch_df = lvl6_sch_df.drop(g)
    lvl6_sch_df.dropna(axis=1, inplace=True)
    # print("Sch df:")
    # display(lvl6_sch_df)
    for col in lvl6_sch_df.columns:
        lvl6_sch_df[col] = lvl6_sch_df[col].apply(
            lambda x: x == "11:30-3:30" or x == "3:30-7:30"
        )

    day_mask = lvl6_sch_df.all(axis=0)
    # print("Day mask:")
    # display(day_mask)
    # print("Schedule:")
    # display(sch)

    # day_mask = day_mask[]

    # FIXME: masking does not work properly, need time integration
    days = lvl6_sch_df.columns.to_series()
    days.mask(day_mask, inplace=True)
    days.dropna(inplace=True)
    # if set(days) != set():
    # print(f"Conflict days: {set(list(days))}")
    # display(sch)
    time_dict = get_lvl6_conflict_times(lvl6_sch_df, days)
    return set(days), time_dict


def set_shift(
    sch: pd.DataFrame, gs: Set[str], lvl: int
) -> Tuple[pd.DataFrame, Set[str]]:
    global days_off
    global dates_worked
    global available_shifts
    global data
    g = random.choice(tuple(gs))
    do = days_off[g]
    dw = dates_worked[g]
    lvl6_conflicts = get_lvl6_conflicts(sch, g) if lvl == 6 else (set(), dict())
    lvl6_conflict_days, lvl6_conflict_times = lvl6_conflicts[0], lvl6_conflicts[1]
    # print(lvl6_conflict_days, lvl6_conflict_times)
    available_days = set(available_shifts.keys()) - do - dw - lvl6_conflict_days
    # print(available_days, type(available_days))
    # print(f'g: {g}, do: {do}, dw: {dw}, lvl6: {lvl6_conflicts}, avail: {available_days}')
    if available_days != set():
        # print("found available days...")
        shift_day = random.choice(tuple(available_days))
        conf_times = (
            lvl6_conflict_times[shift_day]
            if shift_day in lvl6_conflict_times
            else set()
        )
        new_times = [x for x in available_shifts[shift_day] if x not in conf_times]
        shift_time = random.choice(new_times)
        sch.loc[g, shift_day] = shift_time
        remove_shift(Shift(shift_day, shift_time))
        data.loc[g, "num_days_worked"] += 1
        dates_worked[g].add(shift_day)
    gs.remove(g)
    return sch, gs


def give_first_shifts(sch: pd.DataFrame) -> pd.DataFrame:
    # gives every guard one shift to start assignment
    global data
    start_sch = sch.copy()
    start_data = data.copy()
    global unavailable
    empty_gs = sch[data["num_days_worked"] == 0].copy()
    empty_gs.drop(unavailable, axis=0, inplace=True)
    # display(empty_gs)
    data_trimmed = data[data.index.isin(empty_gs.index.values)]
    # display(data_trimmed)
    for lvl in range(2, 7):
        gs = set(empty_gs[data_trimmed["level"] == lvl].index.values)
        while gs != set():
            # print(f'Guards left: {gs}')
            sch, gs = set_shift(sch, gs, lvl)
    if (
        list(
            data[
                ((~data.index.isin(unavailable) & data["num_days_worked"] == 0))
            ].index.values
        )
        != []
    ):
        print("repeating firsts...")
        # display(sch)
        # display(data)
        data = start_data
        return give_first_shifts(start_sch)
    return sch


def give_shifts_lvl_range(sch: pd.DataFrame, start: int, end: int) -> pd.DataFrame:
    global available_shifts
    for lvl in range(start, end):
        next_guards = get_light_guards(lvl)
        while next_guards != set():
            sch, next_guards = set_shift(sch, next_guards, lvl)
            if available_shifts == dict():
                break
        if available_shifts == dict():
            break
    return sch


def has_uneven_offset() -> bool:
    global unavailable
    lvl2 = data[(data["level"] == 2) & ~(data.index.isin(unavailable))]
    lvl3 = data[(data["level"] == 3) & ~(data.index.isin(unavailable))]
    lvl4 = data[(data["level"] == 4) & ~(data.index.isin(unavailable))]
    lvl5 = data[(data["level"] == 5) & ~(data.index.isin(unavailable))]
    lvl6 = data[(data["level"] == 6) & ~(data.index.isin(unavailable))]
    lvls = [lvl2, lvl3, lvl4, lvl5, lvl6]
    new_lvls = [lvl for lvl in lvls if len(lvl) > 0]
    # display(lvls)
    # display(new_lvls)
    off = 9999
    for lvl in new_lvls:
        # display(lvl)
        print(f"Level {lvl.iloc[0, 1]}, Off: {lvl['num_days_worked'].min()}")
        if lvl["num_days_worked"].min() <= off:
            off = lvl["num_days_worked"].min()
        else:
            return True
    return False


def give_offset_shifts(sch: pd.DataFrame) -> pd.DataFrame:
    global data
    start_sch = sch.copy()
    start_data = data.copy()
    end = 6
    while end > 2:
        sch = give_shifts_lvl_range(sch, 2, end)
        end -= 1
    if has_uneven_offset():
        print("repeating offset...")
        # display(sch)
        # display(data)
        data = start_data
        return give_offset_shifts(start_sch)
    return sch


def give_shifts_by_seniority(sch: pd.DataFrame) -> pd.DataFrame:
    # returns an updated df schedule when given the initial df with partial
    #   data, the remaining shifts dict, and the days_off dict
    global available_shifts
    global data
    start_sch = sch.copy()
    start_data = data.copy()
    i = 0
    while available_shifts != dict() and i < 5:
        sch = give_shifts_lvl_range(sch, 2, 7)
        # display(sch)
        # display(data)
        i += 1
    if has_uneven_offset():
        data = start_data
        return give_shifts_by_seniority(start_sch)
    return sch


def give_shifts(sch: pd.DataFrame) -> pd.DataFrame:
    sch = give_first_shifts(sch)
    sch = give_offset_shifts(sch)
    sch = give_shifts_by_seniority(sch)
    return sch


def sort_df(df: pd.DataFrame) -> pd.DataFrame:
    global data
    df["Rank"] = data["level"]
    df.sort_values(["Rank"], ascending=True, inplace=True)
    df.drop("Rank", 1, inplace=True)
    return df


def create_schedule() -> pd.DataFrame:
    sch = init_data()
    sch = sort_df(sch)
    # sch = set_meet_days(sch)
    sch = set_hannah_days(sch)
    sch = give_shifts(sch)
    return sch


#%%
# i = 0
# while i < 100:
sch = create_schedule()
# display(sch)
# i += 1
# display(sch)
# display(data)
# print(data['num_days_worked'].sum())

sch.index = sch.index.str.capitalize()
filename = f"Guard Schedule {sch.columns[0].strftime('%m-%d')}->{sch.columns[-1].strftime('%m-%d')}.csv"
sch.columns = sch.columns.map(lambda x: x.strftime("%a, %b %d"))
sch.to_csv(os.path.join(os.path.abspath(__file__ + "/../"), filename))
# %%

# %%
