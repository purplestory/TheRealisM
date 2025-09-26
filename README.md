# TheRealisM - 고도몰 이전 프로젝트

## 프로젝트 개요
오래전 만들어진 고도몰 이나무 시즌4 독립형 쇼핑몰의 카테고리와 상품을 
새로운 고도몰 basic 무료버전으로 이전하기 위한 프로젝트입니다. 
기존 상품 DB를 새로운 형식으로 변환하는 Python 스크립트입니다.

## 설정 방법

### 1. config.json 파일 생성
```bash
cp config.example.json config.json
```

### 2. config.json 편집
```json
{
    "managerId": "실제_관리자_아이디",
    "managerPw": "실제_관리자_패스워드"
}
```

## 사용 방법

### 상품 DB 변환
```bash
python3 convert_db.py "입력파일.csv" "출력파일.csv"
```

### 카테고리 자동화 (고도몰)
```bash
python3 8th.py
```

## 주의사항
- `config.json` 파일은 Git에 커밋되지 않습니다
- 민감한 정보는 절대 코드에 하드코딩하지 마세요
- `config.example.json`을 참고하여 설정하세요

## 파일 구조
- `convert_db.py` - 상품 DB 변환 스크립트
- `8th.py` - 고도몰 카테고리 자동화 스크립트
- `category_list.csv` - 카테고리 목록
- `기존 상품 DB/` - 원본 상품 데이터
- `변환된 상품 DB/` - 변환된 결과 데이터
