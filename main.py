import asyncio
import sys

from src.classes import Aeroplane, AeroplanesAPI, JSONSaver


def scroll_cmd():
    print("\n" * 100)


def filter_by_countries(planes: list) -> list | bool:
    print('Введите список стран), разделяя их символом ";".\n' "Страны вводятся по-английски, соблюдая регистр")
    user_input = input("input: ").split(";")
    if not user_input:
        return False
    countries = [*map(lambda x: x.strip(), user_input)]
    return Aeroplane.filter_by_country(countries, planes)


def filter_by_range(planes: list) -> list | bool:
    user_input = input("Минимальная высота: ").strip()
    min_range = 0
    max_range = 0
    if user_input.isdigit():
        min_range = int(user_input)
    else:
        print("Некорректная высота. Возвращаю в главное меню")
        return False
    user_input = input("Максимальная высота: ").strip()
    if user_input.isdigit():
        max_range = int(user_input)
    else:
        print("Некорректная высота. Возвращаю в главное меню")
        return False
    return Aeroplane.filter_by_range(planes, (min_range, max_range))


def filter_by_ground(planes: list) -> list | bool:
    print("1. Только на земле\n" "2. Только в воздухе\n" "3. Оставить без изменений")
    match input("input: "):
        case "1":
            return Aeroplane.filter_by_ground(planes, True)
        case "2":
            return Aeroplane.filter_by_ground(planes, is_grounded=False)
        case "3":
            return False
        case _:
            print("Некорректный ввод. Возвращаю в главное меню...")
            return False


def get_top(planes: list) -> list | bool:
    user_input = input("Количество для вывода в топ-n: ").strip()
    if user_input.isdigit():
        return Aeroplane.get_top(planes, int(user_input))
    else:
        print("Некорректное число. Возвращаю в главное меню")
        return False


def wait_for_actions():
    input("Enter to retun in main menu...")


async def fetch_aeroplanes_data(obj, country):
    await obj.set_box(country)
    await obj.get_aeroplanes()
    return obj


async def get_aeroplanes(aeroplanes):
    if aeroplanes:
        print("Ваш список самолётов не пустой.\n" "Вы действительно хотите продолжить? Да/Нет")
        match input("input: ").strip().lower():
            case "да":
                pass
            case "нет":
                print("Данные не изменены. Возвращаю в главное меню")
                return False
            case _:
                print("Некорректный ввод.")
                return False

    user_input = input(
        "Введите страны, самолёты над которыми хотите получить.\n"
        'Если стран несколько, разделяйте их символом ";"\n'
        "Страны: "
    ).split(";")
    countries = [*map(lambda x: x.strip(), user_input)]
    print(f"Список стран: {countries}")
    wait_for_actions()

    api_objects = [AeroplanesAPI() for i in range(len(countries))]

    try:
        api_objects = await asyncio.gather(
            *[fetch_aeroplanes_data(obj, country) for obj, country in zip(api_objects, countries)])
        # await asyncio.gather(*[obj.set_box(country) for obj, country in zip(api_objects, countries)])
        # await asyncio.gather(*[obj.get_aeroplanes() for obj in api_objects])
    except IndexError:
        scroll_cmd()
        print("Произошла ошибка. Возможно, введённые данные некорректны. Попробуйте снова\n")
        return await get_aeroplanes(aeroplanes)

    aeroplanes = Aeroplane.cast_to_aeroplane([aeroplane for api in api_objects for aeroplane in api.aeroplanes])

    return aeroplanes


def sort_aeroplanes(planes):
    return sorted(planes, reverse=True, key=lambda x: alt if (alt := x["baro_altitude"]) else 0)


def create_file_manager(filetype):
    scroll_cmd()
    print("Введите название файла.\n" "(Расширение можно не указывать)")
    filename = input("input: ").strip()
    print("Укажите путь к файлу.\n" "(Не существующие пути поддерживаются)")
    path = input("input: ")
    return filetype(path, filename)


def get_data(filemanager):
    return filemanager.data


def read_data(filemanager):
    filemanager.read_aeroplane()
    if filemanager.data:
        return True
    return False


def save_file(filemanager):
    filemanager.save_file()


def update_file_data(filemanager, aeroplanes):
    filemanager.update_data(aeroplanes)


def update_aeroplanes(filemanager, aeroplanes):
    scroll_cmd()
    if aeroplanes:
        print("Ваш список самолётов содержит данные.\n" "1. Я хочу перезаписать\n" "0. Вернуться назад")
        match input("input: ").strip():
            case "1":
                pass
            case "0":
                return False
            case _:
                print("Некорректный ответ. Возвращаю в главное меню")
                return False

    print("Обновляю данные...")
    aeroplanes = Aeroplane.cast_to_aeroplane(filemanager.data)
    return aeroplanes


def delete_aeroplanes(filemanager, aeroplanes):
    for i in aeroplanes:
        filemanager.delete_aeroplane(i)


def confirm_delete_aeroplanes(filemanager):
    while True:
        scroll_cmd()
        print("Введите ICAO24 самолёта.\n" 'Если их несколько, разделяйте их символом ";"')
        user_input = input("input: ").split(";")
        user_input = [*map(lambda x: x.strip(), user_input)]
        scroll_cmd()
        print(
            f"Список самолётов для удаления: {user_input}\n"
            f"1. Да, удалить.\n"
            f"2. Изменить выбор\n"
            f"0. Вернуться назад"
        )
        match input("input: ").strip():
            case "1":
                delete_aeroplanes(filemanager, user_input)
                print("Самолёты удалены")
                wait_for_actions()
                return True
            case "2":
                continue
            case "0":
                return False


def delete_aeroplane_menu(filemanager):
    while True:
        scroll_cmd()
        print("Меню удаления самолётов.\n"
              "1. Вывести все самолёты\n"
              "2. Удалить самолёты\n"
              "0. Вернуться назад")
        match input("input: "):
            case "1":
                if aeroplanes := filemanager.data:
                    print(*[f"{i}. {plane}" for i, plane in enumerate(aeroplanes)], sep="\n")
                else:
                    print("Самолётов по фильтрам не найдено")
                wait_for_actions()
            case "2":
                confirm_delete_aeroplanes(filemanager)
            case "0":
                return False


def add_aeroplanes(filemanager, aeroplanes):
    print('Добавляю самолёты в файловый менеджер...')
    for i in aeroplanes:
        filemanager.add_aeroplane(i)
    print('Самолёты добавлены')


def work_with_file(aeroplanes, filetype):
    filemanager = create_file_manager(filetype)
    while True:
        scroll_cmd()
        print(
            "Меню работы с файлами:\n"
            "1. Прочитать файл\n"
            "2. Вывести информацию\n"
            "3. Сохранить файл\n"
            "4. Обновить самолёты в файловом менеджере\n"
            "5. Продолжить работу с текущим набором самолётов\n"
            "6. Удалить самолёт\n"
            "7. Добавить новые самолёты к имеющимся\n"
            "0. Вернуться в меню\n"
            f"Вы работаете с файлом: {filemanager.get_fullpath()}\n"
            f'{'\nНа текущий момент данных для обработки в файле нет.\n'
               'Чтобы добавить, воспользуйтесь п.1' if len(filemanager.data) == 0 else ''}'
        )
        match input("input: "):
            case "1":
                if read_data(filemanager):
                    print("Файл прочитан и содержит данные")
                else:
                    print("Файл пустой")
                wait_for_actions()
            case "2":
                print("Файл содержит: ")
                print(*get_data(filemanager), sep="\n\n")
                wait_for_actions()
            case "3":
                print("Сохраняю...")
                save_file(filemanager)
                print("Файл сохранён")
                wait_for_actions()
            case "4":
                print("Добавляю самолёты для обработки")
                update_file_data(filemanager, aeroplanes)
            case "5":
                temp = update_aeroplanes(filemanager, aeroplanes)
                if temp:
                    aeroplanes = temp
                return aeroplanes
            case "6":
                if delete_aeroplane_menu(filemanager):
                    print("Самолёты удалены")
                else:
                    print("Список остался неизменным")
                wait_for_actions()
            case '7':
                scroll_cmd()
                add_aeroplanes(filemanager, aeroplanes)
                wait_for_actions()
            case "0":
                return False


def set_filetype():
    scroll_cmd()
    file_types = {"1": JSONSaver}
    print("Укажите тип файла, с которым хотите работать:\n"
          "1. JSON\n"
          "0. Вернуться в меню")
    if (user_input := input("input: ").strip()) == "0":
        print("false")
        return False
    print(f"{user_input=}")
    if user_input in file_types:
        print("filetypes")
        return file_types[user_input]
    print("another false")
    return False


def get_tutor():
    tutor = [
        '''
        Краткая инструкция. РЕКОМЕНДУЕТСЯ к прочтению при первом запуске
        Чтобы пропустить её при след. запуске, примените параметр --skip-tutor
        
        1. Изначально список самолётов пустой. Вам будет предоставлено меню.
        Если у вас нет JSON файла с сохранёнными самолётами,
        рекомендуется выбрать п.1 из меню - Получить новые самолёты.
        Будет предложено ввести список стран. Доступен множественный ввод через ;.
        Если введено несколько локаций, произойдёт поиск по каждой из них параллельно.
        Далее они склеиваются в единый набор данных для обработки.
        
        Если введено несколько стран, их bounding box может пересекаться,
        что, очевидно, может привести к дублированию некоторых данных.
        В таком случае дублирующие записи будут исключены из набора данных, оставляя лишь уникальные значения.
        Все удалённые элементы будут выводиться в процессе объединения наборов данных.
        ''',
        '''
        2. В меню доступны различные варианты обработки данных.
        Каждый вариант обработки данных изменяет набор (искл.: Топ по высоте).
        После каждого изменения рекомендуется выводить список, чтобы оценить изменения - п.2 гл. меню.
        Если список самолётов оказывается пустым, будет выведено соответствующее сообщение.
        ''',
        '''
        3. П.8 главного меню подразумевает работу с файлом.
        При выборе соответствующего раздела будет предложено выбрать тип файла.
        После подтверждения типа файла, необходимо ввести:
        <Имя файла>.
        <Путь к файлу>.
        Имя файла по умолчанию - saved_aeroplanes.
        Писать полный путь не требуется - он будет сформирован автоматически,
        даже если файла или указанной директории не существует.
        Расширение файла также можно не указывать - при отсутствии оно генерируется автоматически
        в зависимости от расширения файла, выбранного ранее.
        
        Полный путь и имя файла будут приведены в меню по ходу работы с файловым менеджером.
        ''',
        '''
        4. Набор данных при работе с файлами и изначальный список самолётов – НЕЗАВИСИМЫЕ наборы данных.
        Изначально набор данных при работе с файлами отсутствует.
        Его можно заполнить тремя способами:
        - Прочитать из файла - п.1 меню работы с файлами.
        - Создать из набора самолётов, полученных в гл. меню - п.4 меню работы с файлами.
        !!! Набор данных файлового менеджера будет полностью заменён. В таком случае будет выведено подтверждение !!!
        - Добавить дополнительные самолёты - п.7 меню работы с файлами.
        В таком случае набор данных в файловом менеджере не заменяется, а дополняется новыми данными из набора данных,
        полученного в гл. меню.
        При дублировании данные уникализируются - дублирующиеся экземпляры не добавляются
        (сравнение по уникальному ICAO24 самолёта).
        ''',
        '''
        5. Для вывода содержимого файлового менеджера
        (набора данных, занесённого в него. Данные, полученные в гл. меню не задействованы)
        используйте п.2 меню работы с файлами - Вывести информацию.
        ''',
        '''
        6. Для сохранения результатов используйте п.3 меню работы с файлами - Сохранить информацию.
        Данные будут сохранены в соответствующей директории.
        !!! Данные будут перезаписаны !!!
        Если хотели ДОБАВИТЬ в файл новые данные, а не заменять их полностью, воспользуйтесь п.1 и п.7 меню работы с файлами,
        после чего переходите к сохранению данных.
        ''',
        '''
        7. П5. меню работы с файлами подразумевает замену набора данных в гл. меню на набор,
        полученный в ходе работы с файловым менеджером.
        Если там уже имеются данные, будет выведено соответствующее предупреждение.
        ''',
        '''
        8. Удаление данных. п.6 меню работы с файлами.
        Раздел удаления данных из файлового менеджера.
        Будет предложено 3 варианта:
        - Вывести список самолётов в файловом менеджере
        - Удалить самолёты
        - Вернуться назад
        * Список самолётов выводится пронумерованно в виде словарного представления каждого самолёта.
        Удаление происходит путём ввода уник. идентификатора самолёта (ICAO24). Если их несколько - разделить символом ";".
        '''
    ]

    for i, v in enumerate(tutor):
        scroll_cmd()
        print(f'Страница {i + 1} из {len(tutor)}')
        print(v)
        print('Enter to next tutorial page.\n'
              '"skip" to skip all tutorial')
        match input('input: ').strip():
            case '':
                continue
            case 'skip':
                break


async def main():
    if '--skip-tutor' not in sys.argv:
        get_tutor()

    aeroplanes = []

    while True:
        scroll_cmd()
        print(
            "Меню:\n"
            "1. Получить новые самолёты\n"
            "2. Вывести все Самолёты\n"
            "3. Отфильтровать по странам.\n"
            "4. Отфильтровать по высоте\n"
            "5. Отфильтровать по нахождению на земле\n"
            "6. Получить Топ-n по высоте\n"
            "7. Отсортировать самолёты по высоте\n"
            "8. Работать с файлом\n"
            "0. Закрыть."
        )
        if not aeroplanes:
            print("Список самолётов пустует. Получите новый (п.1) или загрузите из файла (п.8)")
        match input("input: "):
            case "1":
                scroll_cmd()
                if (temp := await get_aeroplanes(aeroplanes)) != False:
                    aeroplanes = temp
                    scroll_cmd()
                    print("Самолёты получены. Возвращаю в главное меню")
                else:
                    print('Изменений не произошло.')
                wait_for_actions()
            case "2":
                if aeroplanes:
                    print(*[f"{i}. {plane}" for i, plane in enumerate(aeroplanes)], sep="\n")
                else:
                    print("Самолётов по фильтрам не найдено")
                wait_for_actions()
            case "3":
                print("Фильтрую...")
                if aeroplanes_ := filter_by_countries(aeroplanes):
                    aeroplanes = aeroplanes_
                    print("Данные отфильтрованы.")
                else:
                    print('Данные остались без изменений')
                wait_for_actions()
            case "4":
                print("Фильтрую...")
                if aeroplanes_ := filter_by_range(aeroplanes):
                    aeroplanes = aeroplanes_
                    print("Данные отфильтрованы.")
                else:
                    print("Данные остались без изменений. Повторите попытку")
                wait_for_actions()
            case "5":
                print("Фильтрую...")
                aeroplanes = filter_by_ground(aeroplanes)
                if aeroplanes:
                    print("Данные отфильтрованы.")
                else:
                    print("Данные остались без изменений. Повторите попытку")
                wait_for_actions()
            case "6":
                print(*[f"{i}. {plane}" for i, plane in enumerate(get_top(aeroplanes))], sep="\n")
                wait_for_actions()
            case "7":
                print("Сортирую...")
                aeroplanes = sort_aeroplanes(aeroplanes)
                print("Данные отсортированы")
                wait_for_actions()
            case "8":
                filetype = set_filetype()
                if filetype:
                    temp = work_with_file(aeroplanes, filetype)
                    if temp:
                        aeroplanes = temp
                        print("Список самолётов обновлён")
                print("Работа с файлами завершена")
                wait_for_actions()
            case "0":
                sys.exit()


if __name__ == "__main__":
    asyncio.run(main())
