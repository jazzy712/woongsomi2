// document.addEventListener('DOMContentLoaded', () => {
//   const btn     = document.getElementById('yt-search-btn');
//   const input   = document.getElementById('yt-keyword');
//   const results = document.getElementById('video-results');
//   const iframe  = document.getElementById('videoIframe');
//   const modalEl = document.getElementById('videoModal');
//   const videoModal = new bootstrap.Modal(modalEl);

//   // 검색 실행 함수
//   function performSearch() {
//     const q = input.value.trim();
//     if (!q) {
//       alert("검색어를 입력하세요");
//       return;
//     }
//     fetch(`/savings/api/videos/?q=${encodeURIComponent(q)}`)
//       .then(r => r.json())
//       .then(json => {
//         results.innerHTML = '';   // 이전 결과 삭제
//         (json.items || []).forEach(item => {
//           const videoId  = item.id.videoId;
//           const title    = item.snippet.title;
//           const thumb    = item.snippet.thumbnails.medium.url;
//           const date     = item.snippet.publishedAt.split('T')[0];
//           const col = document.createElement('div');
//           col.className = 'col-md-4';
//           col.innerHTML = `
//             <div class="card h-100">
//               <img src="${thumb}" class="card-img-top" alt="${title}">
//               <div class="card-body d-flex flex-column">
//                 <h5 class="card-title">${title}</h5>
//                 <p class="card-text text-muted">${date}</p>
//                 <button
//                   class="btn btn-primary mt-auto play-btn"
//                   data-video-id="${videoId}">
//                   영상 보기
//                 </button>
//               </div>
//             </div>`;
//           results.appendChild(col);
//         });
//       })
//       .catch(err => {
//         console.error(err);
//         alert("동영상 검색 중 오류가 발생했습니다.");
//       });
//   }

//   // 플레이 버튼 클릭 → 모달 오픈 & iframe src 설정
//   results.addEventListener('click', (e) => {
//     if (!e.target.classList.contains('play-btn')) return;
//     const videoId = e.target.getAttribute('data-video-id');
//     iframe.src = `https://www.youtube.com/embed/${videoId}?autoplay=1`;
//     videoModal.show();

//     // 모달 닫힐 때 재생 중지
//     modalEl.addEventListener('hidden.bs.modal', () => {
//       iframe.src = '';
//     }, { once: true });
//   });

//   // 검색 버튼 & Enter 키 바인딩
//   btn.addEventListener('click', performSearch);
//   input.addEventListener('keyup', (e) => {
//     if (e.key === 'Enter') performSearch();
//   });
// });

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

    // ← URL을 문자열로 감싸야 합니다!
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

          // ← HTML 전체를 backtick으로 감싸서 템플릿 리터럴로!
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
            </div>
          `;
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

