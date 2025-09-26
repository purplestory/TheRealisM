import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import traceback
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
import json

# === robust 요소 대기/탐색 함수 ===


def robust_wait_until(driver, condition, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(condition)
    except Exception:
        return None


def robust_find_element(driver, by, value, timeout=5):
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    except Exception:
        return None

# === robust 트리 상태 초기화 ===


def reset_tree_state(driver):
    try:
        # 페이지 새로고침
        driver.refresh()
        time.sleep(2)

        # 트리 컨테이너가 로드될 때까지 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "categoryTree"))
        )

        # 모든 노드 닫기
        driver.execute_script("""
            var tree = $.tree.reference('categoryTree');
            if (tree) {
                tree.close_all();
            }
        """)

        time.sleep(1)
        print("[디버그] 트리 상태 초기화 완료")
    except Exception as e:
        print(f"[경고] 트리 초기화 중 오류: {e}")
    
# === robust 트리 노드 열린 상태 대기 ===


def open_category_and_wait(driver, category_name, timeout=30):
    try:
        # 페이지가 완전히 로드될 때까지 대기
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
    
        # 트리 컨테이너가 안정화될 때까지 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "categoryTree"))
        )

        # 먼저 카테고리 노드를 찾음
        category_xpath = f"//div[@id='categoryTree']//li/a[contains(text(), '{category_name}')]"
        category_node = robust_wait_until(
            driver, EC.presence_of_element_located(
                (By.XPATH, category_xpath)), 10)
        if not category_node:
            print(f"[경고] '{category_name}' 노드를 찾지 못함")
            return False
            
        # 부모 li 요소의 class 확인
        parent_li = category_node.find_element(By.XPATH, "./ancestor::li[1]")
        li_class = parent_li.get_attribute('class') or ''
        
        # 이미 열린 상태면 추가 작업 없이 바로 반환
        if 'open' in li_class:
            return True
            
        # 닫힌 상태일 때만 열기 시도
        if 'closed' in li_class:
            close_all_btn = robust_wait_until(
                driver, EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "a.close_all")), 10)
            if close_all_btn:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});",
                    close_all_btn)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", close_all_btn)
                time.sleep(1)
                
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                category_node)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", category_node)
            time.sleep(1)
            driver.execute_script(
                "$.tree.reference('categoryTree').open_branch(arguments[0]);", parent_li)
            time.sleep(1)
            
            # 열린 상태 확인
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    li_class = parent_li.get_attribute('class') or ''
                    if 'open' in li_class:
                        ul = parent_li.find_element(By.TAG_NAME, 'ul')
                        if ul.is_displayed() and 'display: none' not in (ul.get_attribute('style') or ''):
                            return True
                except Exception:
                    pass
                time.sleep(0.5)
            print(f"[경고] '{category_name}' 열기 실패")
            return False
            
        return True
    except Exception as e:
        print(f"[에러] '{category_name}' 열기 중 오류: {e}")
        return False

# === robust 계층 탐색 ===


def find_category_node(driver, category_name, parent_name=None, max_attempts=3):
    """카테고리 노드를 찾는 함수"""
    for attempt in range(max_attempts):
        try:
            # 트리 컨테이너가 안정화될 때까지 대기
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )

            # 트리 컨테이너 찾기
            tree_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "categoryTree"))
            )

            # 알림창이 있으면 처리
            try:
                alert = driver.switch_to.alert
                if "새 카테고리" in alert.text:
                    alert.dismiss()
                    time.sleep(1)
            except:
                pass

            if parent_name:
                # 부모 노드 찾기
                parent_xpath = f"//div[@id='categoryTree']//a[contains(text(), '{parent_name}')]"
                parent_node = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, parent_xpath))
                )

                # 부모 노드 클릭 및 대기
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", parent_node)
                driver.execute_script("arguments[0].click();", parent_node)
                time.sleep(1)

                # 부모 노드의 li 요소 확인
                parent_li = parent_node.find_element(By.XPATH, "./ancestor::li[1]")
                li_class = parent_li.get_attribute('class') or ''

                # closed 노드인 경우 열기 시도
                if 'closed' in li_class:
                    try:
                        # 1. 전체열기 버튼으로 초기화
                        open_all_btn = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "a[rel='open_all']"))
                        )
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", open_all_btn)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", open_all_btn)
                        time.sleep(1)

                        # 2. 노드 클릭으로 열기
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", parent_node)
                        driver.execute_script("arguments[0].click();", parent_node)
                        time.sleep(1)

                        # 3. jQuery tree API로 직접 열기
                        driver.execute_script("$.tree.reference('categoryTree').open_branch(arguments[0]);", parent_li)
                        time.sleep(1)
                    except Exception as e:
                        print(f"[경고] 부모 노드 열기 실패: {e}")

                # ul 태그 찾기
                ul = None
                for retry2 in range(10):
                    try:
                        ul = parent_li.find_element(By.TAG_NAME, "ul")
                        if ul.is_displayed() and 'display: none' not in (ul.get_attribute('style') or ''):
                            break
                    except Exception:
                        time.sleep(0.5)

                if not ul:
                    print(f"[경고] '{parent_name}' 노드의 ul을 찾을 수 없음")
                    return None

                # 자식 노드 찾기
                child_anchors = ul.find_elements(By.TAG_NAME, "a")
                for a in child_anchors:
                    try:
                        if a.text.strip() == category_name:
                            return a
                    except StaleElementReferenceException:
                        continue
                    except Exception as e:
                        continue
                return None
            else:
                # 직접 노드 찾기 - contains() 사용하여 부분 일치도 허용
                xpath = f"//div[@id='categoryTree']//a[contains(text(), '{category_name}')]"
                node = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                return node

        except Exception as e:
            if attempt < max_attempts - 1:
                driver.refresh()
                time.sleep(2)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "categoryTree"))
                )
            time.sleep(1)

    return None


def find_child_category_node(driver, parent_name, child_name, max_attempts=3):
    """부모 노드 아래에서 자식 노드를 찾는 함수"""
    parent_name = parent_name.strip()
    child_name = child_name.strip()

    for attempt in range(max_attempts):
        try:
            # 부모 노드 찾기
            parent_node = find_category_node(driver, parent_name)
            if not parent_node:
                print(f"[경고] 부모 노드 '{parent_name}'를 찾지 못함")
                return None
                
            # 부모 노드의 li 요소 확인
            parent_li = parent_node.find_element(By.XPATH, "./ancestor::li[1]")
            li_class = parent_li.get_attribute('class') or ''
            
            # leaf 노드인 경우
            if 'leaf' in li_class:
                return None
            
            # closed 노드인 경우 열기 시도
            if 'closed' in li_class:
                try:
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", parent_node)
                    driver.execute_script("arguments[0].click();", parent_node)
                    time.sleep(1)
                    driver.execute_script(
                        "$.tree.reference('categoryTree').open_branch(arguments[0]);", parent_li)
                    time.sleep(1)
                except Exception as e:
                    print(f"[경고] 노드 열기 실패: {e}")
                    return None
                    
            # ul 태그 찾기
            ul = None
            for retry2 in range(10):
                try:
                    ul = parent_li.find_element(By.TAG_NAME, "ul")
                    if ul.is_displayed() and 'display: none' not in (ul.get_attribute('style') or ''):
                        break
                except Exception:
                    time.sleep(0.5)
                    
            if not ul:
                print(f"[경고] '{parent_name}' 노드의 ul을 찾을 수 없음")
                return None
                
            # 자식 노드 찾기
            child_anchors = ul.find_elements(By.TAG_NAME, "a")
            for a in child_anchors:
                try:
                    if a.text.strip() == child_name:
                        return a
                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    continue
            print(f"[경고] '{child_name}' 노드를 찾지 못함")
            return None
                
        except Exception as e:
            print(f"[경고] 부모 노드 처리 중 오류: {e}")
        time.sleep(1)
        
    return None

# === robust 계층별 자식 노드 존재 및 표시 보장 ===


def should_create_child(driver, parent_name, child_name):
    """동일 부모 아래 동일 이름의 자식이 이미 존재하는지 robust하게 탐색"""
    node = find_category_node(driver, child_name, parent_name=parent_name)
    if node:
        print(f"[확인] 이미 존재하는 자식: {child_name}")
        return False
    return True


def ensure_all_children_exist(driver, parent_node, csv_child_names, level='중분류', code_list=None, medium_df=None, small_df=None, large_name=None, medium_name=None):
    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        parent_name = parent_node.text.strip()
        # robust하게 계층 정보 추출 및 자식명 읽기
        existing_names = []
        for retry in range(3):
            try:
                existing_names = [name.strip() for name in get_child_names(driver, parent_node, large_name=large_name, medium_name=medium_name, level=level)]
                break
            except Exception:
                if level == '소분류' and large_name and medium_name:
                    parent_node = find_child_category_node(driver, large_name, medium_name)
                elif level == '중분류' and large_name:
                    parent_node = find_category_node(driver, large_name)
                time.sleep(0.5)
        # 생성할 카테고리 목록 준비
        to_create = []
        to_create_codes = []
        for name, code in zip(csv_child_names, code_list if code_list else [None] * len(csv_child_names)):
            # robust: 이미 트리에 존재하는지 find_category_node로 한 번 더 체크
            if name.strip() not in existing_names and should_create_child(driver, parent_name, name.strip()):
                to_create.append(name)
                to_create_codes.append(code)
        if not to_create:
            print(f"[확인] 모든 {level}가 이미 존재합니다")
            return []
        print(f"[생성] {len(to_create)}개의 {level} 생성 필요")
        created_categories = []
        # CSV의 카테고리 수만큼 반복
        for i, (child_name, child_code) in enumerate(zip(to_create, to_create_codes)):
            print(f"\n[생성] {i+1}/{len(to_create)} 번째 {level} 생성 시작: {child_name}")
            # 1. 하위 카테고리 생성 버튼 클릭
            if not click_create_subcategory_button(driver, parent_node, large_name=large_name, medium_name=medium_name, level=level):
                print(f"[경고] {child_name} {level} 생성 버튼 클릭 실패")
                continue
            # 2. '새 카테고리' 노드 찾기
            new_category = find_new_category_node(driver, parent_node, large_name=large_name, medium_name=medium_name, level=level)
            if not new_category:
                print(f"[경고] {child_name} {level}의 '새 카테고리' 노드를 찾을 수 없음")
                continue
            # 3. 노드 ID 가져오기
            try:
                parent_li = new_category.find_element(By.XPATH, "./ancestor::li[1]")
                node_id = parent_li.get_attribute('id')
                if level == '대분류':
                    if node_id:
                        print(f"[디버그] {child_name} {level} 노드 ID: {node_id}")
                else:
                    if not node_id:
                        print(f"[경고] {child_name} {level} 노드에 ID가 없습니다")
                        continue
                    print(f"[디버그] {child_name} {level} 노드 ID: {node_id}")
            except StaleElementReferenceException:
                print(f"[경고] {child_name} {level} 노드가 stale 상태입니다")
                continue
            except NoSuchElementException:
                print(f"[경고] {child_name} {level} 노드의 부모 li 요소를 찾을 수 없습니다")
                continue
            except Exception as e:
                print(f"[경고] {child_name} {level} 노드 ID 가져오기 실패: {e}")
                continue
            # 4. 카테고리명 입력
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", new_category)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", new_category)
                time.sleep(1)
                name_input = driver.find_element(By.NAME, "cateNm")
                name_input.clear()
                name_input.send_keys(child_name)
                time.sleep(0.5)
                # 5. 저장 버튼 클릭
                save_btn = driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='저장'].btn.btn-red.save")
                if save_btn.is_displayed() and save_btn.is_enabled():
                    driver.execute_script("arguments[0].click();", save_btn)
                    print(f"[저장] '{child_name}' {level} 저장 완료")
                    time.sleep(2)  # 저장 후 충분한 대기 시간
                    created_categories.append(child_name)
            except Exception as e:
                print(f"[경고] {child_name} {level} 이름 변경/저장 실패: {e}")
                continue
            print(f"[완료] {child_name} {level} 생성 완료")
        print(f"[완료] {level} 생성 프로세스 종료")
        return created_categories
    except Exception as e:
        print(f"[경고] ensure_all_children_exist 함수 오류: {e}")
        return []

# === robust 메인 ===


def sync_categories_hierarchical(driver, large_df, medium_df, small_df):
    """대분류→중분류→소분류 계층을 따라가며, 부모-자식 관계를 명확히 인식하고, 각 계층별로 실제 트리와 CSV를 비교해 부족한 자식만 생성하는 계층적 로직"""
    try:
        print("\n[트리-CSV 누락 카테고리 계층적 자동 등록 시작]")
        reset_tree_state(driver)
        
        # 결과 수집을 위한 딕셔너리
        results = {
            'total': {
                'large': {'created': 0, 'csv': len(large_df)},
                'medium': {'created': 0, 'csv': len(medium_df)},
                'small': {'created': 0, 'csv': len(small_df)}
            },
            'categories': {}
        }
        
        for lidx, lrow in large_df.iterrows():
            large_name = lrow['large_name']
            large_code = lrow['large_code']
            print(f"\n[대분류] {large_code}. {large_name}")
            
            # 대분류별 결과 초기화
            results['categories'][large_name] = {
                'large': {'created': 0, 'csv': 1},
                'medium': {'created': 0, 'csv': 0, 'details': []},
                'small': {'created': 0, 'csv': 0, 'details': []}
            }
            
            lnode = find_category_node(driver, large_name)
            if not lnode:
                print(f"[경고] 대분류 '{large_name}' 노드를 찾지 못함")
                continue
            if not open_category_and_wait(driver, large_name):
                print(f"[경고] 대분류 '{large_name}' 열기 실패")
                continue
            time.sleep(2)
            
            mdf = medium_df[medium_df['large_name'] == large_name]
            mnames = mdf['medium_name'].tolist()
            mcodes = mdf['medium_code'].tolist() if 'medium_code' in mdf.columns else None
            
            # 중분류 CSV 수 업데이트
            results['categories'][large_name]['medium']['csv'] = len(mdf)
            results['total']['medium']['csv'] = len(medium_df)
            
            created_medium = ensure_all_children_exist(driver, lnode, mnames, level='중분류', code_list=mcodes, large_name=large_name)
            if created_medium:
                results['categories'][large_name]['medium']['created'] = len(created_medium)
                results['categories'][large_name]['medium']['details'] = created_medium
                results['total']['medium']['created'] += len(created_medium)
            
            for midx, (mname, mcode) in enumerate(zip(mnames, mcodes)):
                print(f"\n[중분류] {mcode}. {mname}")
                mnode = find_category_node(driver, mname, parent_name=large_name)
                if not mnode:
                    print(f"[생성] 중분류 '{mname}' 생성 필요")
                    continue
                if not open_category_and_wait(driver, mname, timeout=10):
                    print(f"[경고] 중분류 '{mname}' 열기 실패")
                    continue
                    
                sdf = small_df[(small_df['large_name'] == large_name) & (small_df['medium_name'] == mname)]
                snames = sdf['small_name'].tolist()
                scodes = sdf['small_code'].tolist() if 'small_code' in sdf.columns else None
                
                # 소분류 CSV 수 업데이트
                results['categories'][large_name]['small']['csv'] += len(sdf)
                results['total']['small']['csv'] = len(small_df)
                
                created_small = ensure_all_children_exist(driver, mnode, snames, level='소분류', code_list=scodes, large_name=large_name, medium_name=mname)
                if created_small:
                    results['categories'][large_name]['small']['created'] += len(created_small)
                    results['categories'][large_name]['small']['details'].extend(created_small)
                    results['total']['small']['created'] += len(created_small)
                
                for sidx, (sname, scode) in enumerate(zip(snames, scodes)):
                    print(f"[소분류] {scode}. {sname}")
        
        # 결과 모달 표시
        show_results_modal(driver, results)
        print("\n[누락 카테고리 계층적 등록 완료]")
    except Exception as e:
        print(f"[경고] sync_categories_hierarchical 오류: {e}")
        import traceback
        print(traceback.format_exc())
        return False
    return True

def show_results_modal(driver, results):
    """카테고리 생성 결과를 모달로 표시"""
    modal_html = """
    <div id=\"categoryResultsModal\" style=\"
        display: none;
        position: fixed;
        z-index: 1000;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0.4);
    \">
        <div style=\"
            background-color: #fefefe;
            margin: 5% auto;
            padding: 20px;
            border: 1px solid #888;
            width: 80%;
            max-height: 80%;
            overflow-y: auto;
            border-radius: 5px;
        \">
            <h2 style=\"text-align: center; margin-bottom: 20px;\">카테고리 생성 결과</h2>
            <div id=\"resultsContent\"></div>
            <div style=\"text-align: center; margin-top: 20px;\">
                <button onclick=\"document.getElementById('categoryResultsModal').style.display='none'\" 
                        style=\"padding: 10px 20px; background-color: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer;\">
                    확인
                </button>
            </div>
        </div>
    </div>
    """
    
    # 모달 HTML 삽입
    driver.execute_script("""
        var modal = document.createElement('div');
        modal.innerHTML = arguments[0];
        document.body.appendChild(modal.firstChild);
    """, modal_html)
    
    # resultsContent가 생성될 때까지 대기
    for _ in range(20):  # 최대 2초 대기
        exists = driver.execute_script("return document.getElementById('resultsContent') !== null;")
        if exists:
            break
        time.sleep(0.1)
    
    # 결과 내용 생성
    content_html = "<div style='margin-bottom: 20px;'>"
    
    # 전체 요약
    content_html += f"""
    <h3>전체 요약</h3>
    <table style='width: 100%; border-collapse: collapse; margin-bottom: 20px;'>
        <tr style='background-color: #f2f2f2;'>
            <th style='padding: 8px; border: 1px solid #ddd;'>분류</th>
            <th style='padding: 8px; border: 1px solid #ddd;'>생성된 카테고리</th>
            <th style='padding: 8px; border: 1px solid #ddd;'>CSV 데이터</th>
        </tr>
        <tr>
            <td style='padding: 8px; border: 1px solid #ddd;'>대분류</td>
            <td style='padding: 8px; border: 1px solid #ddd;'>{results['total']['large']['created']}</td>
            <td style='padding: 8px; border: 1px solid #ddd;'>{results['total']['large']['csv']}</td>
        </tr>
        <tr>
            <td style='padding: 8px; border: 1px solid #ddd;'>중분류</td>
            <td style='padding: 8px; border: 1px solid #ddd;'>{results['total']['medium']['created']}</td>
            <td style='padding: 8px; border: 1px solid #ddd;'>{results['total']['medium']['csv']}</td>
        </tr>
        <tr>
            <td style='padding: 8px; border: 1px solid #ddd;'>소분류</td>
            <td style='padding: 8px; border: 1px solid #ddd;'>{results['total']['small']['created']}</td>
            <td style='padding: 8px; border: 1px solid #ddd;'>{results['total']['small']['csv']}</td>
        </tr>
    </table>
    """
    
    # 대분류별 상세 결과
    for large_name, data in results['categories'].items():
        content_html += f"""
        <h3>{large_name}</h3>
        <table style='width: 100%; border-collapse: collapse; margin-bottom: 20px;'>
            <tr style='background-color: #f2f2f2;'>
                <th style='padding: 8px; border: 1px solid #ddd;'>분류</th>
                <th style='padding: 8px; border: 1px solid #ddd;'>생성된 카테고리</th>
                <th style='padding: 8px; border: 1px solid #ddd;'>CSV 데이터</th>
            </tr>
            <tr>
                <td style='padding: 8px; border: 1px solid #ddd;'>중분류</td>
                <td style='padding: 8px; border: 1px solid #ddd;'>{data['medium']['created']}</td>
                <td style='padding: 8px; border: 1px solid #ddd;'>{data['medium']['csv']}</td>
            </tr>
            <tr>
                <td style='padding: 8px; border: 1px solid #ddd;'>소분류</td>
                <td style='padding: 8px; border: 1px solid #ddd;'>{data['small']['created']}</td>
                <td style='padding: 8px; border: 1px solid #ddd;'>{data['small']['csv']}</td>
            </tr>
        </table>
        """
        
        # 생성된 카테고리 상세 목록
        if data['medium']['details']:
            content_html += "<h4>생성된 중분류</h4><ul>"
            for category in data['medium']['details']:
                content_html += f"<li>{category}</li>"
            content_html += "</ul>"
            
        if data['small']['details']:
            content_html += "<h4>생성된 소분류</h4><ul>"
            for category in data['small']['details']:
                content_html += f"<li>{category}</li>"
            content_html += "</ul>"
    
    content_html += "</div>"
    
    # 결과 내용 삽입
    driver.execute_script("""
        document.getElementById('resultsContent').innerHTML = arguments[0];
        document.getElementById('categoryResultsModal').style.display = 'block';
    """, content_html)
    
    # 모달이 닫힐 때까지 대기
    while True:
        try:
            if driver.execute_script("return document.getElementById('categoryResultsModal').style.display === 'none'"):
                break
        except:
            break
        time.sleep(0.5)

def verify_tree_code_and_name(driver, large_df, medium_df, small_df, filter_large_names=None, filter_medium_names=None):
    print("\n[트리 전체 카테고리 코드/이름 일치 검증 시작]")
    # 대분류
    for large_li in driver.find_elements(By.CSS_SELECTOR, "#categoryTree > li"):
        try:
            large_code = normalize_code(large_li.get_attribute('id'))
            large_a = large_li.find_element(By.TAG_NAME, 'a')
            large_name = large_a.text.strip()
            
            # 선택된 대분류만 검증
            if filter_large_names and large_name not in filter_large_names:
                continue
                
            # robust하게 클릭
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", large_a)
            large_a.click()
            time.sleep(0.2)
            
            # CSV에서 정규화된 코드로 검색
            row = large_df[large_df['large_code'].apply(normalize_code) == large_code]
            csv_name = row.iloc[0]['large_name'] if not row.empty else None
            if large_name != csv_name:
                print(f"[불일치][대분류] 코드:{large_code} 트리명:'{large_name}' CSV명:'{csv_name}'")
            # 중분류
            try:
                ul = large_li.find_element(By.TAG_NAME, 'ul')
                for medium_li in ul.find_elements(By.CSS_SELECTOR, ":scope > li[rel='node']"):
                    medium_code = normalize_code(medium_li.get_attribute('id'))
                    medium_a = medium_li.find_element(By.TAG_NAME, 'a')
                    medium_name = medium_a.text.strip()
                    
                    # 선택된 중분류만 검증
                    if filter_medium_names and (large_name, medium_name) not in filter_medium_names:
                        continue
                        
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", medium_a)
                    medium_a.click()
                    time.sleep(0.2)
                    
                    # CSV에서 정규화된 코드로 검색
                    row = medium_df[medium_df['medium_code'].apply(normalize_code) == medium_code]
                    csv_name = row.iloc[0]['medium_name'] if not row.empty else None
                    if medium_name != csv_name:
                        print(f"[불일치][중분류] 코드:{medium_code} 트리명:'{medium_name}' CSV명:'{csv_name}'")
                    # 소분류
                    try:
                        ul2 = medium_li.find_element(By.TAG_NAME, 'ul')
                        for small_li in ul2.find_elements(By.CSS_SELECTOR, ":scope > li[rel='node']"):
                            small_code = normalize_code(small_li.get_attribute('id'))
                            small_a = small_li.find_element(By.TAG_NAME, 'a')
                            small_name = small_a.text.strip()
                            
                            # 선택된 중분류의 소분류만 검증
                            if filter_medium_names and (large_name, medium_name) not in filter_medium_names:
                                continue
                                
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", small_a)
                            small_a.click()
                            time.sleep(0.2)
                            
                            # CSV에서 정규화된 코드로 검색
                            row = small_df[
                                (small_df['large_name'] == large_name) & 
                                (small_df['medium_name'] == mname) &
                                (small_df['small_name'] == sname)
                            ]['small_code'].iloc[0]
                            
                            if small_name != csv_name:
                                print(f"[불일치][소분류] 코드:{small_code} 트리명:'{small_name}' CSV명:'{csv_name}'")
                    except Exception:
                        continue
            except Exception:
                continue
        except Exception:
            continue
    print("[검증 완료]\n")

# === robust 메인 ===
def main():
    # 통합된 카테고리 파일 읽기
    df = pd.read_csv('godomall_categories.csv')
    # 1. 먼저 대/중/소분류 분리
    large_df = df[df['중분류코드'].isna()].copy()
    medium_df = df[df['중분류코드'].notna() & df['소분류코드'].isna()].copy()
    small_df = df[df['소분류코드'].notna()].copy()
    # 2. 각 df에 대해 robust하게 코드 컬럼 전처리(문자열 변환 및 zero-padding, strip)
    for d in [large_df, medium_df, small_df]:
        for col in ['대분류코드', '중분류코드', '소분류코드']:
            if col in d.columns:
                d[col] = d[col].astype(str).str.replace('.0','',regex=False).str.strip().str.zfill(3)
    # robust 컬럼명 매핑
    large_df = large_df.rename(columns={
        '대분류코드': 'large_code',
        '대분류명': 'large_name'
    })
    medium_df = medium_df.rename(columns={
        '대분류코드': 'large_code',
        '대분류명': 'large_name',
        '중분류코드': 'medium_code',
        '중분류명': 'medium_name'
    })
    small_df = small_df.rename(columns={
        '대분류코드': 'large_code',
        '대분류명': 'large_name',
        '중분류코드': 'medium_code',
        '중분류명': 'medium_name',
        '소분류코드': 'small_code',
        '소분류명': 'small_name'
    })
    # robust 코드 컬럼 str/zero-padding 재보장
    for d in [large_df, medium_df, small_df]:
        for col in ['large_code', 'medium_code', 'small_code']:
            if col in d.columns:
                d[col] = d[col].astype(str).str.replace('.0','',regex=False).str.strip().str.zfill(3)

    # config.json에서 아이디/비밀번호 읽기
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            managerId = config.get('managerId')
            managerPw = config.get('managerPw')
            if not managerId or not managerPw:
                print('[에러] config.json에 managerId 또는 managerPw가 없습니다.')
                return
    except Exception as e:
        print(f'[에러] config.json 파일을 읽을 수 없습니다: {e}')
        return

    driver = None
    try:
        driver = setup_driver()
        login_to_godomall(driver, managerId, managerPw)
        # === 대분류 선택 ===
        print("\n[대분류 선택]")
        large_names = large_df['large_name'].tolist()
        for i, name in enumerate(large_names):
            print(f"{i+1}. {name}")
        selected = input("작업할 대분류 번호(쉼표로 구분, 전체=엔터): ")
        if selected.strip():
            idxs = [int(x)-1 for x in selected.split(',') if x.strip().isdigit() and 0 < int(x) <= len(large_names)]
            selected_names = [large_names[i] for i in idxs]
            large_df = large_df[large_df['large_name'].isin(selected_names)]
            medium_df = medium_df[medium_df['large_name'].isin(selected_names)]
            small_df = small_df[small_df['large_name'].isin(selected_names)]
        else:
            selected_names = large_names
        print(f"[입력 후] selected_names: {selected_names}")
        # === 중분류 선택 ===
        selected_medium = []
        for lname in selected_names:
            mdf = medium_df[medium_df['large_name'] == lname]
            mnames = mdf['medium_name'].tolist()
            if not mnames:
                print(f"[경고] 대분류 '{lname}'에 중분류가 없습니다.")
                continue
            print(f"\n[중분류 선택 - 대분류: {lname}]")
            for i, mname in enumerate(mnames):
                print(f"{i+1}. {mname}")
            sel = input(f"작업할 중분류 번호(쉼표, 전체=엔터): ")
            if sel.strip():
                midxs = [int(x)-1 for x in sel.split(',') if x.strip().isdigit() and 0 < int(x) <= len(mnames)]
                sel_mnames = [mnames[i] for i in midxs]
            else:
                sel_mnames = mnames
            for mname in sel_mnames:
                selected_medium.append((lname, mname))
        print(f"[입력 후] selected_medium: {selected_medium}")
        # medium_df, small_df를 선택된 대/중분류만 남기도록 필터링
        if selected_medium:
            medium_df = medium_df[[ (row['large_name'], row['medium_name']) in selected_medium for _, row in medium_df.iterrows() ]]
            small_df = small_df[[ (row['large_name'], row['medium_name']) in selected_medium for _, row in small_df.iterrows() ]]
        filter_large_names = selected_names
        filter_medium_names = selected_medium if selected_medium else None
        print(f"[디버그] medium_df shape: {medium_df.shape}, small_df shape: {small_df.shape}")
        print(f"[디버그] filter_large_names: {filter_large_names}, filter_medium_names: {filter_medium_names}")
        # === 선택한 대분류/중분류 robust 오픈 ===
        for lname in filter_large_names:
            # 대분류 한 번만 열기
            if not open_category_and_wait(driver, lname):
                print(f"[경고] 대분류 '{lname}' 열기 실패")
                continue
                
            # 중분류 노드들 한 번에 열기
            mdf = medium_df[medium_df['large_name'] == lname]
            mnames = mdf['medium_name'].tolist()
            parent_li = find_category_node(driver, lname).find_element(By.XPATH, "./ancestor::li[1]")
            li_class = parent_li.get_attribute('class') or ''
            if 'leaf' in li_class:
                print(f"[디버그] 대분류 '{lname}'가 leaf 노드입니다. 중분류 노드 찾기 루프를 건너뜁니다.")
            else:
                for mname in mnames:
                    mnode = find_child_category_node(driver, lname, mname)
                    if mnode:
                        time.sleep(0.3)
            
            # 모든 작업이 완료된 후에만 닫기
            time.sleep(1)  # 작업 완료 대기
            for mname in mnames:
                mnode = find_child_category_node(driver, lname, mname)
                if mnode:
                    time.sleep(0.1)
            lnode = find_category_node(driver, lname)
            if lnode:
                time.sleep(0.1)
            
        # print("[진입] print_category_counts_debug 호출 직전")
        # print_category_counts_debug(driver, large_df, medium_df, small_df, filter_large_names, filter_medium_names)
        print("[진입] sync_categories_hierarchical 호출 직전")
        sync_categories_hierarchical(driver, large_df, medium_df, small_df)
        print("[진입] verify_tree_code_and_name 호출 직전")
        verify_tree_code_and_name(driver, large_df, medium_df, small_df, filter_large_names, filter_medium_names)
    except Exception as e:
        print(f"[프로그램 종료] 치명적 에러 발생: {e}")
        print(traceback.format_exc())
        if driver:
            driver.quit()
        return

def robust_open_tree_node(driver, node, large_name=None, medium_name=None, level='중분류'):
    """트리 노드(li)가 open 상태가 될 때까지 더블클릭으로 robust하게 연다. stale 발생 시 계층 정보로 parent_node fresh 재탐색"""
    for retry in range(3):
        try:
            parent_li = node.find_element(By.XPATH, "./ancestor::li[1]")
            for _ in range(5):
                li_class = parent_li.get_attribute('class') or ''
                if 'open' in li_class:
                    return True
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", node)
                    driver.execute_script("var evt = document.createEvent('MouseEvents'); evt.initEvent('dblclick', true, true); arguments[0].dispatchEvent(evt);", node)
                    time.sleep(0.7)
                except Exception:
                    continue
            return 'open' in (parent_li.get_attribute('class') or '')
        except StaleElementReferenceException:
            print("[stale] robust_open_tree_node: node stale, 재탐색 시도")
            if level == '소분류' and large_name and medium_name:
                node = find_child_category_node(driver, large_name, medium_name)
            elif level == '중분류' and large_name:
                node = find_category_node(driver, large_name)
            else:
                return False
            time.sleep(0.7)
        except Exception as e:
            print(f"[경고] robust_open_tree_node 오류: {e}")
            time.sleep(0.5)
    print("[경고] robust_open_tree_node robust 재시도 실패")
    return False

# === 브라우저/드라이버 설정 ===
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--window-size=1200,800')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    service = Service('/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(60)
    driver.set_script_timeout(30)
    # 화면 해상도(zoom) 조정
    driver.execute_script("document.body.style.zoom='80%'")
    return driver

# === 로그인 ===
def login_to_godomall(driver, managerId, managerPw):
    driver.get('https://gdadmin-therealism86.godomall.com/base/login.php')
    driver.execute_script("document.body.style.zoom='80%'")
    
    # 로그인 페이지 로드 대기
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.NAME, 'managerId'))
    )
    
    id_input = driver.find_element(By.NAME, 'managerId')
    id_input.send_keys(managerId)
    pw_input = driver.find_element(By.NAME, 'managerPw')
    pw_input.send_keys(managerPw)
    login_button = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"].btn-black')
    login_button.click()
    
    # 로그인 후 gnb 메뉴 로드 대기
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '.gnb'))
    )
    
    # 카테고리 페이지로 이동
    driver.get('https://gdadmin-therealism86.godomall.com/goods/category_tree.php')
    driver.execute_script("document.body.style.zoom='80%'")
    
    # 페이지 로드 완료 대기
    WebDriverWait(driver, 20).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )
    
    # 페이지가 완전히 안정화될 때까지 대기
    time.sleep(5)
    
    # 엔터 submit 제한 해제
    driver.execute_script("$(document).off('keypress', 'input');")

def click_create_subcategory_button(driver, parent_node, large_name=None, medium_name=None, level='중분류'):
    """하위 카테고리 생성 버튼 클릭 및 저장 후 상태 변화 대기"""
    try:
        print(f"[디버그] {level} 생성 버튼 클릭 시도")
        
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        
        # 부모 노드가 stale이면 재탐색
        try:
            _ = parent_node.is_displayed()
        except StaleElementReferenceException:
            print("[stale] click_create_subcategory_button: parent_node stale, 재탐색 시도")
            if level == '소분류' and large_name and medium_name:
                parent_node = find_child_category_node(driver, large_name, medium_name)
            elif level == '중분류' and large_name:
                parent_node = find_category_node(driver, large_name)
            else:
                parent_node = find_category_node(driver, parent_node.text.strip())
            
            if not parent_node:
                print("[경고] parent_node 재탐색 실패")
                return False
            time.sleep(0.5)
            
        # 부모 노드 클릭
        try:
            print("[디버그] 부모 노드 클릭 시도")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", parent_node)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", parent_node)
            time.sleep(1)
            print("[디버그] 부모 노드 클릭 완료")
        except Exception as e:
            print(f"[경고] parent_node 클릭 실패: {e}")
            return False
            
        # 생성 버튼 찾기
        print("[디버그] 생성 버튼 찾기 시도")
        create_btn = driver.find_element(By.CSS_SELECTOR, "input[type='button'][value='하위 카테고리 생성'].btn.btn-white.btn-sm")
        if not create_btn:
            print("[경고] 하위 카테고리 생성 버튼을 찾을 수 없습니다.")
            return False
            
        # 생성 버튼 클릭
        print("[디버그] 생성 버튼 클릭 시도")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", create_btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", create_btn)
        time.sleep(1)
        
        # 저장 버튼 클릭
        try:
            save_btn = driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='저장'].btn.btn-red.save")
            if save_btn.is_displayed() and save_btn.is_enabled():
                driver.execute_script("arguments[0].click();", save_btn)
                print("[디버그] '새 카테고리' 임시 저장 완료")
                time.sleep(2)  # 저장 후 충분한 대기 시간
        except Exception as e:
            print(f"[경고] 임시 저장 버튼 클릭 실패: {e}")
            return False
        
        # 저장 후 부모 노드 다시 찾기
        try:
            if level == '소분류' and large_name and medium_name:
                parent_node = find_child_category_node(driver, large_name, medium_name)
            elif level == '중분류' and large_name:
                parent_node = find_category_node(driver, large_name)
            else:
                parent_node = find_category_node(driver, parent_node.text.strip())
            
            if not parent_node:
                print("[경고] 저장 후 부모 노드를 찾을 수 없음")
                return False
                
            # 부모 노드의 li 요소 확인
            parent_li = parent_node.find_element(By.XPATH, "./ancestor::li[1]")
            li_class = parent_li.get_attribute('class') or ''
            
            # closed 상태로 변경될 때까지 대기
            start_time = time.time()
            while time.time() - start_time < 10:  # 10초 타임아웃
                if 'closed' in li_class:
                    print("[디버그] 부모 노드가 closed 상태로 변경됨")
                    break
                time.sleep(0.5)
                li_class = parent_li.get_attribute('class') or ''
            
            # 노드 열기
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", parent_node)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", parent_node)
            time.sleep(1)
            driver.execute_script("$.tree.reference('categoryTree').open_branch(arguments[0]);", parent_li)
            time.sleep(1)
            
            # '새 카테고리' 노드 찾기
            new_category = find_new_category_node(driver, parent_node, large_name=large_name, medium_name=medium_name, level=level)
            if new_category:
                print("[디버그] '새 카테고리' 노드 찾음")
                return True
        except Exception as e:
            print(f"[경고] 부모 노드 상태 변화 대기 중 오류: {e}")
            return False
            
        print("[경고] '새 카테고리' 노드를 찾을 수 없음")
        return False
            
    except Exception as e:
        print(f"[경고] 하위 카테고리 생성 버튼 클릭 실패: {e}")
        return False

def get_child_names(driver, parent_node, large_name=None, medium_name=None, level='중분류'):
    """
    parent_node 아래의 자식 카테고리 이름 리스트를 반환 (진단용 상세 로그 추가)
    """
    for retry in range(3):
        try:
            # parent_node가 stale이면 재탐색
            try:
                _ = parent_node.is_displayed()
            except StaleElementReferenceException:
                print("[stale] get_child_names: parent_node stale, 재탐색 시도")
                if level == '소분류' and large_name and medium_name:
                    parent_node = find_child_category_node(driver, large_name, medium_name)
                elif level == '중분류' and large_name:
                    parent_node = find_category_node(driver, large_name)
                else:
                    parent_node = find_category_node(driver, parent_node.text.strip())
                if not parent_node:
                    print("[경고] get_child_names: parent_node 재탐색 실패")
                    return []
                time.sleep(0.5)

            # 부모 노드가 보이도록 스크롤
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", parent_node)
            time.sleep(0.5)

            # 부모 노드 클릭하여 확실히 활성화
            driver.execute_script("arguments[0].click();", parent_node)
            time.sleep(0.5)

            # parent_li 찾기
            parent_li = None
            for _ in range(3):
                try:
                    parent_li = parent_node.find_element(By.XPATH, "./ancestor::li[1]")
                    break
                except StaleElementReferenceException:
                    print("[stale] get_child_names: parent_li stale, 재탐색 시도")
                    if level == '소분류' and large_name and medium_name:
                        parent_node = find_child_category_node(driver, large_name, medium_name)
                    elif level == '중분류' and large_name:
                        parent_node = find_category_node(driver, large_name)
                    else:
                        parent_node = find_category_node(driver, parent_node.text.strip())
                    time.sleep(0.5)

            if not parent_li:
                print("[경고] get_child_names: parent_li를 찾을 수 없음")
                return []

            li_class = parent_li.get_attribute('class') or ''
            print(f"[진단] parent_li class: {li_class} (level={level}, parent={parent_node.text.strip()})")

            # ul 찾기
            ul = None
            for _ in range(3):
                try:
                    ul = parent_li.find_element(By.TAG_NAME, "ul")
                    if ul.is_displayed() and 'display: none' not in (ul.get_attribute('style') or ''):
                        break
                except StaleElementReferenceException:
                    print("[stale] get_child_names: ul stale, 재탐색 시도")
                    if level == '소분류' and large_name and medium_name:
                        parent_node = find_child_category_node(driver, large_name, medium_name)
                    elif level == '중분류' and large_name:
                        parent_node = find_category_node(driver, large_name)
                    else:
                        parent_node = find_category_node(driver, parent_node.text.strip())
                    time.sleep(0.5)
                except NoSuchElementException:
                    print(f"[진단] ul 요소가 없습니다. (level={level}, parent={parent_node.text.strip()})")
                    ul = None
                    break

            if not ul:
                print(f"[진단] ul 없음: {parent_node.text.strip()} (level={level}) → 자식 없음으로 간주")
                # 전체 트리에서 동일 이름의 자식이 있는지 한 번 더 robust하게 체크
                # (시즌상품전 특이 현상 진단)
                if large_name and medium_name:
                    print(f"[진단] 전체 트리에서 소분류 탐색: parent={medium_name}")
                    for child in [
                        '봄 디스플레이 추천상품전', '부활절', '5월 카네이션 어버이날',
                        '여름 디스플레이 추천상품전', '가을 디스플레이 추천상품전', '4계절 땡처리 - 원가 이하 판매']:
                        node = find_category_node(driver, child, parent_name=medium_name)
                        print(f"[진단] find_category_node('{child}', parent='{medium_name}') → {'존재' if node else '없음'}")
                return []

            # 자식 노드들 찾기
            child_names = []
            child_anchors = ul.find_elements(By.TAG_NAME, "a")
            for a in child_anchors:
                try:
                    name = a.text.strip()
                    if name:
                        child_names.append(name)
                except StaleElementReferenceException:
                    print("[stale] get_child_names: child anchor stale, 건너뜀")
                    continue
                except Exception as e:
                    print(f"[경고] get_child_names: child anchor 처리 중 오류: {e}")
                    continue
            print(f"[진단] {parent_node.text.strip()}의 자식 노드: {child_names}")
            return child_names
        except Exception as e:
            print(f"[경고] get_child_names 오류 (시도 {retry + 1}/3): {e}")
            time.sleep(0.5)
    print("[경고] get_child_names: 모든 시도 실패")
    return []

def find_new_category_node(driver, parent_node, large_name=None, medium_name=None, level='중분류', timeout=10):
    """
    '새 카테고리' 노드를 찾는 함수
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # 페이지가 완전히 로드될 때까지 대기
            WebDriverWait(driver, 5).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            # parent_node가 stale이면 재탐색
            try:
                _ = parent_node.is_displayed()
            except StaleElementReferenceException:
                print("[stale] find_new_category_node: parent_node stale, 재탐색 시도")
                if level == '소분류' and large_name and medium_name:
                    parent_node = find_child_category_node(driver, large_name, medium_name)
                elif level == '중분류' and large_name:
                    parent_node = find_category_node(driver, large_name)
                else:
                    parent_node = find_category_node(driver, parent_node.text.strip())
                if not parent_node:
                    print("[경고] parent_node 재탐색 실패")
                    time.sleep(0.5)
                    continue
                time.sleep(0.5)

            # 부모 노드가 보이도록 스크롤
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", parent_node)
            time.sleep(0.5)

            # 부모 노드 클릭하여 확실히 활성화
            driver.execute_script("arguments[0].click();", parent_node)
            time.sleep(0.5)

            # parent_li 찾기
            parent_li = None
            for _ in range(3):
                try:
                    parent_li = parent_node.find_element(By.XPATH, "./ancestor::li[1]")
                    break
                except StaleElementReferenceException:
                    print("[stale] find_new_category_node: parent_li stale, 재탐색 시도")
                    if level == '소분류' and large_name and medium_name:
                        parent_node = find_child_category_node(driver, large_name, medium_name)
                    elif level == '중분류' and large_name:
                        parent_node = find_category_node(driver, large_name)
                    else:
                        parent_node = find_category_node(driver, parent_node.text.strip())
                    time.sleep(0.5)

            if not parent_li:
                print("[경고] find_new_category_node: parent_li를 찾을 수 없음")
                time.sleep(0.5)
                continue

            # 여러 방법으로 '새 카테고리' 노드 찾기 시도
            new_category = None
            
            # 1. XPath로 직접 찾기 (더 구체적인 선택자 사용)
            try:
                xpath = f"//li[contains(@class, 'node')]//a[contains(text(), '새 카테고리')]"
                new_category = driver.find_element(By.XPATH, xpath)
                if new_category:
                    print("[디버그] XPath로 '새 카테고리' 노드 찾음")
                    return new_category
            except:
                pass

            # 2. CSS 선택자로 찾기 (더 구체적인 선택자 사용)
            try:
                new_category = driver.find_element(By.CSS_SELECTOR, "li.node a[title*='새 카테고리']")
                if new_category:
                    print("[디버그] CSS 선택자로 '새 카테고리' 노드 찾음")
                    return new_category
            except:
                pass

            # 3. JavaScript로 찾기 (DOM API 사용)
            try:
                new_category = driver.execute_script("""
                    var parentId = arguments[0];
                    var parentLi = document.getElementById(parentId);
                    if (parentLi) {
                        // 1. ul 내부에서 찾기
                        var ul = parentLi.querySelector('ul');
                        if (ul) {
                            var newCategory = ul.querySelector('a[title*="새 카테고리"]');
                            if (newCategory) return newCategory;
                        }
                        
                        // 2. 전체 트리에서 찾기
                        var allLinks = document.querySelectorAll('#categoryTree a');
                        for (var i = 0; i < allLinks.length; i++) {
                            if (allLinks[i].textContent.includes('새 카테고리')) {
                                return allLinks[i];
                            }
                        }
                    }
                    return null;
                """, parent_li.get_attribute('id'))
                
                if new_category:
                    print("[디버그] JavaScript로 '새 카테고리' 노드 찾음")
                    return new_category
            except Exception as e:
                print(f"[경고] JavaScript로 '새 카테고리' 노드 찾기 실패: {e}")

            # 4. 부모 노드 아래에서 직접 찾기
            try:
                child_anchors = parent_li.find_elements(By.TAG_NAME, "a")
                for a in child_anchors:
                    if '새 카테고리' in a.text.strip():
                        print("[디버그] 부모 노드 아래에서 '새 카테고리' 노드 찾음")
                        return a
            except:
                pass

            # 5. 전체 트리에서 찾기
            try:
                all_links = driver.find_elements(By.CSS_SELECTOR, "#categoryTree a")
                for link in all_links:
                    if '새 카테고리' in link.text.strip():
                        print("[디버그] 전체 트리에서 '새 카테고리' 노드 찾음")
                        return link
            except:
                pass

            # 페이지 새로고침 후 재시도
            if time.time() - start_time > timeout/2:  # 타임아웃의 절반이 지났을 때
                print("[디버그] 페이지 새로고침 후 '새 카테고리' 노드 찾기 재시도")
                driver.refresh()
                time.sleep(2)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "categoryTree"))
                )
                if parent_node:
                    try:
                        _ = parent_node.is_displayed()
                    except:
                        if level == '소분류' and large_name and medium_name:
                            parent_node = find_child_category_node(driver, large_name, medium_name)
                        elif level == '중분류' and large_name:
                            parent_node = find_category_node(driver, large_name)

            time.sleep(0.5)
            
        except Exception as e:
            print(f"[경고] '새 카테고리' 노드 찾기 중 오류: {e}")
            time.sleep(0.5)
    
    print("[경고] '새 카테고리' 노드를 찾을 수 없음")
    return None

if __name__ == "__main__":
    main() 