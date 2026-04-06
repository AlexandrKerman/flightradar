import sys
from stringprep import c7_set

from src.classes import AeroplanesAPI, Aeroplane, JSONSaver
import asyncio


def scroll_cmd():
    print('\n' * 100)


def answer_checker(question=None, valid_answers=None):
    while True:
        valid_answers = [*map(str, valid_answers)]
        user_input = input(question if question else '').strip().lower()
        if user_input in valid_answers:
            return user_input
        print(f'Некорректный ответ. Доступные варианты: {valid_answers}')
        return False


def filter_by_countries(planes: list) -> list:
    print('Введите список стран), разделяя их символом ";".\n'
          'Страны вводятся по-английски, соблюдая регистр')
    user_input = input('input: ').split(';')
    countries = [*map(lambda x: x.strip(), user_input)]
    return Aeroplane.filter_by_country(countries, planes)


def filter_by_range(planes: list) -> list | bool:
    user_input = input('Минимальная высота: ').strip()
    min_range = 0
    max_range = 0
    if user_input.isdigit():
        min_range = int(user_input)
    else:
        print('Некорректная высота. Возвращаю в главное меню')
        return False
    user_input = input('Максимальная высота: ').strip()
    if user_input.isdigit():
        max_range = int(user_input)
    else:
        print('Некорректная высота. Возвращаю в главное меню')
        return False
    return Aeroplane.filter_by_range(planes, (min_range, max_range))


def filter_by_ground(planes: list) -> list | bool:
    print('1. Только на земле\n'
          '2. Только в воздухе\n'
          '3. Оставить без изменений')
    match input('input: '):
        case '1':
            return Aeroplane.filter_by_ground(planes, True)
        case '2':
            return Aeroplane.filter_by_ground(planes, is_grounded=False)
        case '3':
            return False
        case _:
            print('Некорректный ввод. Возвращаю в главное меню...')
            return False


def get_top(planes: list) -> list | bool:
    user_input = input('Количество для вывода в топ-n: ').strip()
    if user_input.isdigit():
        return Aeroplane.get_top(planes, int(user_input))
    else:
        print('Некорректное число. Возвращаю в главное меню')
        return False


def wait_for_actions():
    input('Enter to retun in main menu...')


async def get_aeroplanes(aeroplanes):
    if aeroplanes:
        print('Ваш список самолётов не пустой.\n'
              'Вы действительно хотите продолжить? Да/Нет')
        match input('input: ').strip().lower():
            case 'да':
                pass
            case 'нет':
                print('Данные не изменены. Возвращаю в главное меню')
                return aeroplanes
            case _:
                print('Некорректный ввод.')
                return aeroplanes

    user_input = input('Введите страны, самолёты над которыми хотите получить.\n'
                       'Если стран несколько, разделяйте их символом ";"\n'
                       'Страны: ').split(';')
    countries = [*map(lambda x: x.strip(), user_input)]
    print(f'Список стран: {countries}')
    wait_for_actions()

    api_objects = [AeroplanesAPI() for i in range(len(countries))]

    try:
        await asyncio.gather(*[obj.set_box(country) for obj, country in zip(api_objects, countries)])
        await asyncio.gather(*[obj.get_aeroplanes(country) for obj, country in zip(api_objects, countries)])
    except IndexError:
        scroll_cmd()
        print('Произошла ошибка. Возможно, введённые данные некорректны. Попробуйте снова\n')
        return await get_aeroplanes(aeroplanes)

    aeroplanes = Aeroplane.cast_to_aeroplane(
        [aeroplane for api in api_objects for aeroplane in api.aeroplanes])

    return aeroplanes


def sort_aeroplanes(planes):
    return sorted(planes, key=lambda x: alt if (alt := x['baro_altitude']) else 0)


def create_file_manager(filetype):
    scroll_cmd()
    print('Введите название файла.\n'
          '(Расширение можно не указывать)')
    filename = input('input: ').strip()
    print('Укажите путь к файлу.\n'
          '(Не существующие пути поддерживаются)')
    path = input('input: ')
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
        print('Ваш список самолётов содержит данные.\n'
              '1. Я хочу перезаписать\n'
              '0. Вернуться назад')
        match input('input: ').strip():
            case '1':
                pass
            case '0':
                return False
            case _:
                print('Некорректный ответ. Возвращаю в главное меню')
                return False

    print('Обновляю данные...')
    aeroplanes = Aeroplane.cast_to_aeroplane(filemanager.data)
    return aeroplanes


def delete_aeroplanes(filemanager, aeroplanes):
    for i in aeroplanes:
        filemanager.delete_aeroplane(i)



def confirm_delete_aeroplanes(filemanager):
    while True:
        scroll_cmd()
        print('Введите ICAO24 самолёта.\n'
              'Если их несколько, разделяйте их символом ";"')
        user_input = input('input: ').split(';')
        user_input = [*map(lambda x: x.strip(), user_input)]
        scroll_cmd()
        print(f'Список самолётов для удаления: {user_input}\n'
              f'1. Да, удалить.\n'
              f'2. Изменить выбор\n'
              f'0. Вернуться назад')
        match input('input: ').strip():
            case '1':
                delete_aeroplanes(filemanager, user_input)
                print('Самолёты удалены')
                wait_for_actions()
                return True
            case '2':
                continue
            case '0':
                return False


def delete_aeroplane_menu(filemanager, aeroplanes):
    while True:
        scroll_cmd()
        print('Меню удаления самолётов.\n'
              '1. Вывести все самолёты\n'
              '2. Удалить самолёты\n'
              '0. Вернуться назад')
        match input('input: '):
            case '1':
                if aeroplanes:
                    print(*[f'{i}. {plane}' for i, plane in enumerate(filemanager.data)], sep='\n')
                else:
                    print('Самолётов по фильтрам не найдено')
                wait_for_actions()
            case '2':
                confirm_delete_aeroplanes(filemanager)
            case '0':
                return False


def work_with_file(aeroplanes, filetype):
    filemanager = create_file_manager(filetype)
    while True:
        scroll_cmd()
        print('Меню работы с файлами:\n'
              '1. Прочитать файл\n'
              '2. Вывести информацию\n'
              '3. Сохранить файл\n'
              '4. Обновить самолёты в файловом менеджере\n'
              '5. Продолжить работу с текущим набором самолётов\n'
              '6. Удалить самолёт\n'
              '0. Вернуться в меню\n'
              f'Вы работаете с файлом: {filemanager.get_fullpath()}\n'
              f'{'\nНа текущий момент данных для обработки в файле нет.\n'
                 'Чтобы добавить, воспользуйтесь п.1' if len(filemanager.data) == 0 else ''}')
        match input('input: '):
            case '1':
                if read_data(filemanager):
                    print('Файл прочитан и содержит данные')
                else:
                    print('Файл пустой')
                wait_for_actions()
            case '2':
                print('Файл содержит: ')
                print(*get_data(filemanager), sep='\n\n')
                wait_for_actions()
            case '3':
                print('Сохраняю...')
                save_file(filemanager)
                print('Файл сохранён')
                wait_for_actions()
            case '4':
                print('Добавляю самолёты для обработки')
                update_file_data(filemanager, aeroplanes)
            case '5':
                temp = update_aeroplanes(filemanager, aeroplanes)
                if temp:
                    aeroplanes = temp
                return aeroplanes
            case '6':
                if delete_aeroplane_menu(filemanager, aeroplanes):
                    print('Самолёты удалены')
                else:
                    print('Список остался неизменным')
                wait_for_actions()
            case '0':
                return False


def set_filetype():
    scroll_cmd()
    file_types = {
        '1': JSONSaver
    }
    print('Укажите тип файла, с которым хотите работать:\n'
          '1. JSON\n'
          '0. Вернуться в меню')
    if (user_input := input('input: ').strip()) == '0':
        print('false')
        return False
    print(f'{user_input=}')
    if user_input in file_types:
        print('filetypes')
        return file_types[user_input]
    print('another false')
    return False


async def main():
    aeroplanes = []
    # aeroplanes = await get_aeroplanes(aeroplanes)

    while True:
        scroll_cmd()
        print('Меню:\n'
              '1. Получить новые самолёты\n'
              '2. Вывести все Самолёты\n'
              '3. Отфильтровать по странам.\n'
              '4. Отфильтровать по высоте\n'
              '5. Отфильтровать по нахождению на земле\n'
              '6. Получить Топ-n по высоте\n'
              '7. Отсортировать самолёты по высоте\n'
              '8. Работать с файлом\n'
              '0. Закрыть.')
        if not aeroplanes:
            print('Список самолётов пустует. Получите новый (п.1) или загрузите из файла (п.8)')
        match input('input: '):
            case '1':
                scroll_cmd()
                aeroplanes = await get_aeroplanes(aeroplanes)
                scroll_cmd()
                print('Самолёты получены. Возвращаю в главное меню')
                wait_for_actions()
            case '2':
                if aeroplanes:
                    print(*[f'{i}. {plane}' for i, plane in enumerate(aeroplanes)], sep='\n')
                else:
                    print('Самолётов по фильтрам не найдено')
                wait_for_actions()
            case '3':
                print('Фильтрую...')
                aeroplanes = filter_by_countries(aeroplanes)
                print('Данные отфильтрованы.')
                wait_for_actions()
            case '4':
                print('Фильтрую...')
                aeroplanes = filter_by_range(aeroplanes)
                if aeroplanes:
                    print('Данные отфильтрованы.')
                else:
                    print('Данные остались без изменений. Повторите попытку')
                wait_for_actions()
            case '5':
                print('Фильтрую...')
                aeroplanes = filter_by_ground(aeroplanes)
                if aeroplanes:
                    print('Данные отфильтрованы.')
                else:
                    print('Данные остались без изменений. Повторите попытку')
                wait_for_actions()
            case '6':
                print(*[f'{i}. {plane}' for i, plane in enumerate(get_top(aeroplanes))], sep='\n')
                wait_for_actions()
            case '7':
                print('Сортирую...')
                aeroplanes = sort_aeroplanes(aeroplanes)
                print('Данные отсортированы')
                wait_for_actions()
            case '8':
                filetype = set_filetype()
                if filetype:
                    temp = work_with_file(aeroplanes, filetype)
                    if temp:
                        aeroplanes = temp
                        print('Список самолётов обновлён')
                print('Работа с файлами завершена')
                wait_for_actions()
            case '0':
                sys.exit()


if __name__ == "__main__":
    asyncio.run(main())
