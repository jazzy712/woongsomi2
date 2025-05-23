// static/js/youtube_search.js

document.addEventListener('DOMContentLoaded', () => {
  const btn     = document.getElementById('yt-search-btn');
  const input   = document.getElementById('yt-keyword');
  const results = document.getElementById('video-results');

  // 검색 실행 함수
  function performSearch() {
    const q = input.value.trim();
    if (!q) {
      alert("검색어를 입력하세요");
      return;
    }
    fetch(`/savings/api/videos/?q=${encodeURIComponent(q)}`)
      .then(r => r.json())
      .then(json => {
        results.innerHTML = '';   // 이전 결과 지우기
        (json.items || []).forEach(item => {
          const videoId  = item.id.videoId;
          const title    = item.snippet.title;
          const thumb    = item.snippet.thumbnails.medium.url;
          const date     = item.snippet.publishedAt.split('T')[0];
          const col = document.createElement('div');
          col.className = 'col-md-4';
          col.innerHTML = `
            <div class="card h-100">
              <img src="${thumb}" class="card-img-top" alt="${title}">
              <div class="card-body d-flex flex-column">
                <h5 class="card-title">${title}</h5>
                <p class="card-text text-muted">${date}</p>
                <a href="https://www.youtube.com/watch?v=${videoId}"
                   target="_blank" class="btn btn-primary mt-auto">
                  영상 보기
                </a>
              </div>
            </div>`;
          results.appendChild(col);
        });
      })
      .catch(err => {
        console.error(err);
        alert("동영상 검색 중 오류가 발생했습니다.");
      });
  }

  // 버튼 클릭으로 검색
  btn.addEventListener('click', performSearch);

  // Enter 키로도 검색 실행
  input.addEventListener('keyup', (e) => {
    if (e.key === 'Enter') {
      performSearch();
    }
  });
});
