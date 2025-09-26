// 메가메뉴 캐시 객체
const megaMenuCache = {};

// 메가메뉴 초기화
function initMegaMenu() {
    // 메가메뉴 컨테이너 생성
    const megaMenuContainer = document.createElement('div');
    megaMenuContainer.className = 'mega-menu';
    
    // 검색창 추가
    const searchBox = document.createElement('div');
    searchBox.className = 'category-search';
    searchBox.innerHTML = '<input type="text" placeholder="카테고리 검색...">';
    megaMenuContainer.appendChild(searchBox);
    
    // 최근 본 카테고리 섹션 추가
    const recentCategories = document.createElement('div');
    recentCategories.className = 'recent-categories';
    recentCategories.innerHTML = '<h4>최근 본 카테고리</h4><ul></ul>';
    megaMenuContainer.appendChild(recentCategories);
    
    // 메가메뉴 컨테이너를 DOM에 추가
    document.querySelector('.gnb_menu_box').appendChild(megaMenuContainer);
    
    // 이벤트 리스너 등록
    setupEventListeners();
    
    // 최근 본 카테고리 로드
    loadRecentCategories();
}

// 이벤트 리스너 설정
function setupEventListeners() {
    // 대분류 메뉴 호버 이벤트
    document.querySelectorAll('.depth0 > li').forEach(item => {
        item.addEventListener('mouseenter', handleMenuHover);
        item.addEventListener('mouseleave', handleMenuLeave);
    });
    
    // 검색 이벤트
    const searchInput = document.querySelector('.category-search input');
    searchInput.addEventListener('input', handleSearch);
    
    // 메가메뉴 영역 호버 이벤트
    const megaMenu = document.querySelector('.mega-menu');
    megaMenu.addEventListener('mouseenter', () => megaMenu.style.display = 'block');
    megaMenu.addEventListener('mouseleave', () => megaMenu.style.display = 'none');
}

// 메뉴 호버 처리
function handleMenuHover(e) {
    const cateCd = e.currentTarget.querySelector('a').href.split('cateCd=')[1];
    showMegaMenu(cateCd);
}

// 메뉴 리브 처리
function handleMenuLeave(e) {
    const megaMenu = document.querySelector('.mega-menu');
    if (!megaMenu.matches(':hover')) {
        megaMenu.style.display = 'none';
    }
}

// 메가메뉴 표시
function showMegaMenu(cateCd) {
    const megaMenu = document.querySelector('.mega-menu');
    
    // 캐시된 메뉴가 없으면 생성
    if (!megaMenuCache[cateCd]) {
        const menuContent = document.querySelector(`.depth0 > li a[href*="cateCd=${cateCd}"]`)
            .closest('li')
            .querySelector('.depth1')
            .cloneNode(true);
        megaMenuCache[cateCd] = menuContent;
    }
    
    // 메뉴 내용 업데이트
    const menuContainer = megaMenu.querySelector('.depth1') || document.createElement('ul');
    menuContainer.className = 'depth1';
    menuContainer.innerHTML = megaMenuCache[cateCd].innerHTML;
    
    if (!megaMenu.querySelector('.depth1')) {
        megaMenu.insertBefore(menuContainer, megaMenu.querySelector('.recent-categories'));
    }
    
    // 메가메뉴 표시
    megaMenu.style.display = 'block';
    
    // 최근 본 카테고리에 추가
    addRecentCategory(cateCd);
}

// 검색 처리
function handleSearch(e) {
    const keyword = e.target.value.toLowerCase();
    const items = document.querySelectorAll('.depth2 > li');
    
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(keyword) ? '' : 'none';
    });
}

// 최근 본 카테고리 추가
function addRecentCategory(cateCd) {
    const recentCategories = JSON.parse(localStorage.getItem('recentCategories') || '[]');
    const categoryName = document.querySelector(`.depth0 > li a[href*="cateCd=${cateCd}"]`).textContent;
    
    // 중복 제거 및 최대 5개 유지
    const newRecent = [
        { cateCd, name: categoryName },
        ...recentCategories.filter(item => item.cateCd !== cateCd)
    ].slice(0, 5);
    
    localStorage.setItem('recentCategories', JSON.stringify(newRecent));
    loadRecentCategories();
}

// 최근 본 카테고리 로드
function loadRecentCategories() {
    const recentCategories = JSON.parse(localStorage.getItem('recentCategories') || '[]');
    const recentList = document.querySelector('.recent-categories ul');
    
    recentList.innerHTML = recentCategories.map(item => `
        <li>
            <a href="../goods/goods_list.php?cateCd=${item.cateCd}">${item.name}</a>
        </li>
    `).join('');
}

// 메가메뉴 HTML 생성 함수
function createMegaMenuHtml(categoryData) {
  let html = '<div class="mega-menu">';
  
  // 최근 본 카테고리 섹션 추가
  html += `
    <div class="recent-categories">
      <h3>최근 본 카테고리</h3>
      <ul></ul>
    </div>
  `;
  
  // 카테고리 데이터로 메뉴 생성
  Object.values(categoryData).forEach(category => {
    if (category.children && category.children.length > 0) {
      html += `
        <div class="mega-column">
          <h2 class="depth1">
            <a href="../goods/goods_list.php?cateCd=${category.cateCd}">${category.cateNm}</a>
          </h2>
          <div class="depth2${!category.children.some(child => child.children) ? ' no-medium' : ''}">
      `;
      
      // 중분류가 없는 경우 소분류를 직접 표시
      if (!category.children.some(child => child.children)) {
        html += '<ul class="depth3">';
        category.children.forEach(child => {
          html += `
            <li>
              <a href="../goods/goods_list.php?cateCd=${child.cateCd}">${child.cateNm}</a>
            </li>
          `;
        });
        html += '</ul>';
      } else {
        // 중분류가 있는 경우 기존 구조 유지
        category.children.forEach(child => {
          html += `
            <div class="depth3">
              <h3><a href="../goods/goods_list.php?cateCd=${child.cateCd}">${child.cateNm}</a></h3>
          `;
          
          if (child.children && child.children.length > 0) {
            html += '<ul class="depth4">';
            child.children.forEach(grandChild => {
              html += `
                <li>
                  <a href="../goods/goods_list.php?cateCd=${grandChild.cateCd}">${grandChild.cateNm}</a>
                </li>
              `;
            });
            html += '</ul>';
          }
          
          html += '</div>';
        });
      }
      
      html += '</div></div>';
    }
  });
  
  html += '</div>';
  return html;
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', initMegaMenu); 