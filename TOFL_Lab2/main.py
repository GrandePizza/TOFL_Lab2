import requests
"""Запускать на Ubuntu"""
# Глобальные переменные
ALPHABET = "abc012"
BASE_URL = "http://127.0.0.1:8080"
TABLE = {
    'main_prefixes': ["ε"],
    'non_main_prefixes': [],
    'suffixes': ["ε"],
    'table': {}
}
MAT_MODE = True

def init_automaton(mode="easy"):
    """Инициализация автомата в заданном режиме."""
    if MAT_MODE:
        response = requests.post(f"{BASE_URL}/start", json={"mode": mode})
        return response.status_code == 200


def check_word(word):
    """Запрос к MAT для проверки слова на принадлежность языку."""
    if MAT_MODE:
        response = requests.post(f"{BASE_URL}/checkWord", json={"word": word})
        return response.json().get("response") == '1'
    else:
        print("Является ли слово", word, "словом языка? 1/0")
        response = input()
        return response == '1'


def check_table():
    """Запрос к MAT для проверки таблицы на соответствие автомату."""
    main_prefixes_str = " ".join(TABLE['main_prefixes'])
    non_main_prefixes_str = " ".join(TABLE['non_main_prefixes'])
    suffixes_str = " ".join(TABLE['suffixes'])

    # Преобразуем таблицу в строку "0 1 0 ..." в зависимости от принадлежности слов к языку

    table_values = []

    for prefix in TABLE['main_prefixes'] + TABLE['non_main_prefixes']:
        current_prefix = prefix
        if prefix == 'ε':
            current_prefix = ''
        for suffix in TABLE['suffixes']:
            current_suffix = suffix
            if current_suffix == 'ε':
                current_suffix = ''
            # Проверяем наличие значения в таблице
            if TABLE['table'].get(current_prefix + current_suffix):
                table_values.append("1")
            else:
                table_values.append("0")

    table_str = " ".join(table_values)

    data = {
        "main_prefixes": main_prefixes_str,
        "non_main_prefixes": non_main_prefixes_str,
        "suffixes": suffixes_str,
        "table": table_str
    }

    if MAT_MODE:
        response = requests.post(f"{BASE_URL}/checkTable", json=data)
        result = response.json()
        if result.get('response') == 'true':
            return {"type": "success"}
        elif result.get('type'):
            return {"type": "counterexample", "response": result.get('response')}
        elif not result.get('type'):
            return {"type": "counterexample", "response": result.get('response')}
        else:
            return {"type": "error", "message": "Unexpected response format"}
    else:
        print("Верна ли данная таблица? +/-")
        print(data)
        response_true_false = input()
        if response_true_false == '+':
            return {"type": "success"}
        else:
            print("Введите контрпример")
            counterexample = input()
            return {"type": "counterexample", "response": counterexample}



def fill_table():
    """Заполнение таблицы на основе текущих префиксов и суффиксов."""
    for prefix in TABLE['main_prefixes'] + TABLE['non_main_prefixes']:
        for suffix in TABLE['suffixes']:
            current_prefix = prefix if prefix != 'ε' else ''
            current_suffix = suffix if suffix != 'ε' else ''
            word = current_prefix + current_suffix
            if word not in TABLE['table']:
                TABLE['table'][word] = check_word(word)


def extend_prefixes():
    """Построение дополнений для текущих префиксов."""
    new_prefixes = set()
    for prefix in TABLE['main_prefixes']:
        current_prefix = prefix if prefix != 'ε' else ''
        for symbol in ALPHABET:
            new_prefix = current_prefix + symbol
            if new_prefix not in TABLE['main_prefixes'] and new_prefix not in TABLE['non_main_prefixes']:
                new_prefixes.add(new_prefix)
    TABLE['non_main_prefixes'].extend(new_prefixes)


def check_completeness():
    """Проверка на полноту таблицы."""
    main_prefixes = TABLE['main_prefixes']
    non_main_prefixes = []
    for non_main_prefix in TABLE['non_main_prefixes']:
        equivalent_prefixes_found = False
        for main_prefix in main_prefixes:
            current_main_prefix = main_prefix if main_prefix != 'ε' else ''
            areEquivalent = True
            for suffix in TABLE['suffixes']:
                current_suffix = suffix if suffix != 'ε' else ''
                if TABLE['table'][non_main_prefix + current_suffix] != TABLE['table'][current_main_prefix + current_suffix]:
                    areEquivalent = False
                    break
            if areEquivalent:
                equivalent_prefixes_found = True
                break
        if not equivalent_prefixes_found:
                main_prefixes.append(non_main_prefix)
        else:
            non_main_prefixes.append(non_main_prefix)

    # Обновляем TABLE с измененными списками
    TABLE['main_prefixes'] = main_prefixes
    TABLE['non_main_prefixes'] = non_main_prefixes


def add_counterexample_suffixes(counterexample):
    """Добавление суффиксов из контрпримера."""
    suffixes = [counterexample[-i:] for i in range(1, len(counterexample) + 1)]
    for suffix in suffixes:
        if suffix not in TABLE['suffixes']:
            TABLE['suffixes'].append(suffix)


def learner_algorithm():
    """Основной алгоритм L* Лернера."""
    # Начальная инициализация автомата и таблицы
    init_automaton()
    while True:
        # Шаг 1: заполнение текущей таблицы запросами к MAT
        fill_table()

        # Шаг 2: дополнение префиксов
        extend_prefixes()

        # Шаг 3: заполнение таблицы для дополнений запросами к MAT
        fill_table()

        # Шаг 4: проверка полноты таблицы
        check_completeness()

        while not TABLE['non_main_prefixes']:
            extend_prefixes()
            fill_table()
            check_completeness()

        # Шаг 5: отправка таблицы MAT
        result = check_table()
        if result["type"] == "success":
            print("Автомат угадан!")
            print(TABLE)
            break
        elif result["type"] == "counterexample":
            add_counterexample_suffixes(result["response"])
        else:
            print("Ошибка:", result.get("message"))
            break


# Запуск алгоритма
learner_algorithm()
