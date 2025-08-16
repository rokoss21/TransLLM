# 📋 Примеры использования TransLLM Enhanced v2.0

## 🎯 Различные сценарии перевода

### 1️⃣ **Проект с китайскими символами (СОХРАНЕНИЕ)**
*Для проектов типа bazi_lib, где китайские символы - это технические термины*

```bash
python3 project_translator.py /path/to/chinese_project \
    --api-key YOUR_GROQ_KEY \
    --target-lang Russian \
    --source-lang English \
    --custom-instructions "PRESERVE_CHINESE_CHARACTERS
CRITICAL: Preserve ALL Chinese characters exactly: 甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥
These are essential technical terms and must NEVER be translated."
```

**Результат:** Все китайские символы остаются как есть, переводятся только комментарии и строки.

---

### 2️⃣ **Обычный проект с китайским текстом (ПЕРЕВОД)** 
*Для проектов, где китайский текст нужно переводить*

```bash
python3 project_translator.py /path/to/normal_project \
    --api-key YOUR_GROQ_KEY \
    --target-lang Russian \
    --source-lang Chinese \
    --custom-instructions "TRANSLATE_CHINESE_CHARACTERS
Translate ALL Chinese characters to target language.
Chinese text should be fully converted to readable Russian text."
```

**Результат:** Китайский текст переводится на русский язык.

---

### 3️⃣ **Большой проект (БЫСТРО)**
*Для быстрого перевода больших проектов*

```bash
python3 project_translator.py /path/to/large_project \
    --api-key YOUR_GROQ_KEY \
    --target-lang Russian \
    --source-lang English \
    --chunk-size 200 \
    --max-concurrent 15 \
    --custom-instructions "Focus on speed while maintaining code structure."
```

**Результат:** Быстрый перевод с максимальной параллельностью.

---

### 4️⃣ **Критически важный проект (МАКСИМАЛЬНАЯ ТОЧНОСТЬ)**
*Для проектов, где важна абсолютная точность*

```bash
python3 project_translator.py /path/to/critical_project \
    --api-key YOUR_GROQ_KEY \
    --target-lang Russian \
    --source-lang English \
    --chunk-size 50 \
    --max-concurrent 3 \
    --custom-instructions "MAXIMUM_PRECISION
Translate with extreme care. Double-check all code structure.
Preserve ALL technical terms, URLs, and configuration values."
```

**Результат:** Медленный но очень точный перевод.

---

### 5️⃣ **JavaScript/React проект**
*Для фронтенд проектов с JSX*

```bash
python3 project_translator.py /path/to/react_project \
    --api-key YOUR_GROQ_KEY \
    --target-lang Russian \
    --source-lang English \
    --chunk-size 100 \
    --custom-instructions "React/JSX project translation:
- Preserve all JSX tags and attributes
- Preserve className, id, and data-* attributes
- Translate only user-visible strings and comments
- Keep component names in English"
```

**Результат:** Корректный перевод React проекта с сохранением JSX структуры.

---

### 6️⃣ **Python проект с docstrings**
*Для Python проектов с документацией*

```bash
python3 project_translator.py /path/to/python_project \
    --api-key YOUR_GROQ_KEY \
    --target-lang Russian \
    --source-lang English \
    --chunk-size 120 \
    --custom-instructions "Python project translation:
- Translate all docstrings to Russian
- Translate comments but preserve # TODO, # FIXME, # NOTE
- Keep function and variable names in English
- Preserve type hints exactly"
```

**Результат:** Python код с русскими docstrings и комментариями.

---

### 7️⃣ **Медицинский/Научный проект**
*Для проектов со специальной терминологией*

```bash
python3 project_translator.py /path/to/medical_project \
    --api-key YOUR_GROQ_KEY \
    --target-lang Russian \
    --source-lang English \
    --custom-instructions "Medical/Scientific translation:
- Preserve all medical terms in Latin
- Preserve drug names, chemical formulas
- Translate general text but keep technical precision
- Preserve units: mg, ml, °C, etc."
```

**Результат:** Корректный перевод с сохранением медицинской терминологии.

---

### 8️⃣ **Проект с SQL и базами данных**
*Для проектов с запросами к БД*

```bash
python3 project_translator.py /path/to/database_project \
    --api-key YOUR_GROQ_KEY \
    --target-lang Russian \
    --source-lang English \
    --custom-instructions "Database project translation:
- Preserve ALL SQL queries exactly
- Keep table names, column names unchanged  
- Preserve database connection strings
- Translate only comments and user messages"
```

**Результат:** Перевод с сохранением всех SQL запросов и схем БД.

---

### 9️⃣ **Конфигурационные файлы**
*Для проектов с большим количеством конфигов*

```bash
python3 project_translator.py /path/to/config_project \
    --api-key YOUR_GROQ_KEY \
    --target-lang Russian \
    --source-lang English \
    --custom-instructions "Configuration files translation:
- Preserve JSON, YAML, XML structure exactly
- Keep all keys, paths, URLs unchanged
- Translate only description values and comments
- Preserve environment variables"
```

**Результат:** Переведенные описания при сохранении структуры конфигов.

---

### 🔟 **Многоязычный проект**
*Для проектов с несколькими языками*

```bash
python3 project_translator.py /path/to/multilang_project \
    --api-key YOUR_GROQ_KEY \
    --target-lang Russian \
    --source-lang English \
    --custom-instructions "Multilingual project:
- Preserve existing translations in other languages
- Keep i18n keys unchanged: t('key.name')
- Preserve language codes: en, fr, de, es
- Translate only English comments and new text"
```

**Результат:** Корректная работа с i18n системами и переводами.

---

## 🚀 **Запуск для проекта bazi_lib (улучшенная версия)**

```bash
cd /Users/deus21/Desktop/Projects/TransLLM

python3 project_translator.py /Users/deus21/Desktop/Projects/baczi-lib \
    --api-key YOUR_GROQ_KEY \
    --target-lang Russian \
    --source-lang English \
    --chunk-size 150 \
    --max-concurrent 10 \
    --custom-instructions "PRESERVE_CHINESE_CHARACTERS

🇨🇳 CRITICAL PRESERVATION RULES:
- Preserve ALL Chinese characters exactly: 甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥木火土金水
- These are essential Bazi technical terms (Heavenly Stems, Earthly Branches, Five Elements)
- NEVER translate, modify, or replace Chinese characters
- Chinese characters are NOT user text - they are technical identifiers
- Keep all animal names in Chinese: 鼠牛虎兔龙蛇马羊猴鸡狗猪

📋 TRANSLATE ONLY:
- Code comments (# comment, // comment)  
- Docstrings in triple quotes
- User-facing error messages
- Documentation strings

🚫 NEVER TRANSLATE:
- Variable, function, class names
- Chinese technical terms and symbols
- URLs, file paths, import statements
- Configuration keys and values"
```

**Ожидаемый результат:**
- ✅ Все китайские символы бацзы сохранены
- ✅ Комментарии переведены на русский  
- ✅ Подробный отчет с указанием точных проблемных строк
- ✅ Автоматическая проверка синтаксиса Python
- ✅ Детализированные рекомендации по исправлению

---

## 📊 **Интерпретация отчетов**

После выполнения любой из команд вы получите:

### 📄 `TRANSLATION_REPORT.md` - читаемый отчет
### 📋 `TRANSLATION_REPORT.json` - детализированные данные

**Пример анализа отчета:**
```markdown
## ❌ Файлы с ошибками

### `core/dizhi.py`
- ⚠️ Python syntax error at line 372: invalid syntax in 'No Russian text to translate.'

### `calendar/__init__.py`  
- ⚠️ Lost Chinese characters (should be preserved): 节气
```

**Действия:**
1. Откройте `core/dizhi.py`, строка 372
2. Удалите артефакт "No Russian text to translate."
3. Откройте `calendar/__init__.py`
4. Восстановите потерянные символы 节气

---

**TransLLM Enhanced v2.0** - гибкий инструмент для любых сценариев перевода! 🎯
