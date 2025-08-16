#!/usr/bin/env python3
"""
Универсальный переводчик проектов с помощью LLM
Автоматически переводит все файлы проекта, сохраняя структуру и синтаксис
"""

import os
import shutil
import json
import asyncio
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import tempfile
import logging
from concurrent.futures import ThreadPoolExecutor
import time
import ast
import re
from collections import defaultdict

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TranslationConfig:
    """Конфигурация для перевода"""
    source_project_path: str
    target_language: str = "English"
    source_language: str = "Russian"
    chunk_size: int = 150
    preserve_patterns: List[str] = None  # Паттерны для сохранения (например, китайские символы)
    custom_instructions: str = ""
    supported_extensions: List[str] = None
    exclude_dirs: List[str] = None
    exclude_files: List[str] = None
    llm_provider: str = "groq"  # groq, openai, anthropic
    api_key: str = ""
    model_name: str = "openai/gpt-oss-120b"
    max_concurrent_requests: int = 10
    
    def __post_init__(self):
        if self.preserve_patterns is None:
            self.preserve_patterns = [
                r'[\u4e00-\u9fff]',  # Китайские символы
                r'[\u3040-\u309f]',  # Японская хирагана
                r'[\u30a0-\u30ff]',  # Японская катакана
            ]
        
        if self.supported_extensions is None:
            self.supported_extensions = [
                '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss',
                '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go',
                '.rs', '.swift', '.kt', '.dart', '.vue', '.svelte'
            ]
        
        if self.exclude_dirs is None:
            self.exclude_dirs = [
                'node_modules', '__pycache__', '.git', '.svn', '.hg',
                'venv', 'env', '.env', 'dist', 'build', '.next',
                'target', 'bin', 'obj', '.pytest_cache', '.mypy_cache'
            ]
        
        if self.exclude_files is None:
            self.exclude_files = [
                'README.md', 'LICENSE', 'CHANGELOG.md', 'requirements.txt',
                'package.json', 'package-lock.json', 'yarn.lock',
                '.gitignore', '.dockerignore', 'Dockerfile'
            ]


class ProjectAnalyzer:
    """Анализатор структуры проекта"""
    
    def __init__(self, config: TranslationConfig):
        self.config = config
        
    def analyze_project(self, project_path: str) -> Dict:
        """Анализирует структуру проекта"""
        project_info = {
            'total_files': 0,
            'translatable_files': 0,
            'file_types': {},
            'directory_structure': {},
            'estimated_chunks': 0,
            'files_to_translate': []
        }
        
        for root, dirs, files in os.walk(project_path):
            # Исключаем ненужные директории
            dirs[:] = [d for d in dirs if d not in self.config.exclude_dirs]
            
            for file in files:
                project_info['total_files'] += 1
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, project_path)
                
                # Проверяем расширение файла
                _, ext = os.path.splitext(file)
                if ext in self.config.supported_extensions and file not in self.config.exclude_files:
                    project_info['translatable_files'] += 1
                    project_info['file_types'][ext] = project_info['file_types'].get(ext, 0) + 1
                    
                    # Считаем количество строк для оценки чанков
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = sum(1 for _ in f)
                            chunks = (lines // self.config.chunk_size) + 1
                            project_info['estimated_chunks'] += chunks
                            
                            project_info['files_to_translate'].append({
                                'path': relative_path,
                                'full_path': file_path,
                                'extension': ext,
                                'lines': lines,
                                'estimated_chunks': chunks
                            })
                    except Exception as e:
                        logger.warning(f"Не удалось проанализировать файл {file_path}: {e}")
        
        return project_info


class FileChunker:
    """Разбивает файлы на чанки для перевода"""
    
    def __init__(self, config: TranslationConfig):
        self.config = config
        
    def split_file(self, file_path: str, output_dir: str) -> List[str]:
        """Разбивает файл на чанки с добавлением маркеров границ"""
        chunks = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Создаем чанки
            for i in range(0, len(lines), self.config.chunk_size):
                chunk_lines = lines[i:i + self.config.chunk_size]
                chunk_index = i // self.config.chunk_size
                
                # Добавляем маркер начала чанка (кроме первого)
                if i > 0:
                    chunk_content = f"---CHUNK_START_{chunk_index:04d}---\n" + ''.join(chunk_lines)
                else:
                    chunk_content = ''.join(chunk_lines)
                
                # Добавляем маркер окончания чанка (кроме последнего)
                if i + self.config.chunk_size < len(lines):
                    chunk_content += f"---CHUNK_END_{chunk_index:04d}---\n"
                
                # Создаем имя файла чанка используя относительный путь от проекта
                relative_path = os.path.relpath(file_path, self.config.source_project_path)
                safe_name = relative_path.replace(os.sep, '_').replace('.', '_')
                chunk_filename = f"{safe_name}_chunk_{chunk_index:04d}.txt"
                chunk_path = os.path.join(output_dir, chunk_filename)
                
                # Сохраняем чанк с метаинформацией
                chunk_data = {
                    'original_file': file_path,
                    'chunk_index': chunk_index,
                    'start_line': i,
                    'end_line': min(i + self.config.chunk_size, len(lines)),
                    'content': chunk_content,
                    'has_start_marker': i > 0,
                    'has_end_marker': i + self.config.chunk_size < len(lines)
                }
                
                with open(chunk_path, 'w', encoding='utf-8') as chunk_file:
                    json.dump(chunk_data, chunk_file, ensure_ascii=False, indent=2)
                
                chunks.append(chunk_path)
                
        except Exception as e:
            logger.error(f"Ошибка разбиения файла {file_path}: {e}")
            
        return chunks


class LLMTranslator:
    """Переводчик с использованием различных LLM провайдеров"""
    
    def __init__(self, config: TranslationConfig):
        self.config = config
        self.session = None
        
    async def setup_client(self):
        """Настраивает клиента для выбранного провайдера"""
        if self.config.llm_provider == "groq":
            try:
                from groq import AsyncGroq
                self.client = AsyncGroq(api_key=self.config.api_key)
            except ImportError:
                raise ImportError("Установите groq: pip install groq")
                
        elif self.config.llm_provider == "openai":
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=self.config.api_key)
            except ImportError:
                raise ImportError("Установите openai: pip install openai")
                
        elif self.config.llm_provider == "anthropic":
            try:
                import anthropic
                self.client = anthropic.AsyncAnthropic(api_key=self.config.api_key)
            except ImportError:
                raise ImportError("Установите anthropic: pip install anthropic")
        else:
            raise ValueError(f"Неподдерживаемый провайдер: {self.config.llm_provider}")
    
    def create_system_prompt(self) -> str:
        """Создает системный промпт для перевода с встроенными системными инструкциями"""
        
        # Встроенные системные инструкции (неизменные) - УЛУЧШЕННАЯ ВЕРСИЯ v2.2
        system_instructions = """
=== ULTRA-STRICT CODE TRANSLATION PROTOCOL v2.3 ===
You are a PRECISION code translator with ZERO tolerance for deviations.
Mission: Translate {source_lang} natural language to {target_lang} with ABSOLUTE preservation of code structure.

=== ABSOLUTE REQUIREMENTS (VIOLATION = COMPLETE FAILURE) ===
1. PRESERVE LINE STRUCTURE: Maintain similar line count (minor deviations acceptable for readability)
2. EXACT PRESERVATION: indentation, whitespace, ALL brackets (), [], {{}}, semicolons, commas
3. CAREFUL PRESERVATION: blank lines, empty lines, line breaks (maintain logical spacing)
4. EXACT PRESERVATION: special characters, operators, punctuation marks
5. EXACT PRESERVATION: ALL triple quotes \"\"\" and ''' for docstrings - NEVER REMOVE THEM
6. OUTPUT RESTRICTION: ONLY translated code - ZERO additional content whatsoever
7. ABSOLUTELY FORBIDDEN: any explanatory text, meta-comments, process descriptions

=== TRANSLATION SCOPE - TRANSLATE ONLY THESE ===
• User-facing comments: # comment, // comment, /* comment */, <!-- comment -->
• Documentation strings: \"\"\"docstring\"\"\", '''docstring''', /** docstring */
• User interface text strings with natural language content
• Error/log/notification messages meant for end users
• Descriptive string literals (NOT technical identifiers or constants)

=== ABSOLUTE TRANSLATION EXCLUSIONS - NEVER TRANSLATE ===
• ALL programming syntax: keywords, operators, control structures  
• ALL identifiers: variables, functions, classes, methods, modules
• ALL technical constants: paths, URLs, endpoints, database queries
• Import statements, module references, package names
• Regular expressions, SQL, JSON keys, XML attributes, configuration
• Version numbers, timestamps, hashes, UUIDs, technical IDs
• Mathematical formulas, algorithms, data structures
• Chunk boundary markers: ---CHUNK_START_XXXX---, ---CHUNK_END_XXXX---
• Programming language constructs and patterns
• Args:, Returns:, Raises:, Parameters:, Note:, Warning: in docstrings
• String constants used by program logic ("strong", "weak", "active", etc.)
• Enumeration values, status codes, technical classifications

=== SPECIAL CHARACTER PRESERVATION ===
• Preserve ALL characters matching patterns specified in PROJECT-SPECIFIC INSTRUCTIONS
• When uncertain about special characters → PRESERVE exactly as provided
• Mathematical symbols [\u2200-\u22FF], Technical symbols [\u2300-\u23FF]
• Any CJK characters [\u4E00-\u9FFF], [\u3040-\u309F], [\u30A0-\u30FF], [\uAC00-\uD7AF]
• Follow project-specific preservation rules from custom instructions

=== META-COMMENT BAN - ABSOLUTELY FORBIDDEN ===
🚫 NEVER add ANY of these phrases:
• "No changes needed"
• "Already in [language]"
• "Only [something] was translated"
• "Most text is already"
• "Translation complete"
• "Code remains the same"
• ANY explanatory comments about the translation process
• ANY meta-commentary whatsoever

=== FLEXIBLE LINE COUNT CONTROL ===
📏 INPUT has N lines → OUTPUT should have SIMILAR line count (minor variations acceptable):
• Maintain logical structure and readability
• Avoid excessive line additions or removals
• Preserve meaningful empty lines and spacing
• Minor adjustments for readability are acceptable
• Focus on preserving code structure over exact line matching

=== FORMATTING PROTOCOL - ZERO TOLERANCE ===
• FORBIDDEN: markdown blocks (```), HTML tags, any markup
• FORBIDDEN: "Translation:", "Result:", "Output:", explanations
• FORBIDDEN: process commentary, status updates, notes
• REQUIRED: identical visual structure and formatting
• REQUIRED: preserve tabs vs spaces exactly as original
• REQUIRED: same line endings, character encoding

=== PRE-OUTPUT VERIFICATION CHECKLIST ===
Before returning result, VERIFY:
✅ Line count: input lines = output lines (count manually)
✅ Structure: all (), [], {{}} brackets match exactly  
✅ Whitespace: indentation, spacing identical
✅ Special chars: follow project-specific preservation rules
✅ No meta-comments: zero explanatory text added
✅ Only user comments/strings translated
✅ Technical terms, constants, identifiers unchanged
✅ Code logic and flow completely preserved

=== ERROR HANDLING ===
• Uncertain about translation? → PRESERVE original
• Line count might change? → PRESERVE original
• Structure might break? → PRESERVE original
• Special characters detected? → Follow project rules or PRESERVE exactly
• Technical term unclear? → PRESERVE unchanged

=== FINAL OUTPUT REQUIREMENTS ===
Return EXCLUSIVELY:
• The translated code with same structure
• Same encoding, line endings as input
• Zero additional content
• Zero metadata or comments
• Zero explanatory text

🔥 CRITICAL: Any violation of these rules = COMPLETE FAILURE
💀 Adding meta-comments = IMMEDIATE FAILURE
⚡ Wrong line count = IMMEDIATE FAILURE
🚨 Ignoring project-specific preservation rules = IMMEDIATE FAILURE
        """
        
        # Добавляем пользовательские инструкции если есть
        if self.config.custom_instructions:
            system_instructions += "\n\n=== PROJECT-SPECIFIC INSTRUCTIONS ===\n" + self.config.custom_instructions
        
        return system_instructions

    def create_user_prompt(self, content: str) -> str:
        """Создает пользовательский промпт"""
        line_count = len(content.splitlines())
        return f"""INPUT ({line_count} lines):
{content}

OUTPUT ({line_count} lines required - translate {self.config.source_language} to {self.config.target_language}):"""

    async def translate_chunk(self, chunk_content: str) -> str:
        """Переводит один чанк кода"""
        try:
            if self.config.llm_provider == "groq":
                response = await self.client.chat.completions.create(
                    model=self.config.model_name,
                    messages=[
                        {"role": "system", "content": self.create_system_prompt()},
                        {"role": "user", "content": self.create_user_prompt(chunk_content)}
                    ],
                    temperature=0.0,  # Максимальная детерминированность (снижено)
                    max_tokens=4096
                )
                return response.choices[0].message.content.strip()
                
            elif self.config.llm_provider == "openai":
                response = await self.client.chat.completions.create(
                    model=self.config.model_name,
                    messages=[
                        {"role": "system", "content": self.create_system_prompt()},
                        {"role": "user", "content": self.create_user_prompt(chunk_content)}
                    ],
                    temperature=0.0,  # Максимальная детерминированность (снижено)
                    max_tokens=4096
                )
                return response.choices[0].message.content.strip()
                
        except Exception as e:
            logger.error(f"Ошибка перевода чанка: {e}")
            return chunk_content  # Возвращаем оригинал при ошибке


class ChunkMerger:
    """Объединяет переведенные чанки обратно в файлы"""
    
    def merge_chunks(self, chunks_dir: str, output_file: str, source_project_path: str) -> bool:
        """Объединяет чанки в исходный файл с использованием маркеров границ для точного слияния"""
        try:
            # Получаем относительный путь файла от корня проекта
            project_root = os.path.basename(source_project_path)
            
            # Извлекаем относительный путь из output_file
            if '_translated' in output_file:
                rel_output_path = output_file.split('_translated' + os.sep, 1)[1] if os.sep + '_translated' + os.sep in output_file else output_file.split('_translated/', 1)[1]
            else:
                rel_output_path = os.path.basename(output_file)
            
            # Создаем безопасное имя файла для поиска чанков (как в split_file)
            safe_name = rel_output_path.replace(os.sep, '_').replace('.', '_')
            
            # Ищем все чанки с этим именем
            chunk_files = []
            for chunk_file in os.listdir(chunks_dir):
                if chunk_file.startswith(safe_name + '_chunk_') and chunk_file.endswith('.txt'):
                    chunk_path = os.path.join(chunks_dir, chunk_file)
                    try:
                        with open(chunk_path, 'r', encoding='utf-8') as f:
                            chunk_data = json.load(f)
                        chunk_files.append((chunk_path, chunk_data['chunk_index'], chunk_data))
                    except Exception as e:
                        logger.warning(f"Не удалось прочитать чанк {chunk_path}: {e}")
                        
            if not chunk_files:
                logger.error(f"Не найдены чанки для файла {output_file}, искали по имени: {safe_name}")
                return False
            
            # Сортируем по индексу чанка
            chunk_files.sort(key=lambda x: x[1])
            
            # Объединяем чанки с использованием маркеров
            merged_lines = []
            
            for i, (chunk_path, chunk_index, chunk_data) in enumerate(chunk_files):
                chunk_content = chunk_data['content']
                
                # Удаляем маркеры границ, но используем их для точного слияния
                cleaned_content = self.remove_boundary_markers(chunk_content)
                
                # Для первого чанка добавляем контент как есть
                if i == 0:
                    merged_lines.append(cleaned_content)
                else:
                    # Для последующих чанков объединяем без разрывов
                    if merged_lines and merged_lines[-1] and not merged_lines[-1].endswith('\n'):
                        merged_lines[-1] += '\n'  # Добавляем разрыв если его нет
                    merged_lines.append(cleaned_content)
            
            # Записываем объединенный файл
            merged_content = ''.join(merged_lines)
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(merged_content)
            
            # Проверяем результат объединения
            original_file_path = chunk_files[0][2].get('original_file') if chunk_files else None
            if original_file_path and os.path.exists(original_file_path):
                try:
                    with open(original_file_path, 'r', encoding='utf-8') as f:
                        original_lines = f.readlines()
                    
                    merged_file_lines = merged_content.splitlines(keepends=True)
                    if len(original_lines) != len(merged_file_lines):
                        logger.warning(f"Количество строк в объединенном файле не совпадает с оригиналом: {len(original_lines)} -> {len(merged_file_lines)}")
                except Exception as e:
                    logger.warning(f"Не удалось проверить результат объединения: {e}")
            
            logger.debug(f"Объединено {len(chunk_files)} чанков для файла {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка объединения чанков для {output_file}: {e}")
            return False
    
    def remove_boundary_markers(self, content: str) -> str:
        """Удаляет маркеры границ из содержимого чанка"""
        import re
        
        # Удаляем маркеры начала и конца чанков (куда бы они не попали)
        content = re.sub(r'---CHUNK_START_\d+---\n?', '', content)
        content = re.sub(r'---CHUNK_END_\d+---\n?', '', content)
        
        return content


class ProjectTranslator:
    """Главный класс для перевода проекта"""
    
    def __init__(self, config: TranslationConfig):
        self.config = config
        self.analyzer = ProjectAnalyzer(config)
        self.chunker = FileChunker(config)
        self.translator = LLMTranslator(config)
        self.merger = ChunkMerger()
        
    async def translate_project(self):
        """Переводит весь проект"""
        logger.info("🚀 Начинаем перевод проекта...")
        
        # 1. Анализируем проект
        logger.info("📊 Анализируем структуру проекта...")
        project_info = self.analyzer.analyze_project(self.config.source_project_path)
        
        logger.info(f"Найдено файлов: {project_info['total_files']}")
        logger.info(f"Файлов для перевода: {project_info['translatable_files']}")
        logger.info(f"Ожидаемое количество чанков: {project_info['estimated_chunks']}")
        
        # 2. Создаем рабочие директории
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = os.path.join(temp_dir, "backup")
            chunks_dir = os.path.join(temp_dir, "chunks")
            translated_chunks_dir = os.path.join(temp_dir, "translated_chunks")
            
            # 3. Создаем резервную копию
            logger.info("💾 Создаем резервную копию проекта...")
            shutil.copytree(self.config.source_project_path, backup_dir)
            
            # 4. Разбиваем файлы на чанки
            logger.info("✂️ Разбиваем файлы на чанки...")
            os.makedirs(chunks_dir, exist_ok=True)
            all_chunks = []
            
            for file_info in project_info['files_to_translate']:
                chunks = self.chunker.split_file(file_info['full_path'], chunks_dir)
                all_chunks.extend(chunks)
            
            logger.info(f"Создано {len(all_chunks)} чанков")
            
            # 5. Настраиваем переводчика
            logger.info("🤖 Настраиваем LLM переводчика...")
            await self.translator.setup_client()
            
            # 6. Переводим чанки
            logger.info("🌐 Начинаем перевод чанков...")
            os.makedirs(translated_chunks_dir, exist_ok=True)
            
            semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
            tasks = []
            
            for chunk_path in all_chunks:
                task = self.translate_chunk_with_semaphore(semaphore, chunk_path, translated_chunks_dir)
                tasks.append(task)
            
            # Выполняем перевод с ограничением на количество одновременных запросов
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            successful_translations = sum(1 for r in results if r is True)
            logger.info(f"Переведено {successful_translations}/{len(all_chunks)} чанков за {end_time - start_time:.2f} сек")
            
            # 7. Объединяем переведенные чанки
            logger.info("🔗 Объединяем переведенные чанки...")
            output_project_dir = f"{self.config.source_project_path}_translated"
            
            # Воссоздаем структуру проекта
            merge_successful = 0
            validation_errors = []
            detailed_validation_results = {}
            
            for file_info in project_info['files_to_translate']:
                relative_path = file_info['path']
                output_file = os.path.join(output_project_dir, relative_path)
                if self.merger.merge_chunks(translated_chunks_dir, output_file, self.config.source_project_path):
                    # Проверяем целостность объединенного файла
                    validation_result = self.validate_merged_file(file_info['full_path'], output_file)
                    detailed_validation_results[relative_path] = validation_result
                    
                    if validation_result['valid']:
                        merge_successful += 1
                    else:
                        validation_errors.append(f"{relative_path}: {validation_result['error']}")
                else:
                    detailed_validation_results[relative_path] = {
                        'valid': False,
                        'errors': ['Failed to merge chunks'],
                        'error': 'Failed to merge chunks'
                    }
            
            logger.info(f"Успешно объединено {merge_successful}/{len(project_info['files_to_translate'])} файлов")
            if validation_errors:
                logger.warning(f"Ошибки валидации файлов: {len(validation_errors)}")
                for error in validation_errors[:5]:  # Показываем первые 5 ошибок
                    logger.warning(f"  • {error}")
            
            # 8. Копируем нетранслируемые файлы
            logger.info("📁 Копируем остальные файлы...")
            for root, dirs, files in os.walk(backup_dir):
                # Исключаем ненужные директории
                dirs[:] = [d for d in dirs if d not in self.config.exclude_dirs]
                
                for file in files:
                    src_path = os.path.join(root, file)
                    rel_path = os.path.relpath(src_path, backup_dir)
                    dst_path = os.path.join(output_project_dir, rel_path)
                    
                    # Проверяем, нужно ли копировать файл
                    _, ext = os.path.splitext(file)
                    if ext not in self.config.supported_extensions or file in self.config.exclude_files:
                        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                        shutil.copy2(src_path, dst_path)
            
            logger.info(f"✅ Перевод завершен! Результат сохранен в: {output_project_dir}")
            
            # 9. Создаем расширенный отчет
            self.create_translation_report(
                project_info, 
                output_project_dir, 
                successful_translations, 
                len(all_chunks),
                detailed_validation_results
            )
    
    async def translate_chunk_with_semaphore(self, semaphore: asyncio.Semaphore, chunk_path: str, output_dir: str):
        """Переводит чанк с ограничением по количеству одновременных запросов"""
        async with semaphore:
            try:
                # Читаем чанк
                with open(chunk_path, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)
                
                # Переводим содержимое
                translated_content = await self.translator.translate_chunk(chunk_data['content'])
                
                # Очищаем от markdown кодовых блоков если они есть
                translated_content = self.clean_markdown_blocks(translated_content)
                
                # Валидируем перевод для сохранения структуры
                translated_content = self.validate_translation(chunk_data['content'], translated_content)
                
                # Обновляем данные чанка
                chunk_data['content'] = translated_content
                
                # Сохраняем переведенный чанк
                output_path = os.path.join(output_dir, os.path.basename(chunk_path))
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(chunk_data, f, ensure_ascii=False, indent=2)
                
                return True
                
            except Exception as e:
                logger.error(f"Ошибка перевода чанка {chunk_path}: {e}")
                return False
    
    def clean_markdown_blocks(self, content: str) -> str:
        """Очищает контент от markdown кодовых блоков"""
        import re
        
        # Убираем markdown кодовые блоки в начале и конце
        content = re.sub(r'^\s*```[\w]*\s*\n', '', content)
        content = re.sub(r'\n\s*```\s*$', '', content)
        
        return content
    
    def validate_translation(self, original_content: str, translated_content: str) -> str:
        """Проверяет и исправляет перевод, чтобы сохранить структуру"""
        original_lines = original_content.splitlines()
        translated_lines = translated_content.splitlines()
        
        # Проверяем количество строк (более мягкий подход)
        if len(original_lines) != len(translated_lines):
            line_diff = abs(len(original_lines) - len(translated_lines))
            logger.warning(f"Количество строк не совпадает: {len(original_lines)} -> {len(translated_lines)}")
            # Только для критических изменений возвращаем оригинал
            if line_diff > max(10, len(original_lines) * 0.15):  # Больше 15% от общего количества или 10 строк
                logger.error("Перевод сильно искажен, возвращаем оригинал")
                return original_content
        
        # Проверяем первую и последнюю строку - они должны иметь такую же структуру
        if len(original_lines) > 0 and len(translated_lines) > 0:
            # Проверяем первую строку
            orig_first = original_lines[0].strip()
            trans_first = translated_lines[0].strip()
            if orig_first and not orig_first.startswith('//') and not orig_first.startswith('#'):
                # Если первая строка - это код, она должна сохраниться
                if len(orig_first.split()) > 0 and len(trans_first.split()) > 0:
                    orig_tokens = orig_first.replace('{', '').replace('}', '').replace('(', '').replace(')', '').split()
                    trans_tokens = trans_first.replace('{', '').replace('}', '').replace('(', '').replace(')', '').split()
                    if len(orig_tokens) > 0 and orig_tokens[0] != trans_tokens[0] if trans_tokens else True:
                        logger.warning("Первая строка изменена, восстанавливаем")
                        translated_lines[0] = original_lines[0]
        
        return '\n'.join(translated_lines)
    
    def validate_merged_file(self, original_file_path: str, merged_file_path: str) -> Dict:
        """Расширенная проверка целостности объединенного файла"""
        try:
            # Читаем файлы
            with open(original_file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
                original_lines = original_content.splitlines()
            
            with open(merged_file_path, 'r', encoding='utf-8') as f:
                merged_content = f.read()
                merged_lines = merged_content.splitlines()
            
            errors = []
            
            # 1. Проверяем количество строк
            if len(original_lines) != len(merged_lines):
                errors.append(f'Line count mismatch: {len(original_lines)} vs {len(merged_lines)}')
            
            # 2. Проверяем синтаксис Python (если это Python файл)
            if original_file_path.endswith('.py'):
                syntax_errors = self.validate_python_syntax(merged_content, merged_file_path)
                if syntax_errors:
                    errors.extend(syntax_errors)
            
            # 3. Проверяем структуру кода
            original_structure = self.extract_structure(original_lines)
            merged_structure = self.extract_structure(merged_lines)
            
            if original_structure != merged_structure:
                structure_diff = self.find_structure_differences(original_lines, merged_lines)
                errors.append(f'Code structure changed: {structure_diff}')
            
            # 4. Проверяем сохранение китайских символов
            chinese_validation = self.validate_chinese_characters(original_content, merged_content)
            if not chinese_validation['valid']:
                errors.extend(chinese_validation['errors'])
            
            # 5. Проверяем отступы
            indentation_errors = self.validate_indentation(original_lines, merged_lines)
            if indentation_errors:
                errors.extend(indentation_errors)
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'error': '; '.join(errors) if errors else None
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f'Validation exception: {e}'],
                'error': f'Validation error: {e}'
            }
    
    def extract_structure(self, lines: List[str]) -> str:
        """Извлекает структурные элементы кода для сравнения"""
        structure_elements = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#') or stripped.startswith('//'):
                continue  # Пропускаем пустые строки и комментарии
            
            # Извлекаем значимые структурные элементы
            structure_line = ''
            for char in stripped:
                if char in '{}()[];,=+-*/<>!&|':
                    structure_line += char
                elif char.isalnum() or char == '_':
                    # Сохраняем первый символ идентификаторов
                    if not structure_line or not structure_line[-1].isalnum():
                        structure_line += char
                elif char in ' \t':
                    if structure_line and not structure_line[-1] == ' ':
                        structure_line += ' '
            
            if structure_line:
                structure_elements.append(structure_line.strip())
        
        return '\n'.join(structure_elements)
    
    def validate_python_syntax(self, content: str, file_path: str) -> List[str]:
        """Проверяет синтаксис Python файла"""
        errors = []
        try:
            ast.parse(content)
        except SyntaxError as e:
            error_msg = f"Python syntax error at line {e.lineno}: {e.msg}"
            if hasattr(e, 'text') and e.text:
                error_msg += f" in '{e.text.strip()}'"
            errors.append(error_msg)
        except Exception as e:
            errors.append(f"Python parsing error: {e}")
        
        return errors
    
    def validate_chinese_characters(self, original: str, translated: str) -> Dict:
        """Проверяет изменения китайских символов (настраивается через custom_instructions)"""
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
        
        original_chinese = set(chinese_pattern.findall(original))
        translated_chinese = set(chinese_pattern.findall(translated))
        
        errors = []
        
        # Проверяем только если включена проверка сохранения китайских символов
        preserve_chinese = 'PRESERVE_CHINESE_CHARACTERS' in self.config.custom_instructions
        translate_chinese = 'TRANSLATE_CHINESE_CHARACTERS' in self.config.custom_instructions
        
        if preserve_chinese:
            # Режим сохранения: китайские символы должны остаться
            lost_chars = original_chinese - translated_chinese
            if lost_chars:
                errors.append(f"Lost Chinese characters (should be preserved): {''.join(sorted(lost_chars))}")
            
            new_chars = translated_chinese - original_chinese
            if new_chars:
                errors.append(f"New Chinese characters appeared: {''.join(sorted(new_chars))}")
                
        elif translate_chinese:
            # Режим перевода: китайские символы должны исчезнуть (переведены)
            remaining_chars = translated_chinese & original_chinese  # Пересечение
            if remaining_chars:
                errors.append(f"Chinese characters not translated: {''.join(sorted(remaining_chars))}")
        
        # Если ни один режим не указан, пропускаем проверку
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def validate_indentation(self, original_lines: List[str], translated_lines: List[str]) -> List[str]:
        """Проверяет правильность отступов"""
        errors = []
        
        if len(original_lines) != len(translated_lines):
            return errors  # Уже проверено в другом месте
        
        for i, (orig_line, trans_line) in enumerate(zip(original_lines, translated_lines), 1):
            # Извлекаем отступы (пробелы и табы в начале строки)
            orig_indent = len(orig_line) - len(orig_line.lstrip())
            trans_indent = len(trans_line) - len(trans_line.lstrip())
            
            if orig_indent != trans_indent:
                errors.append(f"Indentation mismatch at line {i}: {orig_indent} vs {trans_indent} spaces")
        
        return errors
    
    def find_structure_differences(self, original_lines: List[str], translated_lines: List[str]) -> str:
        """Находит конкретные различия в структуре"""
        orig_brackets = self.count_brackets(original_lines)
        trans_brackets = self.count_brackets(translated_lines)
        
        differences = []
        for bracket_type, orig_count in orig_brackets.items():
            trans_count = trans_brackets.get(bracket_type, 0)
            if orig_count != trans_count:
                differences.append(f"{bracket_type}: {orig_count}->{trans_count}")
        
        return "; ".join(differences) if differences else "unknown structural change"
    
    def count_brackets(self, lines: List[str]) -> Dict[str, int]:
        """Подсчитывает количество скобок разных типов"""
        brackets = defaultdict(int)
        
        for line in lines:
            # Пропускаем строки-комментарии и строки
            in_string = False
            in_comment = False
            
            for i, char in enumerate(line):
                # Обработка строк
                if char in ['"', "'"] and (i == 0 or line[i-1] != '\\'):
                    in_string = not in_string
                    continue
                
                # Обработка комментариев
                if not in_string and char == '#':
                    in_comment = True
                    break
                
                if not in_string and not in_comment:
                    if char in '()[]{}':  
                        brackets[char] += 1
        
        return dict(brackets)
    
    def create_translation_report(self, project_info: Dict, output_dir: str, successful: int, total: int, validation_results: Dict = None):
        """Создает расширенный отчет о переводе с детальной информацией об ошибках"""
        
        # Анализируем результаты валидации
        validation_summary = {
            'total_files_validated': 0,
            'files_with_errors': 0,
            'common_error_types': defaultdict(int),
            'files_by_status': {'valid': [], 'invalid': []}
        }
        
        if validation_results:
            validation_summary['total_files_validated'] = len(validation_results)
            
            for file_path, result in validation_results.items():
                if result['valid']:
                    validation_summary['files_by_status']['valid'].append(file_path)
                else:
                    validation_summary['files_by_status']['invalid'].append(file_path)
                    validation_summary['files_with_errors'] += 1
                    
                    # Анализируем типы ошибок
                    if 'errors' in result:
                        for error in result['errors']:
                            if 'Line count mismatch' in error:
                                validation_summary['common_error_types']['line_count_mismatch'] += 1
                            elif 'Python syntax error' in error:
                                validation_summary['common_error_types']['python_syntax_error'] += 1
                            elif 'Code structure changed' in error:
                                validation_summary['common_error_types']['structure_change'] += 1
                            elif 'Chinese characters' in error:
                                validation_summary['common_error_types']['chinese_characters'] += 1
                            elif 'Indentation mismatch' in error:
                                validation_summary['common_error_types']['indentation_error'] += 1
                            else:
                                validation_summary['common_error_types']['other'] += 1
        
        report = {
            "translation_summary": {
                "source_project": self.config.source_project_path,
                "target_language": self.config.target_language,
                "total_files": project_info['total_files'],
                "translatable_files": project_info['translatable_files'],
                "total_chunks": total,
                "successful_chunks": successful,
                "success_rate": f"{(successful/total)*100:.2f}%" if total > 0 else "0%",
                "file_types": project_info['file_types']
            },
            "validation_summary": validation_summary,
            "detailed_validation_results": validation_results or {},
            "config_used": {
                "llm_provider": self.config.llm_provider,
                "model_name": self.config.model_name,
                "chunk_size": self.config.chunk_size,
                "temperature": "0.0 (снижено для максимальной детерминированности)",
                "preserve_patterns": self.config.preserve_patterns,
                "max_concurrent_requests": self.config.max_concurrent_requests
            },
            "recommendations": self.generate_recommendations(validation_summary)
        }
        
        # Сохраняем JSON отчет
        report_path = os.path.join(output_dir, "TRANSLATION_REPORT.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Создаем читаемый Markdown отчет
        md_report_path = os.path.join(output_dir, "TRANSLATION_REPORT.md")
        self.create_markdown_report(report, md_report_path)
        
        logger.info(f"📊 Отчеты сохранены: {report_path} и {md_report_path}")
    
    def generate_recommendations(self, validation_summary: Dict) -> List[str]:
        """Генерирует рекомендации на основе результатов валидации"""
        recommendations = []
        
        if validation_summary['files_with_errors'] == 0:
            recommendations.append("✅ Перевод выполнен идеально! Все файлы прошли валидацию.")
        else:
            error_types = validation_summary['common_error_types']
            
            if error_types.get('line_count_mismatch', 0) > 0:
                recommendations.append("⚠️ Обнаружены расхождения в количестве строк. Рекомендуется проверить системный промпт на строгость требований.")
            
            if error_types.get('python_syntax_error', 0) > 0:
                recommendations.append("🐍 Найдены синтаксические ошибки Python. Рекомендуется запустить проверку синтаксиса на всех .py файлах.")
            
            if error_types.get('structure_change', 0) > 0:
                recommendations.append("🏗️ Изменения в структуре кода. Возможно, нужно усилить промпт о сохранении скобок и операторов.")
            
            if error_types.get('chinese_characters', 0) > 0:
                recommendations.append("🇨🇳 Проблемы с китайскими символами. Проверьте паттерны сохранения в конфигурации.")
            
            if error_types.get('indentation_error', 0) > 0:
                recommendations.append("📏 Ошибки отступов. Рекомендуется проверить файлы Python на корректность форматирования.")
        
        return recommendations
    
    def create_markdown_report(self, report_data: Dict, output_path: str):
        """Создает читаемый Markdown отчет"""
        md_content = f"""# 📊 Отчет о переводе проекта

## 🎯 Сводка перевода

- **Исходный проект:** `{report_data['translation_summary']['source_project']}`
- **Целевой язык:** {report_data['translation_summary']['target_language']}
- **Всего файлов:** {report_data['translation_summary']['total_files']}
- **Файлов для перевода:** {report_data['translation_summary']['translatable_files']}
- **Чанков переведено:** {report_data['translation_summary']['successful_chunks']}/{report_data['translation_summary']['total_chunks']}
- **Успешность:** {report_data['translation_summary']['success_rate']}

## 🔍 Результаты валидации

- **Всего проверено файлов:** {report_data['validation_summary']['total_files_validated']}
- **Файлов с ошибками:** {report_data['validation_summary']['files_with_errors']}
- **Файлов без ошибок:** {len(report_data['validation_summary']['files_by_status']['valid'])}

### Типы ошибок:

"""
        
        for error_type, count in report_data['validation_summary']['common_error_types'].items():
            error_name = {
                'line_count_mismatch': '📏 Несоответствие количества строк',
                'python_syntax_error': '🐍 Синтаксические ошибки Python',
                'structure_change': '🏗️ Изменения структуры кода',
                'chinese_characters': '🇨🇳 Проблемы с китайскими символами',
                'indentation_error': '📐 Ошибки отступов',
                'other': '❓ Прочие ошибки'
            }.get(error_type, error_type)
            
            md_content += f"- {error_name}: {count}\n"
        
        md_content += f"""

## ⚙️ Конфигурация перевода

- **LLM провайдер:** {report_data['config_used']['llm_provider']}
- **Модель:** {report_data['config_used']['model_name']}
- **Размер чанка:** {report_data['config_used']['chunk_size']} строк
- **Температура:** {report_data['config_used']['temperature']}
- **Максимум запросов:** {report_data['config_used']['max_concurrent_requests']}

## 💡 Рекомендации

"""
        
        for rec in report_data['recommendations']:
            md_content += f"- {rec}\n"
        
        if report_data['validation_summary']['files_with_errors'] > 0:
            md_content += f"""

## ❌ Файлы с ошибками

"""
            
            for file_path in report_data['validation_summary']['files_by_status']['invalid'][:10]:  # Показываем первые 10
                validation_result = report_data['detailed_validation_results'].get(file_path, {})
                md_content += f"### `{file_path}`\n"
                if 'errors' in validation_result:
                    for error in validation_result['errors']:
                        md_content += f"- ⚠️ {error}\n"
                md_content += "\n"
        
        md_content += f"""

---
**Дата создания отчета:** {time.strftime('%Y-%m-%d %H:%M:%S')}  
**Переводчик:** TransLLM Enhanced v2.0
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)


def load_static_config() -> dict:
    """Загружает статическую конфигурацию из папки TransLLM"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_data = {}
    
    # Загружаем основную конфигурацию из config.json
    config_file = os.path.join(script_dir, "config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            logger.info(f"📋 Загружена статическая конфигурация из {config_file}")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки конфигурации: {e}")
            return {}
    else:
        logger.error(f"❌ Файл конфигурации не найден: {config_file}")
        return {}
    
    # Загружаем пользовательские правила из user_rules.md
    user_rules_file = os.path.join(script_dir, "user_rules.md")
    if os.path.exists(user_rules_file):
        try:
            with open(user_rules_file, 'r', encoding='utf-8') as f:
                user_instructions = f.read().strip()
                config_data['user_instructions'] = user_instructions
            logger.info(f"👤 Загружены пользовательские правила из {user_rules_file}")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка загрузки пользовательских правил: {e}")
    
    return config_data

def create_default_config_files(project_path: str):
    """Создает файлы конфигурации по умолчанию если их нет"""
    config_file = os.path.join(project_path, "translllm_config.json")
    sys_rules_file = os.path.join(project_path, "sys_rules.md")
    user_rules_file = os.path.join(project_path, "user_rules.md")
    
    # Создаем config.json если его нет
    if not os.path.exists(config_file):
        default_config = {
            "llm_provider": "groq",
            "model_name": "openai/gpt-oss-120b",
            "api_key": "YOUR_API_KEY_HERE",
            "target_language": "Russian",
            "source_language": "English",
            "chunk_size": 150,
            "temperature": 0.0,
            "max_concurrent_requests": 10,
            "supported_extensions": [".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".java", ".cpp", ".c", ".h", ".cs", ".php", ".rb", ".go", ".rs", ".swift", ".kt"],
            "exclude_dirs": ["node_modules", "__pycache__", ".git", "venv", "env", "dist", "build"],
            "exclude_files": ["README.md", "LICENSE", "package.json", ".gitignore"]
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        logger.info(f"📄 Создан файл конфигурации: {config_file}")
    
    # Создаем sys_rules.md если его нет
    if not os.path.exists(sys_rules_file):
        default_sys_rules = """# 🤖 Системные правила перевода

## Базовые требования
- INPUT LINE COUNT = OUTPUT LINE COUNT (ОБЯЗАТЕЛЬНО)
- Сохранять ТОЧНО: отступы, пробелы, скобки, точки с запятой, запятые
- Сохранять ТОЧНО: пустые строки, переносы строк
- НЕ добавлять дополнительный текст, объяснения, комментарии, markdown
- Возвращать ТОЛЬКО переведенный код

## Что переводить
- Комментарии: # комментарий, // комментарий, /* комментарий */
- Docstrings: \"\"\"текст\"\"\", '''текст'''
- Строки с естественным языком (не технические строки)
- Сообщения для пользователей и ошибки

## Что НЕ переводить
- Синтаксис кода, ключевые слова, операторы
- Имена переменных, функций, классов, модулей
- Import statements, пути файлов, URLs
- Технические идентификаторы, константы, ключи
- Регулярные выражения, SQL, конфигурация"""
        
        with open(sys_rules_file, 'w', encoding='utf-8') as f:
            f.write(default_sys_rules)
        logger.info(f"📜 Создан файл системных правил: {sys_rules_file}")
    
    # Создаем user_rules.md если его нет
    if not os.path.exists(user_rules_file):
        default_user_rules = """# 👤 Пользовательские правила перевода

## Специальные инструкции для этого проекта

### Режим работы с китайскими символами:
<!-- Раскомментируйте нужный режим -->

<!-- Режим 1: Сохранение китайских символов (для технических проектов)
PRESERVE_CHINESE_CHARACTERS
Критически важно: Сохранять ВСЕ китайские символы точно: 甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥木火土金水
Это важные технические термины, которые НИКОГДА нельзя переводить.
-->

<!-- Режим 2: Перевод китайских символов (для обычных проектов)
TRANSLATE_CHINESE_CHARACTERS
Переводить ВСЕ китайские символы на целевой язык.
Китайский текст должен быть полностью конвертирован в читаемый текст.
-->

### Дополнительные правила:
- Добавьте здесь специфичные для проекта инструкции
- Особые термины для сохранения
- Специальные форматы и структуры
"""
        
        with open(user_rules_file, 'w', encoding='utf-8') as f:
            f.write(default_user_rules)
        logger.info(f"👤 Создан файл пользовательских правил: {user_rules_file}")

async def main():
    parser = argparse.ArgumentParser(description="Universal project translator using LLM - Enhanced v2.1")
    parser.add_argument("project_path", help="Path to project for translation")
    parser.add_argument("--target-lang", help="Target language (overrides config)")
    parser.add_argument("--source-lang", help="Source language (overrides config)")
    parser.add_argument("--llm-provider", choices=["groq", "openai", "anthropic"], help="LLM provider (overrides config)")
    parser.add_argument("--api-key", help="API key for LLM provider (overrides config)")
    parser.add_argument("--model", help="Model name to use (overrides config)")
    parser.add_argument("--chunk-size", type=int, help="Chunk size in lines (overrides config)")
    parser.add_argument("--max-concurrent", type=int, help="Max concurrent requests (overrides config)")
    parser.add_argument("--user-rules", help="Custom user rules for this project (overrides template)")
    
    args = parser.parse_args()
    
    # Загружаем статическую конфигурацию из папки TransLLM
    static_config = load_static_config()
    
    # Проверяем наличие конфигурации
    if not static_config:
        logger.error("❌ Static configuration files not found!")
        logger.info("💡 Make sure config.json exists in TransLLM directory with proper API key")
        return
    
    # Объединяем конфигурацию (параметры командной строки переопределяют файловые)
    target_language = args.target_lang or static_config.get("target_language", "Russian")
    source_language = args.source_lang or static_config.get("source_language", "English")
    llm_provider = args.llm_provider or static_config.get("llm_provider", "groq")
    api_key = args.api_key or static_config.get("api_key")
    chunk_size = args.chunk_size or static_config.get("chunk_size", 100)
    max_concurrent = args.max_concurrent or static_config.get("max_concurrent_requests", 10)
    model_name = args.model or static_config.get("model_name")
    
    # Проверяем API ключ
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        logger.error("❌ API key not set!")
        logger.info("💡 Set API key in config.json or pass via --api-key")
        return
    
    # Определяем модель по умолчанию если не указана
    if not model_name:
        model_defaults = {
            "groq": "llama-3.3-70b-versatile",
            "openai": "gpt-4",
            "anthropic": "claude-3-sonnet-20240229"
        }
        model_name = model_defaults[llm_provider]
    
    # Получаем пользовательские инструкции
    user_instructions = args.user_rules or static_config.get('user_instructions', '')
    
    config = TranslationConfig(
        source_project_path=args.project_path,
        target_language=target_language,
        source_language=source_language,
        chunk_size=chunk_size,
        custom_instructions=user_instructions,
        llm_provider=llm_provider,
        api_key=api_key,
        model_name=model_name,
        max_concurrent_requests=max_concurrent,
        supported_extensions=static_config.get("supported_extensions"),
        exclude_dirs=static_config.get("exclude_dirs"),
        exclude_files=static_config.get("exclude_files")
    )
    
    logger.info("🚀 Configuration loaded:")
    logger.info(f"   🤖 LLM: {llm_provider}/{model_name}")
    logger.info(f"   🌐 Languages: {source_language} → {target_language}")
    logger.info(f"   📦 Chunks: {chunk_size} lines, {max_concurrent} concurrent")
    logger.info(f"   📁 Project: {args.project_path}")
    
    translator = ProjectTranslator(config)
    await translator.translate_project()


if __name__ == "__main__":
    asyncio.run(main())
