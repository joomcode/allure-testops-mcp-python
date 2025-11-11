# Быстрое тестирование MCP сервера

## Шаг 1: Установка зависимостей

```bash
cd /Users/alexander.shurov/allure_testops/mcp/python
pip install -r requirements.txt
```

## Шаг 2: Настройка переменных окружения

```bash
export ALLURE_TESTOPS_URL='https://your-allure-instance.com'
export ALLURE_TOKEN='your-api-token'
export PROJECT_ID='1'
```

## Шаг 3: Простой тест

```bash
python test_simple.py
```

Должно вывести:
```
✓ ALLURE_TESTOPS_URL: https://...
✓ ALLURE_TOKEN: ...
✓ PROJECT_ID: 1
✓ allure_client imported
✓ index imported
✓ Server initialized with X tools
```

## Шаг 4: Полный тест

```bash
python test_mcp.py
```

Это проверит:
- Подключение к Allure TestOps API
- Регистрацию инструментов
- Выполнение обработчиков
- Структуру MCP сервера

## Шаг 5: Запуск сервера

```bash
python index.py
```

Сервер должен запуститься и ждать ввода на stdin. Вы увидите:
```
Allure TestOps MCP Server running on stdio
Connected to: https://...
Project ID: 1
Registered X tools
```

## Тестирование через Cursor

1. Добавьте в `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "allure-testops-python": {
      "command": "python3",
      "args": [
        "/Users/alexander.shurov/allure_testops/mcp/python/index.py"
      ],
      "env": {
        "ALLURE_TESTOPS_URL": "https://your-instance.com",
        "ALLURE_TOKEN": "your-token",
        "PROJECT_ID": "1"
      }
    }
  }
}
```

2. Перезапустите Cursor
3. Попробуйте использовать инструменты в чате

## Устранение проблем

### Ошибка импорта
```bash
# Убедитесь, что вы в правильной директории
cd /Users/alexander.shurov/allure_testops/mcp/python

# Проверьте, что все файлы на месте
ls -la controllers/
```

### Ошибка подключения к API
- Проверьте правильность URL
- Проверьте токен
- Проверьте сетевую доступность

### Ошибка "Unknown tool"
- Убедитесь, что все контроллеры импортированы в index.py
- Проверьте, что обработчики реализованы




