// static/js/bank_search.js

let map, polyline;
let markers = [], infoWindows = [];
let currentMarker = null, currentInfoWindow = null;

window.onload = () => {
  const sidoSelect  = document.getElementById('sido-select');
  const gugunSelect = document.getElementById('gugun-select');
  const bankSelect  = document.getElementById('bank-select');
  const searchBtn   = document.getElementById('search-btn');
  const listEl      = document.getElementById('bank-list');

  // 1) 지도 초기화 (서울광장 기준)
  map = new kakao.maps.Map(document.getElementById('map'), {
    center: new kakao.maps.LatLng(37.5665, 126.9780),
    level: 4
  });

  // 2) data.json 로 시/도, 은행목록 채우기
  fetch(DATA_JSON_URL)
    .then(res => res.json())
    .then(data => {
      // 시/도 옵션
      data.mapInfo.forEach(region => {
        const opt = document.createElement('option');
        opt.value = region.name;
        opt.textContent = region.name;
        sidoSelect.appendChild(opt);
      });
      // 은행 옵션
      data.bankInfo.forEach(bank => {
        const opt = document.createElement('option');
        opt.value = bank;
        opt.textContent = bank;
        bankSelect.appendChild(opt);
      });

      // 3) 시/도 선택 시 → 구/군/시 활성화 & 채우기
      sidoSelect.addEventListener('change', () => {
        const sel = data.mapInfo.find(r => r.name === sidoSelect.value);
        gugunSelect.disabled = false;
        gugunSelect.innerHTML = '<option value="" disabled selected>구/군/시 선택</option>';
        sel?.countries.forEach(g => {
          const o = document.createElement('option');
          o.value = g;
          o.textContent = g;
          gugunSelect.appendChild(o);
        });
      });

      // 4) 검색 버튼 클릭
      searchBtn.addEventListener('click', () => {
        const sido  = sidoSelect.value;
        const gugun = gugunSelect.value;
        const bank  = bankSelect.value;
        if (!sido || !gugun || !bank) {
          return alert('모든 항목을 선택해주세요.');
        }

        // **이전 결과 완전 초기화**
        clearAll();

        const ps      = new kakao.maps.services.Places();
        const keyword = `${gugun} ${bank}`;
        const bounds  = new kakao.maps.LatLngBounds();

        ps.keywordSearch(keyword, (results, status) => {
          if (status !== kakao.maps.services.Status.OK || !results.length) {
            return alert('검색 결과가 없습니다.');
          }

          // 결과 순회하며 렌더링
          results.forEach(place => {
            const pos = new kakao.maps.LatLng(place.y, place.x);

            // 마커
            const marker = new kakao.maps.Marker({ map, position: pos });
            markers.push(marker);
            bounds.extend(pos);

            // 인포윈도우
            const iw = new kakao.maps.InfoWindow({
              content: `<div style="padding:8px;">
                          <strong>${place.place_name}</strong><br/>
                          ${place.address_name}<br/>
                          ${place.phone || '연락처 정보 없음'}<br/>
                          <small>클릭하여 경로보기</small>
                        </div>`
            });
            infoWindows.push(iw);

            // 토글 클릭 핸들러
            kakao.maps.event.addListener(marker, 'click', () => {
              if (currentMarker === marker) {
                // 같은 마커 두번 클릭: 닫기
                if (currentInfoWindow) {
                  currentInfoWindow.close();
                  currentInfoWindow = null;
                  currentMarker = null;
                }
                if (polyline) {
                  polyline.setMap(null);
                  polyline = null;
                }
              } else {
                // 다른 마커 클릭: 이전 닫고 열기
                infoWindows.forEach(i => i.close());
                if (polyline) {
                  polyline.setMap(null);
                  polyline = null;
                }
                iw.open(map, marker);
                currentInfoWindow = iw;
                currentMarker = marker;
                drawRoute(pos);
              }
            });

            // 리스트 아이템
            const li = document.createElement('li');
            li.className = 'list-group-item';
            li.style.cursor = 'pointer';
            li.innerHTML = `<strong>${place.place_name}</strong><br/>${place.address_name}`;
            li.addEventListener('click', () => {
              map.setCenter(pos);
              kakao.maps.event.trigger(marker, 'click');
            });
            listEl.appendChild(li);
          });

          map.setBounds(bounds);
        });
      });
    })
    .catch(err => console.error('data.json 로딩 실패', err));
};

// 이전 마커·인포윈도우·폴리라인·목록 전부 지우는 함수
function clearAll() {
  markers.forEach(m => m.setMap(null));
  markers = [];

  infoWindows.forEach(i => i.close());
  infoWindows = [];

  if (polyline) {
    polyline.setMap(null);
    polyline = null;
  }

  const listEl = document.getElementById('bank-list');
  listEl.innerHTML = '';
}

// Kakao RoutingService 로 도보 경로 그리기
function drawRoute(destination) {
  if (polyline) {
    polyline.setMap(null);
    polyline = null;
  }

  new kakao.maps.services.RoutingService().route({
    origin: map.getCenter(),
    destination,
    travelMode: kakao.maps.services.TravelMode.WALKING
  }, (res, status) => {
    if (status === kakao.maps.services.Status.OK) {
      const path = res.routes[0].path.map(p => new kakao.maps.LatLng(p.y, p.x));
      polyline = new kakao.maps.Polyline({
        map,
        path,
        strokeWeight: 4,
        strokeColor: '#007aff',
        strokeOpacity: 0.9,
        strokeStyle: 'solid'
      });
      const bounds = new kakao.maps.LatLngBounds();
      path.forEach(pt => bounds.extend(pt));
      map.setBounds(bounds);
    }
  });
}
