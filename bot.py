"""
Бот "Організатор подій"
Консольний чат-бот для організації подій студента.
"""

import json
import os
from datetime import datetime, date, timedelta

# Шлях до файлу зі збереженими подіями
EVENTS_FILE = "events.json"


# ─────────────────────────────────────────────
# Збереження / завантаження даних
# ─────────────────────────────────────────────

def load_events() -> list:
    """Завантажує події з JSON-файлу. Повертає порожній список, якщо файл не існує."""
    if os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_events(events: list) -> None:
    """Зберігає список подій у JSON-файл."""
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────
# Допоміжні функції
# ─────────────────────────────────────────────

def parse_date(text: str) -> date | None:
    """Перетворює рядок 'YYYY-MM-DD' на об'єкт date. Повертає None при помилці."""
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_time(text: str):
    """Перетворює рядок 'HH:MM' на об'єкт time. Повертає None при помилці."""
    try:
        return datetime.strptime(text.strip(), "%H:%M").time()
    except ValueError:
        return None


def format_event(index: int, event: dict) -> str:
    """Форматує одну подію для виведення у консоль."""
    duration = f", тривалість: {event['duration']} хв" if event.get("duration") else ""
    return (
        f"[{index}] {event['name']}\n"
        f"    Дата: {event['date']}  Час: {event['time']}\n"
        f"    Категорія: {event['category']}{duration}"
    )


def check_conflict(events: list, new_event: dict) -> list:
    """
    Перевіряє конфлікти нової події з існуючими.
    Повертає список подій, що перетинаються за часом.
    """
    conflicts = []
    if not new_event.get("duration"):
        return conflicts  # без тривалості перевірка неможлива

    new_start = datetime.strptime(f"{new_event['date']} {new_event['time']}", "%Y-%m-%d %H:%M")
    new_end = new_start + timedelta(minutes=int(new_event["duration"]))

    for ev in events:
        if ev["date"] != new_event["date"] or not ev.get("duration"):
            continue
        ev_start = datetime.strptime(f"{ev['date']} {ev['time']}", "%Y-%m-%d %H:%M")
        ev_end = ev_start + timedelta(minutes=int(ev["duration"]))
        # Перетин: start1 < end2 AND start2 < end1
        if new_start < ev_end and ev_start < new_end:
            conflicts.append(ev)

    return conflicts


# ─────────────────────────────────────────────
# Команди бота
# ─────────────────────────────────────────────

def cmd_greet() -> None:
    """Вітає користувача."""
    print("\nПривіт! Я Організатор подій.")
    print("   Введи 'help', щоб побачити список команд.\n")


def cmd_help() -> None:
    """Виводить список доступних команд."""
    print("""
╔══════════════════════════════════════════════════╗
║            ДОСТУПНІ КОМАНДИ                      ║
╠══════════════════════════════════════════════════╣
║  вітання          — привітатися з ботом          ║
║  help             — цей список                   ║
║  додати подію     — додати нову подію            ║
║  показати події   — всі збережені події          ║
║  події на тиждень — події поточного тижня        ║
║  події на дату    — події на конкретну дату      ║
║  події за період  — події між двома датами       ║
║  події за категорією — фільтр за категорією      ║
║  пошук            — пошук за словом              ║
║  сьогодні         — події на сьогодні            ║
║  завтра           — події на завтра              ║
║  найближча        — найближча майбутня подія     ║
║  редагувати подію — змінити дані події           ║
║  видалити подію   — видалити подію               ║
║  вийти            — завершити програму           ║
╚══════════════════════════════════════════════════╝
""")


def cmd_add_event(events: list) -> None:
    """Додає нову подію після введення даних користувачем."""
    print("\n── Додавання нової події ──")

    name = input("Назва події: ").strip()
    if not name:
        print("ПОМИЛКА: Назва не може бути порожньою.")
        return

    # Введення дати
    while True:
        date_str = input("Дата (YYYY-MM-DD): ").strip()
        if parse_date(date_str):
            break
        print("ПОМИЛКА: Невірний формат дати. Спробуй ще раз.")

    # Введення часу
    while True:
        time_str = input("Час початку (HH:MM): ").strip()
        if parse_time(time_str):
            break
        print("ПОМИЛКА: Невірний формат часу. Спробуй ще раз.")

    category = input("Категорія / опис: ").strip() or "Без категорії"

    # Тривалість (необов'язково)
    duration_str = input("Тривалість у хвилинах (Enter — пропустити): ").strip()
    duration = None
    if duration_str.isdigit():
        duration = int(duration_str)

    new_event = {
        "name": name,
        "date": date_str,
        "time": time_str,
        "category": category,
        "duration": duration,
    }

    # Перевірка конфліктів
    conflicts = check_conflict(events, new_event)
    if conflicts:
        print("\nУВАГА! Ця подія перетинається з:")
        for c in conflicts:
            print(f"   • {c['name']} ({c['date']} {c['time']}, {c['duration']} хв)")
        confirm = input("Все одно додати? (так/ні): ").strip().lower()
        if confirm != "так":
            print("Додавання скасовано.")
            return

    events.append(new_event)
    save_events(events)
    print(f"Подію '{name}' додано!")


def cmd_show_events(events: list) -> None:
    """Виводить усі збережені події."""
    if not events:
        print("\nСписок подій порожній.")
        return
    print(f"\n── Усі події ({len(events)}) ──")
    for i, ev in enumerate(events):
        print(format_event(i, ev))


def cmd_week_events(events: list) -> None:
    """Показує події поточного тижня."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # понеділок
    week_end = week_start + timedelta(days=6)             # неділя

    week_events = [
        (i, ev) for i, ev in enumerate(events)
        if week_start <= parse_date(ev["date"]) <= week_end
    ]

    print(f"\n── Події цього тижня ({week_start} — {week_end}) ──")
    if not week_events:
        print("Немає подій на цей тиждень.")
    else:
        for i, ev in week_events:
            print(format_event(i, ev))


def cmd_events_by_date(events: list) -> None:
    """Виводить події на конкретну дату."""
    date_str = input("Введи дату (YYYY-MM-DD): ").strip()
    if not parse_date(date_str):
        print("ПОМИЛКА: Невірний формат дати.")
        return
    result = [(i, ev) for i, ev in enumerate(events) if ev["date"] == date_str]
    print(f"\n── Події на {date_str} ──")
    if not result:
        print("Немає подій на цю дату.")
    else:
        for i, ev in result:
            print(format_event(i, ev))


def cmd_events_by_period(events: list) -> None:
    """Виводить події між двома датами."""
    start_str = input("Дата початку (YYYY-MM-DD): ").strip()
    end_str = input("Дата кінця   (YYYY-MM-DD): ").strip()
    start = parse_date(start_str)
    end = parse_date(end_str)
    if not start or not end:
        print("ПОМИЛКА: Невірний формат дати.")
        return
    if start > end:
        print("ПОМИЛКА: Дата початку не може бути пізніше дати кінця.")
        return
    result = [
        (i, ev) for i, ev in enumerate(events)
        if start <= parse_date(ev["date"]) <= end
    ]
    print(f"\n── Події з {start_str} по {end_str} ──")
    if not result:
        print("Немає подій за цей період.")
    else:
        for i, ev in result:
            print(format_event(i, ev))


def cmd_events_by_category(events: list) -> None:
    """Виводить події за категорією."""
    cat = input("Введи категорію: ").strip().lower()
    result = [
        (i, ev) for i, ev in enumerate(events)
        if cat in ev["category"].lower()
    ]
    print(f"\n── Події з категорією '{cat}' ──")
    if not result:
        print("Немає подій з такою категорією.")
    else:
        for i, ev in result:
            print(format_event(i, ev))


def cmd_search(events: list) -> None:
    """Шукає події за словом у назві або описі."""
    keyword = input("Введи слово для пошуку: ").strip().lower()
    result = [
        (i, ev) for i, ev in enumerate(events)
        if keyword in ev["name"].lower() or keyword in ev["category"].lower()
    ]
    print(f"\n── Результати пошуку '{keyword}' ──")
    if not result:
        print("Нічого не знайдено.")
    else:
        for i, ev in result:
            print(format_event(i, ev))


def cmd_today(events: list) -> None:
    """Виводить події на сьогодні."""
    today_str = date.today().isoformat()
    result = [(i, ev) for i, ev in enumerate(events) if ev["date"] == today_str]
    print(f"\n── Події на сьогодні ({today_str}) ──")
    if not result:
        print("Сьогодні немає подій.")
    else:
        for i, ev in result:
            print(format_event(i, ev))


def cmd_tomorrow(events: list) -> None:
    """Виводить події на завтра."""
    tomorrow_str = (date.today() + timedelta(days=1)).isoformat()
    result = [(i, ev) for i, ev in enumerate(events) if ev["date"] == tomorrow_str]
    print(f"\n── Події на завтра ({tomorrow_str}) ──")
    if not result:
        print("Завтра немає подій.")
    else:
        for i, ev in result:
            print(format_event(i, ev))


def cmd_nearest(events: list) -> None:
    """Знаходить найближчу майбутню подію."""
    today = date.today()
    future = [
        ev for ev in events
        if parse_date(ev["date"]) >= today
    ]
    if not future:
        print("\nНемає майбутніх подій.")
        return
    nearest = min(future, key=lambda ev: (ev["date"], ev["time"]))
    idx = events.index(nearest)
    print("\n── Найближча подія ──")
    print(format_event(idx, nearest))


def cmd_edit_event(events: list) -> None:
    """Редагує існуючу подію."""
    if not events:
        print("\nСписок подій порожній.")
        return
    cmd_show_events(events)
    try:
        idx = int(input("\nНомер події для редагування: "))
        if idx < 0 or idx >= len(events):
            print("ПОМИЛКА: Невірний номер.")
            return
    except ValueError:
        print("ПОМИЛКА: Введи число.")
        return

    ev = events[idx]
    print(f"\nРедагування: {ev['name']} ({ev['date']} {ev['time']})")
    print("Залиш поле порожнім, щоб не змінювати.")

    new_name = input(f"Нова назва [{ev['name']}]: ").strip()
    new_date = input(f"Нова дата  [{ev['date']}]: ").strip()
    new_time = input(f"Новий час  [{ev['time']}]: ").strip()
    new_cat  = input(f"Категорія  [{ev['category']}]: ").strip()

    if new_name:
        ev["name"] = new_name
    if new_date:
        if parse_date(new_date):
            ev["date"] = new_date
        else:
            print("ПОМИЛКА: Невірний формат дати — дату не змінено.")
    if new_time:
        if parse_time(new_time):
            ev["time"] = new_time
        else:
            print("ПОМИЛКА: Невірний формат часу — час не змінено.")
    if new_cat:
        ev["category"] = new_cat

    save_events(events)
    print("Подію оновлено!")


def cmd_delete_event(events: list) -> None:
    """Видаляє подію зі списку."""
    if not events:
        print("\nСписок подій порожній.")
        return
    cmd_show_events(events)
    try:
        idx = int(input("\nНомер події для видалення: "))
        if idx < 0 or idx >= len(events):
            print("ПОМИЛКА: Невірний номер.")
            return
    except ValueError:
        print("ПОМИЛКА: Введи число.")
        return

    removed = events.pop(idx)
    save_events(events)
    print(f"Подію '{removed['name']}' видалено.")


# ─────────────────────────────────────────────
# Головний цикл
# ─────────────────────────────────────────────

def main() -> None:
    """Головна функція: завантажує дані та запускає цикл обробки команд."""
    events = load_events()
    cmd_greet()

    # Словник: команда → функція
    commands = {
        "вітання":            lambda: cmd_greet(),
        "help":               lambda: cmd_help(),
        "додати подію":       lambda: cmd_add_event(events),
        "показати події":     lambda: cmd_show_events(events),
        "події на тиждень":   lambda: cmd_week_events(events),
        "події на дату":      lambda: cmd_events_by_date(events),
        "події за період":    lambda: cmd_events_by_period(events),
        "події за категорією":lambda: cmd_events_by_category(events),
        "пошук":              lambda: cmd_search(events),
        "сьогодні":           lambda: cmd_today(events),
        "завтра":             lambda: cmd_tomorrow(events),
        "найближча":          lambda: cmd_nearest(events),
        "редагувати подію":   lambda: cmd_edit_event(events),
        "видалити подію":     lambda: cmd_delete_event(events),
    }

    while True:
        user_input = input("\n> ").strip().lower()

        if user_input == "вийти":
            print("До побачення!")
            break
        elif user_input in commands:
            commands[user_input]()
        else:
            print("Невідома команда. Введи 'help' для списку команд.")


if __name__ == "__main__":
    main()
