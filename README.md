# Release notes action
GitHub action для подготовки release notes для команд, работающих по Gitflow и ведущих планирование задач в Yandex Tracker.
## Оглавление
- [Release notes action](#release-notes-action)
  - [Оглавление](#оглавление)
  - [Что умеет](#что-умеет)
  - [Пример готового release notes](#пример-готового-release-notes)
  - [Подготовка](#подготовка)
    - [Заведите в секретах репозитория следующие переменные:](#заведите-в-секретах-репозитория-следующие-переменные)
    - [Подключите к репозиторию экшен](#подключите-к-репозиторию-экшен)
  - [Как это работает](#как-это-работает)
    - [Общий случай](#общий-случай)
    - [Коммиты без задач](#коммиты-без-задач)
    - [Эпики](#эпики)
    - [Создание черновика релиза](#создание-черновика-релиза)
  - [Обработка ошибок](#обработка-ошибок)
  - [Дополнительные сведения](#дополнительные-сведения)
## Что умеет
* Определеяет по именам коммитов скоуп задач, вошедших в релиз.
* По каждой задаче достает из API Трекера её название и ссылку на задачу.
* Указывает автора pull request'а задачи и ссылку на реквест.
* Группирует задачи эпиков.
* Помещает готовый release notes в описание релизного PR.
* Создает черновик релиза на GitHub.
## Пример готового release notes
> ## What's Changed 
>
> * [[QUEUE-1511](https://tracker.yandex.ru/#)] Поправить цифры в plan application by [@grmnga](https://github.com/grmnga) in [#1234](https://github.com/organization/repository/pull/#)
> * [[QUEUE-1577](https://tracker.yandex.ru/#)] Справочник ролей by [@nemestny](https://github.com/nemestny) in [#1235](https://github.com/organization/repository/pull/1235)
> * [[QUEUE-1636](https://tracker.yandex.ru/#)] [Frontend] Выпилить старый код после переноса справочника by [@Zhuk7777](https://github.com/Zhuk7777) in [#1236](https://github.com/organization/repository/pull/#)
>
> ### Epic: [[QUEUE-1560](https://tracker.yandex.ru/#)] Перенос правочника под nextjs in [#1237](https://github.com/organization/repository/pull/#)
> * [[QUEUE-1561](https://tracker.yandex.ru/#)] [Frontend] Страница close reasons  by [@Nats92](https://github.com/Nats92) in [#1238](https://github.com/organization/repository/pull/#)
> * [[QUEUE-1562](https://tracker.yandex.ru/#)] [Frontend] CRUD close reason by [@Nats92](https://github.com/Nats92) in [#1239](https://github.com/organization/repository/pull/#)
## Подготовка
### Заведите в секретах репозитория следующие переменные:
| Переменная          | Назначение                                                                                                     |
|---------------------|----------------------------------------------------------------------------------------------------------------|
| YANDEX_ORG_ID       | Идентификатор организации, зарегистрированной в Yandex Tracker                                                 |
| YANDEX_OAUTH2_TOKEN | Токен авторизации. Для его получения необходимо следовать [инструкции](https://yandex.ru/dev/id/doc/ru/access) | 

### Подключите к репозиторию экшен
Добавьте в каталог `.github/workspace/` вашего репозитория файл `release-notes.yaml` следующего содержания
```YAML
name: Release Notes
on:
  pull_request:
    branches: 
      - 'master' # ветка, при открытии PR в которую будет стартовать экшен
jobs:
  release_notes:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Generate release notes
        uses: evrone-erp/release-notes-action@master
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          yandex_org_id: ${{ secrets.YANDEX_ORG_ID }}
          yandex_oauth2_token: ${{ secrets.YANDEX_OAUTH2_TOKEN }}
```
По умолчанию экшен стартует при открытии Pull Request, направленного в ветку `master`. Изменить это поведение можно, указав другую целевую ветку в файле `release-notes.yaml`
## Как это работает
### Общий случай
За аксиому принято правило - каждая задача заходит через свой Pull request (что соответствует Gitflow). Экшен ищет пары "commit + соответсвующий ему merge-commit". Через merge-commit определяется автор pull request (исполнитель задачи). По коммиту определеяется ключ задачи. Экшен ожидает названия коммитов вида [*-*], например:
```
[QUEUE-1798] add loading indicator
[PROJECT-98] Fix missing path
[TEST-257] rabbit_mq user_sync
```
По содержимому квадратх скобок экшен определяет ключ здачи, по которому будет пытаться найти её в Yandex Tracker.
Собрав данные о задачах и их исполнителях, экшен формирует описание для pull request, в котором перечисляет все задачи. Описание каждой задачи имеет вид:
```
[<ключ задачи в виде ссылки на зазачу>] <Название задачи из Yandex Tracker> by <автор pull request> in <ссылка на Pull request>
```
**Исключение**: исключением из правила об обязательном наличии merge-коммитов являются hotfix-ветки, т.е. ветки, название которых начинается со слова hotfix. 
### Коммиты без задач
Если экшен обнаруживает коммиты, в которых не находит ключ задачи, соответствующая ему строка в итоговом release notes будет выглядеть, как:
```
<Название коммита> by <автор pull request> in <ссылка на Pull request>
```
Например:

> * CVE fix: puma, google-protobuf by [@florineot](https://github.com/florineot) in [#509](https://github.com/organization/repository/pull/#)
> * Support: update fugit by [@grmnga](https://github.com/grmnga) in [#491](https://github.com/organization/repository/pull/#)


### Эпики
Под эпиком подразумевается Pull request, в который зашли задачи через отдельные реквесты, и который позже сам зашел в develop. Экшен умеет распознавать такие сценарии и группировать задачи, которые зашли через эпик. В таком случае в release notes появляется подзаголовок вида 
```
Epic: [<ключ задачи в виде ссылки на зазачу>] <Название задачи из Yandex Tracker> in <ссылка на Pull request>
```
А после перечисляются задачи этого эпика.
Пример:
> ### Epic: [[QUEUE-1560](https://tracker.yandex.ru/#)] Перенос правочника под nextjs in [#1237](https://github.com/organization/repository/pull/#)
> * [[QUEUE-1561](https://tracker.yandex.ru/#)] [Frontend] Страница close reasons  by [@Nats92](https://github.com/Nats92) in [#1238](https://github.com/organization/repository/pull/#)
> * [[QUEUE-1562](https://tracker.yandex.ru/#)] [Frontend] CRUD close reason by [@Nats92](https://github.com/Nats92) in [#1239](https://github.com/organization/repository/pull/#)
> * [[QUEUE-1563](https://tracker.yandex.ru/#)] [Frontend] [Backend] web_api CRUD close reason by [@grmnga](https://github.com/grmnga) in [#1240](https://github.com/organization/repository/pull/#)


### Создание черновика релиза
Помимо генерации release notes экшен также создает черновик релиза. Номер нового релиза определеяется по следующему правилу:
* если это рядовой релиз (PR в master), то инкрементируется минорная версия
* если это hotfix (имя ветки начинается с hotfix), то инкрементируется patch-версия.
## Обработка ошибок
Сервис Yandex Tracker может быть недоступен или возвращать код ответа, отличный от 200. В этом случае в логах выполнения экшена будет выведена информация об этом и сама ошибка. Убедитесь, что вы проверили лог, если экшен не работает корректно.
## Дополнительные сведения
[Release-notes-action](https://github.com/evrone-erp/release-notes-action)
проект создан и поддержан [Evrone](https://evrone.com/)

[<img src="https://evrone.com/logo/evrone-sponsored-logo.png" width=231>](https://evrone.com/?utm_source=evrone-django-template)
