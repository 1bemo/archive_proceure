from datetime import datetime
import os
import shutil
from os import system
import subprocess

# -------------------------------------------- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ -------------------------------------------- #

# текущий путь 
current_path = os.path.abspath(__file__).replace('\\main.py','')

# параметры по умолчанию
sql_base_names = []
sql_user_name = ''
sql_user_pass = ''
files_for_archive = []
winrar_path = ''
archive_pass = ''
path_to = ''
archive_id = ''
log_file_path = ''
temp_path = ''
reserv_path = ''
archive_extension = ''

# -------------------------------------------- ФУНКЦИИ -------------------------------------------- #

# полностью чистит содержимое каталога. ignore_paths - исключения
def clear_folder(folder_path, ignore_paths = []):
    returned = ''
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                if file_path not in ignore_paths:
                    os.unlink(file_path)
            elif os.path.isdir(file_path):
                if file_path not in ignore_paths:
                    shutil.rmtree(file_path)
        except Exception as e:
            returned += f'. Ошибка удаления %s. Причина: %s' % (file_path, e)  
    return returned

# логирование с записью в файл
def log(text = ''):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    str = f'{'' if text.strip() == '' else f'{now}: '}{text}' 
    print(str)
    global log_file_path
    if not log_file_path.strip() == '':
        log_file = open(log_file_path, 'at', -1, 'utf-8')
        log_file.write(str + '\n')
        log_file.close()

# пинг до IP
def ping_to_ip(ip):
    response = system(f'ping -n 2 {ip} > nul')
    return response == 0

# упаковка файлов winrar'ом
def rar_pack(winrar_path, password, to_path, files_paths):
    rar_command = [winrar_path, 'a', '-r', f'-hp{password}', '-m5', '-dh', to_path].__add__(files_paths) 
    returned = ''
    try:
        subprocess.run(rar_command)
    except subprocess.CalledProcessError as e:
        returned = str(e)
    return returned

# выгрузка бекапов из SQL
def sql_backup(sql_user, sql_password, sql_base_names, sql_script_file_path, target_folder, sql_log_path):
    returned = []

    scqript_text = ''
    for base_name in sql_base_names:
        base_target_path = f'{target_folder}\\{base_name}.bak'
        scqript_text += f"BACKUP DATABASE [{base_name}] TO DISK = N'{base_target_path}' WITH NOFORMAT, NOINIT, NAME = N'{base_name}', SKIP, NOREWIND, NOUNLOAD, NO_COMPRESSION, STATS = 10\nGO\n"
        returned.append(base_target_path)

    sql_script_file = open(sql_script_file_path, 'wt', -1, 'utf-8')
    sql_script_file.write(scqript_text)
    sql_script_file.close()

    sql_command = ['sqlcmd', '-U', sql_user, '-P', sql_password, '-i', sql_script_file_path, '-o', sql_log_path]
    
    try:
        subprocess.run(sql_command)
    except subprocess.CalledProcessError as e:
        log(f'[ВНИМАНИЕ] Ошибка в выполнении SQL скрипта: {e}')
    except Exception as e:
        log(f'[ВНИМАНИЕ] Ошибка в выполнении SQL скрипта: {e}')
    
    if os.path.exists(sql_script_file_path):
        os.remove(sql_script_file_path)
    return returned

# ------------------------------------------------------------------------------------------------- #

def main():

    # декларируем взаимодействие с глобальными переменными
    global sql_base_names
    global sql_user_name
    global sql_user_pass
    global files_for_archive
    global winrar_path
    global archive_pass
    global path_to
    global archive_id
    global log_file_path
    global temp_path
    global reserv_path
    global archive_extension


    # ---------------------------- получаем настройки из файла cfg ---------------------------- #

    cfg_file_name = 'config.cfg'
    cfg_file_path = f'{current_path}\\{cfg_file_name}'          # путь до cfg-файла

    file_settings = open(cfg_file_path, 'rt', -1, 'utf-8')      # открываем файл с настройками. rt - режим чтение текстового документа. utf-8 - кодировка

    for line in file_settings:
        l = line.strip()            # чистим от пробелов

        if l == '' or l[0] == '#':  # пропускаем пустые и с первым символом '#'
            continue
        
        ind = l.find(':')           # ищем вхождение имвола двоеточие
        if ind == -1:               # пропускаем, если такого нет
            continue

        param = l[:ind].strip()     # имя параметра
        value = l[ind + 1:].strip() # значение параметра
        
        # разбираем параметры
        if param == 'filesForArchive':
            files_for_archive_str = value.strip()
            if not files_for_archive_str == '':
                spltters = files_for_archive_str.split(';')     # делим пути по разделителю ';'
                for spl in spltters:
                    files_for_archive.append(spl.strip())       # добавляем в список, убирая лишние пробелы
        elif param == 'sqlBaseNames':
            sql_base_names_str = value.strip()
            if not sql_base_names_str == '':
                spltters = sql_base_names_str.split(';')        # делим пути по разделителю ';'
                for spl in spltters:
                    sql_base_names.append(spl.strip())          # добавляем в список, убирая лишние пробелы
        elif param == 'sqlUserName':
            sql_user_name = value
        elif param == 'sqlUserPassword':
            sql_user_pass = value
        elif param == 'winrarPath':
            winrar_path = value
        elif param == 'archivePass':
            archive_pass = value
        elif param == 'pathTo':
            path_to = value
        elif param == 'archiveID':
            archive_id = value
        elif param == 'logFileName':
            log_file_name = value
            log_file_path = f'{current_path}\\{log_file_name}'
        elif param == 'tempCatalogName':
            temp_catalog_name = value
            temp_path = f'{current_path}\\{temp_catalog_name}'
        elif param == 'reservCatalogName':
            reserv_catalog_name = value
            reserv_path = f'{current_path}\\{reserv_catalog_name}'
        elif param == 'archiveExtension':
            archive_extension = value
        else:
            print(f'Неизвестный параметр: {param}')
            continue

    file_settings.close()

    # ---------------------------- ОСНОВНАЯ ЛОГИКА ---------------------------- #

    log('') # отступ пустой строки
    log('Начало выполнения процедуры')

    # ---------------------------- проверка необходимости выгрузки SQL ---------------------------- #

    need_sql = False
    if not len(sql_base_names) == 0:
        need_sql = True

    # ---------------------------- проверяем наличие файлов и каталогов ---------------------------- #

    # проверка winrar
    if not os.path.exists(winrar_path):
        log(f'[ВНИМАНИЕ] Не найден WinRar по пути: {winrar_path}. Работа скрипта остановлена')
        return
    
    # проверка TEMP директории
    if not os.path.exists(temp_path):
        os.mkdir(temp_path)

    # проверка ARCHIV директории
    if not os.path.exists(reserv_path):
        os.mkdir(reserv_path)

    # проверка архивируемых файлов
    existed_files = []
    for arch_path in files_for_archive:
        if os.path.exists(arch_path):
            existed_files.append(arch_path)
        else:
            log(f'[ВНИМАНИЕ] Не найден архивируемый файл {arch_path}. Архивация будет выполнена без него')
    files_for_archive = existed_files

    # ---------------------------- чистка временной папки ---------------------------- #

    is_good = clear_folder(temp_path)
    if is_good == '':
        log(f'[УСПЕХ] Врменная папка "{temp_path}" очищена')
    else:
        log(f'[ВНИМАНИЕ] Не удалось очистить временную папку. Причина: {is_good}')

    # ---------------------------- SQL выгрузка, если надо ---------------------------- #'

    if need_sql:

        # проверка наличия интерпретатора SQL
        has_sql = False
        try:
            subprocess.run(['sqlcmd', '--version'])
            has_sql = True
        except FileNotFoundError:
            log('[ВНИМАНИЕ] Не найден интерпретатор SQL команд')

        # если SQL установлен
        if has_sql:

            # проверка данных для запуска SQL скрипта
            if sql_user_name == '' or sql_user_pass == '':
                log('[ВНИМАНИЕ] Не указаны данные пользователя для SQL')
            else:
                # все ок. Выполняем SQL выгрузку

                sql_script_path = f'{current_path}\\sql_script.txt'
                sql_log_path = f'{current_path}\\sql_log.log'
                log(f'Начало выгрузки бекапов SQL')
                        
                backup_paths = sql_backup(sql_user_name, sql_user_pass, sql_base_names, sql_script_path, temp_path, sql_log_path)

                if not len(backup_paths) == 0:           
                    log('[УСПЕХ] Выгрузка бекапов SQL завершена')

                    # проверяем наличие всех выгруженных бекапов
                    for bckp in backup_paths:
                        if not os.path.exists(bckp):
                            log(f'[ВНИМАНИЕ] Не найден бекап после SQL выгрузки: {bckp}. Более подробное описание в {sql_log_path}')
                        else:
                            log(f'[УСПЕХ] Проверено наличие бекапа после SQL выгрузки: {bckp}')
                            files_for_archive.append(bckp)
                else:
                    log(f'[ВНИМАНИЕ] Не удалось выгрузить SQL бекап. Более подробное описание в {sql_log_path}')

    # ---------------------------- проверка надобности процедуры ---------------------------- #

    if len(files_for_archive) == 0:
        log(f'[ВНИМАНИЕ] Нет файлов для архивации. Работа скрипта остановлена')
        return

    # ---------------------------- если каталог "куда копируем - path_to" является не локальным каталогом, сначала пингуем до него ---------------------------- #

    need_copy = True

    if path_to[:2] == '\\\\':

        # получаем IP-адрес
        add_cuted = path_to[2:]
        ip_address = add_cuted[:(add_cuted.find('\\'))]

        # проверяем на доступность
        need_copy = ping_to_ip(ip_address)
        
        if need_copy:
            log(f'[УСПЕХ] Сервер {ip_address} доступен. Будет выполнено копирование после архивации')
        else:
            log(f'[ВНИМАНИЕ] Сервер {ip_address} не доступен. Архивация будет выполнена без копирования')

    # ---------------------------- Архивация ---------------------------- #

    # формируем имя архива
    now = datetime.now().strftime('%Y-%m-%d')
    archiv_name = f'{now}-({archive_id}).{archive_extension}'
    archiv_path = f'{temp_path}\\{archiv_name}'

    log('Начало архивации')
    error_text = rar_pack(f'{winrar_path}', archive_pass, archiv_path, files_for_archive)
    if (error_text == ''):
        if os.path.exists(archiv_path):
            log(f'[УСПЕХ] Архивация выполнена. Существование файла архивации проверено: {archiv_path}')
        else:
            log(f'[ВНИМАНИЕ] Архивация выполнена, но проверка существование файла "{archiv_path}" не успешна. Работа скрипта остановлена')
            return
    else:
        log(f'[ВНИМАНИЕ] Архивация не выполнена. Пакет WinRar вернул ошибку. Работа скрипта остановлена. Описание ошибки: {error_text}')
        return
    
    # ---------------------------- Перемещение в резерв ---------------------------- #

    reserv_archv_path = f'{reserv_path}\\{archiv_name}'
    log(f'Перемещение архива в резерв')
    shutil.move(archiv_path, reserv_archv_path)
    if not os.path.exists(reserv_archv_path):
        log(f'[ВНИМАНИЕ] После окончания перемещения, проверка существования файла резерва "{reserv_archv_path}" не успешна. Работа скрипта остановлена')
        return
    else:
        log('[УСПЕХ] Файл после перемещения в резерв проверен')

        # чистка старых резервов
        is_good = clear_folder(reserv_path, [reserv_archv_path])
        if is_good == '':
            log('[УСПЕХ] Старые резервы почищены')
        else:
            log(f'[ВНИМАНИЕ] Не удалось очистить от старых резервов. Причина: {is_good}')

        # чистка временного каталога
        is_good = clear_folder(temp_path)
        if is_good == '':
            log('[УСПЕХ] Временный каталог почищен')
        else:
            log(f'[ВНИМАНИЕ] Не удалось почистить временный каталог. Причина: {is_good}')

    # ---------------------------- Копирование, если нужно ---------------------------- #

    if need_copy:

        # проверка на существование каталога для копирования
        if not os.path.exists(path_to):
            log(f'[ВНИМАНИЕ] Каталог "{path_to}" не найден или к нему нет доступа. Копирование не будет выполнено')
        else:

            file_to = f'{path_to}\\{archiv_name}'   # целевое имя файла

            log(f'Начало копирования')
            shutil.copyfile(reserv_archv_path, file_to)

            if not os.path.exists(file_to):
                log(f'[ВНИМАНИЕ] После окончания копирования, проверка существования файла {file_to} не успешна. Работа скрипта остановлена')
                return
            else:
                log('[УСПЕХ] Файл после копирования проверен')

    # ---------------------------- КОНЕЦ ПРОЦЕДУРЫ ---------------------------- #

    log('Конец выполнения процедуры')

# Запуск основной функции
main()