import pandas as pd
import os
import re
import sys

def extract_category_code(filename):
    """파일명에서 카테고리 코드 추출"""
    match = re.search(r'DB-1-1-(\d+)', filename)
    if match:
        code = match.group(1)
        # 카테고리 코드를 3자리씩 나누어 개행으로 구분
        return '\n'.join([code[i:i+3] for i in range(0, len(code), 3)])
    return ''

def safe_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0

def convert_db(input_file, output_file, sample_file):
    # 샘플 DB 읽기
    df_sample = pd.read_csv(sample_file, encoding='utf-8-sig', header=1)
    
    # 기존 DB 읽기
    df = pd.read_csv(input_file, encoding='utf-8-sig', header=1)
    
    # 필드 매핑
    df_new = pd.DataFrame()
    
    # 상품명(필수)
    df_new['상품명_기본'] = df['goodsnm']
    df_new['goods_name'] = df['goodsnm']
    
    # 상품분류(필수) -> 카테고리 코드
    df_new['카테고리 코드'] = df['goodscate']
    df_new['category_code'] = df['goodscate']
    
    # 제조사 -> 제조사
    df_new['제조사'] = df['maker']
    df_new['maker_name'] = df['maker']
    
    # 상품설명 -> PC/모바일 상세 설명 모두에 복사
    df_new['PC쇼핑몰 상세 설명'] = df['longdesc']
    df_new['goods_desc_pc'] = df['longdesc']
    df_new['모바일쇼핑몰 상세 설명'] = df['longdesc']
    df_new['goods_desc_mobile'] = df['longdesc']
    
    # 이미지 관련 필드들을 하나로 합치기
    df_new['이미지명'] = df.apply(lambda row: '\n'.join([
        f"main^|^{row['img_i']}" if pd.notna(row['img_i']) else '',
        f"list^|^{row['img_s']}" if pd.notna(row['img_s']) else '',
        f"detail^|^{row['img_m']}" if pd.notna(row['img_m']) else ''
    ]).strip(), axis=1)
    df_new['image_name'] = df_new['이미지명']
    
    # 옵션출력방식 -> 옵션 표시 방법
    df_new['옵션 표시 방법'] = df['opttype'].map({'single': 's', 'double': 'd'})
    df_new['option_display'] = df_new['옵션 표시 방법']
    
    # 가격/재고 옵션명 -> 옵션명 (구분자: ^|^)
    df_new['옵션명'] = df.apply(lambda row: 
        f"수량(Set)^|^색상(Color)" if pd.notna(row['optnm']) and row['optnm'] else 
        "수량(Set)" if pd.notna(row['opts']) and row['opts'] else '', axis=1)
    df_new['option_name'] = df_new['옵션명']
    
    # 가격/재고 옵션목록 처리
    def process_opts(opts_str, addoptnm_str=None, addopts_str=None):
        if pd.isna(opts_str) or not opts_str:
            return '', '', '', '', '', ''
        
        # 옵션 조합들을 |로 분리
        opt_combinations = opts_str.split('|')
        opt_names = []
        prices = []
        fixed_prices = []
        cost_prices = []
        stocks = []
        
        for opt in opt_combinations:
            parts = opt.split('^')
            if len(parts) >= 7:
                option_name = parts[0] if parts[0] else ''
                opt_names.append(option_name)
                prices.append(safe_float(parts[2]) if len(parts) > 2 else 0)
                fixed_prices.append(safe_float(parts[3]) if len(parts) > 3 else 0)
                cost_prices.append(safe_float(parts[4]) if len(parts) > 4 else 0)
                stocks.append(safe_float(parts[6]) if len(parts) > 6 else 0)
        
        # 추가상품 옵션명 추출
        addopt_names = []
        addopt_prices = []
        if not pd.isna(addopts_str) and addopts_str != '^':
            addopts_list = addopts_str.split('|')
            for addopt in addopts_list:
                add_parts = addopt.split('^')
                # 두 번째 값이 옵션명, 세 번째 값이 추가금액
                if len(add_parts) >= 3 and add_parts[1]:
                    addopt_names.append(add_parts[1])
                    addopt_prices.append(safe_float(add_parts[2]))
                elif len(add_parts) >= 2 and add_parts[1]:
                    addopt_names.append(add_parts[1])
                    addopt_prices.append(0)
        
        # 곱집합 조합 생성 및 각 조합별 가격/재고/매입가 생성
        option_value_list = []
        option_price_list = []
        option_cost_price_list = []
        stock_cnt_list = []
        
        if addopt_names:
            for i, addopt in enumerate(addopt_names):
                add_price = addopt_prices[i] if i < len(addopt_prices) else 0
                for j, optname in enumerate(opt_names):
                    option_value_list.append(f"{addopt}^|^{optname}")
                    if '세트' in addopt or '박스' in addopt:
                        option_price_list.append(f"{add_price:.2f}")
                    else:
                        option_price_list.append("0.00")
                    option_cost_price_list.append(f"{cost_prices[j] if j < len(cost_prices) else 0:.2f}")
                    stock_cnt_list.append(f"{int(stocks[j]) if j < len(stocks) else 0}")
        else:
            for j, optname in enumerate(opt_names):
                option_value_list.append(optname)
                option_price_list.append("0.00")
                option_cost_price_list.append(f"{cost_prices[j] if j < len(cost_prices) else 0:.2f}")
                stock_cnt_list.append(f"{int(stocks[j]) if j < len(stocks) else 0}")
        
        option_value = '\n'.join(option_value_list)
        option_price = '\n'.join(option_price_list)
        option_cost_price = '\n'.join(option_cost_price_list)
        stock_cnt = '\n'.join(stock_cnt_list)
        
        return option_value, option_cost_price, option_price, stock_cnt, '', ''
    
    # 옵션목록 처리 적용
    processed_opts = df.apply(lambda row: process_opts(row['opts'], row['addoptnm'], row['addopts']), axis=1)
    df_new['옵션값'] = processed_opts.apply(lambda x: x[0])
    df_new['option_value'] = df_new['옵션값']
    df_new['옵션매입가격'] = processed_opts.apply(lambda x: x[1])
    df_new['option_cost_price'] = df_new['옵션매입가격']
    df_new['옵션가격'] = processed_opts.apply(lambda x: x[2])
    df_new['option_price'] = df_new['옵션가격']
    df_new['재고'] = processed_opts.apply(lambda x: x[3])
    df_new['stock_cnt'] = df_new['재고']
    
    # 모델명 -> 매입처 상품명
    df_new['매입처 상품명'] = df['model_name']
    df_new['purchase_goods_name'] = df['model_name']
    
    # 상품번호(goods_no)는 빈 값으로 처리
    if 'goods_no' in df_sample.columns:
        df_new['goods_no'] = ''
    if '상품번호' in df_sample.columns:
        df_new['상품번호'] = ''
    
    # 나머지 필드는 빈 값으로
    for col in df_sample.columns:
        if col not in df_new.columns:
            df_new[col] = ''
    
    # 샘플 DB의 칼럼 순서로 정렬
    df_new = df_new[df_sample.columns]
    
    # 샘플 DB의 헤더(1~2행)만 복사
    with open(sample_file, 'r', encoding='utf-8-sig') as f:
        header_lines = [next(f) for _ in range(2)]  # 1~2행만
    
    # 결과 저장
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        # 헤더 쓰기
        for line in header_lines:
            f.write(line)
        
        # 데이터 쓰기
        df_new.to_csv(f, index=False, header=False, encoding='utf-8-sig')

def main():
    # 샘플 DB 파일
    sample_file = '기존 상품 DB/sample_product_db.csv'

    # 명령행 인자: [입력파일, 출력파일]
    if len(sys.argv) == 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        convert_db(input_file, output_file, sample_file)
        print(f'변환 완료: {input_file}')
    else:
        # 디렉토리 일괄 변환
        input_dir = '기존 상품 DB'
        output_dir = '변환된 상품 DB'
        os.makedirs(output_dir, exist_ok=True)
        for filename in os.listdir(input_dir):
            if filename.endswith('.csv') and filename.startswith('DB-'):
                input_file = os.path.join(input_dir, filename)
                output_file = os.path.join(output_dir, f'converted_{filename}')
                convert_db(input_file, output_file, sample_file)
                print(f'변환 완료: {filename}')

if __name__ == '__main__':
    main() 