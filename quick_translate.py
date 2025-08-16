#!/usr/bin/env python3
"""
Быстрый запуск перевода проектов
Простой интерфейс для project_translator.py
"""

import os
import sys
import json
import argparse
from pathlib import Path

def load_config():
    """Загружает конфигурацию из файла"""
    config_path = Path(__file__).parent / "translation_config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def get_api_key_from_env(provider: str) -> str:
    """Получает API ключ из переменных окружения"""
    env_vars = {
        "groq": "GROQ_API_KEY",
        "openai": "OPENAI_API_KEY", 
        "anthropic": "ANTHROPIC_API_KEY"
    }
    
    key = os.getenv(env_vars.get(provider, ""))
    if not key:
        print(f"⚠️  API ключ не найден в переменной окружения {env_vars.get(provider, '')}")
        print(f"Пожалуйста, установите: export {env_vars.get(provider, '')}='your-api-key'")
    return key

def main():
    config = load_config()
    default_config = config.get("default_config", {})
    
    parser = argparse.ArgumentParser(description="🚀 Быстрый переводчик проектов")
    parser.add_argument("project", help="Путь к проекту для перевода")
    parser.add_argument("-l", "--lang", default=default_config.get("target_language", "English"), 
                       help="Целевой язык (по умолчанию: English)")
    parser.add_argument("-p", "--provider", choices=["groq", "openai", "anthropic"], 
                       default=default_config.get("llm_provider", "groq"), 
                       help="LLM провайдер")
    parser.add_argument("-m", "--model", help="Модель для использования")
    parser.add_argument("-c", "--concurrent", type=int, 
                       default=default_config.get("max_concurrent_requests", 10),
                       help="Максимальное количество одновременных запросов")
    parser.add_argument("--chunk-size", type=int, 
                       default=default_config.get("chunk_size", 150),
                       help="Размер чанка в строках")
    parser.add_argument("--dry-run", action="store_true", help="Только анализ, без перевода")
    parser.add_argument("--chinese", action="store_true", help="Сохранить китайские символы")
    parser.add_argument("--formal", action="store_true", help="Формальный тон перевода")
    
    args = parser.parse_args()
    
    # Проверяем существование проекта
    if not os.path.exists(args.project):
        print(f"❌ Проект не найден: {args.project}")
        sys.exit(1)
    
    # Получаем API ключ
    api_key = get_api_key_from_env(args.provider)
    if not api_key and not args.dry_run:
        sys.exit(1)
    
    # Определяем модель
    if not args.model:
        models = config.get("llm_providers", {}).get(args.provider, {}).get("models", [])
        if models:
            args.model = models[0]
        else:
            print(f"⚠️  Модель не указана для провайдера {args.provider}")
            sys.exit(1)
    
    # Формируем дополнительные инструкции
    custom_instructions = []
    templates = config.get("custom_instructions_templates", {})
    
    if args.chinese:
        custom_instructions.append(templates.get("preserve_chinese", ""))
    if args.formal:
        custom_instructions.append(templates.get("formal_tone", ""))
    
    custom_instructions_str = " ".join(custom_instructions)
    
    print("🎯 Конфигурация перевода:")
    print(f"   Проект: {args.project}")
    print(f"   Целевой язык: {args.lang}")
    print(f"   Провайдер: {args.provider}")
    print(f"   Модель: {args.model}")
    print(f"   Размер чанка: {args.chunk_size}")
    print(f"   Одновременных запросов: {args.concurrent}")
    if custom_instructions_str:
        print(f"   Доп. инструкции: {custom_instructions_str[:100]}...")
    
    if args.dry_run:
        print("\n🔍 Запуск в режиме анализа...")
        # Здесь можно добавить предварительный анализ без API вызовов
        from project_translator import ProjectAnalyzer, TranslationConfig
        
        config_obj = TranslationConfig(
            source_project_path=args.project,
            target_language=args.lang,
            chunk_size=args.chunk_size
        )
        
        analyzer = ProjectAnalyzer(config_obj)
        project_info = analyzer.analyze_project(args.project)
        
        print(f"\n📊 Результаты анализа:")
        print(f"   Всего файлов: {project_info['total_files']}")
        print(f"   Для перевода: {project_info['translatable_files']}")
        print(f"   Ожидаемо чанков: {project_info['estimated_chunks']}")
        print(f"   Типы файлов: {project_info['file_types']}")
        
        estimated_cost_groq = project_info['estimated_chunks'] * 0.001  # Примерная цена за чанк
        print(f"\n💰 Примерная стоимость (Groq): ~${estimated_cost_groq:.2f}")
        
        return
    
    # Импортируем и запускаем основной скрипт
    try:
        import asyncio
        from project_translator import ProjectTranslator, TranslationConfig
        
        config_obj = TranslationConfig(
            source_project_path=args.project,
            target_language=args.lang,
            chunk_size=args.chunk_size,
            custom_instructions=custom_instructions_str,
            llm_provider=args.provider,
            api_key=api_key,
            model_name=args.model,
            max_concurrent_requests=args.concurrent
        )
        
        translator = ProjectTranslator(config_obj)
        asyncio.run(translator.translate_project())
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Установите необходимые зависимости:")
        if args.provider == "groq":
            print("pip install groq")
        elif args.provider == "openai":
            print("pip install openai")
        elif args.provider == "anthropic":
            print("pip install anthropic")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка выполнения: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
