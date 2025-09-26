import pandas as pd
import os
import glob

def convert_product_db(input_file, output_file):
    # 기존 DB 파일 읽기
    df = pd.read_csv(input_file, encoding='utf-8')
    
    # 새로운 형식의 데이터프레임 생성
    new_df = pd.DataFrame()
    
    # 필드 매핑
    new_df['goods_no'] = df['상품번호']
    new_df['goods_name'] = df['상품명']
    new_df['name_main'] = df['상품명']
    new_df['name_list'] = df['상품명']
    new_df['name_detail'] = df['상품명']
    new_df['goods_price'] = df['가격']
    new_df['fixed_price'] = df['가격']
    new_df['cost_price'] = df['가격'] * 0.7  # 매입가를 판매가의 70%로 가정
    new_df['goods_desc_pc'] = df['상품설명']
    new_df['image_name'] = df['이미지']
    
    # 기본값 설정
    new_df['commission'] = 0
    new_df['goods_state'] = 'n'  # 신상품
    new_df['display_pc_yn'] = 'y'
    new_df['display_mobile_yn'] = 'y'
    new_df['sell_pc_yn'] = 'y'
    new_df['sell_mobile_yn'] = 'y'
    new_df['option_yn'] = 'n'
    new_df['stock_type'] = 'y'
    new_df['tax_free_type'] = 't'
    new_df['tax_percent'] = 10
    
    # 결과 저장
    new_df.to_csv(output_file, index=False, encoding='utf-8')

def main():
    # 입력 디렉토리
    input_dir = '기존 상품 DB'
    
    # 출력 디렉토리
    output_dir = 'converted_products'
    os.makedirs(output_dir, exist_ok=True)
    
    # DB-1-1-1 ~ DB-1-1-40 파일 처리
    for i in range(1, 41):
        input_file = os.path.join(input_dir, f'DB-1-1-{i}.xls.csv')
        output_file = os.path.join(output_dir, f'converted_DB-1-1-{i}.csv')
        
        if os.path.exists(input_file):
            print(f'Converting {input_file}...')
            convert_product_db(input_file, output_file)
            print(f'Converted to {output_file}')

if __name__ == '__main__':
    main() 