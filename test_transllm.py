#!/usr/bin/env python3
"""
TransLLM Quick Test Script
=========================

This script performs a quick test to verify TransLLM is working correctly.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

def create_test_project():
    """Create a small test project for translation"""
    test_dir = tempfile.mkdtemp(prefix="transllm_test_")
    
    # Create a simple Python file with Russian comments
    test_content = '''#!/usr/bin/env python3
"""
Тестовый модуль для проверки работы переводчика
"""

def hello_world():
    """Функция для вывода приветствия"""
    # Выводим приветствие на экран
    print("Привет, мир!")  # Русский комментарий
    return "success"

class TestClass:
    """Тестовый класс для демонстрации"""
    
    def __init__(self):
        # Инициализируем переменные
        self.message = "Тестовое сообщение"
    
    def get_message(self):
        """Возвращает сообщение"""
        return self.message

if __name__ == "__main__":
    # Запускаем тест
    hello_world()
'''
    
    test_file = Path(test_dir) / "test_module.py"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    return test_dir

def run_test():
    """Run the TransLLM test"""
    print("🧪 TransLLM Functionality Test")
    print("=" * 40)
    
    # Check if API key is available
    if not os.getenv("GROQ_API_KEY"):
        print("❌ GROQ_API_KEY not found!")
        print("   Please set your API key:")
        print("   export GROQ_API_KEY='your-key-here'")
        return False
    
    print("✅ API key found")
    
    # Create test project
    test_dir = create_test_project()
    print(f"✅ Test project created: {test_dir}")
    
    try:
        # Import and test TransLLM
        from project_translator import ProjectTranslator, TranslationConfig
        print("✅ TransLLM modules imported successfully")
        
        # Configure translation
        config = TranslationConfig(
            source_project_path=test_dir,
            target_language="English",
            source_language="Russian",
            llm_provider="groq",
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="openai/gpt-oss-120b",
            chunk_size=50,  # Small chunks for quick test
            max_concurrent_requests=1  # Single request for stability
        )
        print("✅ Configuration created")
        
        # Create translator
        translator = ProjectTranslator(config)
        print("✅ Translator instance created")
        
        # Test project analysis
        analyzer = translator.analyzer
        project_info = analyzer.analyze_project(test_dir)
        
        print(f"✅ Project analysis complete:")
        print(f"   📁 Total files: {project_info['total_files']}")
        print(f"   📄 Translatable files: {project_info['translatable_files']}")
        print(f"   📦 Estimated chunks: {project_info['estimated_chunks']}")
        
        if project_info['translatable_files'] > 0:
            print("✅ Test project structure is valid")
            return True
        else:
            print("❌ No translatable files found in test project")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed:")
        print("   pip install groq")
        return False
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False
    finally:
        # Clean up test directory
        shutil.rmtree(test_dir, ignore_errors=True)
        print("🧹 Test cleanup completed")

def check_dependencies():
    """Check if required dependencies are available"""
    print("\n🔍 Checking Dependencies")
    print("=" * 40)
    
    dependencies = {
        'groq': False,
        'openai': False,
        'anthropic': False
    }
    
    for dep in dependencies:
        try:
            __import__(dep)
            dependencies[dep] = True
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} (optional)")
    
    # Check if at least one provider is available
    if any(dependencies.values()):
        print("✅ At least one LLM provider is available")
        return True
    else:
        print("❌ No LLM providers found!")
        print("   Install at least one:")
        print("   pip install groq")
        return False

if __name__ == "__main__":
    print("🌟 TransLLM System Test")
    print("=" * 50)
    
    # Check dependencies first
    deps_ok = check_dependencies()
    
    if deps_ok:
        # Run functionality test
        test_result = run_test()
        
        print("\n📊 Test Results")
        print("=" * 40)
        if test_result:
            print("🎉 All tests PASSED!")
            print("✅ TransLLM is ready to use")
            print("\n🚀 Try translating a real project:")
            print("   python3 quick_translate.py /path/to/project --model openai/gpt-oss-120b")
        else:
            print("❌ Some tests FAILED!")
            print("🔧 Check the error messages above and resolve issues")
    else:
        print("\n❌ Dependency check failed!")
        print("🔧 Install required dependencies and try again")
    
    print("\n" + "=" * 50)
