// static/js/bank_search.js

document.addEventListener('DOMContentLoaded', () => {
  const geocoder       = new kakao.maps.services.Geocoder();
  const mapDiv         = document.getElementById('map');
  const inputEl        = document.getElementById('address');
  const searchBtn      = document.getElementById('search-bank-btn');

  let map, placesService;
  let currentCenter    = null;
  let routeLine        = null;
  let currentInfoWindow= null;
  let currentMarker    = null;

  // 1) 지도 초기화 & PlacesService 생성
  function initMap(center) {
    map = new kakao.maps.Map(mapDiv, {
      center,
      level: 4
    });
    placesService    = new kakao.maps.services.Places(map);
    currentCenter    = center;
  }

  // 2) 페이지 로드 시 기본 지도 띄우기 (서울광장 중심)
  const defaultCenter = new kakao.maps.LatLng(37.5665, 126.9780);
  initMap(defaultCenter);

  // 이하 기존 searchBanks(), drawRoute() 등 그대로…
  function drawRoute(destination) {
    if (!currentCenter) return;
    if (routeLine) routeLine.setMap(null);

    kakao.maps.services.RoutingService.route({
      origin:      currentCenter,
      destination: destination,
      travelMode:  kakao.maps.services.TravelMode.WALKING
    }, (result, status) => {
      if (status === kakao.maps.services.Status.OK) {
        const coords = result.routes[0].path.map(p =>
          new kakao.maps.LatLng(p.y, p.x)
        );
        routeLine = new kakao.maps.Polyline({
          map,
          path: coords,
          strokeWeight: 5,
          strokeColor:  '#00a8ff',
          strokeOpacity: 0.7,
          strokeStyle: 'solid'
        });
        const bounds = new kakao.maps.LatLngBounds();
        coords.forEach(pt => bounds.extend(pt));
        map.setBounds(bounds);
      }
    });
  }

  function searchBanks(center) {
    initMap(center);

    const options = {
      location: center,
      radius:   5000,
      sort:     kakao.maps.services.SortBy.DISTANCE
    };

    placesService.keywordSearch('은행', (data, status) => {
      if (status !== kakao.maps.services.Status.OK) {
        alert('은행 정보를 불러오지 못했습니다.');
        return;
      }
      const bounds = new kakao.maps.LatLngBounds();
      const listEl = document.getElementById('bank-list');
      listEl.innerHTML = '';

      data.forEach(place => {
        const pos = new kakao.maps.LatLng(place.y, place.x);

        // InfoWindow
        const infoWindow = new kakao.maps.InfoWindow({
          content: `<div style="padding:8px;">
                      <strong>${place.place_name}</strong><br/>
                      ${place.address_name}<br/>
                      ${place.phone || '연락처 정보 없음'}
                    </div>`
        });

        // Marker
        const marker = new kakao.maps.Marker({ map, position: pos });
        kakao.maps.event.addListener(marker, 'click', () => {
          if (currentMarker === marker) {
            currentInfoWindow.close();
            currentInfoWindow = currentMarker = null;
            if (routeLine) routeLine.setMap(null);
          } else {
            if (currentInfoWindow) currentInfoWindow.close();
            infoWindow.open(map, marker);
            currentInfoWindow = infoWindow;
            currentMarker     = marker;
            drawRoute(pos);
          }
        });

        // List item
        const li = document.createElement('li');
        li.className = 'list-group-item';
        li.style.cursor = 'pointer';
        li.innerHTML = `<strong>${place.place_name}</strong><br/>${place.address_name}`;
        li.addEventListener('click', () => {
          map.setCenter(pos);
          kakao.maps.event.trigger(marker, 'click');
        });
        listEl.appendChild(li);

        bounds.extend(pos);
      });

      map.setBounds(bounds);
    }, options);
  }

  // Enter 눌러도 검색
  inputEl.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      e.preventDefault();
      searchBtn.click();
    }
  });

  // 검색 버튼
  searchBtn.addEventListener('click', () => {
    const query = inputEl.value.trim();
    if (!query) {
      alert('주소나 역 이름을 입력해주세요.');
      return;
    }
    geocoder.addressSearch(query, (res, st) => {
      if (st === kakao.maps.services.Status.OK && res.length) {
        const { y, x } = res[0];
        searchBanks(new kakao.maps.LatLng(y, x));
      } else {
        // 역 이름 등 키워드 검색 fallback
        placesService.keywordSearch(query, (places, st2) => {
          if (st2 === kakao.maps.services.Status.OK && places.length) {
            const { y, x } = places[0];
            searchBanks(new kakao.maps.LatLng(y, x));
          } else {
            alert('위치를 찾지 못했습니다.');
          }
        });
      }
    });
  });

});
