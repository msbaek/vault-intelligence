#!/usr/bin/env python3
"""
의존성 테스트 스크립트
"""

def test_dependencies():
    """필수 패키지 설치 확인"""
    print("🔍 의존성 확인 중...")
    
    required_packages = {
        'sentence_transformers': 'sentence-transformers',
        'sklearn': 'scikit-learn', 
        'numpy': 'numpy',
        'torch': 'torch',
        'yaml': 'pyyaml',
        'networkx': 'networkx',
        'matplotlib': 'matplotlib'
    }
    
    missing_packages = []
    available_packages = []
    
    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
            available_packages.append(f"✅ {package_name}")
        except ImportError:
            missing_packages.append(f"❌ {package_name}")
    
    print("\n📦 패키지 상태:")
    for pkg in available_packages:
        print(f"  {pkg}")
    for pkg in missing_packages:
        print(f"  {pkg}")
    
    if missing_packages:
        print(f"\n⚠️  누락된 패키지: {len(missing_packages)}개")
        print("설치 명령어:")
        for module_name, package_name in required_packages.items():
            try:
                __import__(module_name)
            except ImportError:
                print(f"  pip install {package_name}")
    else:
        print(f"\n✅ 모든 필수 패키지가 설치되어 있습니다!")
    
    return len(missing_packages) == 0

if __name__ == "__main__":
    test_dependencies()